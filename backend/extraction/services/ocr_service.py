"""German OCR service using PaddleOCR."""
import logging
from typing import Dict, List, Any

from .base_service import BaseExtractionService, ExtractionServiceError

logger = logging.getLogger(__name__)


class GermanOCRService(BaseExtractionService):
    """OCR service for German documents using PaddleOCR."""

    def __init__(self, config: Dict[str, Any], timeout_seconds: int = 300):
        """Initialize OCR service.

        Args:
            config: Configuration dictionary with ocr_* settings
            timeout_seconds: Maximum processing time
        """
        super().__init__(config, timeout_seconds)
        self.ocr = None
        self._initialize()

    def _initialize(self):
        """Initialize PaddleOCR."""
        try:
            from paddleocr import PaddleOCR

            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='german',
                gpu=self.config.get('ocr_use_cuda', False),
            )
            logger.info("GermanOCRService initialized")
        except ImportError:
            logger.warning(
                "PaddleOCR not installed. "
                "Install with: pip install paddleocr"
            )
            self.ocr = None

    def process(self, file_path: str) -> Dict[str, Any]:
        """Extract text from document using PaddleOCR.

        Args:
            file_path: Path to file (PDF, image)

        Returns:
            Dictionary with:
                - text: Extracted OCR text
                - confidence: Average confidence score
                - lines: List of recognized text lines with positions
                - processing_time_ms: Processing time

        Raises:
            ExtractionServiceError: If processing fails
        """
        self._validate_file(
            file_path,
            max_size_mb=self.config.get('max_file_size_mb', 50)
        )

        if not self.ocr:
            raise ExtractionServiceError(
                "PaddleOCR not available. Please install: pip install paddleocr"
            )

        try:
            results, processing_time_ms = self._measure_time(
                self._extract_text,
                file_path
            )
            return {
                'text': results['text'],
                'confidence': results['confidence'],
                'lines': results['lines'],
                'processing_time_ms': processing_time_ms,
            }
        except Exception as e:
            raise ExtractionServiceError(f"OCR processing failed: {str(e)}")

    def _extract_text(self, file_path: str) -> Dict[str, Any]:
        """Extract text from file.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with extracted text and metadata
        """
        # Handle PDF files
        if file_path.lower().endswith('.pdf'):
            return self._extract_from_pdf(file_path)

        # Handle image files
        return self._extract_from_image(file_path)

    def _extract_from_image(self, file_path: str) -> Dict[str, Any]:
        """Extract text from image.

        Args:
            file_path: Path to image file

        Returns:
            Dictionary with text and confidence
        """
        result = self.ocr.ocr(file_path, cls=True)

        text = ""
        confidence_scores = []
        lines = []

        for line in result:
            for word_info in line:
                bbox, text_data = word_info[0], word_info[1]
                word = text_data[0]
                conf = text_data[1]

                text += word + " "
                confidence_scores.append(conf)

                lines.append({
                    'text': word,
                    'confidence': conf,
                    'bbox': bbox,
                })

        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else 0
        )

        return {
            'text': text.strip(),
            'confidence': avg_confidence,
            'lines': lines,
        }

    def _extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF.

        Args:
            file_path: Path to PDF file

        Returns:
            Dictionary with text and confidence
        """
        try:
            from pdf2image import convert_from_path
        except ImportError:
            raise ExtractionServiceError(
                "pdf2image not installed. "
                "Install with: pip install pdf2image pillow"
            )

        text = ""
        confidence_scores = []
        lines = []

        # Convert PDF to images
        images = convert_from_path(file_path, first_page=1, last_page=5)

        for image in images:
            result = self.ocr.ocr(image, cls=True)

            for line in result:
                for word_info in line:
                    bbox, text_data = word_info[0], word_info[1]
                    word = text_data[0]
                    conf = text_data[1]

                    text += word + " "
                    confidence_scores.append(conf)

                    lines.append({
                        'text': word,
                        'confidence': conf,
                        'bbox': bbox,
                    })

        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else 0
        )

        return {
            'text': text.strip(),
            'confidence': avg_confidence,
            'lines': lines,
        }
