from flask import Flask, request, jsonify
import pandas as pd
import joblib
import cx_Oracle
import os
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

class DatabaseConfig:
    def __init__(self):
        self.ip = os.getenv('DB_IP')
        self.port = os.getenv('DB_PORT')
        self.sid = os.getenv('DB_SID')
        self.username = os.getenv('DB_USERNAME')  # No defaults!
        self.password = os.getenv('DB_PASSWORD')  # No defaults!
        
        if not all([self.ip, self.port, self.sid, self.username, self.password]):
            raise ValueError("All database credentials must be set in environment variables")

    def get_dsn(self):
        return cx_Oracle.makedsn(self.ip, self.port, self.sid)

# Initialize database configuration
try:
    db_config = DatabaseConfig()
except ValueError as e:
    print(f"Database configuration error: {e}")
    db_config = None

# Load the trained model
try:
    model = joblib.load('model.pkl')
except FileNotFoundError:
    print("Warning: Model file 'model.pkl' not found. Predictions will not work.")
    model = None

def get_db_connection():
    """Establish connection to Oracle database"""
    if not db_config:
        raise ValueError("Database not configured")
    
    dsn = db_config.get_dsn()
    return cx_Oracle.connect(
        user=db_config.username,
        password=db_config.password,
        dsn=dsn
    )

def extract_features_for_hpan(hpan: str) -> Dict[str, Any]:
    """
    Extract features for a given HPAN from the database
    Returns dictionary of features or None if HPAN not found
    """
    if not db_config:
        raise ValueError("Database not configured")
    
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

        # Initialize combined metrics
        combined_features = {
            'total_tx': 0,
            'total_amt': 0.0,
            'unq_acquinstid': set(),
            'avg_days_bn_tx': []
        }
        credit_scores = []

        # Process each card
        for card_data in request_data.get('data', []):
            if not isinstance(card_data, dict):
                continue

            card_number = card_data.get('card_number')
            if not card_number:
                continue

            try:
                hpan = str(card_number)
                features = extract_features_for_hpan(hpan)
                
                if not features:
                    continue  # Skip cards with no transactions

                # Aggregate features
                combined_features['total_tx'] += features['total_tx']
                combined_features['total_amt'] += features['total_amt']
                combined_features['unq_acquinstid'].add(features['unq_acquinstid'])
                combined_features['avg_days_bn_tx'].append(features['avg_days_bn_tx'])

                # Calculate individual score
                if model:
                    input_data = pd.DataFrame([[
                        features['total_tx'],
                        features['total_amt'],
                        features['unq_acquinstid'],
                        features['avg_days_bn_tx']
                    ]], columns=['total_tx', 'total_amt', 'unq_acquinstid', 'avg_days_bn_tx'])
                    
                    credit_score = int(float(model.predict(input_data)[0]))
                    credit_scores.append(credit_score)

            except Exception as e:
                print(f"Error processing card {card_number}: {str(e)}")
                continue

        # Calculate final combined score
        if credit_scores:
            combined_score = int(sum(credit_scores)/len(credit_scores))
            combined_risk = get_risk_level(combined_score)
            
            final_features = {
                'total_tx': combined_features['total_tx'],
                'total_amt': float(combined_features['total_amt']),
                'unq_acquinstid': len(combined_features['unq_acquinstid']),
                'avg_days_bn_tx': float(sum(combined_features['avg_days_bn_tx'])/len(combined_features['avg_days_bn_tx'])) if combined_features['avg_days_bn_tx'] else 0.0
            }
        else:
            combined_score = 0
            combined_risk = "UNKNOWN"
            final_features = {
                'total_tx': 0,
                'total_amt': 0.0,
                'unq_acquinstid': 0,
                'avg_days_bn_tx': 0.0
            }

        # Return only the combined result
        return jsonify({
            'fayda_number': fayda_number,
            'type': 'CREDIT_SCORE',
            'score': combined_score,
            'risk_level': combined_risk,
            'features': final_features,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)