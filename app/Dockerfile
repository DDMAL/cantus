# syntax=docker/dockerfile:1
# Download and install python dependencies in a container
FROM python:3.12.3 AS dependency-install-container
ARG DEVELOPMENT
COPY ./poetry.lock ./pyproject.toml ./app/install-packages.sh /code/
WORKDIR /code
RUN chmod u+x /code/install-packages.sh && \
    /code/install-packages.sh $DEVELOPMENT

FROM python:3.12.3
COPY app/django-config.sh app/celery-worker.sh app/gunicorn.conf.py /code/
COPY app/cantus-staticpages/ /code/cantus-staticpages/
COPY app/production-mei-files/ /code/production-mei-files/
EXPOSE 8001

RUN chmod u+x /code/django-config.sh /code/celery-worker.sh
COPY app/public /code/public
# Copy environment dependencies, but not poetry, to the django container
COPY --from=dependency-install-container /code/.venv /code/.venv
# Add our python environment binaries and package files to the path
ENV PATH="$PATH:/code/.venv/bin/" \
    PYTHONPATH="/code/.venv/lib/python3.12/site-packages/" \
    DJANGO_SETTINGS_MODULE="cantusdata.settings"

# The commit built, reported by the cantus_build_info metric. Declared last so
# that a new commit does not invalidate the layers above.
ARG GIT_SHA
ENV CANTUS_GIT_SHA=$GIT_SHA

WORKDIR /code/public