"""Image preprocessing service for OCR accuracy improvement."""
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageEnhance
import io

logger = logging.getLogger(__name__)


class ImagePreprocessor:
    """Preprocess images to improve OCR accuracy."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize image preprocessor.

        Args:
            config: Configuration dictionary with preprocessing settings
                - deskew_enabled: Enable deskew (default: True)
                - denoise_enabled: Enable denoise (default: True)
                - contrast_enabled: Enable contrast enhancement (default: True)
                - binarize_enabled: Enable binarization (default: True)
                - deskew_threshold: Angle threshold for deskew (default: 0.5)
        """
        self.config = config or {}
        self.deskew_enabled = self.config.get('deskew_enabled', True)
        self.denoise_enabled = self.config.get('denoise_enabled', True)
        self.contrast_enabled = self.config.get('contrast_enabled', True)
        self.binarize_enabled = self.config.get('binarize_enabled', True)
        self.deskew_threshold = self.config.get('deskew_threshold', 0.5)

    def preprocess(self, image_input: Any, timeout_seconds: float = 5.0) -> np.ndarray:
        """Apply preprocessing pipeline to image.

        Args:
            image_input: Image path (str/Path) or PIL Image or numpy array
            timeout_seconds: Maximum time for preprocessing (not enforced, for planning)

        Returns:
            Preprocessed image as numpy array (BGR format for OpenCV)

        Raises:
            ValueError: If image cannot be loaded or processed
        """
        try:
            # Load image if needed
            image = self._load_image(image_input)

            # Convert to grayscale for processing
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Apply preprocessing steps in order
            if self.deskew_enabled:
                gray = self.deskew(gray)
                logger.debug("Deskew applied")

            if self.denoise_enabled:
                gray = self.denoise(gray)
                logger.debug("Denoise applied")

            if self.contrast_enabled:
                gray = self.enhance_contrast(gray)
                logger.debug("Contrast enhancement applied")

            if self.binarize_enabled:
                gray = self.binarize(gray)
                logger.debug("Binarization applied")

            return gray

        except Exception as e:
            raise ValueError(f"Image preprocessing failed: {str(e)}")

    def _load_image(self, image_input: Any) -> np.ndarray:
        """Load image from various input types.

        Args:
            image_input: Path, PIL Image, or numpy array

        Returns:
            Image as numpy array (BGR format)
        """
        if isinstance(image_input, (str, Path)):
            # Load from file path
            image = cv2.imread(str(image_input))
            if image is None:
                raise ValueError(f"Cannot load image: {image_input}")
            return image

        elif isinstance(image_input, Image.Image):
            # Convert PIL Image to numpy array
            image = np.array(image_input)
            if len(image.shape) == 3 and image.shape[2] == 3:
                # Convert RGB to BGR
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            return image

        elif isinstance(image_input, np.ndarray):
            # Already numpy array
            return image_input

        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

    def deskew(self, image: np.ndarray) -> np.ndarray:
        """Detect and correct document rotation.

        Uses contour detection and Hough transform to find document edges
        and correct rotation angle.

        Args:
            image: Grayscale image

        Returns:
            Deskewed image
        """
        try:
            # Get image dimensions
            height, width = image.shape

            # Apply threshold to get binary image
            _, binary = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY)

            # Find contours
            contours, _ = cv2.findContours(
                binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                logger.debug("No contours found for deskew, returning original")
                return image

            # Get largest contour (likely the document)
            largest_contour = max(contours, key=cv2.contourArea)

            # Get rotated rectangle
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]

            # Normalize angle
            if angle < -45:
                angle = 90 + angle
            if angle > 45:
                angle = angle - 90

            # Only rotate if angle is significant
            if abs(angle) < self.deskew_threshold:
                logger.debug(f"Angle {angle:.2f} below threshold, skipping deskew")
                return image

            # Apply rotation
            center = (width // 2, height // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            deskewed = cv2.warpAffine(
                image, rotation_matrix, (width, height),
                borderMode=cv2.BORDER_REFLECT,
                flags=cv2.INTER_LINEAR
            )

            logger.debug(f"Deskew applied with angle: {angle:.2f}°")
            return deskewed

        except Exception as e:
            logger.warning(f"Deskew failed: {str(e)}, returning original image")
            return image

    def denoise(self, image: np.ndarray) -> np.ndarray:
        """Remove scan artifacts and noise.

        Uses bilateral filtering (preserves edges) combined with morphological
        operations to remove small noise while preserving text.

        Args:
            image: Grayscale image

        Returns:
            Denoised image
        """
        try:
            # Apply bilateral filter (edge-preserving noise reduction)
            denoised = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)

            # Apply morphological opening to remove small noise
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            denoised = cv2.morphologyEx(denoised, cv2.MORPH_OPEN, kernel, iterations=1)

            # Apply small closing to fill gaps in text
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
            denoised = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel, iterations=1)

            logger.debug("Denoise applied successfully")
            return denoised

        except Exception as e:
            logger.warning(f"Denoise failed: {str(e)}, returning original image")
            return image

    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance image contrast using CLAHE.

        CLAHE (Contrast Limited Adaptive Histogram Equalization) improves contrast
        without over-amplifying noise in homogeneous areas.

        Args:
            image: Grayscale image

        Returns:
            Contrast-enhanced image
        """
        try:
            # Create CLAHE object
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(image)

            logger.debug("Contrast enhancement applied successfully")
            return enhanced

        except Exception as e:
            logger.warning(f"Contrast enhancement failed: {str(e)}, returning original")
            return image

    def binarize(self, image: np.ndarray) -> np.ndarray:
        """Convert to binary (black and white) for cleaner OCR.

        Uses adaptive thresholding (Otsu's method) to handle varying lighting
        conditions across the document.

        Args:
            image: Grayscale image

        Returns:
            Binary image (0 or 255 values only)
        """
        try:
            # Apply Gaussian blur to reduce noise before thresholding
            blurred = cv2.GaussianBlur(image, (5, 5), 0)

            # Use adaptive thresholding (Otsu) for better results with varying lighting
            _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            logger.debug("Binarization applied successfully")
            return binary

        except Exception as e:
            logger.warning(f"Binarization failed: {str(e)}, returning original")
            return image

    def get_preprocessing_stats(self, image: np.ndarray, preprocessed: np.ndarray) -> Dict[str, Any]:
        """Calculate statistics on preprocessing impact.

        Args:
            image: Original image
            preprocessed: Preprocessed image

        Returns:
            Dictionary with statistics:
                - original_mean: Mean pixel value (brightness)
                - preprocessed_mean: Mean pixel value after preprocessing
                - original_std: Standard deviation
                - preprocessed_std: Standard deviation after preprocessing
                - contrast_improvement: Percentage improvement in contrast
        """
        orig_mean = float(cv2.mean(image)[0])
        orig_std = float(cv2.meanStdDev(image)[1][0])

        prep_mean = float(cv2.mean(preprocessed)[0])
        prep_std = float(cv2.meanStdDev(preprocessed)[1][0])

        contrast_improvement = ((prep_std - orig_std) / orig_std * 100) if orig_std > 0 else 0

        return {
            'original_mean': orig_mean,
            'preprocessed_mean': prep_mean,
            'original_std': orig_std,
            'preprocessed_std': prep_std,
            'contrast_improvement_percent': contrast_improvement,
        }
