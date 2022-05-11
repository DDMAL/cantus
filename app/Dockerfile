# syntax=docker/dockerfile:1
FROM python:3.6.9
COPY . ./code/
SHELL ["/bin/bash", "-c"]


# RUN npm install -g gulp

ENV SECRET_KEY foo

WORKDIR /code/
# RUN python -m venv app_env
# RUN source app_env/bin/activate
RUN pip install -r requirements.txt

# WORKDIR /code/cantusdata/frontend
# RUN npm install
# RUN gulp build --release