
FROM python:3.9-slim

WORKDIR /app

COPY ./frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY db /app/db

COPY shared_modules/ /app/

COPY ./frontend/. /app/


CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]