import numpy as np
from pydub import AudioSegment
import tempfile
import subprocess
from pathlib import Path


class AudioMixer:
    def __init__(self, vocal_path=None, instrumental_path=None):
        """
        Инициализация микшера с путями к аудиофайлам
        :param vocal_path: путь к файлу с вокалом (поддерживаются WAV, MP3, FLAC и др.)
        :param instrumental_path: путь к файлу с инструменталом
        """
        self._check_ffmpeg_installed()
        self.vocal_path = vocal_path
        self.instrumental_path = instrumental_path
        self.vocal_audio = None
        self.instrumental_audio = None

        if vocal_path:
            self.load_vocal(vocal_path)
        if instrumental_path:
            self.load_instrumental(instrumental_path)

    def _check_ffmpeg_installed(self):
        """Проверяет наличие FFmpeg в системе и устанавливает если нужно"""
        try:
            subprocess.run(["ffmpeg", "-version"],
                           check=True,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError(
                "FFmpeg не установлен. Установите FFmpeg для работы с аудио:\n"
                "Linux: sudo apt install ffmpeg\n"
                "Mac: brew install ffmpeg\n"
                "Windows: скачайте с https://ffmpeg.org/"
            )

    def load_vocal(self, path):
        """Загрузка вокального трека"""
        self.vocal_path = path
        self.vocal_audio = AudioSegment.from_file(path)

    def load_instrumental(self, path):
        """Загрузка инструментального трека"""
        self.instrumental_path = path
        self.instrumental_audio = AudioSegment.from_file(path)

    def check_audio_files(self):
        """Проверка загружены ли оба аудиофайла"""
        if self.vocal_audio is None or self.instrumental_audio is None:
            raise ValueError("Оба аудиофайла должны быть загружены перед сведением")

    def normalize_audio(self, target_dBFS=-20.0, instrumental_offset=-3.0):
        """
        Нормализация громкости аудиофайлов
        :param target_dBFS: целевой уровень громкости вокала
        :param instrumental_offset: на сколько dB сделать инструментал тише вокала
        """
        self.check_audio_files()

        # Нормализация вокала
        vocal_change = target_dBFS - self.vocal_audio.dBFS
        self.vocal_audio = self.vocal_audio.apply_gain(vocal_change)

        # Нормализация инструментала
        instrumental_target = target_dBFS + instrumental_offset
        instrumental_change = instrumental_target - self.instrumental_audio.dBFS
        self.instrumental_audio = self.instrumental_audio.apply_gain(instrumental_change)

    def align_durations(self, strategy="trim"):
        """
        Выравнивание длительности треков
        :param strategy: стратегия выравнивания:
            - "trim" - обрезать по более короткому
            - "loop" - зациклить более короткий
            - "pad" - дополнить тишиной
        """
        self.check_audio_files()

        vocal_len = len(self.vocal_audio)
        instrumental_len = len(self.instrumental_audio)

        if vocal_len == instrumental_len:
            return

        if strategy == "trim":
            if vocal_len > instrumental_len:
                self.vocal_audio = self.vocal_audio[:instrumental_len]
            else:
                self.instrumental_audio = self.instrumental_audio[:vocal_len]

        elif strategy == "loop":
            if vocal_len > instrumental_len:
                loops = int(np.ceil(vocal_len / instrumental_len))
                self.instrumental_audio = self.instrumental_audio * loops
                self.instrumental_audio = self.instrumental_audio[:vocal_len]
            else:
                loops = int(np.ceil(instrumental_len / vocal_len))
                self.vocal_audio = self.vocal_audio * loops
                self.vocal_audio = self.vocal_audio[:instrumental_len]

        elif strategy == "pad":
            silence = AudioSegment.silent(duration=abs(vocal_len - instrumental_len),
                                          frame_rate=self.vocal_audio.frame_rate)
            if vocal_len > instrumental_len:
                self.instrumental_audio += silence
            else:
                self.vocal_audio += silence

    def mix_audio(self, vocal_volume=1.0, instrumental_volume=0.8, fade_duration=500):
        """
        Сведение вокала и инструментала
        :param vocal_volume: громкость вокала (0.0 - 1.0)
        :param instrumental_volume: громкость инструментала (0.0 - 1.0)
        :param fade_duration: длительность fade-in/out в миллисекундах
        :return: смешанный аудиосегмент
        """
        self.check_audio_files()
        self.align_durations()

        # Применяем уровни громкости
        vocal = self.vocal_audio - (20 * (1 - vocal_volume))
        instrumental = self.instrumental_audio - (20 * (1 - instrumental_volume))

        # Применяем fade-in/out
        vocal = self.fade_in_out(vocal, fade_duration)
        instrumental = self.fade_in_out(instrumental, fade_duration)

        # Смешиваем треки
        mixed = vocal.overlay(instrumental)

        return mixed

    def export_mixed_audio(self, output_path, **mix_kwargs):
        """
        Экспорт смешанного аудио в файл
        :param output_path: путь для сохранения результата (расширение определяет формат)
        :param mix_kwargs: аргументы для mix_audio
        """
        mixed = self.mix_audio(**mix_kwargs)

        # Определяем формат по расширению файла
        ext = Path(output_path).suffix[1:].lower()

        # Особые параметры для FLAC
        if ext == "flac":
            # Используем временный WAV файл для конвертации в FLAC
            with tempfile.NamedTemporaryFile(suffix=".wav") as tmp_wav:
                mixed.export(tmp_wav.name, format="wav")

                # Конвертируем в FLAC с максимальным качеством
                subprocess.run([
                    "ffmpeg", "-y", "-i", tmp_wav.name,
                    "-c:a", "flac", "-compression_level", "12",
                    output_path
                ], check=True)
        else:
            # Для других форматов используем стандартный экспорт
            mixed.export(output_path, format=ext)

    @staticmethod
    def fade_in_out(audio_segment, fade_duration=500):
        """Применяет fade-in и fade-out к аудио"""
        return audio_segment.fade_in(fade_duration).fade_out(fade_duration)

    def get_audio_info(self):
        """Возвращает информацию о аудиофайлах"""
        self.check_audio_files()
        return {
            "vocal": {
                "duration": len(self.vocal_audio) / 1000,
                "channels": self.vocal_audio.channels,
                "sample_rate": self.vocal_audio.frame_rate,
                "dBFS": self.vocal_audio.dBFS
            },
            "instrumental": {
                "duration": len(self.instrumental_audio) / 1000,
                "channels": self.instrumental_audio.channels,
                "sample_rate": self.instrumental_audio.frame_rate,
                "dBFS": self.instrumental_audio.dBFS
            }
        }

if __name__ == "__main__":
    # Создание микшера
    mixer = AudioMixer("vocal.flac", "instrumental.wav")

    # Нормализация с кастомными параметрами
    mixer.normalize_audio(target_dBFS=-18.0, instrumental_offset=-2.5)

    # Выравнивание длительности с зацикливанием
    mixer.align_durations(strategy="loop")

    # Экспорт в FLAC с максимальным качеством
    mixer.export_mixed_audio(
        "final_mix.flac",
        vocal_volume=0.95,
        instrumental_volume=0.85,
        fade_duration=800
    )

    # Получение информации о файлах
    print(mixer.get_audio_info())