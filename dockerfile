FROM ubuntu
COPY ./ /workspace
WORKDIR /workspace

# && apt-get -y install python3  python3-pip \
#     && ln -s /usr/bin/python3 /usr/bin/python \
#     && ln -s /usr/bin/pip3 /usr/bin/pip \
#     && apt-get update \