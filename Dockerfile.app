FROM python:3.9

WORKDIR /EGT309prj/EGT309prj

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS app
COPY app.py .
CMD ["python", "app.py"]