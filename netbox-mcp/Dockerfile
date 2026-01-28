FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install .

# Copy source code
COPY src/ src/

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the server via uvicorn (executing the main function indirectly via python or direct uvicorn)
# Since we define main() calling uvicorn.run, we can just run the script.
CMD ["python", "src/server.py"]
