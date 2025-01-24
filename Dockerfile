FROM python:3.14.0a4-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000

# Specify the command to run when the container starts
CMD ["python", "main.py", "trmq", "!", "true"] 