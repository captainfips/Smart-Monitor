#!/bin/bash

# Config Parameters
read -p "Enter database password: " dbpassword
read -p "Enter SSL domain (leave empty to skip): " ssldomain
if [ -n "$ssldomain" ]; then
    read -p "Enter SSL email: " sslemail
fi
echo "Values set:"
echo $dbpassword $ssldomain $sslemail

# Install dependencies, PostgreSQL, TimescaleDB, Grafana, Python
sudo apt install -y curl ca-certificates apt-transport-https software-properties-common wget
sudo install -d /usr/share/postgresql-common/pgdg
sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc
sudo sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
echo "deb https://packagecloud.io/timescale/timescaledb/debian/ $(lsb_release -c -s) main" | sudo tee /etc/apt/sources.list.d/timescaledb.list
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/timescaledb.gpg
sudo mkdir -p /etc/apt/keyrings/
wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
sudo apt update
sudo apt install -y nginx postgresql-17 postgresql-client-17 timescaledb-2-postgresql-17 grafana python3 python3-psycopg2 python3-pycryptodome git
sudo systemctl enable grafana-server.service
sudo systemctl start grafana-server.service

# Tune database and set password for postgres user, then create database
sudo timescaledb-tune --yes
sudo systemctl restart postgresql@17-main.service
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '$dbpassword';"
sudo echo "localhost:5432:*:postgres:$dbpassword" > /home/$(whoami)/.pgpass
sudo chmod 600 /home/$(whoami)/.pgpass # Restrict access
sudo -u postgres psql -f ./database_creation/smart_monitor.sql # Create Database with grafana user

# Config nginx to serve site, API and acme cert site
sudo rm ./nginx/nginx.conf -f
cp ./nginx/nginx.conf.empty ./nginx/nginx.conf
sed -i "s|<ssldomain>|$ssldomain|g" ./nginx/nginx.conf
sudo rm /etc/nginx/nginx.conf -f
sudo cp $(realpath ./nginx/nginx.conf) /etc/nginx/nginx.conf
sudo systemctl restart nginx.service

# ACME.sh for SSL cert
if [ -n "$ssldomain" ]; then
  git clone --depth 1 https://github.com/acmesh-official/acme.sh.git
  acmeshdir=/home/$(whoami)/.acme.sh
  cd acme.sh && chmod 700 acme.sh && ./acme.sh --install --nocron
  cd ..
  rm acme.sh -rf
  bash $acmeshdir/acme.sh --register-account -m $sslemail
  sudo mkdir /var/www/acme
  sudo chown $(whoami):$(whoami) /var/www/acme
  sudo mkdir /etc/nginx/ssl
  sudo mkdir /etc/nginx/ssl/$ssldomain
  sudo chown $(whoami):$(whoami) /etc/nginx/ssl -R
  bash $acmeshdir/acme.sh --issue -w /var/www/acme -d $ssldomain --force --log
  bash $acmeshdir/acme.sh --install-cert -d $ssldomain \
    --key-file       /etc/nginx/ssl/$ssldomain/key.pem \
    --fullchain-file /etc/nginx/ssl/$ssldomain/cert.pem \
    --reloadcmd     "sudo systemctl force-reload nginx"
  (crontab -l ; echo "19 3 3 * * $acmeshdir/acme.sh --renew -d $ssldomain --force > $(realpath .)/acmesh.log") | crontab -
fi

# Add cron jobs for logging and weekly backup
(crontab -l ; echo "* * * * * $(realpath .)/logging/data_to_database.py > /dev/null 2>> $(realpath .)/error.log") | crontab -
(crontab -l ; echo "* * * * * sleep 30 && $(realpath .)/logging/data_to_database.py > /dev/null 2>> $(realpath .)/error.log") | crontab -
(crontab -l ; echo "19 4 * * 1 /usr/bin/bash $(realpath .)/database/create_backup.sh") | crontab -