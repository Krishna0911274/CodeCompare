# We start with a small Linux image that already contains Python.
FROM python:3.12-slim

# Inside the container, /app becomes our project directory.
WORKDIR /app

# Copies your Django dependencies into the container.
COPY requirements.txt .

# Installs Django and your other Python packages.
RUN pip install --no-cache-dir -r requirements.txt

# Copies our CodeCompare project into the container.
COPY . .

# Tells Docker that our Django application uses port 8000.
EXPOSE 8000

# Starts Django when the container starts.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]