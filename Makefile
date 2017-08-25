all:
PREFIX = lsstsqre/squash-api
NGINX_TEMPLATE = kubernetes/nginx/nginx-template.conf
NGINX_CONFIG = kubernetes/nginx/nginx.conf
REPLACE = ./kubernetes/replace.sh
DEPLOYMENT_TEMPLATE = kubernetes/deployment-template.yaml
DEPLOYMENT_CONFIG = kubernetes/deployment.yaml
SERVICE_CONFIG = kubernetes/service.yaml

build: check-tag
	docker build -t $(PREFIX):${TAG} .

push: check-tag
	docker push $(PREFIX):${TAG}

service:
	@echo "Creating service..."
	kubectl delete --ignore-not-found=true services squash-api
	kubectl create -f $(SERVICE_CONFIG)

configmap:
	@echo "Creating config map for nginx configuration..."
	kubectl delete --ignore-not-found=true configmap squash-api-nginx-conf
	@$(REPLACE) $(NGINX_TEMPLATE) $(NGINX_CONFIG)
	kubectl create configmap squash-api-nginx-conf --from-file=$(NGINX_CONFIG)

deployment: check-tag service configmap
	@echo "Creating deployment..."
	@$(REPLACE) $(DEPLOYMENT_TEMPLATE) $(DEPLOYMENT_CONFIG)
	kubectl delete --ignore-not-found=true deployment squash-api
	kubectl create -f $(DEPLOYMENT_CONFIG)

update: check-tag
	@echo "Updating squash-bokeh deployment..."
	@$(REPLACE) $(DEPLOYMENT_TEMPLATE) $(DEPLOYMENT_CONFIG)
	kubectl apply -f $(DEPLOYMENT_CONFIG) --record
	kubectl rollout history deployment squash-api

clean:
	rm $(DEPLOYMENT_CONFIG)

check-tag:
	@if test -z ${TAG}; then echo "Error: TAG is undefined."; exit 1; fi

