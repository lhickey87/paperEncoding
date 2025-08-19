# Dockerfile for the backend service

FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /code

# Copy and install dependencies
# This path is relative to the backend directory
COPY ./backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the shared db module and the backend code
# These paths are relative to the project root (the build context)
COPY db /code/db
COPY ./backend/. /code/

# Command to run the backend application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]