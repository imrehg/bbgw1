FROM resin/beaglebone-green-wifi-alpine-python:3.5

MAINTAINER Gergely Imreh <gergely@resin.io>

ENV INITSYSTEM on

# Defines our working directory in container
WORKDIR /usr/src/app

# Add dependencies
RUN apk add \
     git \
     build-base \
     i2c-tools \
     linux-headers \
    --no-cache --allow-untrusted \
    --repository http://dl-3.alpinelinux.org/alpine/edge/testing/

# Copy requirements.txt first for better cache on later pushes
COPY ./requirements.txt /requirements.txt

# pip install python deps from requirements.txt on the resin.io build server
# Need to upgrade setuptools, and that might have some spurious errors on upgrage
RUN pip install -U setuptools || pip install -U setuptools
RUN pip install -r /requirements.txt

# This will copy all files in our root to the working  directory in the container
COPY . ./

# main.py will run when container starts up on the device
CMD ["/usr/local/bin/python", "src/station.py"]
