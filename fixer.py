from voicefixer import VoiceFixer
import os
from pydub import AudioSegment
import time
import torch
import logging
from typing import Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('voice_processing.log')  # File output
    ]
)


class VoiceImprover:
    """Audio processing pipeline for voice restoration and enhancement."""

    def __init__(self):
        """Initialize the voice processing pipeline."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing VoiceFixer engine...")

        try:
            self.vf = VoiceFixer()
            self.logger.info(f"VoiceFixer initialized.")
        except Exception as e:
            self.logger.error(f"VoiceFixer initialization failed: {str(e)}")
            raise RuntimeError("Failed to initialize VoiceFixer") from e

    def check_hardware(self) -> Tuple[bool, str]:
        """Verify GPU availability and return status.

        Returns:
            Tuple of (cuda_available, status_message)
        """
        if not torch.cuda.is_available():
            return False, "CUDA not available - Falling back to CPU"

        device_count = torch.cuda.device_count()
        current_device = torch.cuda.current_device()
        device_name = torch.cuda.get_device_name(current_device)
        memory = torch.cuda.get_device_properties(current_device).total_memory / (1024 ** 3)

        status = (f"CUDA active - Device {current_device}: {device_name} "
                  f"(VRAM: {memory:.1f}GB)")
        return True, status

    def _restore_audio(self, input_path: str, output_dir: str, mode: int = 0) -> str:
        """Restore vocal track with detailed logging.

        Args:
            input_path: Path to source audio file
            output_dir: Directory for processed files
            mode: VoiceFixer processing mode (0-2)

        Returns:
            Path to restored audio file
        """
        self.logger.info(f"Processing audio: {os.path.basename(input_path)}")
        output_path = os.path.join(output_dir, "restored.wav")

        try:
            # Verify input file
            if not os.path.isfile(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")

            # Check filesize
            file_size = os.path.getsize(input_path) / (1024 ** 2)  # MB
            self.logger.debug(f"Input file size: {file_size:.2f}MB")

            # Hardware check
            cuda_available, hw_status = self.check_hardware()
            self.logger.info(hw_status)

            # Process audio
            start_time = time.time()
            self.vf.restore(
                input=input_path,
                output=output_path,
                mode=mode,
                cuda=cuda_available
            )

            # Verify output
            if not os.path.exists(output_path):
                raise RuntimeError("Output file was not created")

            process_time = time.time() - start_time
            self.logger.info(f"Restoration completed in {process_time:.2f}s")
            return output_path

        except Exception as e:
            self.logger.error(f"Restoration failed: {str(e)}", exc_info=True)
            raise

    def _enhance_audio(self, original_path: str, processed_path: str) -> AudioSegment:
        """Apply audio enhancement pipeline.

        Args:
            original_path: Path to source audio
            processed_path: Path to restored audio

        Returns:
            Enhanced AudioSegment object
        """
        self.logger.info("Applying audio enhancements...")

        try:
            # Load audio tracks
            original = AudioSegment.from_wav(original_path)
            processed = AudioSegment.from_wav(processed_path)

            # Log audio properties
            self.logger.debug(
                f"Original: {original.channels}ch, {original.frame_rate}Hz, "
                f"{len(original) / 1000:.1f}s"
            )
            self.logger.debug(
                f"Processed: {processed.channels}ch, {processed.frame_rate}Hz"
            )

            # Blend tracks with 5ms phase alignment
            blended = processed.overlay(original - 10, position=5)

            # Apply effects chain
            enhanced = (
                blended
                .low_pass_filter(8000)  # Smooth highs
                .overlay(blended - 10, position=20)  # Short delay
                .overlay(blended - 15, position=150)  # Reverb effect
            )

            return enhanced

        except Exception as e:
            self.logger.error(f"Enhancement failed: {str(e)}", exc_info=True)
            raise

    def process(self, input_path: str, output_dir: str, mode: int = 0) -> Optional[str]:
        """Complete audio processing pipeline.

        Args:
            input_path: Source audio file path
            output_dir: Output directory path
            mode: Processing mode (0=basic, 1=aggressive, 2=experimental)

        Returns:
            Path to final output file or None if failed
        """
        self.logger.info(f"Starting processing pipeline for {input_path}")

        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            self.logger.debug(f"Output directory: {output_dir}")

            # 1. Restoration phase
            restored_path = self._restore_audio(input_path, output_dir, mode)

            # 2. Enhancement phase
            final_audio = self._enhance_audio(input_path, restored_path)

            # 3. Export results
            timestamp = int(time.time())
            final_path = os.path.join(output_dir, f"enhanced_{timestamp}.wav")
            final_audio.export(final_path, format="wav")

            # Verify output
            if not os.path.exists(final_path):
                raise RuntimeError("Final output file not created")

            # Log final stats
            duration = len(final_audio) / 1000
            size = os.path.getsize(final_path) / (1024 ** 2)
            self.logger.info(
                f"SUCCESS: Created {final_path}\n"
                f"Duration: {duration:.1f}s | Size: {size:.1f}MB"
            )

            return final_path

        except Exception as e:
            self.logger.error(f"Processing pipeline failed: {str(e)}", exc_info=True)
            return None


if __name__ == "__main__":
    # Example usage
    processor = VoiceImprover()

    result = processor.process(
        input_path="audio/input.wav",
        output_dir="audio/processed",
        mode=1
    )

    if result:
        print(f"Output saved to: {result}")
    else:
        print("Processing failed - check voice_processing.log for details")