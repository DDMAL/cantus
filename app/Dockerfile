# syntax=docker/dockerfile:1
FROM python:3.6.9
COPY . /code/
EXPOSE 8001

RUN chmod u+x /code/key.sh
RUN chmod u+x /code/django-config.sh
RUN chmod u+x /code/wait-for-it.sh

RUN /code/key.sh

WORKDIR /code/public
RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput