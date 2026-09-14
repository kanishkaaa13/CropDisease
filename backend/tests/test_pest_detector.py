"""
Unit tests for Pest Detection Module.
"""
import pytest
import numpy as np
from PIL import Image

from app.ml.pest_detector import detect_pests, USE_MOCK_MODE


def create_test_image_with_blobs(width=300, height=300, num_blobs=5):
    """Create a test image with dark blob-like spots."""
    img_array = np.ones((height, width, 3), dtype=np.uint8) * 255  # White background
    
    # Add dark circular blobs
    for _ in range(num_blobs):
        x = np.random.randint(20, width - 20)
        y = np.random.randint(20, height - 20)
        radius = np.random.randint(5, 15)
        
        # Create a dark circle
        y_grid, x_grid = np.ogrid[:height, :width]
        mask = (x_grid - x) ** 2 + (y_grid - y) ** 2 <= radius ** 2
        img_array[mask] = [20, 20, 20]  # Dark gray
    
    return Image.fromarray(img_array)


def test_detect_pests_mock_mode():
    """Test pest detection in mock mode."""
    if not USE_MOCK_MODE:
        pytest.skip("Test only applicable in mock mode")
    
    # Create test image with blobs
    test_image = create_test_image_with_blobs(num_blobs=5)
    
    # Run detection
    result = detect_pests(test_image)
    
    # Check structure
    assert "pest_counts" in result
    assert "total_count" in result
    assert "annotated_image_base64" in result
    
    # Check pest_counts structure
    assert "whitefly" in result["pest_counts"]
    assert "unknown" in result["pest_counts"]
    
    # Total count should be sum of individual counts
    assert result["total_count"] == result["pest_counts"]["whitefly"] + result["pest_counts"]["unknown"]
    
    # Annotated image should be base64 string
    assert isinstance(result["annotated_image_base64"], str)
    assert len(result["annotated_image_base64"]) > 0


def test_detect_pests_empty_image():
    """Test pest detection on empty image (no blobs)."""
    if not USE_MOCK_MODE:
        pytest.skip("Test only applicable in mock mode")
    
    # Create empty white image
    img_array = np.ones((300, 300, 3), dtype=np.uint8) * 255
    test_image = Image.fromarray(img_array)
    
    # Run detection
    result = detect_pests(test_image)
    
    # Should detect no pests
    assert result["total_count"] == 0
    assert result["pest_counts"]["whitefly"] == 0
    assert result["pest_counts"]["unknown"] == 0


def test_detect_pests_many_blobs():
    """Test pest detection with many blobs."""
    if not USE_MOCK_MODE:
        pytest.skip("Test only applicable in mock mode")
    
    # Create test image with many blobs
    test_image = create_test_image_with_blobs(num_blobs=20)
    
    # Run detection
    result = detect_pests(test_image)
    
    # Should detect multiple pests
    assert result["total_count"] > 0


def test_detect_pests_annotated_image():
    """Test that annotated image is generated."""
    if not USE_MOCK_MODE:
        pytest.skip("Test only applicable in mock mode")
    
    test_image = create_test_image_with_blobs(num_blobs=3)
    result = detect_pests(test_image)
    
    # Annotated image should be valid base64
    assert result["annotated_image_base64"] is not None
    assert len(result["annotated_image_base64"]) > 0
    
    # Try to decode to verify it's valid
    import base64
    try:
        decoded = base64.b64decode(result["annotated_image_base64"])
        assert len(decoded) > 0
    except Exception as e:
        pytest.fail(f"Failed to decode base64 image: {e}")


def test_detect_pests_different_sizes():
    """Test pest detection with different blob sizes."""
    if not USE_MOCK_MODE:
        pytest.skip("Test only applicable in mock mode")
    
    # Create image with various blob sizes
    img_array = np.ones((300, 300, 3), dtype=np.uint8) * 255
    
    # Small blob (whitefly-sized)
    x, y, radius = 50, 50, 3
    y_grid, x_grid = np.ogrid[:300, :300]
    mask = (x_grid - x) ** 2 + (y_grid - y) ** 2 <= radius ** 2
    img_array[mask] = [20, 20, 20]
    
    # Large blob
    x, y, radius = 150, 150, 25
    mask = (x_grid - x) ** 2 + (y_grid - y) ** 2 <= radius ** 2
    img_array[mask] = [20, 20, 20]
    
    test_image = Image.fromarray(img_array)
    result = detect_pests(test_image)
    
    # Should detect both blobs
    assert result["total_count"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
