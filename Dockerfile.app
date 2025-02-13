<<<<<<< HEAD
FROM python:3.9

WORKDIR /EGT309prj/EGT309prj

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS app
COPY app.py .
CMD ["python", "app.py"]
=======
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# # Copy the requirements file and install dependencies
# COPY requirements.txt .

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
>>>>>>> 30478c28181ecd8f4db97d1d341a585d46d710d1
