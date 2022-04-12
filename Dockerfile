# syntax=docker/dockerfile:1
FROM ubuntu:18.04
ENV HOMEUSER=ubuntu
ENV DEBIAN_FRONTEND=noninteractive
COPY . /home/${HOMEUSER}
WORKDIR /home/${HOMEUSER}
RUN apt-get update && apt-get install -y \
    build-essential \
    libjpeg8-dev \
    libpq-dev \
    libxslt-dev \
    libxslt1-dev \
    openjdk-8-jdk \
    postgresql \
    postgresql-contrib \
    python3-dev \
    python3-venv \
    python3-pip \
    software-properties-common \
    zlib1g-dev
RUN add-apt-repository ppa:openjdk-r/ppa && \
    apt-get update && \
    apt-get install -y openjdk-8-jdk
USER postgres
RUN psql -c "create user cantus_admin with encrypted password 'Pl4c3H0ld3r';"
RUN psql -c "alter user cantus_admin with SUPERUSER;"
RUN psql -c "create database cantus_db with owner cantus_admin;"
USER root
RUN chmod +x etc/provision/setup-*
RUN etc/provision/setup-variables.sh
RUN etc/provision/setup-privileged.sh
USER ubuntu
RUN etc/provision/setup-unprivileged.sh
USER root
RUN etc/provision/setup-systemd.sh
EXPOSE 80
EXPOSE 8983
CMD ["bash"]

