API = lsstsqre/squash-api
NGINX  = lsstsqre/squash-api-nginx
NGINX_CONFIG = kubernetes/nginx/nginx.conf
DEPLOYMENT_TEMPLATE = kubernetes/deployment-template.yaml
DEPLOYMENT_CONFIG = kubernetes/deployment.yaml
SERVICE_CONFIG = kubernetes/service.yaml
STATIC = kubernetes/nginx/static
REPLACE = ./kubernetes/replace.sh

$(STATIC):
	cd squash; python manage.py collectstatic

build: check-tag $(STATIC)
	docker build -t $(API):${TAG} .
	docker build -t $(NGINX):${TAG} kubernetes/nginx

push: check-tag
	docker push $(API):${TAG}
	docker push $(NGINX):${TAG}

service:
	@echo "Creating service..."
	kubectl delete --ignore-not-found=true services squash-api
	kubectl create -f $(SERVICE_CONFIG)

configmap:
	@echo "Creating config map for nginx configuration..."
	kubectl delete --ignore-not-found=true configmap squash-api-nginx-conf
	kubectl create configmap squash-api-nginx-conf --from-file=$(NGINX_CONFIG)

deployment: check-tag service configmap
	@echo "Creating deployment..."
	@$(REPLACE) $(DEPLOYMENT_TEMPLATE) $(DEPLOYMENT_CONFIG)
	kubectl delete --ignore-not-found=true deployment squash-api
	kubectl create -f $(DEPLOYMENT_CONFIG)

update: check-tag
	@echo "Updating squash-api deployment..."
	@$(REPLACE) $(DEPLOYMENT_TEMPLATE) $(DEPLOYMENT_CONFIG)
	kubectl apply -f $(DEPLOYMENT_CONFIG) --record
	kubectl rollout history deployment squash-api

clean:
	rm $(DEPLOYMENT_CONFIG)
	rm $(NGINX_CONFIG)
	rm -f $(STATIC)

check-tag:
	@if test -z ${TAG}; then echo "Error: TAG is undefined."; exit 1; fi

