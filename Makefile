.PHONY: build run stop logs shell kafka-logs

# Имя контейнера и образа
CONTAINER_NAME=vf
IMAGE_NAME=vf-container

# Сборка Docker-образов через docker-compose
build:
	docker build -t voicefixer .

run:
	docker run --gpus all voicefixer

