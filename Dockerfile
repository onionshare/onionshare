FROM python:3-slim-bullseye AS builder

RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get -y install \
    lsb-release apt-transport-https wget pgp && \
  echo "deb [signed-by=/usr/share/keyrings/tor-archive-keyring.gpg] https://deb.torproject.org/torproject.org $(lsb_release -cs) main" >> /etc/apt/sources.list && \
   wget -qO- https://deb.torproject.org/torproject.org/A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89.asc | gpg --dearmor | tee /usr/share/keyrings/tor-archive-keyring.gpg && \
  apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get -y install \
    deb.torproject.org-keyring \
    obfs4proxy \
    tor && \
  apt-get purge -y apt-transport-https wget pgp apt-transport-https lsb-release && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

ADD ./cli /app/
WORKDIR /app
RUN pip3 install --no-cache-dir .

ENTRYPOINT [ "/usr/local/bin/onionshare" ]
