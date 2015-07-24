> *Warning*: Some of the information here may be out of date or wrong. Use at your own risk! This file is being kept around for context.

There are two servers to be configured for use with nginx: the IIPImage server for the images and the WSGI server for the Django application.

# IIPImage

The IIPImage server uses FastCGI. Its nginx configuration looks something like this:

    upstream iip {
        server unix:/var/run/supervisor/iipserver.sock fail_timeout=0;
    }

    server {
        listen         8001;
        server_name  localhost;
        root /Users/weigao/Documents/development/diva.js/build;

        location /fcgi-bin/iipserver.fcgi{
            fastcgi_pass    iip;
            fastcgi_param   PATH_INFO $fastcgi_script_name;
            fastcgi_param   REQUEST_METHOD $request_method;
            fastcgi_param   QUERY_STRING $query_string;
            fastcgi_param   CONTENT_TYPE $content_type;
            fastcgi_param   CONTENT_LENGTH $content_length;
        }
    }

The [Diva documentation](https://github.com/DDMAL/diva.js/wiki/Installation#setting-up-the-backend-iipimage) has a bit more on that.

There should be a corresponding entry in the supervisor configuration (in somewhere like `/etc/supervisor/conf.d/`) to run the actual server:

    [fcgi-program:iipserver]
    command=/usr/local/share/iipimage/iipsrv.fcgi
    socket=unix:///tmp/%(program_name)s.sock
    user=www-data
    autostart=true
    autorestart=unexpected
    redirect_stderr=true
    redirect_stdout=true
    environment=JPEG_QUALITY='100',MEMCACHED_SERVERS="127.0.0.1:11211",MEMCACHED_TIMEOUT='604800',MAX_LAYERS='4',MAX_CVT='7000'

# Django/WSGI

The basic configuration looks like this:

    upstream cantusdata_server {
      server unix:/tmp/cantusdata.sock fail_timeout=0;
    }
    
    server {
        server_name cantus.simssa.ca;
        client_max_body_size 4G;
    
        access_log /var/log/nginx/cantus-nginx-access.log;
        error_log /var/log/nginx/cantus-nginx-error.log;
    
    
        # iip is defined in the diva configuration.
        location /fcgi-bin/iipsrv.fcgi {
            fastcgi_pass iip;
            fastcgi_param   PATH_INFO $fastcgi_script_name;
            fastcgi_param   REQUEST_METHOD $request_method;
            fastcgi_param   QUERY_STRING $query_string;
            fastcgi_param   CONTENT_TYPE $content_type;
            fastcgi_param   CONTENT_LENGTH $content_length;
        }
    
        location /static/ {
            alias   /srv/webapps/cantus/public/cantusdata-static/;
        }
    
        location /media/ {
            alias   /srv/webapps/cantus/public/cantusdata/media/;
        }
    
        location / {
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header Host $http_host;
            proxy_redirect off;
            # proxy_buffering off;
    
            # FIXME: https://github.com/DDMAL/cantus/issues/223
            if (!-f $request_filename) {
               proxy_pass http://cantusdata_server;
                break;
            }
        }
    }
            
And for supervisor:

    [program:cantus]
    command = /path/to/cantus/public/gunicorn_start.sh
    user = www-data
    stdout_logfile = /path/to/cantus/public/logs/gunicorn_supervisor.log
    redirect_stderr = true
