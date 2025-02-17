FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# # Copy the requirements file and install dependencies
# COPY requirements.txt .

RUN apt-get update && apt-get install -y \
    libgomp1 \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*
    
# Copy the application script
COPY app.py ./
COPY templates/ ./templates
COPY models/ ./models
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask application port
EXPOSE 5010

# Run the Flask application
CMD ["python", "app.py"]
