# Standardized container to track and development enviroment
FROM ubuntu
ENV DOCKER=true
ENV TZ=America/Toronto
ENV DISPLAY=:99
ENV DEBIAN_FRONTEND=noninteractive
RUN mkdir /workspace /workspace/logs/
WORKDIR /workspace
COPY /requirements.txt /workspace/requirements.txt
RUN apt-get -y update \
    && apt-get -y install python3 python3-pip \
    && ln -s /usr/bin/python3 /usr/bin/python \
    && ln -s /usr/bin/pip3 /usr/bin/pip \
    && apt-get -y update
RUN pip install -r /workspace/requirements.txt && touch /workspace/logs/climbr.log
CMD tail -f /workspace/logs/climbr.log