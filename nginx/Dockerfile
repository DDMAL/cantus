FROM nginx
COPY . ./code/
SHELL ["/bin/bash", "-c"]

RUN sed -i "s/HOMEUSER/$HOMEUSER/" /code/nginx.conf
RUN cp /code/nginx.conf /etc/nginx/nginx.conf