import json
import pandas as pd
import joblib
import requests
from sklearn.model_selection import GridSearchCV
import lightgbm as lgb
from http.server import BaseHTTPRequestHandler, HTTPServer

APP_SERVER_URL = "http://localhost:5010/upload_model"  # URL of the app.py service
CLEAN_SERVER_URL = "http://localhost:5001"  # URL of the app.py service

class ModelTrainingServer(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            # Parse the incoming JSON data
            data = json.loads(post_data)

            # Convert JSON data to DataFrame
            X_train = pd.DataFrame(data['X_train'])
            y_train = pd.Series(data['y_train'])

            print("Data received successfully!")
            print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")

            # ---- LightGBM Hyperparameter Tuning ----
            lgb_model = lgb.LGBMRegressor(random_state=42)
            lgb_param_grid = {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'num_leaves': [31, 50, 70],
                'min_child_samples': [10, 20, 30]
            }

            lgb_grid = GridSearchCV(estimator=lgb_model, param_grid=lgb_param_grid, scoring='neg_root_mean_squared_error', cv=3, verbose=1)
            lgb_grid.fit(X_train, y_train)
            print(f"Best LightGBM Params: {lgb_grid.best_params_}")
            print(f"Best LightGBM RMSE: {-lgb_grid.best_score_:.2f}")

            # Save model temporarily
            model_filename = "C:/Users/User/EGT309prj/EGT309prj/models/lightgbm_model.pkl"
            joblib.dump(lgb_grid.best_estimator_, model_filename)

            # Send model to app.py
            files = {'file': open(model_filename, 'rb')}
            response = requests.post(APP_SERVER_URL, files=files)
            response = requests.post(CLEAN_SERVER_URL, files=files)

            if response.status_code == 200:
                print("Model successfully sent to app.py")
            else:
                print("Failed to send model:", response.text)

            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode())

        except Exception as e:
            # Handle exceptions and send failure response
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

if __name__ == '__main__':
    server_address = ('', 5002)  # Running on port 5002
    httpd = HTTPServer(server_address, ModelTrainingServer)
    print("Model server running on port 5002...")
    httpd.serve_forever()