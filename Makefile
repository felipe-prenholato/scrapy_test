help: ## Command help.
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup folders and permissions.
	@mkdir -pv data/postgres data/redis
	@chown 1000:1000 data/*

build: setup  ## runs docker compose build
	@docker compose build

build_nocache: setup ## docker compose build --no-cache
	@docker compose build --no-cache

up: setup ## Start the localstack.
	@docker compose up -d --remove-orphans

down: ## Stop the localstack.
	@docker compose down

clean: down ## Stop the localstack and remove postgres and redis data folders.
	@rm -rf data/postgres data/redis

test: up  ## Run tests with coverage.
	@docker exec -it scrapy_test pytest -vs --cov=app tests/

apply_lint: up ## Apply black and isort.
	@black .
	@isort --profile black .

shell: up ## Runs ipython inside container.
	@docker exec -it scrapy_test bash -lc ipython

bash: up ## Runs bash inside container.
	@docker exec -it scrapy_test bash -l
