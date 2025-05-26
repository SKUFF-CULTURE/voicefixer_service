# Используем официальный образ NVIDIA с CUDA 11.8
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Настройки окружения
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    TORCH_CUDA_VERSION=cu118 \
    TORCH_VERSION=2.0.1

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3.11-distutils \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создаем и настраиваем venv
RUN python3.11 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip setuptools wheel

# Установка PyTorch с GPU-поддержкой
RUN /opt/venv/bin/pip install --no-cache-dir \
    torch==${TORCH_VERSION}+${TORCH_CUDA_VERSION} \
    --extra-index-url https://download.pytorch.org/whl/${TORCH_CUDA_VERSION}

# Установка остальных зависимостей
COPY requirements.txt install_req.sh /tmp/
RUN /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt && \
    chmod +x /tmp/install_req.sh && \
    /tmp/install_req.sh && \
    rm /tmp/requirements.txt /tmp/install_req.sh

# Копируем приложение
WORKDIR /app
COPY . .

# Проверка доступности CUDA
RUN python -c "import torch; print(f'PyTorch version: {torch.__version__}'); assert torch.cuda.is_available(), 'CUDA not available!'"

# Настройки CUDA
ENV CUDA_HOME=/usr/local/cuda-11.8 \
    LD_LIBRARY_PATH=/usr/local/cuda-11.8/lib64:$LD_LIBRARY_PATH

CMD ["python", "pipeline.py"]