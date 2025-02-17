FROM python:3.9-slim

WORKDIR /src/data_input

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/data_input.py .
COPY requirements.txt ./

EXPOSE 5000

CMD ["python", "data_input.py"]