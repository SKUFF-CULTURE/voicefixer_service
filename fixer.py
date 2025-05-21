from voicefixer import VoiceFixer
import os
from pydub import AudioSegment
import time
import torch

# Настройки
vf = VoiceFixer()
print("CUDA available:", torch.cuda.is_available())

input_vocal = "audio/input.wav"  # Готовый отделённый голос
output_dir = "audio/processed"
os.makedirs(output_dir, exist_ok=True)


# 1. Быстрое восстановление голоса
def restore_vocal(input_path, mode=0):
    output_path = f"{output_dir}/restored.wav"
    vf.restore(input=input_path, output=output_path, mode=mode, cuda=True)
    return output_path


# 2. Мгновенное микширование (оригинал + обработанный)
def blend_tracks(original_path, processed_path, original_db=-10):
    orig = AudioSegment.from_wav(original_path) + original_db
    proc = AudioSegment.from_wav(processed_path)
    return proc.overlay(orig, position=5)  # Сдвиг 5 мс для фазы


# 3. Компактные эффекты (реверб + делей за один проход)
def add_effects(audio_segment):
    return (audio_segment
            .low_pass_filter(8000)  # Чуть смягчить ВЧ
            .overlay(audio_segment - 10, position=20)  # Делей 20 мс
            .overlay(audio_segment - 15, position=150)  # Реверб (имитация)
            )

if __name__ == "__main__":
    t_start = time.time()

    # 1. Восстановление
    restored = restore_vocal(input_vocal, mode=0)

    # 2. Микширование и эффекты
    final = add_effects(
        blend_tracks(input_vocal, restored))

    # . Сохранение
    final_path = f"{output_dir}/final_{int(time.time())}.wav"
    final.export(final_path, format="wav")

    print(f"✅ Готово за {time.time() - t_start:.1f} сек\nФайл: {final_path}")
