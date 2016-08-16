FROM python:3

RUN \
  pip3 install pyinstaller flask stem

ADD . /usr/src/app/
WORKDIR /usr/src/app/

ENTRYPOINT [ "./install/scripts/onionshare" ]
