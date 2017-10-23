# Docker image for squash-graphql microservice
FROM python:3.6-slim
LABEL maintainer "afausti@lsst.org"
WORKDIR /opt
COPY . .

# libmysqlclient-dev adds mysql_config which is needed by mysqlclient
# gcc is required to compile mysqlclient and uwsgi
# FIX: sadly there's one dependency in requirements.txt that requires git
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y libmysqlclient-dev gcc git mysql-client netcat

# set --default-timeout if you are annoyed by pypi.python.org time out errors (default is 15s)
RUN pip install --default-timeout=60 --no-cache-dir -r requirements.txt
WORKDIR /opt/squash

RUN groupadd -r uwsgi_grp && useradd -r -g uwsgi_grp uwsgi
RUN chown -R uwsgi:uwsgi_grp /opt/squash
USER uwsgi

EXPOSE 8000
CMD uwsgi uwsgi.ini
