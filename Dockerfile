FROM python:3.6.6-slim

WORKDIR /app

COPY ./src requirements.txt ./

RUN pip install -r requirements.txt

EXPOSE 8000
CMD sh start.sh 8000