FROM python:3.12-slim

WORKDIR /app

# Install curl and uv
RUN apt-get update && apt-get install -y curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh 

# Copy the entire project
COPY . .

# Install the package and its dependencies
RUN uv pip install .

CMD ["python", "-m", "ai_labeler.main"]
