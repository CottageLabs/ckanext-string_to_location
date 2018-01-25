#!/bin/bash

# Install the Build and Test Dependencies
apt-get update
apt-get install -y curl build-essential tcl

# Download and Extract the Source Code
cd /tmp
curl -O http://download.redis.io/redis-stable.tar.gz
tar xzvf redis-stable.tar.gz
cd redis-stable

# Build and Install Redis
make
make test
make install

# Configure Redis
mkdir /etc/redis
cp /tmp/redis-stable/redis.conf /etc/redis
sed -i "s/^supervised no/supervised systemd/" /etc/redis/redis.conf
sed -i "s/^dir \.\//dir \/var\/lib\/redis/" /etc/redis/redis.conf

# Create a Redis service
cat <<-EOF > /etc/systemd/system/redis.service
[Unit]
Description=Redis In-Memory Data Store
After=network.target

[Service]
User=redis
Group=redis
ExecStart=/usr/local/bin/redis-server /etc/redis/redis.conf
ExecStop=/usr/local/bin/redis-cli shutdown
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Create the Redis User, Group and Directories
adduser --system --group --no-create-home redis
mkdir /var/lib/redis
chown redis:redis /var/lib/redis
chmod 770 /var/lib/redis

# Start Redis
systemctl start redis

# Clean
rm -rf /tmp/redis-stable
rm /tmp/redis-stable.tar.gz
