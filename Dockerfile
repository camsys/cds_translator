FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your entire Flask app
COPY . .

# Expose port 8080 (Cloud Run standard)
EXPOSE 8080

# Start your Flask app
CMD ["python", "app.py"]