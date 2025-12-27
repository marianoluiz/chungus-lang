# Use Python 3.12 slim image
FROM python:3.12.3-alpine


# Set working directory inside container
WORKDIR /app


# Copy only requirement files first (for caching)
COPY requirements.txt requirements-dev.txt /app/


# Install dependencies (cache-friendly)
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt


# Copy the rest of your project code
COPY . /app


# Default entrypoint to run any module
CMD ["python", "-m"]
