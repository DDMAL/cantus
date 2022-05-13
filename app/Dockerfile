# syntax=docker/dockerfile:1
FROM python:3.6.9
COPY . /code/
EXPOSE 8001

ENV SECRET_KEY foo

RUN curl -fsSL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get install -y nodejs 
RUN npm install -g gulp

WORKDIR /code/public/cantusdata/frontend
RUN npm install
RUN gulp build --release

WORKDIR /code/public
RUN pip install -r requirements.txt