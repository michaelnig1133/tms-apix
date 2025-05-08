# # Use an official Python image as the base
# FROM python:3.11

# # Set environment variables
# ENV PYTHONUNBUFFERED=1 \
#     PIP_NO_CACHE_DIR=off \
#     PIPENV_VENV_IN_PROJECT=1
#     PATH="/usr/local/bin:$PATH"

# # Set the working directory in the container
# WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     libpq-dev gcc curl && \
#     rm -rf /var/lib/apt/lists/*

# # Copy Pipenv files first (to leverage Docker's caching mechanism)
# COPY Pipfile Pipfile.lock /app/

# # Install dependencies via Pipenv
# RUN pip install --upgrade pip && pip install pipenv && pipenv install  --system

# # Copy the entire project
# COPY . /app/

# # Expose the port Django runs on
# EXPOSE 8000

# # Run the application
# CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]









# # Use an official Python image as the base
# FROM python:3.11

# # Set environment variables
# ENV PYTHONUNBUFFERED=1 \
#     PIP_NO_CACHE_DIR=off \
#     PIPENV_VENV_IN_PROJECT=1

# # Set the working directory in the container
# WORKDIR /app

# # Install system dependencies
# RUN apt-get update && apt-get install -y \
#     libpq-dev gcc curl && \
#     rm -rf /var/lib/apt/lists/*

# # Copy Pipenv files first (to leverage Docker's caching mechanism)
# COPY Pipfile Pipfile.lock /app/

# # Install dependencies via Pipenv
# #RUN pip install --upgrade pip && pip install pipenv && pipenv install --deploy --system
# RUN pip install --upgrade pip && pip install pipenv && pipenv lock --clear && pipenv install --deploy --system

# # Copy the entire project
# COPY . /app/

# # Expose the port Django runs on
# EXPOSE 8000

# # Run the application
# CMD ["gunicorn", "tms_backend.wsgi:application", "--bind", "0.0.0.0:8000"]








FROM python:3.11

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIPENV_VENV_IN_PROJECT=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y libpq-dev gcc curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock /app/

RUN pip install --upgrade pip && \
    pip install pipenv && \
    pipenv install --deploy --system

COPY . /app/

EXPOSE 8000

CMD ["gunicorn", "tms_backend.wsgi:application", "--bind", "0.0.0.0:8000"]


