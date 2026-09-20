"""
Unit tests for Image Quality Assessment Module.
"""
import pytest
import numpy as np
from PIL import Image

from app.ml.image_quality import check_image_quality, get_farmer_friendly_message


def create_test_image(width=300, height=300, brightness=128, blur=False):
    """Create a test image with specified properties."""
    # Create a solid color image
    img_array = np.full((height, width, 3), brightness, dtype=np.uint8)
    
    if blur:
        # Apply Gaussian blur to simulate a blurry image
        try:
            import cv2
            img_array = cv2.GaussianBlur(img_array, (15, 15), 0)
        except ImportError:
            # If OpenCV not available, just return the solid image
            pass
    
    return Image.fromarray(img_array)


def create_green_leaf_image(width=300, height=300):
    """Create a test image with green leaf-like colors and sharp vein texture."""
    # Create a gradient of green colors
    img_array = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height):
        for j in range(width):
            # Vary green channel to create leaf-like appearance
            green = int(100 + (i / height) * 100)
            img_array[i, j] = [50, green, 30]

    # Add sharp vein structures to simulate high-frequency texture of a real in-focus leaf
    for i in range(0, height, 12):
        img_array[i, :, :] = [30, 220, 20]
    for j in range(0, width, 12):
        img_array[:, j, :] = [20, 70, 10]
    
    return Image.fromarray(img_array)



def test_blur_detection():
    """Test that blurry images are flagged."""
    blurry_image = create_test_image(blur=True)
    result = check_image_quality(blurry_image)
    
    # Should fail due to blur
    assert not result["passed"]
    assert any("too_blurry" in issue for issue in result["issues"])
    assert result["blur_score"] < 100.0  # Below threshold


def test_good_quality_image():
    """Test that good quality images pass all checks."""
    good_image = create_green_leaf_image(width=400, height=400)
    result = check_image_quality(good_image)
    
    # Should pass all checks
    assert result["passed"]
    assert len(result["issues"]) == 0


def test_low_resolution():
    """Test that low resolution images are flagged."""
    low_res_image = create_test_image(width=100, height=100)
    result = check_image_quality(low_res_image)
    
    # Should fail due to low resolution
    assert not result["passed"]
    assert any("too_low_res" in issue for issue in result["issues"])


def test_too_dark():
    """Test that dark images are flagged."""
    dark_image = create_test_image(brightness=20)
    result = check_image_quality(dark_image)
    
    # Should fail due to being too dark
    assert not result["passed"]
    assert any("too_dark" in issue for issue in result["issues"])
    assert result["brightness_score"] < 40.0


def test_too_bright():
    """Test that bright images are flagged."""
    bright_image = create_test_image(brightness=240)
    result = check_image_quality(bright_image)
    
    # Should fail due to being too bright
    assert not result["passed"]
    assert any("too_bright" in issue for issue in result["issues"])
    assert result["brightness_score"] > 220.0


def test_no_plant_detected():
    """Test that images without plant colors are flagged."""
    # Create an image with no green/brown colors (e.g., blue sky)
    img_array = np.zeros((300, 300, 3), dtype=np.uint8)
    img_array[:, :] = [100, 150, 255]  # Blue color
    no_plant_image = Image.fromarray(img_array)
    
    result = check_image_quality(no_plant_image)
    
    # Should fail due to no plant detected
    assert not result["passed"]
    assert any("no_plant_detected" in issue for issue in result["issues"])


def test_farmer_friendly_message():
    """Test that technical issues are converted to farmer-friendly messages."""
    issues = [
        "too_blurry: Image too blurry (score: 50.00, threshold: 100.0)",
        "too_dark: Image too dark (brightness: 30.0, minimum: 40.0)",
    ]
    
    message = get_farmer_friendly_message(issues)
    
    # Should contain farmer-friendly messages
    assert "blurry" in message.lower()
    assert "dark" in message.lower()
    assert "lighting" in message.lower()


def test_multiple_issues():
    """Test that multiple issues are all reported."""
    bad_image = create_test_image(width=150, height=150, brightness=30, blur=True)
    result = check_image_quality(bad_image)
    
    # Should fail with multiple issues
    assert not result["passed"]
    assert len(result["issues"]) >= 2  # At least blur and dark/low-res


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
