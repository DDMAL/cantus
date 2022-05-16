FROM node:10 AS frontend
COPY ./public /code/public
RUN npm install -g gulp

WORKDIR /code/public/frontend
RUN npm install
RUN gulp build --release

FROM nginx
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend /code/public/static /code/static
COPY --from=cantus_app /code/public/cantusdata/static /code/static