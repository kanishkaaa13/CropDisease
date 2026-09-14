"""
Unit tests for DiseaseClassifier module.
"""
import pytest
from PIL import Image
import numpy as np

from app.ml.disease_classifier import predict_disease, DiseaseProbability, get_disease_classifier


def create_test_image(width=300, height=300):
    """Create a simple test image."""
    img_array = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    return Image.fromarray(img_array)


def test_predict_disease_returns_correct_structure():
    """Test that predict_disease returns DiseaseProbability structure."""
    test_image = create_test_image()
    result = predict_disease(test_image)
    
    # Check that result has correct keys
    assert "predicted_label" in result
    assert "confidence" in result
    assert "top3" in result
    assert "is_low_confidence" in result
    
    # Check types
    assert isinstance(result["predicted_label"], str)
    assert isinstance(result["confidence"], float)
    assert isinstance(result["top3"], list)
    assert isinstance(result["is_low_confidence"], bool)
    
    # Check top3 structure
    assert len(result["top3"]) == 3
    for pred in result["top3"]:
        assert "label" in pred
        assert "confidence" in pred


def test_predict_disease_confidence_range():
    """Test that confidence is between 0 and 1."""
    test_image = create_test_image()
    result = predict_disease(test_image)
    
    assert 0.0 <= result["confidence"] <= 1.0


def test_predict_disease_top3_confidence_sum():
    """Test that top3 confidences sum to approximately 1 (or less in mock mode)."""
    test_image = create_test_image()
    result = predict_disease(test_image)
    
    total_confidence = sum(pred["confidence"] for pred in result["top3"])
    # In mock mode, sum might not be exactly 1, but should be reasonable
    assert 0.0 < total_confidence <= 1.0


def test_predict_disease_low_confidence_threshold():
    """Test that is_low_confidence is set correctly based on confidence."""
    test_image = create_test_image()
    result = predict_disease(test_image)
    
    # If confidence < 0.6, is_low_confidence should be True
    if result["confidence"] < 0.6:
        assert result["is_low_confidence"] is True
    else:
        assert result["is_low_confidence"] is False


def test_get_disease_classifier_singleton():
    """Test that get_disease_classifier returns the same instance."""
    classifier1 = get_disease_classifier()
    classifier2 = get_disease_classifier()
    
    assert classifier1 is classifier2


def test_predict_disease_standalone():
    """Test that predict_disease can be called independently."""
    test_image = create_test_image()
    
    # This should work without any FastAPI context
    result = predict_disease(test_image)
    
    assert result is not None
    assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
