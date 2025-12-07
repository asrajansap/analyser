FROM python:3.10-slim


WORKDIR /app


# Copy only necessary files
COPY app/ ./app/
COPY requirements.txt ./requirements.txt


# Install dependencies
RUN pip install --no-cache-dir -r app/requirements.txt


EXPOSE 8080
