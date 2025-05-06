# Use an official Python image as the base
FROM python:3.11

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIPENV_VENV_IN_PROJECT=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl && \
    rm -rf /var/lib/apt/lists/*

# Copy Pipenv files first (to leverage Docker's caching mechanism)
COPY Pipfile Pipfile.lock /app/

# Install dependencies via Pipenv
RUN pip install --upgrade pip && pip install pipenv && pipenv install  --system

# Copy the entire project
COPY . /app/

# Expose the port Django runs on
EXPOSE 8000

# Run the application
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]
