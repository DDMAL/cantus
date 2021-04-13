
echo "==== Collect the exported environment variables ===="
source /home/$HOMEUSER/.bashrc

echo "==== Writing the service file ===="

GUNICORNSERVICE="[Unit] \
Description=gunicorn daemon \
After=network.target \
\
[Service] \
User=$HOMEUSER \
WorkingDirectory=/home/$HOMEUSER/public \
Environment=SECRET_KEY=$SECRET_KEY \
ExecStart=/home/$HOMEUSER/public/app_env/bin/gunicorn -b localhost:8001 cantusdata.wsgi \
Restart=always \
\
[Install] \
WantedBy=multi-user.target"

echo $GUNICORNSERVICE > /etc/systemd/system/gunicorn.service

echo "==== Initializing the new service ===="
systemctl daemon-reload
systemctl start gunicorn
systemctl enable gunicorn


