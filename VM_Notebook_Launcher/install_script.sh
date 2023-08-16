#!/usr/bin/env bash

# Copyright 2019, Institute for Systems Biology
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


source ./setEnvVars.sh

sudo apt-get update

#
# Do not use pip3 to upgrade pip. Does not play well with Debian pip
#

sudo apt-get install -y python3-pip

#
# We want venv support for notebooks:
#

sudo apt-get install -y python3-venv

#
# For idle monitoring, we need tcpdump and multilog
#

sudo apt-get install -y tcpdump

sudo apt-get install -y daemontools

#
# For monitoring, we use pandas:
#

python3 -m pip install pandas

#
# Get jupyter installed:
#

python3 -m pip install jupyter

#
# Was seeing issues on first install (early 2019), these fixed problems. Are they still needed?
#

python3 -m pip install --upgrade --user nbconvert

python3 -m pip install --upgrade --user tornado==5.1.1

#
# Get ready for certs:
#

mkdir .jupyter

#
# Generate self-signed cert on the VM:
#

CERT_SUBJ=`cat certSubj.txt`
rm certSubj.txt
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -subj "${CERT_SUBJ}" -keyout ~/.jupyter/mykey.key -out ~/.jupyter/mycert.pem

#
# Get the password from the file we created on the desktop:
#

PASSWD=`cat passhash.txt`
rm passhash.txt

#
# Get config set up for remote access:
#

~/.local/bin/jupyter notebook --generate-config

cat >> ~/.jupyter/jupyter_notebook_config.py <<END_OF_CONFIG
c = get_config()
c.NotebookApp.ip = '*'
c.NotebookApp.open_browser = False
c.NotebookApp.port = ${SERV_PORT}
c.NotebookApp.allow_origin = '*'
c.NotebookApp.allow_remote_access = True
c.NotebookApp.certfile = u"${HOME}/.jupyter/mycert.pem"
c.NotebookApp.keyfile = u"${HOME}/.jupyter/mykey.key"
c.NotebookApp.password = u"${PASSWD}"
END_OF_CONFIG

#
# Get the virtual environment installed:
#

cd ~
for i in $(seq 1 5); do
  python3 -m venv virtualEnv${i}
  source virtualEnv${i}/bin/activate
  pip install ipykernel
  python -m ipykernel install --user --name=virtualEnv${i}
  deactivate
done


#
# Build directories, move scripts into place:
#

mkdir ${HOME}/log
mkdir ${HOME}/bin
mkdir ${HOME}/idlelogs

chmod u+x cpuLogger.sh
chmod u+x idle_log_wrapper.sh
chmod u+x ishutdown_wrapper.sh

mv cpuLogger.sh ${HOME}/bin
mv idle_checker.py ${HOME}/bin
mv idle_log_wrapper.sh ${HOME}/bin
mv idle_shutdown.py ${HOME}/bin
mv shutdown_wrapper.sh ${HOME}/bin
mv setEnvVars.sh ${HOME}/bin

#
# Supervisor. Apparently, the apt-get gets us the system init.d install, while we
# need to do the pip upgrade to get ourselves to 3.3.1:
#

sudo apt-get install -y supervisor
sudo python3 -m pip install --upgrade supervisor


# Daemon to run notebook server

cat >> ${HOME}/notebook.conf <<END_OF_SUPER
[program:notebooks]
directory=${HOME}
command=${HOME}/.local/bin/jupyter notebook
autostart=true
autorestart=true
user=${USER}
stopasgroup=true
stderr_logfile=${HOME}/log/notebook-err.log
stdout_logfile=${HOME}/log/notebook-out.log
END_OF_SUPER

# Daemon to log VM activity stats

cat >> ${HOME}/idlelog.conf <<END_OF_SUPER_IDLELOG
[program:idlelog]
directory=${HOME}
command=${HOME}/bin/idle_log_wrapper.sh
autostart=true
autorestart=true
user=${USER}
stopasgroup=true
stderr_logfile=${HOME}/log/idlelog-err.log
stdout_logfile=${HOME}/log/idlelog-out.log
END_OF_SUPER_IDLELOG

# Daemon to shutdown idle machine

cat >> ${HOME}/idleshut.conf <<END_OF_SUPER_SHUTDOWN
[program:idleshut]
directory=${HOME}
command=${HOME}/bin/shutdown_wrapper.sh
autostart=true
autorestart=true
user=${USER}
stopasgroup=true
stderr_logfile=${HOME}/log/shutdownlog-err.log
stdout_logfile=${HOME}/log/shutdownlog-out.log
END_OF_SUPER_SHUTDOWN

#
# Supervisor config files:
#

sudo mv ${HOME}/notebook.conf /etc/supervisor/conf.d/
sudo mv ${HOME}/idlelog.conf /etc/supervisor/conf.d/
sudo mv ${HOME}/idleshut.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
