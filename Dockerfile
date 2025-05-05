FROM python:3.11-slim

# Create app directory
WORKDIR /app

# Copy code
COPY app /app

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
