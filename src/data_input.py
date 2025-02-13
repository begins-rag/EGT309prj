from flask import Flask, request, render_template, jsonify
import requests

app = Flask(__name__)

# Render an HTML form for file upload
@app.route('/')
def upload_form():
    return '''
<!doctype html>
<html>
<body>
    <h2>File Upload</h2>
    <form id="upload-form" enctype="multipart/form-data">
        <input type="file" name="file" required id="file-input">
        <button type="submit">Upload</button>
    </form>

    <div id="response"></div>

    <script>
        const form = document.getElementById('upload-form');
        form.addEventListener('submit', async function(event) {
            event.preventDefault();  // Prevent the form from submitting normally
            const fileInput = document.getElementById('file-input');
            const file = fileInput.files[0];
            
            if (file) {
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();
                    document.getElementById('response').innerHTML = JSON.stringify(result);
                } catch (error) {
                    document.getElementById('response').innerHTML = 'Error uploading file';
                }
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
    backend_url = 'http://localhost:5001/clean-data'  # data_cleaning.py URL
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
    app.run(debug=True,port=5000)