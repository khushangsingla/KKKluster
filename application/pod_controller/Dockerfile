FROM python:3.10

RUN apt update && apt upgrade -y

RUN pip install kubernetes psycopg2-binary

COPY . /app
RUN mkdir -p /root/.kube
COPY config /root/.kube/config
WORKDIR /app
CMD [ "python", "server.py" ]
