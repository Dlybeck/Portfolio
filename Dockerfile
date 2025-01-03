# Use an official Python image
FROM python:3.12.3-slim

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose the app's port
EXPOSE 8080

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
