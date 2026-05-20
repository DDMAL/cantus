FROM node:20.18 AS frontend

COPY ./nginx/app/package.json /code/frontend/
RUN npm install -g gulp
WORKDIR /code/frontend

# Download and unzip volpiano fonts file
RUN mkdir -p ../static/fonts
RUN wget http://www.fawe.de/volpiano/volpiano601_web.zip
RUN unzip volpiano601_web.zip
RUN rm volpiano601_web.zip
RUN mv volpiano.woff ../static/fonts/volpiano.woff

# Install front-end dependencies
RUN npm install

# Copy front-end source code and build
COPY ./nginx/app/ /code/frontend/
RUN gulp build --release
RUN mv public/img ../static
RUN mv public/soundfonts ../static

# Install Python dependencies for collectstatic
FROM python:3.12.3 AS python-deps
COPY ./poetry.lock ./pyproject.toml ./app/install-packages.sh /code/
WORKDIR /code
RUN chmod u+x /code/install-packages.sh && /code/install-packages.sh False

# Collect Django static files and bake them into the image
FROM python:3.12.3 AS django-static
COPY --from=python-deps /code/.venv /code/.venv
COPY app/public /code/public
ENV PATH="/code/.venv/bin:$PATH" \
    PYTHONPATH="/code/.venv/lib/python3.12/site-packages/" \
    DJANGO_SETTINGS_MODULE="cantusdata.settings" \
    DJANGO_SECRET_KEY="build-time-placeholder" \
    POSTGRES_DB="dummy" \
    POSTGRES_USER="dummy" \
    POSTGRES_PASSWORD="dummy" \
    DEVELOPMENT="False"
WORKDIR /code/public
RUN python manage.py collectstatic --noinput

# Build final image with nginx
FROM nginx:1.25
COPY ./nginx/nginx.conf /etc/nginx/nginx.conf
COPY --from=frontend /code/static /code/static
COPY --from=django-static /code/static/ /code/static/django/
