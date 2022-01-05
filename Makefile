
IMAGE	?= ghcr.io/furthemore/apis
TAG	?= $(shell git describe --tag --always)

all: help

define HELP

Commands:
	make docker-login               : Login to Github container repository
	make build-base-docker-image    : Build the base docker image
	make build-docker-image         : Make a local docker build of APIS
	make push-docker-image          : Push latest image to Github container repository
        make tag-stage                  : Tag image for deployment to stage server
        make tag-production             : Tag image for deployment to production

	make dev                        : Develop locally with Docker
	make dev-setup                  : Sets up a venv for local development
	make pre-commit-setup           : Installs (or updates) pre-commit hooks

endef
export HELP

help:
	@echo "$${HELP}"

docker-login:
	@[ "${GITHUB_USER}" ] || ( echo ">> GITHUB_USER is not set, check out envrc.example"; exit 1 )
	@[ "${GITHUB_CR_PAT}" ] || ( echo ">> GITHUB_CR_PAT is not set, check out envrc.example"; exit 1 )
	@echo $(GITHUB_CR_PAT) | docker login ghcr.io -u $(GITHUB_USER) --password-stdin


build-base-docker-image:
        # Build the base docker image for all external dependancies
	docker build \
		--file DockerfileBase \
		--tag $(IMAGE):apis-base-$(shell git rev-parse --short HEAD) \
		.

	-docker push $(IMAGE):apis-base-$(shell git rev-parse --short HEAD)
	sed -i 's/apis-base-.*$$/apis-base-$(shell git rev-parse --short HEAD)/' Dockerfile

build-docker-image:
	# tag the current latest as previous, and replace it
	-docker tag $(IMAGE):latest $(IMAGE):previous

	# build and tag new container
	docker build \
		--file Dockerfile \
		--build-arg SENTRY_RELEASE=$(TAG) \
		--tag $(IMAGE):$(TAG) \
		.

	docker tag $(IMAGE):$(TAG) $(IMAGE):latest

tag-stage:
	docker tag $(IMAGE):$(TAG) $(IMAGE):stage
	docker push $(IMAGE):stage

tag-production:
	docker tag $(IMAGE):$(TAG) $(IMAGE):production
	docker push $(IMAGE):production

push-docker-image:
	docker push $(IMAGE):$(TAG)
	docker push $(IMAGE):latest

dev:
	-docker-compose up -d
	docker-compose exec app /bin/bash -c 'DJANGO_DEBUG=1 python /app/manage.py runserver_plus 0.0.0.0:8000'


dev-setup:
	python3 -m venv venv
	source venv/bin/activate
	pip install -r requirements.txt
	cp fm_eventmanager/settings.py.devel fm_eventmanager/settings.py

	@echo "ACTION REQUIRED: Review fm_eventmanager/settings.py"

pre-commit-setup:
	pip3 install pre-commit
	pre-commit install
