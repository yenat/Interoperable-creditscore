from flask import Flask, request, jsonify
import pandas as pd
import joblib
import cx_Oracle
import csv
import os
from typing import Dict, List, Any
from datetime import datetime

app = Flask(__name__)

# Database connection details
DB_CONFIG = {
    "ip": "172.27.201.11",
    "port": "1521",
    "sid": "stdsvfe",
    "username": "yenat",
    "password": "yenat_123"
}

# Load the trained model
try:
    model = joblib.load('model.pkl')
except FileNotFoundError:
    print("Warning: Model file 'model.pkl' not found. Predictions will not work.")
    model = None

def get_db_connection():
    """Establish connection to Oracle database"""
    dsn = cx_Oracle.makedsn(DB_CONFIG["ip"], DB_CONFIG["port"], DB_CONFIG["sid"])
    return cx_Oracle.connect(
        user=DB_CONFIG["username"],
        password=DB_CONFIG["password"],
        dsn=dsn
    )

def extract_features_for_hpan(hpan: str) -> Dict[str, Any]:
    """
    Extract features for a given HPAN from the database
    Returns dictionary of features or None if HPAN not found
    """
    connection = get_db_connection()
    cursor = connection.cursor()
    
    try:
        # Query to get all transactions for the given HPAN
        query = """
        SELECT TRANS_TYPE, ACTAMT, ACQINSTID, UDATE 
        FROM svista.curr_trans 
        WHERE HPAN = :hpan
        ORDER BY UDATE
        """
        cursor.execute(query, hpan=hpan)
        transactions = cursor.fetchall()
        
        if not transactions:
            return None
            
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(transactions, columns=['TRANS_TYPE', 'ACTAMT', 'ACQINSTID', 'UDATE'])
        
        # Convert UDATE to datetime
        df['UDATE'] = pd.to_datetime(df['UDATE'], format='%Y%m%d')
        
        # Calculate features
        features = {
            'total_tx': len(df),
            'total_amt': df['ACTAMT'].sum(),
            'unq_acquinstid': df['ACQINSTID'].nunique(),
        }
        
        # Calculate average days between transactions
        if len(df) > 1:
            df = df.sort_values('UDATE')
            time_diffs = df['UDATE'].diff().dt.days.dropna()
            features['avg_days_bn_tx'] = time_diffs.mean()
        else:
            features['avg_days_bn_tx'] = 0
            
        return features
        
    finally:
        cursor.close()
        connection.close()

def get_risk_level(credit_score: float) -> str:
    """Determine risk level based on credit score"""
    if credit_score >= 750:
        return "LOW"
    elif 500 <= credit_score < 750:
        return "MEDIUM"
    else:
        return "HIGH"

@app.route('/predict', methods=['POST'])
def predict() -> Dict[str, Any]:
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({'error': 'No JSON data provided'}), 400

        fayda_number = request_data.get('fayda_number')
        if not fayda_number:
            return jsonify({'error': 'fayda_number is required'}), 400

        results = []
        for card_data in request_data.get('data', []):
            card_number = card_data.get('card_number')
            if not card_number:
                continue

            hpan = card_number  # Assuming card_number is HPAN for testing
            features = extract_features_for_hpan(hpan)
            if not features:
                results.append({
                    'bic': card_data.get('bic'),
                    'account_number': card_data.get('account_number'),
                    'card_number': card_number,
                    'error': 'No transactions found'
                })
                continue

            # Convert NumPy/pandas types to native Python
            features = {
                'total_tx': int(features['total_tx']),
                'total_amt': float(features['total_amt']),
                'unq_acquinstid': int(features['unq_acquinstid']),
                'avg_days_bn_tx': float(features['avg_days_bn_tx'])
            }

            # Create input_data DataFrame for the model
            input_data = pd.DataFrame([[
                features['total_tx'],
                features['total_amt'],
                features['unq_acquinstid'],
                features['avg_days_bn_tx']
            ]], columns=['total_tx', 'total_amt', 'unq_acquinstid', 'avg_days_bn_tx'])

            if model:
                credit_score = float(model.predict(input_data)[0])  # Now input_data is defined
                risk_level = get_risk_level(credit_score)
            else:
                credit_score = 0.0
                risk_level = "UNKNOWN"

            results.append({
                'bic': card_data.get('bic'),
                'account_number': card_data.get('account_number'),
                'card_number': card_number,
                'credit_score': credit_score,
                'risk_level': risk_level,
                'features': features
            })

        return jsonify({
            'fayda_number': fayda_number,
            'type': 'CREDIT_SCORE',
            'results': results,
            'callbackUrl': request_data.get('callbackUrl', '')
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)