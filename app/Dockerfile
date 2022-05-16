# syntax=docker/dockerfile:1
FROM python:3.6.9
COPY . /code/
EXPOSE 8001

ENV SECRET_KEY foo

WORKDIR /code/public
RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput