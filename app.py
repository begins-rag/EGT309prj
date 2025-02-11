from flask import Flask, request, jsonify, render_template
import pandas as pd
import pickle
import numpy as np
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Configure upload folder and model path
UPLOAD_FOLDER = 'uploads'
MODEL_PATH = 'models/lightgbm_model.pkl'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the model at startup
try:
    with open(MODEL_PATH, 'rb') as model_file:
        model = pickle.load(model_file)
except Exception as e:
    print(f"Error loading model: {str(e)}")
    model = None

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_data(df):
    """
    Preprocess the input data for forecasting.
    """
    try:
        # Create a copy of the dataframe
        forecast_df = df.copy()

        # Store original Resale_Price if it exists
        original_prices = None
        if 'Resale_Price' in forecast_df.columns:
            original_prices = forecast_df['Resale_Price'].values
            forecast_df = forecast_df.drop(columns=['Resale_Price'])

        # Add 1 year to any date-related columns if they exist
        if 'month' in forecast_df.columns:
            forecast_df['month'] = pd.to_datetime(forecast_df['month'], errors='coerce')
            forecast_df['month'] = forecast_df['month'] + pd.DateOffset(years=1)
            forecast_df['month'] = forecast_df['month'].dt.strftime('%Y-%m')

        # Handle missing or invalid data
        forecast_df = forecast_df.dropna()

        return forecast_df, original_prices

    except Exception as e:
        print(f"Error in preprocessing: {str(e)}")
        raise ValueError(f"Error in preprocessing: {str(e)}")

@app.route('/')
def home():
    """Render the home page."""
    return render_template('K8sUI.html')

@app.route('/forecast', methods=['POST'])
def generate_forecast():
    """Generate forecasts based on the uploaded CSV file."""
    if model is None:
        return jsonify({'error': 'Model not loaded'}), 500

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Read the CSV file
            df = pd.read_csv(filepath)

            # Preprocess data for forecasting
            processed_df, original_prices = preprocess_data(df)

            if original_prices is None:
                return jsonify({'error': 'Resale_Price column is missing in the uploaded file'}), 400

            # Generate predictions
            predictions = model.predict(processed_df)

            # Create response dictionary
            result = {
                'average_price': float(np.mean(predictions)),
                'min_price': float(np.min(predictions)),
                'max_price': float(np.max(predictions)),
                'detailed_forecasts': [
                    {
                        'current_price': float(original_prices[i]),
                        'forecasted_price': float(predictions[i])
                    } for i in range(len(predictions))
                ]
            }

            os.remove(filepath)
            return jsonify(result)

        except Exception as e:
            print(f"Error in generate_forecast: {str(e)}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5010)

    #HI