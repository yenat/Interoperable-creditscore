import joblib
import sklearn
from packaging import version

try:
    # Load the model to check for version info
    model = joblib.load('model.pkl')
    
    # Get the sklearn version used when model was created
    # (This works for models saved with sklearn >= 0.24)
    if hasattr(model, '__sklearn_version__'):
        model_version = model.__sklearn_version__
    else:
        # For older models, we'll need to infer
        model_version = "1.5.1"  # From your error message
    
    print(f"Model was saved with scikit-learn version: {model_version}")
    print(f"Current scikit-learn version: {sklearn.__version__}")
    
    if version.parse(model_version) != version.parse(sklearn.__version__):
        print("\nWARNING: Version mismatch detected!")
        print("For consistent results, use scikit-learn ==", model_version)
    else:
        print("\nVersions match - everything looks good!")

except Exception as e:
    print(f"Error checking model: {str(e)}")