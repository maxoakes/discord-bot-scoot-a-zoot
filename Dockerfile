FROM python:3.12.8-bookworm
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN apt-get update -qq && apt-get install ffmpeg -y
EXPOSE 8000

# Specify the command to run when the container starts
CMD ["python", "main.py", "trmq", "!", "true"] 