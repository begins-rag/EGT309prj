from flask import Flask, request, render_template, jsonify
import requests

app = Flask(__name__)

# Render an HTML form for file upload
@app.route('/')
def upload_form():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>File Upload</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            text-align: center;
        }
        .container {
            width: 100%;
            max-width: 1200px;  /* Doubled size */
            background: white;
            padding: 80px;  /* Increased padding */
            box-shadow: 0px 0px 30px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
        }
        h2 {
            font-size: 36px;  /* Bigger heading */
            color: #333;
            margin-bottom: 30px;
        }
        .file-container {
            border: 3px dashed #007bff;
            padding: 30px;
            cursor: pointer;
            border-radius: 12px;
            margin-bottom: 30px;
            height: 200px; /* Bigger file container */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        input[type="file"] {
            display: none;
        }
        label {
            font-size: 24px;
            color: #007bff;
            cursor: pointer;
            font-weight: bold;
        }
        .file-name {
            margin-top: 15px;
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }
        button {
            background-color: #28a745;
            color: white;
            border: none;
            padding: 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 20px;
            width: 100%;
        }
        button:hover {
            background-color: #218838;
        }
        .response {
            margin-top: 30px;
            padding: 20px;
            border-radius: 5px;
            font-size: 18px;
            font-weight: bold;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Upload a File</h2>
        <form id="upload-form">
            <div class="file-container" onclick="document.getElementById('file-input').click();">
                <label for="file-input">Click to Choose a File</label>
                <input type="file" name="file" required id="file-input">
                <div id="file-name" class="file-name">No file selected</div>
            </div>
            <button type="submit">Upload</button>
        </form>
        <div id="response" class="response"></div>
    </div>

    <script>
        const fileInput = document.getElementById('file-input');
        const fileNameDisplay = document.getElementById('file-name');
        const form = document.getElementById('upload-form');
        const responseDiv = document.getElementById('response');

        fileInput.addEventListener('change', function() {
            if (fileInput.files.length > 0) {
                fileNameDisplay.textContent = "Selected file: " + fileInput.files[0].name;
            } else {
                fileNameDisplay.textContent = "No file selected";
            }
        });

        form.addEventListener('submit', async function(event) {
            event.preventDefault();  // Prevent the form from submitting normally
            
            if (fileInput.files.length === 0) {
                responseDiv.innerHTML = "Please select a file.";
                responseDiv.className = "response error";
                return;
            }

            responseDiv.innerHTML = "Uploading...";
            responseDiv.className = "response";

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                
                if (response.ok) {
                    responseDiv.innerHTML = "✅ File uploaded successfully!";
                    responseDiv.className = "response success";
                } else {
                    responseDiv.innerHTML = "❌ Error: " + (result.error || "Unknown error");
                    responseDiv.className = "response error";
                }
            } catch (error) {
                responseDiv.innerHTML = "❌ Failed to upload file";
                responseDiv.className = "response error";
            }
        });
    </script>
</body>
</html>
    '''

# Endpoint to handle file upload and forward the file to the data cleaning service
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']  # Get the uploaded file
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    # Send the file to the data cleaning service via a POST request
    backend_url = 'http://data-cleaning-service:5001/clean-data'  # data_cleaning.py URL
    # backend_url = 'http://localhost:5001/clean-data'  # data_cleaning.py URL
    try:
        response = requests.post(
            backend_url,
            files={'file': (file.filename, file.stream, file.mimetype)}
        )
        # Attempt to parse JSON response
        try:
            backend_response = response.json()
        except requests.exceptions.JSONDecodeError:
            backend_response = {"error": "Backend did not return valid JSON", "response_text": response.text}

        return jsonify({"message": "File sent to backend", "backend_response": backend_response})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Failed to connect to backend", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)