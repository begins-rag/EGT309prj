FROM python:3.7.3-alpine3.9

run mkdir -p /app
WORKDIR /app

COPY .src/requirements.txt /work/requirements.txt
RUN pip install -r requirements.txt

COPY ./src/ /app/