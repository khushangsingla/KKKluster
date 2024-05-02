FROM python:3.10

RUN apt update && apt upgrade -y

RUN pip install kubernetes psycopg2-binary

COPY . /app
WORKDIR /app
RUN [ "python", "server.py" ]
