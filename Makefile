.PHONY: all test clean backend

all: dev-init-python generate-proto backend frontend

generate-python:
	cd ./backend/ml-worker && ./generate-proto.sh $(abspath backend/ml-worker/.venv/bin/python)

generate-java:
	./backend/java-app/gradlew -b backend/java-app/build.gradle clean generateProto	

generate-proto: generate-java generate-python

clean: clean-backend clean-generated-python

clean-generated-python:
	@rm -rf backend/ml-worker/generated

clean-backend:
	cd ./backend/java-app && ./gradlew clean

backend:
	cd ./backend/java-app && ./gradlew build -x test -x integrationTest

frontend:
	cd ./frontend && npm install

liquibase-difflog:
	cd ./backend/java-app && ./gradlew liquibaseDiffChangelog -PrunList=diffLog

test-python:
	cd ./backend/ml-worker && PYTHONPATH=generated:ml_worker .venv/bin/python -m pytest test

dev-init-python:
	cd ./backend/ml-worker && poetry env use python3.7 && poetry install
	cd ./backend/app && poetry env use python3.7 && poetry install