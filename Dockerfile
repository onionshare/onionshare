FROM python:3

ADD ./install/requirements.txt /usr/src/app/install/requirements.txt
WORKDIR /usr/src/app/
RUN \
  pip install --no-cache -r ./install/requirements.txt

ADD . /usr/src/app/

ENTRYPOINT [ "./dev_scripts/onionshare" ]
