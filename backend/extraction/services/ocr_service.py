"""German OCR service using PaddleOCR."""
import logging
from typing import Dict, List, Any, Optional

from .base_service import BaseExtractionService, ExtractionServiceError
from .image_preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)


class GermanOCRService(BaseExtractionService):
    """OCR service for German documents using PaddleOCR."""

    def __init__(self, config: Dict[str, Any], timeout_seconds: int = 300):
        """Initialize OCR service.

        Args:
            config: Configuration dictionary with ocr_* settings:
                - ocr_use_preprocessing: Enable image preprocessing (default: True)
                - ocr_confidence_threshold: Threshold for retry (default: 0.7)
                - ocr_use_cuda: Use GPU (default: False)
                - ocr_max_file_size_mb: Max file size (default: 50)
            timeout_seconds: Maximum processing time
        """
        super().__init__(config, timeout_seconds)
        self.ocr = None
        self.preprocessor = None
        self._initialize()

    def _initialize(self):
        """Initialize PaddleOCR and image preprocessor."""
        try:
            from paddleocr import PaddleOCR

            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang='german',
                gpu=self.config.get('ocr_use_cuda', False),
            )

            # Initialize preprocessor if enabled
            if self.config.get('ocr_use_preprocessing', True):
                self.preprocessor = ImagePreprocessor(self.config)
                logger.info("GermanOCRService initialized with preprocessing enabled")
            else:
                logger.info("GermanOCRService initialized (preprocessing disabled)")

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
        """Extract text from image with optional preprocessing.

        Args:
            file_path: Path to image file

        Returns:
            Dictionary with text and confidence
        """
        confidence_threshold = self.config.get('ocr_confidence_threshold', 0.7)

        # First attempt: without preprocessing
        result = self.ocr.ocr(file_path, cls=True)
        text, confidence_scores, lines = self._parse_ocr_result(result)
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else 0
        )

        # If confidence is low and preprocessing is available, retry with preprocessing
        if avg_confidence < confidence_threshold and self.preprocessor:
            try:
                logger.debug(
                    f"OCR confidence {avg_confidence:.2f} below threshold {confidence_threshold}. "
                    "Retrying with preprocessing..."
                )

                # Preprocess image
                preprocessed = self.preprocessor.preprocess(file_path)

                # Convert numpy array to PIL Image for OCR
                from PIL import Image as PILImage
                preprocessed_pil = PILImage.fromarray(preprocessed)

                # Retry OCR on preprocessed image
                result_preprocessed = self.ocr.ocr(preprocessed_pil, cls=True)
                text_pp, conf_scores_pp, lines_pp = self._parse_ocr_result(result_preprocessed)
                avg_confidence_pp = (
                    sum(conf_scores_pp) / len(conf_scores_pp)
                    if conf_scores_pp else 0
                )

                # Use preprocessed result if better
                if avg_confidence_pp > avg_confidence:
                    logger.debug(
                        f"Preprocessing improved confidence: {avg_confidence:.2f} → {avg_confidence_pp:.2f}"
                    )
                    text, confidence_scores, lines = text_pp, conf_scores_pp, lines_pp
                    avg_confidence = avg_confidence_pp
                else:
                    logger.debug(
                        f"Preprocessing did not improve confidence, using original"
                    )

            except Exception as e:
                logger.warning(f"Preprocessing failed, using original OCR result: {str(e)}")

        return {
            'text': text.strip(),
            'confidence': avg_confidence,
            'lines': lines,
        }

    def _parse_ocr_result(self, result: List) -> tuple:
        """Parse OCR result from PaddleOCR.

        Args:
            result: OCR result from PaddleOCR

        Returns:
            Tuple of (text, confidence_scores, lines)
        """
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

        return text, confidence_scores, lines

    def _extract_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF with optional preprocessing.

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
        confidence_threshold = self.config.get('ocr_confidence_threshold', 0.7)

        # Convert PDF to images (limit to 5 pages)
        images = convert_from_path(file_path, first_page=1, last_page=5)

        for page_num, image in enumerate(images, 1):
            # First attempt: without preprocessing
            result = self.ocr.ocr(image, cls=True)
            page_text, page_confidences, page_lines = self._parse_ocr_result(result)
            page_avg_conf = (
                sum(page_confidences) / len(page_confidences)
                if page_confidences else 0
            )

            # If confidence is low and preprocessing is available, retry with preprocessing
            if page_avg_conf < confidence_threshold and self.preprocessor:
                try:
                    logger.debug(
                        f"Page {page_num}: OCR confidence {page_avg_conf:.2f} below threshold. "
                        "Retrying with preprocessing..."
                    )

                    # Preprocess image
                    preprocessed = self.preprocessor.preprocess(image)

                    # Convert numpy array to PIL Image for OCR
                    from PIL import Image as PILImage
                    preprocessed_pil = PILImage.fromarray(preprocessed)

                    # Retry OCR on preprocessed image
                    result_preprocessed = self.ocr.ocr(preprocessed_pil, cls=True)
                    text_pp, conf_scores_pp, lines_pp = self._parse_ocr_result(result_preprocessed)
                    page_avg_conf_pp = (
                        sum(conf_scores_pp) / len(conf_scores_pp)
                        if conf_scores_pp else 0
                    )

                    # Use preprocessed result if better
                    if page_avg_conf_pp > page_avg_conf:
                        logger.debug(
                            f"Page {page_num}: Preprocessing improved confidence: "
                            f"{page_avg_conf:.2f} → {page_avg_conf_pp:.2f}"
                        )
                        page_text, page_confidences, page_lines = text_pp, conf_scores_pp, lines_pp
                        page_avg_conf = page_avg_conf_pp

                except Exception as e:
                    logger.warning(
                        f"Page {page_num}: Preprocessing failed, using original: {str(e)}"
                    )

            # Add page results to overall results
            text += page_text + " "
            confidence_scores.extend(page_confidences)
            lines.extend(page_lines)

        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else 0
        )

        return {
            'text': text.strip(),
            'confidence': avg_confidence,
            'lines': lines,
        }
