FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY src /app/src
COPY action.yml /app/action.yml

CMD ["python", "-m", "ai_labeler.main"]
