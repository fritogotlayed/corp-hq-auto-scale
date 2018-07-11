.DEFAULT_GOAL := help

docker-build:  ## Runs the docker image build
	docker build --no-cache -t corp-hq-auto-scale:latest .

help:  ## Prints this help message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

run:  ## Executes the seed data against the local mongo database.
	docker run -v /var/run/docker.sock:/var/run/docker.sock -e MONGO_CONNECTION=mongodb://mongodb:27017 -e CORP_HQ_ENVIRONMENT=localDocker --network=corp-hq_default --name=corp-hq-auto-scale -it -d corp-hq-auto-scale:latest
