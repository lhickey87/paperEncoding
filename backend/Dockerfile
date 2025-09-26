# Dockerfile for the backend service
FROM python:3.10-slim

WORKDIR /code

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY /db /code/db

COPY /shared_modules /code/shared_modules
COPY ./backend/ . /code/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]