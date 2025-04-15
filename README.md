# Smart-Monitor
This is the codebase for the project Smart Monitor, including the three setup variants:
* Docker compose file
* Automated setup script
* Manual instructions

For the fastest and easiest way, the Docker version is recommended, as it should work out of the box and can be easily edited via the preconfigured volumes.

## Docker Compose
For the ease of use, a docker version of the Smart Monitor was also created. You have to start the docker containers with the given compose file and an example dashboard should be accessible under [http://localhost:3000](http://localhost:3000). In case you are running Windows on the Host and the Dashboard should also be accessible from other machines, you have to open up Port 3000 in the Firewall.
```
git clone https://github.com/captainfips/Smart-Monitor.git
cd Smart-Monitor
docker compose up -d
```
Access to the serial ports has to be configured for each individual setup in this case.
## Automated Script
For Raspberry Pi OS the manual setup process has been baked into a bash script, that sets up everything and enables the systemd service for the grafana server. One only has to start the given ``setup.sh`` script:
```
git clone https://github.com/captainfips/Smart-Monitor.git
cd Smart-Monitor
sudo bash ./setup.sh
```
Superuser rights are required for the SSL certificate folders, because we need to change ownership from root to our user.
## Manual Setup
This is more or less following the tutorials for each package/program and setting up everything manually -> NOT recommended
### Mandatory Software
1. Python 3: [Install Python on Debian-based systems](https://projects.raspberrypi.org/en/projects/generic-python-install-python3#linux)
2. PostgreSQL: [PostgreSQL Setup](https://www.postgresql.org/download/linux/debian/)
3. TimescaleDB: [Install TimescaleDB on Linux](https://docs.timescale.com/self-hosted/latest/install/installation-linux/)
4. Grafana OSS: [Install Grafana on Debian or Ubuntu](https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/)
5. Nginx: [nginx: Linux packages](https://nginx.org/en/linux_packages.html#Debian)
6. ACME.sh: [An ACME Shell script: acme.sh](https://github.com/acmesh-official/acme.sh)

Python is used to run the logging itself and to write the data to the database. Nginx is used as a reverse proxy to the Grafana Upstream server hosted just internally. This enables encrypted traffic and makes later changes to the server routes easier. ACME.sh is a shell based client that issues the used SSL certificates at ZeroSSL for example.
### Configuring the database
When PostgreSQL is installed correctly, the database server should be reachable via:
```
psql -U postgres -h localhost
```
Then each file from ``./database_creation/`` can be run via:
```
\i ./database_creation/database.sql
\i ./database_creation/fronius.sql
\i ./database_creation/iskra.sql
\i ./database_creation/eastron.sql
```
Now the database and three tables, one for each sensor should be visible with ``\d``. The PostgreSQL client can be closed with ``\q``.
### ACME.sh for updating the certificate
For the following steps the domain ``<SSL_DOMAIN>`` and email ``<SSL_EMAIL>`` for verification have to be inserted!
```
cd ~ && git clone --depth 1 https://github.com/acmesh-official/acme.sh.git && cd acme.sh
chmod 700 acme.sh && ./acme.sh --install --nocron
cd ~/.acme.sh && bash acme.sh --register-account -m <SSL_EMAIL>
sudo mkdir /var/www/acme
sudo chown $(whoami):$(whoami) /var/www/acme
sudo mkdir /etc/nginx/ssl
sudo mkdir /etc/nginx/ssl/<SSL_DOMAIN>
sudo chown $(whoami):$(whoami) /etc/nginx/ssl -R
bash $acmeshdir/acme.sh --issue -w /var/www/acme -d <SSL_DOMAIN> --force --log
bash $acmeshdir/acme.sh --install-cert -d <SSL_DOMAIN> \
  --key-file       /etc/nginx/ssl/<SSL_DOMAIN>/key.pem \
  --fullchain-file /etc/nginx/ssl/<SSL_DOMAIN>/cert.pem \
  --reloadcmd     "sudo systemctl force-reload nginx"
```
With a command-line editor like ``nano`` or ``vim`` the cronjob for updating the certificate regularly has to be created:
```
crontab -e
```
And then add this line to run the script on every 6th day of every month at 2:19am:
```
# m h dom mon dow command
19 2 6 * * /home/{user}/.acme.sh/acme.sh --renew -d {domain} --force --debug > /home/{user}/log_acme.txt
```
### Nginx
The ``nginx.conf`` already includes all available files of the folder ``/etc/nginx/sites-enabled/`` so we just need to add the new file ``grafana`` there:
```
sudo cp ./config/grafana /etc/nginx/sites-enables/grafana
sudo systemctl reload nginx.service
```
### Setup Python scripts
Then the ``data_to_database.py`` script has to be started every 30s:
```
* * * * * cd scripts && /home/{user}/scripts/data_to_database_5.py > /dev/null 2>>/home/{user}/log_error.txt
* * * * * cd scripts && sleep 30 && /home/{user}/scripts/data_to_database_5.py > /dev/null 2>>/home/{user}/log_error.txt
```
### Configuring Grafana
The rest of the dashboard configuration can be done in the browser on either ``http://{raspberry_ip}:3000/`` in case the client device is inside the same local area network or via the issued domain: ``https://ortner.ddnss.org/``

## Example Setup
For testing reasons an example panel has been added to the dashboard and a python script generating random numbers for the database is run in a docker container.

### Iskra AM550
For using an Iskra AM550 smartmeter with the Smart-Monitor, the hex-key to decode the received messages has to be inserted into the ``logging/iskra_data_collection.py`` file.