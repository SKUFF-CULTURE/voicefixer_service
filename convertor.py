import ffmpeg
from pathlib import Path
import shutil
import logging
import re
from unidecode import unidecode

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

class AudioConverter:
    def to_wav(self, input_path: str, output_path: str = None) -> Path:
        return self._convert(input_path, output_path, "wav")

    def to_mp3(self, input_path: str, output_path: str = None) -> Path:
        return self._convert(input_path, output_path, "mp3")

    def to_flac(self, input_path: str, output_path: str = None) -> Path:
        return self._convert(input_path, output_path, "flac")

    @staticmethod
    def _convert(input_path: str, output_path: str, target_format: str) -> Path:
        input_path = Path(input_path).resolve()
        if not input_path.exists():
            raise FileNotFoundError(f"[Converter] File not found: {input_path}")

        if output_path is None:
            output_path = input_path.with_suffix(f".{target_format}")
        else:
            output_path = Path(output_path).resolve()

        logger.info(f"[Converter] Converting {input_path.name} → {output_path.name}")

        try:
            if target_format == "wav":
                # Используем ffmpeg для конвертации в 32-битный WAV
                ffmpeg.input(str(input_path)).output(str(output_path), acodec='pcm_f32le', map_metadata=0, y=None).run()
            else:
                # Для других форматов (например, mp3, flac)
                ffmpeg.input(str(input_path)).output(str(output_path), map_metadata=0, y=None).run()
        except Exception as e:
            logger.exception(f"[Converter] Failed to convert {input_path.name} to {target_format}")
            raise e

        logger.info(f"[Converter] Saved: {output_path}")
        return output_path

    @staticmethod
    def convert_name(input_path: str) -> Path:
        original_path = Path(input_path).resolve()
        stem = Path(original_path).stem

        # Очистка имени: ASCII + нижний регистр + только буквы/цифры/подчёркивания
        safe_stem = unidecode(stem).lower()
        safe_stem = re.sub(r"[^\w]+", "_", safe_stem).strip("_")

        safe_path = original_path.with_name(f"{safe_stem}{original_path.suffix}")

        if safe_path != original_path:
            shutil.copy(original_path, safe_path)
            logger.info(f"[Converter] Copied file to safe name: {safe_path}")
        else:
            logger.info(f"[Converter] Input name already safe: {safe_path.name}")

        return safe_path


if __name__ == "__main__":
    converter = AudioConverter()
    s_path = converter.convert_name("audio/raw/Тёмная ночь.mp3")
    converter.to_wav(input_path=s_path)
