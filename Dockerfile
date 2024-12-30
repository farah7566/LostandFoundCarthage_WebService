# Use the official Python base image from Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 to allow outside access
EXPOSE 5000

# Set environment variables to avoid Python buffering
ENV PYTHONUNBUFFERED=1

# Command to run the Flask app
CMD ["python", "app.py"]
