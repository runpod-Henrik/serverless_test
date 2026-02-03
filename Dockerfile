FROM python:3.11-slim

RUN apt-get update && apt-get install -y git

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt
RUN chmod +x run.sh

CMD ["./run.sh"]