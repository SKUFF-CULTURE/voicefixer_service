#!/bin/bash

#Основные зависимости
pip install git+https://github.com/haoheliu/voicefixer.git

# Удаляем предыдущие версии
pip uninstall -y torch torchaudio torchvision

# Устанавливаем с CUDA 11.8
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118

# Проверяем установку
python -c "import torch; print(f'PyTorch version: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"