FROM ubuntu:precise
MAINTAINER POK DevOps <pok@polimi.it>
ENV COLUMN_TO_PRESERVE=""
ENV COURSE_DIR="/course"
ENV COURSE_CSV="indice.csv"
ENV DROPBOX_ACCESS_TOKEN=""
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update -y
RUN apt-get install build-essential git python-apt python-pip python-six python-setuptools python-beautifulsoup libfreetype6 python-dev libxml2-dev libxslt1-dev libxml2-utils -y

COPY csv2edx /csv2edx
COPY . /
RUN pip install -U pip path.py
RUN python setup.py install

RUN mkdir -p "$COURSE_DIR"
RUN mkdir -p "$COURSE_DIR/src"
WORKDIR $COURSE_DIR/src
CMD csv2edx -v -p -c $COLUMN_TO_PRESERVE -d $COURSE_DIR $COURSE_CSV
