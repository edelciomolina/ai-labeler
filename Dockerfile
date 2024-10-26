FROM python:3.12-slim

WORKDIR /app

# Copy the entire project
COPY . .

# Install the package and its dependencies
RUN pip install .

CMD ["python", "-m", "ai_labeler.main"]
