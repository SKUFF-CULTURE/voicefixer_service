FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Ускоряем загрузку пакетов
RUN sed -i 's|http://archive.ubuntu.com|http://mirror.yandex.ru/ubuntu|g' /etc/apt/sources.list

# Устанавливаем только необходимые системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-venv \
    python3-distutils \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создаем виртуальное окружение с Python 3.10
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Обновляем pip в виртуальном окружении
RUN pip install --upgrade pip setuptools wheel

# Копируем и устанавливаем зависимости
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

RUN pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Устанавливаем специфичные пакеты с явным указанием версий
RUN pip install --no-cache-dir --no-deps\
    voicefixer \
    demucs==4.0.1

# Настройка окружения CUDA
ENV PYTHONUNBUFFERED=1 \
    CUDA_HOME=/usr/local/cuda-11.8 \
    LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH \
    TORCH_HUB=/root/.cache/torch/hub

# Копируем приложение
WORKDIR /app
COPY . .

CMD ["python", "pipeline.py"]