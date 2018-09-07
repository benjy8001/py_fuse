FROM debian:jessie

RUN echo "deb http://deb.debian.org/debian jessie-backports main" >> /etc/apt/sources.list
RUN echo "deb http://deb.debian.org/debian jessie non-free" >> /etc/apt/sources.list

RUN apt-get -y update && apt-get upgrade -y
RUN apt-get install -y python3 python3-dev python3-pip

RUN apt-get install -y vim build-essential kmod fuse config-package-dev apt-utils tree devscripts lintian

RUN mkdir /shared

COPY . /shared/

RUN python3 -m pip install pip setuptools virtualenv --upgrade

RUN mkdir -p /mnt/apps/ && \
    virtualenv -p $(which python3) /mnt/apps/pyfuse && \
    echo "source /mnt/apps/pyfuse/bin/activate" >> /root/.bashrc && \
    /mnt/apps/pyfuse/bin/pip install pip setuptools --upgrade

RUN cd /shared && /mnt/apps/pyfuse/bin/pip install --quiet -r requirements.txt
RUN cd /shared && /mnt/apps/pyfuse/bin/python setup.py develop

COPY etc/init/ /etc/init.d/
COPY etc/systemd/ /etc/systemd/system/
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT /entrypoint.sh

VOLUME ["/shared"]
WORKDIR /shared