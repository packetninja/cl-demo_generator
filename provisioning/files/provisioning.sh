#!/bin/bash

function error() {
  echo -e "\e[0;33mERROR: Provisioning error running $BASH_COMMAND at line $BASH_LINENO of $(basename $0) \e[0m" >&2
}
# Log all output from this script
exec >/var/log/autoprovision 2>&1
trap error ERR

# Workaround for CM-3812; clean out the apt cache before we run apt-get update
$(rm -f /var/lib/apt/lists/partial/* /var/lib/apt/lists/* 2>/dev/null; true)

# Set URL for autorized_keys file
URL="http://172.30.1.1/authorized_keys"

# Set the correct timezone
echo "Europe/GMT" | sudo tee /etc/timezone
dpkg-reconfigure --frontend noninteractive tzdata

# Pull the authorized_keys file for both root and cumulus account
mkdir -p /root/.ssh
/usr/bin/wget -O /root/.ssh/authorized_keys $URL
mkdir -p /home/cumulus/.ssh
/usr/bin/wget -O /home/cumulus/.ssh/authorized_keys $URL
chown -R cumulus:cumulus /home/cumulus/.ssh

# Append the Debian repository to sources.list
echo "deb http://http.debian.net/debian wheezy main" >> /etc/apt/sources.list
echo "deb http://http.debian.net/debian wheezy-updates main" >> /etc/apt/sources.list
echo "deb http://security.debian.org/ wheezy/updates main" >> /etc/apt/sources.list

# Update and install packages
apt-get update -y
apt-get upgrade -y
apt-get install python-apt -y
apt-get install netshow -y

# Optionally you can for example license the switch based on the hostname
# Uncomment the below lines to use
#/usr/bin/wget -O /etc/cumulus/license.txt http://192.0.2.251/$HOSTNAME.lic
#/usr/cumulus/bin/cl-license -i /etc/cumulus/license.txt

# Below lines MUST be present!
#CUMULUS-AUTOPROVISIONING
exit 0
