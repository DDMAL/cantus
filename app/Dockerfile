# syntax=docker/dockerfile:1
FROM python:3.8.17
COPY app/django-config.sh /code/
COPY poetry.lock /code/
COPY pyproject.toml /code/
COPY app/cantus-staticpages/ /code/cantus-staticpages/
EXPOSE 8001

RUN chmod u+x /code/django-config.sh

RUN echo $(tr -dc A-Za-z0-9 </dev/urandom | head -c 64) >> /etc/key.txt

RUN pip install poetry==1.8.2

WORKDIR /code
RUN poetry install

WORKDIR /code/public