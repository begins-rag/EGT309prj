from flask import Flask, request, jsonify, render_template
import pandas as pd
import joblib
import numpy as np
import io
import requests

app = Flask(__name__)

# Store the model in memory (no file system dependency)
model = None

# URL of data_cleaning.py service
DATA_CLEANING_URL = "http://data-cleaning-service:5001/clean-data"

@app.route('/')
def home():
    """Render the homepage."""
    return render_template('K8sUI.html')

@app.route('/upload_model', methods=['POST'])
def upload_model():
    """
    Receive the trained model file from data_modelling.py
    and load it into memory.
    """
    global model

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # Load model into memory from in-memory file
        model = joblib.load(io.BytesIO(file.read()))
        print("✅ Model successfully loaded into memory!")
        return jsonify({'message': 'Model uploaded and loaded successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/check_model', methods=['GET'])
def check_model():
    """
    Check if a model is currently loaded in memory.
    """
    if model is None:
        return jsonify({'model_loaded': False, 'message': 'No model is currently loaded'}), 200
    return jsonify({'model_loaded': True, 'message': 'A model is currently loaded and ready for predictions'}), 200

def preprocess_data(df):
    """
    Preprocess the input data for forecasting.
    """
    try:
        # Create a copy of the dataframe
        forecast_df = df.copy()
        
        # Store original Resale_Price if it exists
        original_price = None
        if 'Resale_Price' in forecast_df.columns:
            original_price = forecast_df['Resale_Price'].copy()
            forecast_df = forecast_df.drop(columns=['Resale_Price'])
            
        # Add 1 year to any date-related columns if they exist
        if 'month' in forecast_df.columns:
            forecast_df['month'] = forecast_df['month'].apply(
                lambda x: (pd.to_datetime(x) + pd.DateOffset(years=1)).strftime('%Y-%m')
            )
            
        return forecast_df, original_price
        
    except Exception as e:
        print(f"⚠ Error in preprocessing: {str(e)}")
        raise Exception(f"Error in preprocessing: {str(e)}")

@app.route('/forecast', methods=['POST'])
def generate_forecast():
    """
    Clean user-uploaded data, preprocess it, then generate a forecast.
    """
    if model is None:
        return jsonify({'error': '⚠ Model not loaded yet. Upload a model first via /upload_model'}), 500

    try:
        # Read the uploaded file
        file = request.files.get('file', None)
        if file:
            raw_df = pd.read_csv(file)
        else:
            return jsonify({'error': 'No file provided for forecasting'}), 400

        # # Step 1: Send raw data to data_cleaning.py
        # print("🔄 Sending raw data for cleaning...")
        # response = requests.post(DATA_CLEANING_URL, data=raw_df.to_csv(index=False), headers={'Content-Type': 'application/json'})
        # print(f"📩 Raw Response from data_cleaning.py: {response.text}")  # 🔥 Debugging
        
        # if response.status_code != 200:
        #     return jsonify({'error': '❌ Error cleaning data', 'details': response.json()}), 500

        # # Step 2: Get cleaned data from response
        # cleaned_data = response.json().get("cleaned_data", [])
        # if not cleaned_data:
        #     return jsonify({'error': 'No cleaned data received'}), 500

        cleaned_df = pd.DataFrame(raw_df)
        print("✅ Received cleaned data for preprocessing and forecasting")

        # Step 3: Preprocess cleaned data
        processed_df, original_prices = preprocess_data(cleaned_df)

        # Step 4: Generate forecast
        predictions = model.predict(processed_df)

        # Step 5: Prepare response
        result = {
            'average_price': float(np.mean(predictions)),
            'min_price': float(np.min(predictions)),
            'max_price': float(np.max(predictions)),
            'detailed_forecasts': [
                {
                    'current_price': float(original_prices.iloc[i]) if original_prices is not None else None,
                    'forecasted_price': float(predictions[i])
                } for i in range(len(predictions))
            ]
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Forecasting Service on Port 5010...")
    app.run(debug=True, host="0.0.0.0", port=5010, threaded=True)