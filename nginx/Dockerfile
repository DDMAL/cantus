FROM node:20.18 AS frontend

COPY ./app/package.json /code/frontend/
RUN npm install -g gulp
WORKDIR /code/frontend

# Download and unzip volpiano fonts file
RUN mkdir -p ../static/fonts
RUN wget http://www.fawe.de/volpiano/volpiano51_web.zip
RUN unzip volpiano51_web.zip
RUN rm volpiano51_web.zip
RUN mv volpiano51_web/volpiano.woff ../static/fonts/volpiano.woff

# Install front-end dependencies
RUN npm install

# Copy front-end source code and build
COPY ./app/ /code/frontend/
RUN gulp build --release
RUN mv public/img ../static
RUN mv public/soundfonts ../static

# Build final image with nginx
FROM nginx:1.25
COPY ./nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend /code/static /code/static
