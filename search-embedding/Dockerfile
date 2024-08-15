
# Use an Alpine image with Python 3.11
FROM python:3.11-slim

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    gfortran \
    libblas-dev \
    liblapack-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


# Set environment variables
ENV PORT=${PORT}
ENV APP_ENV=${APP_ENV}

ENV DB_HOST=${DB_HOST}
ENV DB_PORT=${DB_PORT}
ENV DB_NAME=${DB_NAME}
ENV DB_USER=${DB_USER}
ENV DB_PASSWORD=${DB_PASSWORD}

ENV HF_API_KEY=${HF_API_KEY}
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .
#COPY .env .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the working directory
COPY . .

# Expose the required port (default to 3000)
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "main.py"]
 