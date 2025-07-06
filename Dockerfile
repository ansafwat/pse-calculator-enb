# Use official Python runtime as base image
  FROM python:3.11-slim

  # Set working directory in container
  WORKDIR /app

  # Install system dependencies (added more for numpy 2.x)
  RUN apt-get update && apt-get install -y \
      gcc \
      g++ \
      gfortran \
      libopenblas-dev \
      liblapack-dev \
      pkg-config \
      && rm -rf /var/lib/apt/lists/*

  # Copy requirements first for better caching
  COPY requirements.txt .

  # Install Python dependencies
  RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
      pip install --no-cache-dir -r requirements.txt

  # Copy all application files
  COPY . .

  # Expose port (Render will set PORT env variable)
  EXPOSE 8080

  # Run the application
  CMD gunicorn --bind 0.0.0.0:$PORT pse_calculator_enbridge:server
