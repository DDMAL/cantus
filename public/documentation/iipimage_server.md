> **Beware ye who enter here.** Keeping this around because there's a small chance it will be useful at some point.

Install IIPImage on the machine (not in a specific virtualenv)

Brew install nginx
pip install supervisor

http://supervisord.org/configuration.html#fcgi-program-x-section-settings

To start or stop nginx
Brew services start(restart/stop) nginx

to start/stop iipserver
supervisorctl
start/stop iipserver

Nginx error log is at /usr/local/var/log/nginx
to check error log : tail -fn0 error.log
Modified the config files:(for details about configuration, see nginx_conf.txt)

/usr/local/etc/nginx/nginx.conf
/usr/local/etc/nginx/sites-enabled/localhost.conf
/usr/local/etc/supervisor/conf.d/iipserver.conf

To check if the iipserver is running, go to
http://localhost:8001/fcgi-bin/iipsrv.fcgi

fcgi-bin/iipserver.fcgi points to 
/usr/local/share/iipimage/iipsrv.fcgi as configured in iipserver.conf

convert the images for DIVA:

for st-gallen, use images in
Gershwin: Shared2/St_Gallen/images(raw)/highres PNG

process.py convert images to tiff then to jpeg2000 using kdu_compress script
Because there is a problem with kdu_compress, we will only use process.py to convert from png to tiff:

python process.py -t tiff /path/to/input-images/ /path/to/output-images/ /path/to/output-data/


Opional info for debug if there are problems with libtool: 
brew libtool
brew uninstall libpng, png, libtiff, imagemagick
brew install libpng jpeg libtiff
brew install (–force) imagemagic

To use kdu, you have to modify the PATH_TO_KDU_COMPRESS in
DIVA_HOME/build/processing/process.py accordingly, in my case, kdu_compress is at
"/usr/bin/kdu_compress"

NOTE: DIVA_HOME is the path to diva.js/

assume we have tiff images, to check if they work with the iipserver.
http://localhost:8001/fcgi-bin/iipserver.fcgi?FIF=path/to/image
in my case:
http://localhost:8001/fcgi-bin/iipserver.fcgi?FIF=/Users/weigao/Documents/development/diva.js/build/demo/images/csg-0390_022.tiff&CVT=JPG
