# Use Python base image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy only required files for app.py
COPY app.py ./
COPY templates/ ./templates
COPY models/ ./models
COPY requirements.txt ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask port
EXPOSE 5010

# Run the application
CMD ["python", "app.py"]
