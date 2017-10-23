# squash-graphql

SQuaSH GraphQL microservice.

# GraphQL sample queries

This implementation uses [graphene-django](http://docs.graphene-python.org/projects/django/en/latest/) to create a GraphQL schema from the django ORM model.
 
List all squash metrics, showing unit and description:

```
{
  metrics {
    metric
    unit
    description
  }
}
```


List the first 5 measurements of each metric on `cfht` dataset:

```
{
  metrics {
    metric
    unit
    description
    measurements(first: 5, job_CiDataset: "cfht") {
      edges {
        node {
          value
        }
      }
    }
  }
}
```

NOTE: `job_CiDataset` looks odd, that's because GraphQL change names to CamelCase and in django ORM we do `job__ci_dataset` to access a field in another table through a foreign key. I think we can improve that.


Using the `__debug` field to output the SQL queries being executed: 

```
{
  metrics {
    metric
    unit
    description
   
  }
  # the __debug field will output the SQL queries
  __debug {
    sql {
      sql
      duration
    }
  }
}
```

A generic query to inspect the GraphQL schema:

```
{
  __schema {
    queryType {
      name
      description
      fields {
        name
        description
        isDeprecated
        deprecationReason
      }
    }
  }
}
```

## Kubernetes deployment

`squash-graphql` requires the [squash-db](https://github.com/lsst-sqre/squash-db) microservice and the TLS secrets that are installed by the
[`squash-deployment`](https://github.com/lsst-sqre/squash-deployment) tool.

Assuming you have kubectl configured to access your GKE cluster, you can deploy `squash-graphql` using:

```
TAG=latest make deployment
```

### Debugging

You can inspect the deployment using:

```bash
kubectl describe deployment squash-graphql
```

and the container logs using:
 
``` 
kubectl logs deployment/squash-graphql nginx
kubectl logs deployment/squash-graphql api
```

You can open a terminal inside the `api` container with:

``` 
kubectl exec -it <TAB> -c api /bin/bash
```

### Rolling out updates 

Check the update history with:

```
kubectl rollout history deployment squash-graphql
```

Modify the `squash-graphql` image and then apply the new configuration for the Kubernetes deployment:

```
# you need to setup the env for Django to collect the static files
virtualenv env -p python3
source env/bin/activate
pip install -r requirements.txt
 
TAG=latest make build push update
```

Check the deployment changes:
```
kubectl describe deployments squash-graphql
```

### Scaling up the squash-graphql microservice

Use the `kubectl get replicasets` command to view the current set of replicas, and then the `kubectl scale` command 
to scale up the `squash-graphql` deployment:

``` 
kubectl scale deployments squash-graphql --replicas=3
```

or change the `kubernetes/deployment.yaml` configuration file and apply the new configuration:

```
kubectl apply -f kubernetes/deployment.yaml
```

Check the deployment changes:

``` 
kubectl describe deployments squash-graphql
kubectl get pods
kubectl get replicasets
```

## Development workflow 

For development, you may install the dependencies and set up a local database with test data:

1. Install the software dependencies
```
git clone  https://github.com/lsst-sqre/squash-graphql.git

cd squash-graphql

virtualenv env -p python3
source env/bin/activate
pip install -r requirements.txt
```

2. Development database
 
You can use an instance of [squash-db](https://github.com/lsst-sqre/squash-db) with an external ip address to connect the api running locally.
Usually there's such an instance running under the `squash-dev` namespace on GKE.

3. Running `squash-graphql` locally:

```
cd squash
export SQUASH_DB_HOST=<squash-db external ip address> 
export SQUASH_DB_PASSWORD=********
export SQUASH_API_DEBUG=True
python manage.py runserver
```

The GraphiQL interface will run at `http://localhost:8000`. 

