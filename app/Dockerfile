# syntax=docker/dockerfile:1
# Download and install python dependencies in a container
FROM python:3.12.3 as dependency-install-container
ARG DEVELOPMENT
COPY ./poetry.lock ./pyproject.toml ./app/install-packages.sh /code/
WORKDIR /code
RUN chmod u+x /code/install-packages.sh && \
    /code/install-packages.sh $DEVELOPMENT

FROM python:3.12.3
COPY app/django-config.sh /code/
COPY app/cantus-staticpages/ /code/cantus-staticpages/
COPY app/production-mei-files/ /code/production-mei-files/
EXPOSE 8001

RUN chmod u+x /code/django-config.sh
# Copy environment dependencies, but not poetry, to the django container
COPY --from=dependency-install-container /code/.venv /code/.venv
# Add our python environment binaries and package files to the path
ENV PATH="$PATH:/code/.venv/bin/" \
    PYTHONPATH="$PYTHONPATH:/code/.venv/lib/python3.12/site-packages/" \
    DJANGO_SETTINGS_MODULE="cantusdata.settings"

WORKDIR /code/public