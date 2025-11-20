FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies in specific order to avoid conflicts
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch==2.1.2 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir numpy==1.24.3 && \
    pip install --no-cache-dir transformers==4.35.2 && \
    pip install --no-cache-dir sentence-transformers==2.3.1 && \
    pip install --no-cache-dir flask==3.0.0

# Download the model at build time to speed up startup
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code
COPY app.py .

# Expose port 7860 (required by HuggingFace Spaces)
EXPOSE 7860

# Run the application
CMD ["python", "app.py"]
