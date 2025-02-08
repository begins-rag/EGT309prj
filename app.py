from flask import Flask, request, jsonify, render_template
import pandas as pd
import joblib
import numpy as np
import os
from werkzeug.utils import secure_filename
import requests
import time

app = Flask(__name__)

# Configure upload folder and model path
UPLOAD_FOLDER = 'uploads'
MODEL_PATH = 'models/lightgbm_model.pkl'
CLEANED_DATA_PATH = 'C:/Users/User/EGT309prj/EGT309prj/models/cleaned_data.csv'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Wait until the model is generated
# while not os.path.exists(MODEL_PATH):
#     print("Waiting for model to be generated...")
#     time.sleep(5)  # Check every 5 seconds

# Load the trained model
try:
    model = joblib.load(MODEL_PATH)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {str(e)}")
    model = None

@app.route('/load_cleaned_data', methods=['GET'])
def load_cleaned_data():
    """Serve cleaned data to the UI."""
    if not os.path.exists(CLEANED_DATA_PATH):
        return jsonify({'error': 'No cleaned data found'}), 404

    df = pd.read_csv(CLEANED_DATA_PATH)
    return jsonify(df.to_dict(orient='records'))  # Convert DataFrame to JSON list

def preprocess_data(df):
    """
    Preprocess the input data for forecasting.
    """
    try:
        forecast_df = df.copy()

        original_price = None
        if 'Resale_Price' in forecast_df.columns:
            original_price = forecast_df['Resale_Price'].copy()
            forecast_df = forecast_df.drop(columns=['Resale_Price'])

        if 'month' in forecast_df.columns:
            forecast_df['month'] = forecast_df['month'].apply(
                lambda x: (pd.to_datetime(x) + pd.DateOffset(years=1)).strftime('%Y-%m')
            )
            
        return forecast_df, original_price
    except Exception as e:
        print(f"Error in preprocessing: {str(e)}")
        raise Exception(f"Error in preprocessing: {str(e)}")

@app.route('/')
def home():
    """Render the homepage."""
    return render_template('k8sUI.html')

@app.route('/forecast', methods=['POST'])
def generate_forecast():
    """Generate forecast when a CSV file is uploaded or automatically from CLEANED_DATA_PATH."""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500
    
    file = request.files.get('file', None)

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
    else:
        if not os.path.exists(CLEANED_DATA_PATH):
            return jsonify({'error': 'Cleaned data file not found for auto-forecast'}), 500
        filepath = CLEANED_DATA_PATH
    
    try:
        print(f"Reading file: {filepath}")
        df = pd.read_csv(filepath)

        print("Preprocessing data for forecasting")
        processed_df, original_prices = preprocess_data(df)

        print("Generating predictions")
        predictions = model.predict(processed_df)

        print("Calculating average change percentage")
        avg_change_percentage = np.mean((predictions - original_prices) / original_prices * 100)

        result = {
            'average_price': float(np.mean(predictions)),
            'min_price': float(np.min(predictions)),
            'max_price': float(np.max(predictions)),
            'confidence_score': round(95 - abs(avg_change_percentage), 1),
            'detailed_forecasts': [
                {
                    'current_price': float(original_prices[i]),
                    'forecasted_price': float(predictions[i])
                } for i in range(len(predictions))
            ]
        }

        if file:
            os.remove(filepath)

        return jsonify(result)

    except Exception as e:
        print(f"Error in generate_forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/auto_forecast', methods=['POST'])
def auto_forecast():
    """Automatically loads cleaned data, updates UI, and triggers forecast."""
    if not os.path.exists(CLEANED_DATA_PATH):
        return jsonify({'error': 'Cleaned data not found'}), 500

    try:
        df = pd.read_csv(CLEANED_DATA_PATH)
        data_preview = df.to_dict(orient='records')

        # Auto trigger forecast
        forecast_response = requests.post('http://127.0.0.1:5010/forecast')
        forecast_result = forecast_response.json()

        return jsonify({'data_preview': data_preview, 'forecast_result': forecast_result})

    except Exception as e:
        print(f"Error auto-generating forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Forecasting Service on Port 5010...")
    app.run(debug=True, port=5010, threaded=True)
