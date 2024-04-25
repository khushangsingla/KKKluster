FROM python:3.10

RUN apt update && apt upgrade -y
RUN pip install --upgrade pip
RUN pip install flask PyJWT psycopg2 argon2-cffi pynacl
RUN mkdir /app
WORKDIR /app
COPY app.py /app
COPY db.py /app
COPY utils.py /app
COPY templates/ /app/templates

CMD ["python", "app.py"]
