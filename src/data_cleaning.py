import http.server
import socketserver
import json
import pandas as pd
from io import BytesIO
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder
from geopy.geocoders import Nominatim
import requests  # For sending HTTP requests


PORT = 5001
MODEL_SERVER_URL = 'http://data-modelling-service:5002'  # Model training server
APP_SERVER_URL = 'http://app-service:5010/receive_cleaned_data'  # UI (forecasting) server
CHECK_MODEL_URL = 'http://app-service:5010/check_model'  # Endpoint to check if the model exists
# MODEL_SERVER_URL = 'http://localhost:5002'  # Model training server
# APP_SERVER_URL = 'http://localhost:5010/receive_cleaned_data'  # UI (forecasting) server
# CHECK_MODEL_URL = 'http://localhost:5010/check_model'  # Endpoint to check if the model exists

class FileReceiverHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_type = self.headers['Content-Type'] 
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            # Save the file to the local filesystem
            boundary = content_type.split("boundary=")[-1].encode()
            _, file_data = post_data.split(boundary, 1)
            file_content = file_data.split(b"\r\n\r\n", 1)[-1].rsplit(b"\r\n", 1)[0]
            df = pd.read_csv(BytesIO(file_content))  # Read CSV from extracted file content

            print("Columns:", df.columns)
            print(df.head())

            # # 🔹 Check if the model exists in app.py
            # model_exists = False
            # try:
            #     model_check_response = requests.get(CHECK_MODEL_URL)
            #     if model_check_response.status_code == 200:
            #         model_status = model_check_response.json()
            #         model_exists = model_status.get("model_exists", False)
            # except requests.RequestException as e:
            #     print(f"⚠ Warning: Could not check model existence in app.py: {str(e)}")

            # Find duplicate rows
            duplicates = df[df.duplicated(keep=False)]  # keep=False includes all occurrences of duplicates

            # Show the count of duplicate rows
            print("Number of Duplicate Rows:", duplicates.shape[0])

            # Remove all duplicates and keep only unique rows
            df_cleaned = df.drop_duplicates(keep='first')  # Keep the first occurrence of each duplicate

            df_cleaned = df.dropna()

            df = df_cleaned.applymap(lambda x: x.strip() if isinstance(x, str) else x)


            #Standardize Column Names
            df.rename(columns={
                'month': 'Month',
                'town': 'Town',
                'flat_type': 'Flat_Type',
                'block': 'Block',
                'street_name': 'Street_Name',
                'storey_range': 'Storey_Range',
                'floor_area_sqm': 'Floor_Area_SQM',
                'flat_model': 'Flat_Model',
                'lease_commence_date': 'Lease_Commence_Date',
                'remaining_lease': 'Remaining_Lease',
                'resale_price': 'Resale_Price',

            }, inplace=True)

            # Handle invalid 'Month' entries gracefully
            df['Month'] = pd.to_datetime(df['Month'], format='%Y-%m', errors='coerce')  # 'coerce' turns invalid dates into NaT
            df['Floor_Area_SQM'] = df['Floor_Area_SQM'].astype(float)
            df['Flat_Type'] = df['Flat_Type'].str.title()

            def extract_years(lease):
                if isinstance(lease, str) and 'year' in lease:
                    return int(lease.split(' ')[0])  # Extract the years
                return None

            df['Remaining_Years'] = df['Remaining_Lease'].apply(extract_years)


            def average_storey_range(storey):
                if isinstance(storey, str) and "TO" in storey:
                    start, end = map(int, storey.split(" TO "))
                    return (start + end) / 2
                return None

            df['Average_Storey'] = df['Storey_Range'].apply(average_storey_range)

            #### Data Transformation

            df = df.drop(columns=['Storey_Range'])

            for column in df.columns:
                print(f"Unique values for {column}:")
                print(df[column].unique())
                print("\n")

            #Geolocation addition

            # Create new columns for latitude and longitude based on Town
            def get_lat_long(town):
                if town == 'ANG MO KIO':
                    return 1.369115, 103.845436
                if town == 'BEDOK':
                    return 1.32108871564, 103.924684635
                if town == 'BISHAN':
                    return 1.3505524, 103.8488353
                if town == 'BUKIT BATOK':
                    return 1.3490572, 103.7495906
                if town == 'BUKIT MERAH':
                    return 1.2704395, 103.828318403713
                if town == 'BUKIT PANJANG':
                    return 1.3791486, 103.76141301431
                if town == 'BUKIT TIMAH':
                    return 1.3546901, 103.7763724
                if town == 'CENTRAL AREA':
                    return 1.27916853917468, 103.839909387887
                if town == 'CHOA CHU KANG':
                    return 1.3892601, 103.743728
                if town == 'CLEMENTI':
                    return 1.3140256, 103.7624098
                if town == 'GEYLANG':
                    return 1.3181862, 103.8870563
                if town == 'HOUGANG':
                    return 1.3697 , 103.8892
                if town == 'JURONG EAST':
                    return 1.3240 , 103.7373
                if town == 'JURONG WEST':
                    return 1.3400 , 103.7041
                if town == 'KALLANG/WHAMPOA':
                    return 1.3035, 103.8798
                if town == 'MARINE PARADE':
                    return 1.303 , 103.9072
                if town == 'PASIR RIS':
                    return  1.3739,  103.9493
                if town == 'PUNGGOL':
                    return 1.4051,  103.9023
                if town == 'QUEENSTOWN':
                    return 1.2988, 103.804
                if town == 'SEMBAWANG':
                    return  1.4427 , 103.8188
                if town == 'SENGKANG':
                    return 1.3868121, 103.8914433
                if town == 'SERANGOON':
                    return 1.3500 , 103.8667
                if town == 'TAMPINES':
                    return  1.3500, 103.9500
                if town == 'TOA PAYOH':
                    return 1.3354 , 103.8497
                if town == 'WOODLANDS':
                    return 1.436046 , 103.786057
                if town == 'YISHUN':
                    return 1.4294431  , 103.835005
                else:
                    return None, None  # Default value if town is not found

            # Apply function to create the new columns
            df[['Latitude', 'Longitude']] = df['Town'].apply(lambda x: pd.Series(get_lat_long(x)))


            # Label Encoder
            label_encoder = LabelEncoder()
            scaler = StandardScaler()
            # Assuming your dataframe is named 'df'
            # 1. Month: Split into Year, Month, and Date columns
            df['Month'] = pd.to_datetime(df['Month'])

            # Extract year, month, and day
            df['Year'] = df['Month'].dt.year
            df['Month_Num'] = df['Month'].dt.month
            df['Day'] = df['Month'].dt.day

            # Drop the original 'Month' column if you don't need it anymore
            df = df.drop(columns=['Month'])

            # Fit and transform the 'Town' column
            df['Town'] = label_encoder.fit_transform(df['Town'])
            mapping = {index: label for index, label in enumerate(label_encoder.classes_)}
            print("Mapping:", mapping)

            # 3. Flat_Type: One-hot encoding for Flat_Type
            df['Flat_Type'] = label_encoder.fit_transform(df['Flat_Type'])
            print("\n\n")
            mapping = {index: label for index, label in enumerate(label_encoder.classes_)}
            print("Mapping:", mapping)

            # 4. Block: Convert to numeric label encoding        

            # Extract numeric part and handle NaN values by filling with 0 (or another default value)
            df['Block_Num'] = df['Block'].str.extract(r'(\d+)', expand=False).fillna('0').astype(int)

            df['Block_Alpha'] = df['Block'].str.extract(r'([A-Za-z]+)', expand=False).fillna('0')  # Extract alphabets, fill '0' for missing

            # Label encode the alphabetical column
            df['Block_Alpha_Encoded'] = label_encoder.fit_transform(df['Block_Alpha'])

            # Drop the original Block column (optional)
            df.drop('Block', axis=1, inplace=True)
            df.drop('Block_Alpha', axis=1, inplace=True)
            print("\n\n")
            mapping = {index: label for index, label in enumerate(label_encoder.classes_)}
            print("Mapping:", mapping)

            label_encoder = LabelEncoder()
            scaler = StandardScaler()

            # 5. Street_Name: One-hot encoding for Street_Name
            df['Street_Name_Encoded'] = label_encoder.fit_transform(df['Street_Name'])
            df.drop('Street_Name', axis=1, inplace=True)
            print("\n\n")
            mapping = {index: label for index, label in enumerate(label_encoder.classes_)}
            print("Mapping:", mapping)

            # 7. Floor_Area_SQM: Convert to numeric
            df['Floor_Area_SQM'] = pd.to_numeric(df['Floor_Area_SQM'])
            
            df['Floor_Area_SQM_Scaled'] = scaler.fit_transform(df[['Floor_Area_SQM']])

            # 8. Flat_Model: label encoding for Flat_Model
            df['Flat_Model'] = label_encoder.fit_transform(df['Flat_Model'])
            print("\n\n")
            mapping = {index: label for index, label in enumerate(label_encoder.classes_)}
            print("Mapping:", mapping)


            # 10. Remaining_Lease: Extract remaining years and months
            # Extract years from the 'Remaining_Lease' column
            df['Remaining_Lease_Years'] = df['Remaining_Lease'].str.extract(r'(\d+)\s+years').astype(float)

            # Extract months from the 'Remaining_Lease' column (if exists)
            df['Remaining_Lease_Months'] = df['Remaining_Lease'].str.extract(r'(\d+)\s+months').astype(float)

            # Fill missing months with 0
            df['Remaining_Lease_Months'] = df['Remaining_Lease_Months'].fillna(0)

            # Drop the 'Remaining_Lease' column after extraction
            df.drop('Remaining_Lease', axis=1, inplace=True)

            # Ensure both 'Remaining_Lease_Years' and 'Remaining_Lease_Months' columns are numeric and handle NaN values
            df['Remaining_Lease_Years'] = pd.to_numeric(df['Remaining_Lease_Years'], errors='coerce')  # Convert to numeric, invalid parsing will become NaN
            df['Remaining_Lease_Months'] = pd.to_numeric(df['Remaining_Lease_Months'], errors='coerce')

            # Fill NaN values for years and months with suitable values (e.g., 0 for years and 0 for months)
            df['Remaining_Lease_Years'] = df['Remaining_Lease_Years'].fillna(0).astype(int)
            df['Remaining_Lease_Months'] = df['Remaining_Lease_Months'].fillna(0).astype(int)

            # 11. Resale_Price: Convert to numeric (target variable)
            df['Resale_Price'] = df['Resale_Price'].fillna(df['Resale_Price'].mean())  # Example: filling NaN with mean

            # 12. Drop remaining years (if needed)
            df.drop('Remaining_Years', axis=1, inplace=True)

            # 13. **Average_Storey: Convert to numeric
            df['Average_Storey'] = pd.to_numeric(df['Average_Storey'])

            print("✅ Data cleaning completed. Processing next step...")

            X_train = df.drop(columns=['Resale_Price']).to_dict(orient='records')  # Convert DataFrame to JSON-friendly format
            y_train = df['Resale_Price'].tolist()
            payload = json.dumps({"X_train": X_train, "y_train": y_train})
            response = requests.post(MODEL_SERVER_URL, data=payload, headers={'Content-Type': 'application/json'})
            print("✅ Successfully sent cleaned training data to data_modelling.py!")

            # # Send cleaned data to Model Training
            # try:
            #     response = requests.post(MODEL_SERVER_URL, data=payload, headers={'Content-Type': 'application/json'})
            #     if response.status_code == 200:
            #         print("Data sent successfully to model training!")
            #     else:
            #         print(f"Failed to send data to model server: {response.status_code}", response.text)
            # except requests.RequestException as e:
            #     print(f"Error sending data to model server: {str(e)}")

            # 🔹 If model exists, send cleaned data back to app.py
            # if model_exists:
            #     cleaned_data = df.to_dict(orient='records')
            #     payload = json.dumps({"cleaned_data": cleaned_data})
            #     response = requests.post(APP_SERVER_URL, data=payload, headers={'Content-Type': 'application/json'})
            #     response.raise_for_status()
            #     print("✅ Successfully sent cleaned forecasting data back to app.py!")

            # # 🔹 If no model exists, send cleaned data to data_modelling.py
            # else:
            #     # Separate features and target variable
            #     X_train = df.drop(columns=['Resale_Price']).to_dict(orient='records')  # Convert DataFrame to JSON-friendly format
            #     y_train = df['Resale_Price'].tolist()
            #     payload = json.dumps({"X_train": X_train, "y_train": y_train})
            #     response = requests.post(MODEL_SERVER_URL, data=payload, headers={'Content-Type': 'application/json'})
            #     response.raise_for_status()
            #     print("✅ Successfully sent cleaned training data to data_modelling.py!")

            # Success Response
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps({"message": "Data processed and sent successfully"}).encode())
            

        except Exception as e:
            print(f"❌ Error in data cleaning: {str(e)}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), FileReceiverHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()