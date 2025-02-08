import json
import pandas as pd
import os
import joblib
from sklearn.model_selection import GridSearchCV
import lightgbm as lgb
from catboost import CatBoostRegressor
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests

SAVE_PATH = 'C:/Users/User/EGT309prj/EGT309prj/models'  # Save models here
FORECAST_SERVER_URL = "http://localhost:5010/forecast"  # app.py URL

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

            # Save cleaned dataset for forecasting
            cleaned_data_path = os.path.join(SAVE_PATH, "cleaned_data.csv")
            df_cleaned = X_train.copy()
            df_cleaned["Resale_Price"] = y_train  # Add target column back
            df_cleaned.to_csv(cleaned_data_path, index=False)

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

            # # ---- CatBoost Hyperparameter Tuning ----
            # cat_model = CatBoostRegressor(random_state=42, verbose=0)
            # cat_param_grid = {
            #     'iterations': [100, 200, 300],
            #     'learning_rate': [0.01, 0.1, 0.2],
            #     'depth': [3, 5, 7],
            #     'l2_leaf_reg': [1, 3, 5]
            # }

            # cat_grid = GridSearchCV(estimator=cat_model, param_grid=cat_param_grid, scoring='neg_root_mean_squared_error', cv=3, verbose=1)
            # cat_grid.fit(X_train, y_train)
            # print(f"Best CatBoost Params: {cat_grid.best_params_}")
            # print(f"Best CatBoost RMSE: {-cat_grid.best_score_:.2f}")

            # Save the models to the specified path
            lgb_model_path = os.path.join(SAVE_PATH, 'lightgbm_model.pkl')
            # cat_model_path = os.path.join(SAVE_PATH, 'catboost_model.pkl')
            joblib.dump(lgb_grid.best_estimator_, lgb_model_path)
            # joblib.dump(cat_grid.best_estimator_, cat_model_path)
            print(f"Models saved to {SAVE_PATH}")

            # Send a response back to the client
            response = {
                "message": "Training completed successfully!",
                "lightgbm_best_params": lgb_grid.best_params_,
                "lightgbm_rmse": -lgb_grid.best_score_,
                # "catboost_best_params": cat_grid.best_params_,
                # "catboost_rmse": -cat_grid.best_score_,
                "model_paths": {
                    "lightgbm_model": lgb_model_path
                    # "catboost_model": cat_model_path
                }
            }

             # Send data to app.py for forecasting
            send_status = self.send_data_to_forecasting(cleaned_data_path)

            # If forecasting request is successful, return early to stop further processing
            if send_status:
                print("Forecasting request sent successfully. Stopping further processing.")
                return  # Stops execution but keeps the server running

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

    def send_data_to_forecasting(self, file_path):
        """ Send the cleaned data to app.py for forecasting. """
        try:
            with open(file_path, 'rb') as f:
                response = requests.post(FORECAST_SERVER_URL, files={'file': f})
            
            if response.status_code == 200:
                print("Sent cleaned data to app.py for forecasting!")
                print("Response:", response.json())
                return True  # Indicate success

            print(f"Failed to send data to app.py: {response.status_code}, Response: {response.text}")
            return False  # Indicate failure

        except Exception as e:
            print(f"Error sending data to app.py: {str(e)}")
            return False

if __name__ == '__main__':
    server_address = ('', 5002)  # Running on port 5002
    httpd = HTTPServer(server_address, ModelTrainingServer)
    print("Model server running on port 5002...")
    httpd.serve_forever()