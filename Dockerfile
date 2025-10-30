FROM python:3.11-slim

WORKDIR /app

# Copy dependencies list and install
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copy only the inspector package (license server lives here)
COPY inspector /app/inspector

EXPOSE 5000

ENV PYTHONUNBUFFERED=1
ENV LICENSE_USE_GUMROAD=false

CMD ["python", "-m", "inspector.license_server"]
