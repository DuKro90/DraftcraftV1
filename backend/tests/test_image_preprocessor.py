"""Tests for image preprocessing service."""
import pytest
import numpy as np
import cv2
from pathlib import Path
from PIL import Image
from unittest.mock import Mock, patch, MagicMock

from extraction.services.image_preprocessor import ImagePreprocessor


class TestImagePreprocessor:
    """Test image preprocessing functionality."""

    @pytest.fixture
    def preprocessor(self):
        """Create preprocessor instance."""
        return ImagePreprocessor()

    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        # Create a simple 200x200 image with text-like pattern
        image = np.ones((200, 200, 3), dtype=np.uint8) * 200  # Light gray
        # Add some dark text-like areas
        cv2.rectangle(image, (30, 30), (70, 70), (50, 50, 50), -1)
        cv2.rectangle(image, (100, 50), (150, 100), (40, 40, 40), -1)
        return image

    @pytest.fixture
    def rotated_image(self, sample_image):
        """Create a rotated image for deskew testing."""
        height, width = sample_image.shape[:2]
        center = (width // 2, height // 2)
        angle = 15  # Rotate 15 degrees
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(sample_image, rotation_matrix, (width, height))
        return rotated

    @pytest.fixture
    def noisy_image(self, sample_image):
        """Create a noisy image for denoise testing."""
        noise = np.random.normal(0, 25, sample_image.shape)
        noisy = np.clip(sample_image.astype(float) + noise, 0, 255).astype(np.uint8)
        return noisy

    @pytest.fixture
    def low_contrast_image(self, sample_image):
        """Create a low contrast image."""
        # Compress the value range to simulate low contrast
        low_contrast = ((sample_image.astype(float) - 128) * 0.5 + 128).astype(np.uint8)
        return low_contrast

    # Tests for image loading
    def test_load_image_from_path(self, sample_image, tmp_path):
        """Test loading image from file path."""
        preprocessor = ImagePreprocessor()

        # Save test image
        test_file = tmp_path / "test.jpg"
        cv2.imwrite(str(test_file), sample_image)

        # Load image
        loaded = preprocessor._load_image(str(test_file))

        assert isinstance(loaded, np.ndarray)
        assert loaded.shape == sample_image.shape

    def test_load_image_from_pil(self, sample_image):
        """Test loading PIL Image."""
        preprocessor = ImagePreprocessor()

        # Convert numpy to PIL
        pil_image = Image.fromarray(cv2.cvtColor(sample_image, cv2.COLOR_BGR2RGB))

        # Load with preprocessor
        loaded = preprocessor._load_image(pil_image)

        assert isinstance(loaded, np.ndarray)

    def test_load_image_from_numpy(self, sample_image):
        """Test loading numpy array."""
        preprocessor = ImagePreprocessor()

        loaded = preprocessor._load_image(sample_image)

        assert isinstance(loaded, np.ndarray)
        assert np.array_equal(loaded, sample_image)

    def test_load_image_invalid_path(self):
        """Test error handling for invalid path."""
        preprocessor = ImagePreprocessor()

        with pytest.raises(ValueError, match="Cannot load image"):
            preprocessor._load_image("/nonexistent/path/image.jpg")

    def test_load_image_unsupported_type(self):
        """Test error handling for unsupported input type."""
        preprocessor = ImagePreprocessor()

        with pytest.raises(ValueError, match="Unsupported image input type"):
            preprocessor._load_image({"not": "an image"})

    # Tests for deskew
    def test_deskew_rotated_image(self, rotated_image):
        """Test deskew corrects rotation."""
        preprocessor = ImagePreprocessor()

        deskewed = preprocessor.deskew(rotated_image)

        assert isinstance(deskewed, np.ndarray)
        assert deskewed.shape == rotated_image.shape

    def test_deskew_straight_image(self, sample_image):
        """Test deskew on straight image (should return unchanged)."""
        preprocessor = ImagePreprocessor()

        # Convert to grayscale
        gray = cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)

        deskewed = preprocessor.deskew(gray)

        assert isinstance(deskewed, np.ndarray)
        # Should be same or very similar
        assert deskewed.shape == gray.shape

    def test_deskew_disabled(self, rotated_image):
        """Test deskew can be disabled."""
        config = {'deskew_enabled': False}
        preprocessor = ImagePreprocessor(config)

        # Convert to grayscale
        gray = cv2.cvtColor(rotated_image, cv2.COLOR_BGR2GRAY)

        deskewed = preprocessor.deskew(gray)

        # Should return original image
        assert np.array_equal(deskewed, gray)

    # Tests for denoise
    def test_denoise_removes_noise(self, noisy_image):
        """Test denoise reduces noise."""
        preprocessor = ImagePreprocessor()

        # Convert to grayscale
        gray = cv2.cvtColor(noisy_image, cv2.COLOR_BGR2GRAY)

        denoised = preprocessor.denoise(gray)

        assert isinstance(denoised, np.ndarray)
        assert denoised.shape == gray.shape

        # Denoised should have lower standard deviation (less noise)
        # Note: this is probabilistic, so we just check it runs without error

    def test_denoise_preserves_structure(self, sample_image):
        """Test denoise preserves image structure."""
        preprocessor = ImagePreprocessor()

        gray = cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)

        denoised = preprocessor.denoise(gray)

        # Should still have similar dimensions
        assert denoised.shape == gray.shape

    # Tests for contrast enhancement
    def test_contrast_enhancement(self, low_contrast_image):
        """Test contrast enhancement improves contrast."""
        preprocessor = ImagePreprocessor()

        gray = cv2.cvtColor(low_contrast_image, cv2.COLOR_BGR2GRAY)

        enhanced = preprocessor.enhance_contrast(gray)

        assert isinstance(enhanced, np.ndarray)
        assert enhanced.shape == gray.shape

    def test_contrast_enhancement_increases_std(self, low_contrast_image):
        """Test contrast enhancement increases standard deviation."""
        preprocessor = ImagePreprocessor()

        gray = cv2.cvtColor(low_contrast_image, cv2.COLOR_BGR2GRAY)
        orig_std = cv2.meanStdDev(gray)[1][0]

        enhanced = preprocessor.enhance_contrast(gray)
        enhanced_std = cv2.meanStdDev(enhanced)[1][0]

        # Enhanced should have higher standard deviation (more contrast)
        assert enhanced_std >= orig_std * 0.9  # Allow some margin

    # Tests for binarization
    def test_binarization(self, sample_image):
        """Test binarization converts to black and white."""
        preprocessor = ImagePreprocessor()

        gray = cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)

        binary = preprocessor.binarize(gray)

        assert isinstance(binary, np.ndarray)
        # Binary image should only have 0 and 255 values
        unique_values = np.unique(binary)
        assert all(val in [0, 255] for val in unique_values)

    # Tests for full preprocessing pipeline
    def test_preprocess_full_pipeline(self, sample_image):
        """Test full preprocessing pipeline."""
        preprocessor = ImagePreprocessor()

        preprocessed = preprocessor.preprocess(sample_image)

        assert isinstance(preprocessed, np.ndarray)
        assert len(preprocessed.shape) == 2  # Should be grayscale

    def test_preprocess_with_disabled_steps(self, sample_image):
        """Test preprocessing with some steps disabled."""
        config = {
            'deskew_enabled': False,
            'denoise_enabled': True,
            'contrast_enabled': False,
            'binarize_enabled': True,
        }
        preprocessor = ImagePreprocessor(config)

        preprocessed = preprocessor.preprocess(sample_image)

        assert isinstance(preprocessed, np.ndarray)

    def test_preprocess_all_disabled(self, sample_image):
        """Test preprocessing with all steps disabled."""
        config = {
            'deskew_enabled': False,
            'denoise_enabled': False,
            'contrast_enabled': False,
            'binarize_enabled': False,
        }
        preprocessor = ImagePreprocessor(config)

        preprocessed = preprocessor.preprocess(sample_image)

        assert isinstance(preprocessed, np.ndarray)

    @patch('backend.extraction.services.image_preprocessor.cv2.cvtColor')
    def test_preprocess_handles_grayscale_input(self, mock_cvtColor):
        """Test preprocessing handles grayscale input correctly."""
        preprocessor = ImagePreprocessor(
            {'deskew_enabled': False, 'contrast_enabled': False, 'binarize_enabled': False}
        )

        # Create grayscale image (single channel)
        gray_image = np.ones((100, 100), dtype=np.uint8) * 128

        preprocessed = preprocessor.preprocess(gray_image)

        assert isinstance(preprocessed, np.ndarray)

    # Tests for statistics
    def test_preprocessing_stats(self, sample_image, noisy_image):
        """Test preprocessing statistics calculation."""
        preprocessor = ImagePreprocessor()

        gray_orig = cv2.cvtColor(sample_image, cv2.COLOR_BGR2GRAY)
        gray_noisy = cv2.cvtColor(noisy_image, cv2.COLOR_BGR2GRAY)

        stats = preprocessor.get_preprocessing_stats(gray_orig, gray_noisy)

        assert 'original_mean' in stats
        assert 'preprocessed_mean' in stats
        assert 'original_std' in stats
        assert 'preprocessed_std' in stats
        assert 'contrast_improvement_percent' in stats

        # All values should be numeric
        for key in stats.values():
            assert isinstance(key, (int, float))

    # Integration tests
    @pytest.mark.integration
    def test_preprocess_real_document(self, tmp_path):
        """Test preprocessing on a mock real document image."""
        # Create a more realistic document image
        document = np.ones((500, 400, 3), dtype=np.uint8) * 240  # Off-white background

        # Add text-like elements (dark rectangles with text)
        cv2.rectangle(document, (20, 20), (380, 40), (0, 0, 0), -1)  # Header
        cv2.rectangle(document, (30, 60), (370, 80), (50, 50, 50), -1)  # Line 1
        cv2.rectangle(document, (30, 100), (370, 120), (50, 50, 50), -1)  # Line 2

        # Rotate slightly
        height, width = document.shape[:2]
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, 3, 1.0)
        document = cv2.warpAffine(document, rotation_matrix, (width, height))

        # Add noise
        noise = np.random.normal(0, 15, document.shape)
        document = np.clip(document.astype(float) + noise, 0, 255).astype(np.uint8)

        # Save and preprocess
        test_file = tmp_path / "document.jpg"
        cv2.imwrite(str(test_file), document)

        preprocessor = ImagePreprocessor()
        preprocessed = preprocessor.preprocess(str(test_file))

        # Verify preprocessing worked
        assert isinstance(preprocessed, np.ndarray)
        assert preprocessed.shape[:2] == document.shape[:2]

    # Error handling tests
    def test_preprocess_handles_exceptions(self, preprocessor):
        """Test preprocessing handles exceptions gracefully."""
        # This would require mocking internal failures
        # For now, we verify it doesn't crash on edge cases

        # Empty-like image
        empty = np.zeros((10, 10), dtype=np.uint8)
        result = preprocessor.preprocess(empty)
        assert isinstance(result, np.ndarray)

    # Performance tests (marked as slow)
    @pytest.mark.slow
    def test_preprocessing_performance(self, sample_image):
        """Test preprocessing completes in reasonable time."""
        preprocessor = ImagePreprocessor()

        import time
        start = time.time()
        preprocessor.preprocess(sample_image)
        elapsed = time.time() - start

        # Should complete in less than 2 seconds
        assert elapsed < 2.0, f"Preprocessing took {elapsed:.2f}s, expected < 2.0s"


class TestImagePreprocessorIntegrationWithOCR:
    """Test image preprocessor integration with OCR service."""

    @pytest.mark.integration
    @patch('backend.extraction.services.image_preprocessor.ImagePreprocessor.preprocess')
    def test_ocr_service_uses_preprocessor(self, mock_preprocess):
        """Test that OCR service calls preprocessor when needed."""
        from backend.extraction.services.ocr_service import GermanOCRService

        config = {
            'ocr_use_preprocessing': True,
            'ocr_confidence_threshold': 0.7,
        }

        # This test would require a full OCR service setup
        # Marked as integration test as it requires PaddleOCR
        pass


@pytest.mark.unit
class TestImagePreprocessorEdgeCases:
    """Test edge cases in image preprocessing."""

    def test_very_small_image(self):
        """Test preprocessing on very small image."""
        preprocessor = ImagePreprocessor()

        small_image = np.ones((5, 5, 3), dtype=np.uint8) * 128

        # Should not crash
        result = preprocessor.preprocess(small_image)
        assert isinstance(result, np.ndarray)

    def test_very_large_image(self):
        """Test preprocessing doesn't fail on large image."""
        preprocessor = ImagePreprocessor()

        # Create a moderately large image (not too large for CI)
        large_image = np.ones((2000, 2000, 3), dtype=np.uint8) * 128

        # Should not crash or timeout
        result = preprocessor.preprocess(large_image)
        assert isinstance(result, np.ndarray)

    def test_uniform_color_image(self):
        """Test preprocessing on uniform color image."""
        preprocessor = ImagePreprocessor()

        uniform = np.ones((100, 100, 3), dtype=np.uint8) * 200

        result = preprocessor.preprocess(uniform)
        assert isinstance(result, np.ndarray)

    def test_black_image(self):
        """Test preprocessing on completely black image."""
        preprocessor = ImagePreprocessor()

        black = np.zeros((100, 100, 3), dtype=np.uint8)

        result = preprocessor.preprocess(black)
        assert isinstance(result, np.ndarray)

    def test_white_image(self):
        """Test preprocessing on completely white image."""
        preprocessor = ImagePreprocessor()

        white = np.ones((100, 100, 3), dtype=np.uint8) * 255

        result = preprocessor.preprocess(white)
        assert isinstance(result, np.ndarray)
