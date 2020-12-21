
IMAGE	?= rechner/apis
TAG	?= $(shell git describe --tag --always)

all: help

define HELP

Commands:

	make build-base-docker-image	: Build the base docker image
	make build-docker-image		: Make a local docker build of APIS
	make push-docker-image		: Push final image stage to docker hub

	make dev			: Develop locally with Docker
	make dev-setup			: Sets up a venv for local development
	make pre-commit-setup		: Installs (or updates) pre-commit hooks

endef
export HELP

help:
	@echo "$${HELP}"

build-base-docker-image:
        # Build the base docker iamge for all external dependancies
	docker build \
		--file DockerfileBase \
		--tag $(IMAGE):apis-base-$(shell git rev-parse --short HEAD) \
		.

	-docker push $(IMAGE):apis-base-$(shell git rev-parse --short HEAD)

	@echo -e "\n\n***************\nACTION REQUIRED: Update line 1 of Dockerfile to this: FROM $(IMAGE):apis-base-$(shell git rev-parse --short HEAD)\n****************"


build-docker-image:
	# tag the current latest as previous, and replace it
	-docker tag $(IMAGE):latest $(IMAGE):previous

	# build and tag new container
	docker build \
		--file Dockerfile \
		--tag $(IMAGE):$(TAG) \
		.

	docker tag $(IMAGE):$(TAG) $(IMAGE):latest


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
