# Docker image for squash-api microservice
FROM python:3.6-slim
LABEL maintainer "afausti@lsst.org"
WORKDIR /opt
COPY . .

# libmysqlclient-dev adds mysql_config which is needed by mysqlclient
# gcc is required to compile mysqlclient
# FIX: saddly there's one dependency in requirements.txt that requires git
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y libmysqlclient-dev gcc git

RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /opt/squash
# by default django listens to the (container) localhost, but since we are forwarding port 8000 to
# the external host we have to make it listen to all interfaces
# --noreload is needed so that kubernets can control the pod and thus the service initialization
EXPOSE 8000
CMD  python manage.py runserver 0.0.0.0:8000 --noreload




