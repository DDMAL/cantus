FROM eclipse-temurin:17-jre AS jre-base

ENV JAVA_HOME=/opt/java/openjdk
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Install various dependencies:
# - unzip for unpacking the Cantaloupe jars
# - wget for downloading the OpenJPEG + Cantaloupe files
RUN apt-get update && apt-get install -y \
    unzip \
    wget

# Download OpenJPEG binaries and unpack them.
# OpenJPEG is a dependency when we want Cantaloup
# to server jpeg and jpeg2000 images.
RUN mkdir /opt/openjpeg && mkdir /opt/openjpeg/openjpeg-2.5.0
WORKDIR /opt/openjpeg
RUN wget https://github.com/uclouvain/openjpeg/releases/download/v2.5.0/openjpeg-v2.5.0-linux-x86_64.tar.gz && \
    tar -xzf openjpeg-v2.5.0-linux-x86_64.tar.gz && \
    rm openjpeg-v2.5.0-linux-x86_64.tar.gz && \
    mv openjpeg-v2.5.0-linux-x86_64/* openjpeg-2.5.0

# Download Cantaloupe JARs and unpack them:
RUN mkdir /opt/cantaloupe
WORKDIR /opt/cantaloupe
RUN wget https://github.com/cantaloupe-project/cantaloupe/releases/download/v5.0.5/cantaloupe-5.0.5.zip && \
    unzip cantaloupe-5.0.5.zip && \
    rm cantaloupe-5.0.5.zip

COPY ./cantaloupe.properties /etc/cantaloupe/cantaloupe.properties

EXPOSE 8182