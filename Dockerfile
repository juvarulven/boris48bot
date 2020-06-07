FROM python:3.8-slim

RUN pip install --no-cache-dir pytelegrambotapi
RUN pip install --no-cache-dir requests

WORKDIR /usr/src/boris48bot
COPY . .

CMD ["python", "./start.py"]
