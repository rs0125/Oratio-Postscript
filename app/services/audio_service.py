"""
Audio processing and transcription service using OpenAI Whisper.
"""
import base64
from app.core.logging_config import get_logger
import os
import tempfile
from pathlib import Path
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

import openai

# Handle pydub import gracefully for Python 3.13 compatibility
try:
    from pydub import AudioSegment
    from pydub.exceptions import CouldntDecodeError
    PYDUB_AVAILABLE = True
except ImportError:
    # Fallback for Python 3.13 where audioop is not available
    AudioSegment = None
    CouldntDecodeError = Exception
    PYDUB_AVAILABLE = False

from app.models.internal import AudioData, TranscriptionResult
from app.core.config import settings
from app.core.exceptions import (
    AudioValidationError,
    AudioProcessingError,
    TranscriptionError,
    WhisperError,
    RateLimitError
)

logger = get_logger(__name__)


class AudioService:
    """Service for audio processing and transcription."""
    
    def __init__(self):
        """Initialize the audio service with OpenAI client."""
        self.client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_organization
        )
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Supported audio formats for Whisper
        self.supported_formats = ['wav', 'mp3', 'flac', 'm4a', 'ogg', 'webm']
        
        # Maximum file size (25MB as per settings)
        self.max_file_size = settings.max_audio_size_mb * 1024 * 1024
    
    async def decode_base64_audio(self, base64_audio: str) -> AudioData:
        """
        Decode base64 audio data and validate format.
        
        Args:
            base64_audio: Base64 encoded audio data
            
        Returns:
            AudioData object with validated audio information
            
        Raises:
            AudioValidationError: If audio data is invalid
            AudioProcessingError: If decoding fails
        """
        try:
            logger.info("Decoding base64 audio data")
            
            if not base64_audio or not base64_audio.strip():
                raise AudioValidationError("Audio data cannot be empty")
            
            # Clean the base64 string
            base64_audio = base64_audio.strip()
            
            # Add padding if needed
            missing_padding = len(base64_audio) % 4
            if missing_padding:
                base64_audio += '=' * (4 - missing_padding)
            
            # Decode base64
            try:
                audio_bytes = base64.b64decode(base64_audio, validate=True)
            except Exception as e:
                raise AudioValidationError(f"Invalid base64 encoding: {str(e)}")
            
            # Check file size
            if len(audio_bytes) > self.max_file_size:
                raise AudioValidationError(
                    f"Audio file too large: {len(audio_bytes)} bytes "
                    f"(max: {self.max_file_size} bytes)"
                )
            
            if len(audio_bytes) < 44:  # Minimum WAV header size
                raise AudioValidationError("Audio data too small to be a valid audio file")
            
            # Detect format by examining the header
            audio_format = self._detect_audio_format(audio_bytes)
            
            # Validate format is supported
            if audio_format not in self.supported_formats:
                raise AudioValidationError(
                    f"Unsupported audio format: {audio_format}. "
                    f"Supported formats: {', '.join(self.supported_formats)}"
                )
            
            # Create temporary file to validate with pydub
            with tempfile.NamedTemporaryFile(suffix=f'.{audio_format}', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            try:
                if PYDUB_AVAILABLE:
                    # Validate audio file with pydub
                    audio_segment = await asyncio.get_event_loop().run_in_executor(
                        self.executor, AudioSegment.from_file, temp_path
                    )
                    channels = audio_segment.channels
                else:
                    # Fallback: assume mono for basic validation
                    channels = 1
                    logger.warning("pydub not available, assuming mono audio")
                
                logger.info(
                    f"Successfully decoded audio: format={audio_format}, "
                    f"channels={channels}, size={len(audio_bytes)} bytes"
                )
                
                return AudioData(
                    base64_content=base64_audio,
                    format=audio_format,
                    channels=channels
                )
                
            except CouldntDecodeError as e:
                raise AudioValidationError(f"Invalid or corrupted audio file: {str(e)}")
            except Exception as e:
                raise AudioProcessingError(f"Failed to process audio file: {str(e)}")
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
                    
        except (AudioValidationError, AudioProcessingError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error decoding audio: {e}")
            raise AudioProcessingError(f"Failed to decode audio data: {str(e)}")
    
    def _detect_audio_format(self, audio_bytes: bytes) -> str:
        """
        Detect audio format from file header.
        
        Args:
            audio_bytes: Raw audio file bytes
            
        Returns:
            Detected audio format
        """
        # Check for common audio file signatures
        if audio_bytes.startswith(b'RIFF') and b'WAVE' in audio_bytes[:12]:
            return 'wav'
        elif audio_bytes.startswith(b'ID3') or audio_bytes.startswith(b'\xff\xfb'):
            return 'mp3'
        elif audio_bytes.startswith(b'fLaC'):
            return 'flac'
        elif audio_bytes.startswith(b'ftypM4A'):
            return 'm4a'
        elif audio_bytes.startswith(b'OggS'):
            return 'ogg'
        elif audio_bytes.startswith(b'\x1a\x45\xdf\xa3'):
            return 'webm'
        else:
            # Default to wav if we can't detect
            return 'wav'
    
    async def transcribe_audio(self, audio_data: AudioData) -> TranscriptionResult:
        """
        Transcribe audio using OpenAI Whisper.
        
        Args:
            audio_data: Validated audio data
            
        Returns:
            TranscriptionResult with transcribed text
            
        Raises:
            TranscriptionError: If transcription fails
            AudioProcessingError: If audio processing fails
        """
        temp_path = None
        try:
            logger.info(f"Starting transcription for {audio_data.format} audio")
            
            # Decode base64 to bytes
            audio_bytes = base64.b64decode(audio_data.base64_content)
            
            # Create temporary file for Whisper API
            with tempfile.NamedTemporaryFile(
                suffix=f'.{audio_data.format}', 
                delete=False
            ) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            # Convert to mono WAV if needed for better Whisper performance
            if PYDUB_AVAILABLE and (audio_data.channels > 1 or audio_data.format != 'wav'):
                temp_path = await self._convert_to_mono_wav(temp_path, audio_data.format)
            elif not PYDUB_AVAILABLE and audio_data.format != 'wav':
                logger.warning("pydub not available, cannot convert audio format - using original file")
            
            # Transcribe with OpenAI Whisper
            logger.info("Calling OpenAI Whisper API")
            
            with open(temp_path, 'rb') as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json"
                )
            
            # Extract transcription details
            transcribed_text = transcript.text.strip()
            
            if not transcribed_text:
                raise TranscriptionError("Whisper returned empty transcription")
            
            # Get language and confidence if available
            language = getattr(transcript, 'language', None)
            
            # Whisper doesn't provide confidence in the API response
            # We'll set it to None for now
            confidence = None
            
            logger.info(
                f"Transcription successful: {len(transcribed_text)} characters, "
                f"language: {language}"
            )
            
            return TranscriptionResult(
                text=transcribed_text,
                confidence=confidence,
                language=language
            )
            
        except TranscriptionError:
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error during transcription: {e}")
            raise WhisperError(f"OpenAI API error: {str(e)}", {"error_type": "api_error"})
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise RateLimitError("openai", retry_after=getattr(e, 'retry_after', None))
        except openai.APIConnectionError as e:
            logger.error(f"OpenAI connection error: {e}")
            raise WhisperError("Failed to connect to transcription service", {"error_type": "connection_error"})
        except Exception as e:
            logger.error(f"Unexpected error during transcription: {e}")
            raise TranscriptionError(f"Transcription failed: {str(e)}")
        finally:
            # Clean up temporary files
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
    
    async def _convert_to_mono_wav(self, input_path: str, input_format: str) -> str:
        """
        Convert audio to mono WAV format for optimal Whisper performance.
        
        Args:
            input_path: Path to input audio file
            input_format: Format of input audio
            
        Returns:
            Path to converted mono WAV file
            
        Raises:
            AudioProcessingError: If conversion fails
        """
        if not PYDUB_AVAILABLE:
            raise AudioProcessingError("Audio conversion not available - pydub not installed")
            
        try:
            logger.info(f"Converting {input_format} to mono WAV")
            
            # Load audio with pydub
            audio = await asyncio.get_event_loop().run_in_executor(
                self.executor, AudioSegment.from_file, input_path
            )
            
            # Convert to mono
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Create new temporary file for WAV output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_path = temp_file.name
            
            # Export as WAV
            await asyncio.get_event_loop().run_in_executor(
                self.executor, 
                lambda: audio.export(output_path, format="wav")
            )
            
            # Remove original file
            try:
                os.unlink(input_path)
            except OSError:
                pass
            
            logger.info("Successfully converted to mono WAV")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to convert audio to mono WAV: {e}")
            raise AudioProcessingError(f"Audio conversion failed: {str(e)}")
    
    async def process_and_transcribe(self, base64_audio: str) -> TranscriptionResult:
        """
        Complete pipeline: decode base64 audio and transcribe.
        
        Args:
            base64_audio: Base64 encoded audio data
            
        Returns:
            TranscriptionResult with transcribed text
            
        Raises:
            AudioValidationError: If audio validation fails
            AudioProcessingError: If audio processing fails
            TranscriptionError: If transcription fails
        """
        try:
            logger.info("Starting complete audio processing and transcription pipeline")
            
            # Step 1: Decode and validate audio
            audio_data = await self.decode_base64_audio(base64_audio)
            
            # Step 2: Transcribe audio
            result = await self.transcribe_audio(audio_data)
            
            logger.info("Audio processing and transcription pipeline completed successfully")
            return result
            
        except (AudioValidationError, AudioProcessingError, TranscriptionError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in processing pipeline: {e}")
            raise AudioProcessingError(f"Processing pipeline failed: {str(e)}")
    
    def __del__(self):
        """Cleanup executor on service destruction."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)