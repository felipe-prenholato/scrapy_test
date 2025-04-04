# FastAPI Scrapy Project

## Technical overview

This project is a test project for senior python dev in data team. 

The first idea was to use FastAPI + Scrapy to get information of the sites we want, but lxml worked fine and I ended using it. From Scrapy, I just used the name :).

While testing Market Watch scrapping, I hit the captcha wall. Researched for libs and apps to try to go over captchas, and found that we (as company) will most likely use an internal service or third party service like https://solvecaptcha.com/. So instead, I saved the Market Watch sources to tests/fixtures and used it go over captcha problem. 

I saved sources for following symbols: AAPL, AMZN, DELL, GOOG, HPQ, META, MSFT.

I built two classes to work as client / wrapper, one for the Market Watch and Polygon clients. The idea is to centralize third party services into their own modules, making it easy to turn their code into microservices itself.

The endpoints are on main.py. Had some issues to write functional tests with the database. I'm used to Django where database configuration is really easy to do even for tests, but for FastAPI I got a bit confused since it is moving to SQLModel and I expected some faster and easier way to configure the database for dev and tests. This was causing leaking tests :/. After I solved that problem the work was pretty simple, but it took me some time and I didn't make all pydantic models I wanted.

About logs, I added some on two endpoints, but didn't in third party clients. I understand that prometheus would be better to keep usage metrics, and sentry to catch connection errors.

Finally, I added a nice Makefile and pgcli to container. Love to use then while developing :).

## Setup

The first step is to add `POLYGON_API_KEY` value in `docker-compose.yml`.

Then, just run `make up` and access the project at http://localhost:8000/docs.

To test, run `make tests`.

To run pgcli, use `make bash` and inside the container `pgcli ${POSTGRES_URL/ql+psycopg/}`.

If you have some failure because permissions on Postgres and Redis data folder, update `docker-compose.yml` with your user UID:
```
    # You may want to change this to your user id. 1000 is usually reserved for the first user created in linux systems.
    user: "1000:1000"
```

## Makefile    

Just run `make <command>` from root directory.

```
help                 Command help.
setup                Setup folders and permissions.
build                runs docker compose build
build_nocache        docker compose build --no-cache
up                   Start the localstack.
down                 Stop the localstack.
clean                Stop the localstack and remove postgres and redis data folders.
test                 Run tests with coverage.
apply_lint           Apply black and isort.
shell                Runs ipython inside container.
bash                 Runs bash inside container.
```
