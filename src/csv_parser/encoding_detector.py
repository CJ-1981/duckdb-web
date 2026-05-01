"""
Encoding detection for CSV files with support for Korean character encodings.

This module provides robust character encoding detection using the chardet
library with fallback sequences for low-confidence detections.
"""

import signal
import logging
from pathlib import Path
from typing import Tuple

import chardet

logger = logging.getLogger(__name__)


# Timeout handler for encoding detection
class TimeoutError(Exception):
    """Custom exception for encoding detection timeout."""
    pass


def _timeout_handler(_signum, _frame):
    """Signal handler for timeout."""
    raise TimeoutError("Encoding detection exceeded 5 second timeout")


# @MX:ANCHOR: [AUTO] Core encoding detection function with timeout protection
# @MX:REASON: Called by CSV import workflows and external CSV processing tools
# @MX:SPEC: SPEC-CSV-001 AC-CSV-012, AC-CSV-014
def detect_encoding(file_path: str, timeout: int = 5) -> Tuple[str, float]:
    """
    Detect character encoding of a CSV file with timeout protection.

    This function uses chardet library to detect file encoding with a
    fallback sequence for low-confidence detections. When confidence is
    below 0.7, it attempts to decode with UTF-8, CP949, and EUC-KR in
    sequence to find a working encoding.

    Args:
        file_path: Path to the CSV file
        timeout: Maximum seconds to spend on detection (default: 5)

    Returns:
        Tuple of (encoding_name, confidence_score)
        - encoding_name: Detected encoding name (e.g., 'utf-8', 'cp949')
        - confidence_score: Confidence score from 0.0 to 1.0

    Raises:
        FileNotFoundError: If file does not exist
        TimeoutError: If detection takes longer than timeout seconds
        ValueError: If file path is invalid or file is empty

    Examples:
        >>> detect_encoding('sample.csv')
        ('utf-8', 0.99)

        >>> detect_encoding('korean.csv')
        ('cp949', 0.85)

        >>> detect_encoding('mixed.csv')
        ('utf-8', 0.65)  # Low confidence triggers fallback
    """
    # Validate file path
    path = Path(file_path)
    if not path.exists():
        logger.error(f">>> [ENCODING DETECTOR] File not found: {file_path}")
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    if not path.is_file():
        logger.error(f">>> [ENCODING DETECTOR] Path is not a file: {file_path}")
        raise ValueError(f"Path is not a file: {file_path}")

    if path.stat().st_size == 0:
        logger.warning(f">>> [ENCODING DETECTOR] Empty file: {file_path}")
        raise ValueError(f"Empty file: {file_path}")

    # Set up signal handler for timeout
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)

    try:
        signal.alarm(timeout)

        # Read file content for detection
        with open(file_path, 'rb') as f:
            raw_data = f.read()

        # Use chardet for initial detection
        result = chardet.detect(raw_data)
        detected_encoding = result.get('encoding', 'utf-8')
        confidence = result.get('confidence', 0.0)

        logger.info(
            f">>> [ENCODING DETECTOR] chardet result: {detected_encoding} "
            f"(confidence: {confidence:.2f})"
        )

        # Normalize encoding names
        if detected_encoding:
            detected_encoding = detected_encoding.lower().replace('-', '_')

        # Fallback sequence for low confidence detections
        if confidence < 0.7:
            logger.warning(
                f">>> [ENCODING DETECTOR] Low confidence ({confidence:.2f}), "
                f"attempting fallback sequence"
            )

            # Fallback priority: UTF-8 -> CP949 -> EUC-KR
            fallback_encodings = ['utf_8', 'cp949', 'euc_kr']

            for enc in fallback_encodings:
                try:
                    # Try to decode with this encoding
                    raw_data.decode(enc)

                    # If successful, verify it produces valid text
                    decoded_text = raw_data.decode(enc)

                    # Basic validation: check for printable characters
                    if decoded_text and any(c.isprintable() for c in decoded_text):
                        logger.info(
                            f">>> [ENCODING DETECTOR] Fallback successful: {enc}"
                        )
                        signal.alarm(0)  # Cancel alarm
                        return (enc.replace('_', '-'), 0.75)  # Moderate confidence for fallback

                except (UnicodeDecodeError, LookupError):
                    continue

            # If all fallbacks fail, return chardet result with low confidence
            logger.warning(
                ">>> [ENCODING DETECTOR] All fallbacks failed, using chardet result"
            )

        signal.alarm(0)  # Cancel alarm

        # Normalize encoding name for return
        normalized_encoding = detected_encoding.replace('_', '-')
        if not normalized_encoding:
            normalized_encoding = 'utf-8'  # Default fallback

        return (normalized_encoding, confidence)

    except TimeoutError as e:
        signal.alarm(0)  # Cancel alarm
        logger.error(f">>> [ENCODING DETECTOR] Timeout after {timeout} seconds")
        raise TimeoutError(f"Encoding detection exceeded {timeout} second timeout") from e

    except Exception as e:
        signal.alarm(0)  # Cancel alarm
        logger.error(
            f">>> [ENCODING DETECTOR] Detection failed: {e}",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "file_path": file_path
            }
        )
        raise

    finally:
        # Restore original signal handler
        signal.signal(signal.SIGALRM, old_handler)
