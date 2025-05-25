from noisereduce_processing import AudioRestorer
from demucs_processing import DemucsProcessor
from fixer_processing import VoiceImprover
from convertor import AudioConverter
from mixer_processing_legacy import AudioMixer
from toolbox.common import make_name
import shutil
import logging
import time
import os

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def run(input_path, nfs_dir, uuid: 0):

    logger.info("Starting...")
    start_time = time.time()
    try:

        work_dir = nfs_dir + str(uuid) + '/'
        os.makedirs(work_dir, exist_ok=True)

        # Setting up the instances of processing tools
        audio_converter = AudioConverter()
        pre_restorer = AudioRestorer(mode="vinyl", vinyl_intensity="aggressive")
        post_restorer = AudioRestorer(mode="vinyl", vinyl_intensity="light")
        track_splitter = DemucsProcessor()
        fixer = VoiceImprover()


        # Starting pipeline

        # 0. Convertion
        s_path = audio_converter.convert_name(input_path)
        audio_path = str(audio_converter.to_wav(input_path=str(s_path)))

        logger.info("Step 0 done")

        # 1. Noise reduction
        denoised_path = work_dir + make_name(audio_path, suffix='-denoised')
        pre_restorer.restore(
            input_path=audio_path,
            output_path=denoised_path
        )
        logger.info("Step 1 done")

        # 2. Track splitting
        vocals, instruments = track_splitter.separate(input_path=denoised_path, output_dir=work_dir, model="hdemucs_mmi", mode='vintage')
        logger.info("Step 2 done")

        # 3. Vocal enhancing
        enhanced_vocal_path = work_dir + make_name(vocals, suffix='-enhanced')
        print(vocals)
        print(enhanced_vocal_path)
        fixer.process(
            input_path=vocals,
            output_path=enhanced_vocal_path,
            mode=1
        )
        logger.info("Step 3 done")
        # 4. Cleaning artifacts
        final_vocal_path = work_dir + make_name(enhanced_vocal_path, suffix='-final')
        post_restorer.restore(
            input_path=enhanced_vocal_path,
            output_path=final_vocal_path
        )
        logger.info("Step 4 done")

        # 5. Mastering
        mixer = AudioMixer(vocal_path=final_vocal_path, instrumental_path=instruments)
        mixer.normalize_audio(target_dBFS=-18.0, instrumental_offset=-2.5)
        mixer.align_durations(strategy="pad")
        mixer.export_mixed_audio(
            work_dir + make_name(audio_path, suffix='-improved-mastered'),
            vocal_volume=0.95,
            instrumental_volume=0.85,
            fade_duration=800
        )
        logger.info("Step 5 done")

        # Cleaning demucs temp files
        shutil.rmtree("separated/hdemucs_mmi")

        process_time = time.time() - start_time
        logger.info(f"Done! Pipeline worked in {process_time:.2f}s")
        return 0
    except Exception as e:
        logger.error(e)
        return 1




if __name__ == '__main__':
    run(input_path='audio/raw/Темная ночь.mp3', nfs_dir="audio-", uuid=4)