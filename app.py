from flask import Flask, request, jsonify, render_template
import pandas as pd
import joblib
import numpy as np
<<<<<<< HEAD
import os
<<<<<<< HEAD
=======
from werkzeug.utils import secure_filename
import requests
import time
>>>>>>> c0c7b2ef6fdafa9da20ca3d3952a1bf8277537b4

app = Flask(__name__)

# Configure upload folder and model path
UPLOAD_FOLDER = 'uploads'
MODEL_PATH = 'models/lightgbm_model.pkl'
CLEANED_DATA_PATH = 'C:/Users/User/EGT309prj/EGT309prj/models/cleaned_data.csv'
ALLOWED_EXTENSIONS = {'csv'}
=======
import io
import requests

app = Flask(__name__)

# Store the model in memory (no file system dependency)
model = None
>>>>>>> c4184fbebdff3d0c822bd147ad8279616bc1469a

# URL of data_cleaning.py service
DATA_CLEANING_URL = "http://localhost:5001/clean-data"

<<<<<<< HEAD
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

<<<<<<< HEAD
def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
=======
@app.route('/load_cleaned_data', methods=['GET'])
def load_cleaned_data():
    """Serve cleaned data to the UI."""
    if not os.path.exists(CLEANED_DATA_PATH):
        return jsonify({'error': 'No cleaned data found'}), 404

    df = pd.read_csv(CLEANED_DATA_PATH)
    return jsonify(df.to_dict(orient='records'))  # Convert DataFrame to JSON list
>>>>>>> c0c7b2ef6fdafa9da20ca3d3952a1bf8277537b4
=======
@app.route('/')
def home():
    """Render the homepage."""
    return render_template('k8sUI.html')

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
>>>>>>> c4184fbebdff3d0c822bd147ad8279616bc1469a

def preprocess_data(df):
    """
    Preprocess the input data for forecasting.
    """
    try:
        forecast_df = df.copy()
<<<<<<< HEAD

<<<<<<< HEAD
        # Store original Resale_Price if it exists
        original_prices = None
=======
        original_price = None
>>>>>>> c0c7b2ef6fdafa9da20ca3d3952a1bf8277537b4
=======
        
        # Store original Resale_Price if it exists
        original_price = None
>>>>>>> c4184fbebdff3d0c822bd147ad8279616bc1469a
        if 'Resale_Price' in forecast_df.columns:
            original_price = forecast_df['Resale_Price'].copy()
            forecast_df = forecast_df.drop(columns=['Resale_Price'])
<<<<<<< HEAD

<<<<<<< HEAD
        # Add 1 year to any date-related columns if they exist
        if 'month' in forecast_df.columns:
            forecast_df['month'] = pd.to_datetime(forecast_df['month'], errors='coerce')
            forecast_df['month'] = forecast_df['month'] + pd.DateOffset(years=1)
            forecast_df['month'] = forecast_df['month'].dt.strftime('%Y-%m')

        # Handle missing or invalid data
        forecast_df = forecast_df.dropna()

        return forecast_df, original_prices

=======
        if 'month' in forecast_df.columns:
=======
            
        # Add 1 year to any date-related columns if they exist
        if 'month' in forecast_df.columns:
>>>>>>> c4184fbebdff3d0c822bd147ad8279616bc1469a
            forecast_df['month'] = forecast_df['month'].apply(
                lambda x: (pd.to_datetime(x) + pd.DateOffset(years=1)).strftime('%Y-%m')
            )
            
        return forecast_df, original_price
<<<<<<< HEAD
>>>>>>> c0c7b2ef6fdafa9da20ca3d3952a1bf8277537b4
    except Exception as e:
        print(f"Error in preprocessing: {str(e)}")
        raise ValueError(f"Error in preprocessing: {str(e)}")

@app.route('/')
def home():
<<<<<<< HEAD
    """Render the home page."""
    return render_template('K8sUI.html')
=======
        
    except Exception as e:
        print(f"⚠ Error in preprocessing: {str(e)}")
        raise Exception(f"Error in preprocessing: {str(e)}")
>>>>>>> c4184fbebdff3d0c822bd147ad8279616bc1469a

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
<<<<<<< HEAD
    app.run(debug=True, port=5010)
=======
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
>>>>>>> c0c7b2ef6fdafa9da20ca3d3952a1bf8277537b4
=======
    print("🚀 Starting Forecasting Service on Port 5010...")
    app.run(debug=True, port=5010, threaded=True)
>>>>>>> c4184fbebdff3d0c822bd147ad8279616bc1469a
