.PHONY: build run stop logs shell kafka-logs

# Имя контейнера и образа
CONTAINER_NAME=sosalovo
IMAGE_NAME=sosalovo-container

# Сборка Docker-образов через docker-compose
build:
	docker build -t voicefixer .

run:
	docker run --gpus all voicefixer

