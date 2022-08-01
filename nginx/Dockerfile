FROM node:10 AS frontend
COPY ./public/node/frontend/package.json /code/frontend/
RUN npm install -g gulp

WORKDIR /code/frontend
RUN npm install
COPY ./public/node/ /code/
RUN wget http://www.fawe.de/volpiano/volpiano51_web.zip
RUN unzip volpiano51_web.zip
RUN rm volpiano51_web.zip
RUN mv volpiano51_web/volpiano.woff ../static/fonts/volpiano.woff
RUN gulp build

FROM python:3.6.9 AS django-static
COPY ./public/python /code

WORKDIR /code
RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput

FROM nginx
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend /code/static /code/static
COPY --from=django-static /code/cantusdata/static /code/static
