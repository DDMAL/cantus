#!/bin/bash
echo "==== Writing the service file ===="
cat <<EOF > /etc/systemd/system/gunicorn.service
[Unit]
Description=gunicorn service for the Cantus Ultimus app
After=network.target

[Service]
User=$HOMEUSER
WorkingDirectory=/home/$HOMEUSER/public
Environment=SECRET_KEY=$SECRET_KEY
ExecStart=/home/$HOMEUSER/public/app_env/bin/gunicorn -b localhost:8001 cantusdata.wsgi --timeout 600
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "==== Initializing the new service ===="
systemctl daemon-reload
systemctl start gunicorn
systemctl enable gunicorn


