# Используем базовый образ с CUDA и cuDNN для разработки
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu20.04

# Устанавливаем временную зону в неинтерактивном режиме
ENV TZ=Europe/Moscow \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Устанавливаем системные зависимости и Python 3.11
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    software-properties-common \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    curl \
    libncurses5-dev \
    libncursesw5-dev \
    liblzma-dev \
    tk-dev \
    libgdbm-dev \
    libgdbm-compat-dev \
    libnss3-dev \
    libffi-dev \
    liblzma-dev \
    libmysqlclient-dev \
    libpq-dev \
    git \
    bash \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get install -y python3.11 python3.11-dev python3.11-venv \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 \
    && rm -rf /var/lib/apt/lists/*

# Создаем и активируем виртуальное окружение
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем файлы зависимостей
COPY requirements.txt install_req.sh /tmp/

# Устанавливаем зависимости и запускаем скрипт
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r /tmp/requirements.txt \
    && chmod +x /tmp/install_req.sh \
    && /tmp/install_req.sh \
    && rm /tmp/requirements.txt /tmp/install_req.sh

# Копируем остальной код
COPY . /app
WORKDIR /app

# Настройки CUDA
ENV CUDA_HOME=/usr/local/cuda-11.8 \
    LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# Проверяем установленные версии
RUN python --version \
    && pip --version \
    && nvcc --version \
    && ldconfig -p | grep cudnn

# Запускаем приложение
CMD ["python", "fixer.py"]