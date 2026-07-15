# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.10

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt


ENV PORT 8080


COPY . /app/

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 my_site.wsgi:application