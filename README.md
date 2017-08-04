# squash-api
SQuaSH API microservice


## Development
1. Clone the project, create a virtualenv and install dependencies
```
  git clone  https://github.com/lsst-sqre/squash-api.git

  cd squash-api

  virtualenv env -p python3
  source env/bin/activate
  pip install -r requirements.txt
```

2. Install MariaDB 10.1+

For example, using brew:
```

  brew install mariadb
  mysql.server start
```

3. Initialize the development database

```
  mysql -u root -e "DROP DATABASE qadb"
  mysql -u root -e "CREATE DATABASE qadb"

  cd squash
  python manage.py makemigrations
  python manage.py migrate
```   

4. Execute tests
```
  python manage.py check
  python manage.py test api 
```

5. Load test data
```
  python manage.py loaddata test_data
```

The `squash-api` will run at `http://localhost:8000`. 

### The Django Debug toolbar

By default, `DEBUG=True` in `squash.settings.py` which will 
display the Django debug toolbar. The Django debug toolbar can be used, among other things, to inspect the SQL queries that
are executed when accessing the API endpoints.

### The SQuaSH API admin interface

In development mode access the SQUASH API admin interface at `http://localhost:8000/admin`. You must create a superuser 
in order to login:
 
```
  python manage.py createsuperuser 
```
 

