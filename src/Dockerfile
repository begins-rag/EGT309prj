# Step 1: Use an official lightweight Python runtime as a base image
FROM python:3.10-slim

# Step 2: Set the working directory inside the container
WORKDIR /app

# Step 3: Copy the project files into the container
COPY . /app

# Step 4: Install dependencies (Ensure you have a 'requirements.txt' file)
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Expose the port the app runs on (matches the port in data_cleaning.py)
EXPOSE 5001

# Step 6: Define the command to run your Python script
CMD ["python", "data_cleaning.py"]
