# 1. Start with a lightweight Linux machine that already has Python 3.10
FROM python:3.10-slim

# 2. Create a folder inside the container named /app and move inside it
WORKDIR /app

# 3. Copy your inventory list from your laptop into the container
COPY requirements.txt .

# 4. Install FastAPI, Uvicorn, and Psycopg inside the container
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your code (main.py, etc.) into the container
COPY . .

# 6. The exact command to run when the container wakes up
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]