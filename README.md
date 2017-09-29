# squash-api
SQuaSH API microservice

![SQuaSH API microservice](squash-api.png)

## Requirements

`squash-api` requires the [squash-db](https://github.com/lsst-sqre/squash-api) microservice and the TLS secrets that are installed by the
[`squash-deployment`](https://github.com/lsst-sqre/squash-deployment) tool.

## Kubernetes deployment

Assuming you have kubectl configured to access your GCE cluster, you can deploy `squash-api` using:

```
TAG=latest make deployment
```

### Debugging

You can inspect the deployment using:

```bash
kubectl describe deployment squash-api
```

and the container logs using:
 
``` 
kubectl logs deployment/squash-api nginx
kubectl logs deployment/squash-api api
```

You can open a terminal inside the `api` container with:

``` 
kubectl exec -it <TAB> -c api /bin/bash
```

### Rolling out updates 

Check the update history with:

```
kubectl rollout history deployment squash-api
```

Modify the `squash-api` image and then apply the new configuration for the Kubernetes deployment:

```
# you need to setup the env for Django to collect the static files
virtualenv env -p python3
source env/bin/activate
pip install -r requirements.txt
 
TAG=latest make build push update
```

Check the deployment changes:
```
kubectl describe deployments squash-api
```

### Scaling up the squash-api microservice

Use the `kubectl get replicasets` command to view the current set of replicas, and then the `kubectl scale` command 
to scale up the `squash-api` deployment:

``` 
kubectl scale deployments squash-api --replicas=3
```

or change the `kubernetes/deployment.yaml` configuration file and apply the new configuration:

```
kubectl apply -f kubernetes/deployment.yaml
```

Check the deployment changes:

``` 
kubectl describe deployments squash-api
kubectl get pods
kubectl get replicasets
```

## Development workflow 

For development, you may install the dependencies and set up a local database with test data:

1. Install the software dependencies
```
git clone  https://github.com/lsst-sqre/squash-api.git

cd squash-api

virtualenv env -p python3
source env/bin/activate
pip install -r requirements.txt
```

2. Development database
 
You can install `mariadb 10.1+`, for instance using `brew`:

```
brew install mariadb
mysql.server start
```

then create and initialize the development database

```
mysql -u root -e "DROP DATABASE qadb"
mysql -u root -e "CREATE DATABASE qadb"
 
cd squash
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata test_data
```

3. Run the `squash-api` 

```
export SQUASH_API_DEBUG=True
python manage.py runserver
```

The `squash-api` will run at `http://localhost:8000`. 

### The Django debug toolbar

When you run the `squash-api` with 

```
export SQUASH_API_DEBUG=True
python manage.py runserver
```

you also activate the Django debug toolbar. The Django debug toolbar can be used, among other things, to debug the SQL queries that
are executed when accessing the API.

### The SQuaSH API admin interface

In development mode access the SQuaSH API admin interface at `http://localhost:8000/admin`. 
You need to create a superuser in order to login:
 
```
python manage.py createsuperuser 
```
 

