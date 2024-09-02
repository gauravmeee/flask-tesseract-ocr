# Use the official Python image as a base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies, including Tesseract OCR
RUN apt-get update && \
    apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation
RUN tesseract --version && \
    which tesseract && \
    ls -l /usr/bin/tesseract

# Copy the requirements file
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the Tesseract data path environment variable
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

# Expose the port on which the application will run
EXPOSE 10000

# Command to run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]