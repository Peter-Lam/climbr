# Standardized container to track and development enviroment
FROM ubuntu
RUN mkdir /workspace
WORKDIR /workspace
RUN apt-get -y install python3  python3-pip \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && ln -s /usr/bin/pip3 /usr/bin/pip \
    && apt-get update \
    && pip install ./requirements.txt