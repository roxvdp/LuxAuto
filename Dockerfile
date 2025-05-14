# Gebruik een lichte Python-image test
FROM python:3.11-slim

# Werkdirectory binnen de container
WORKDIR /app

# Kopieer requirements en installeer dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer alle bestanden naar de container
COPY . .

# Laad environment variables (optioneel)
ENV PYTHONUNBUFFERED=1

# Start de Flask-app
CMD ["python", "app.py"]
