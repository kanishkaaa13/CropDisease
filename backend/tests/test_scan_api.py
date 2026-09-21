"""
Pytest test suite for scan API endpoint (/api/v1/scan).
Tests:
- Valid leaf image upload (HTTP 200)
- Corrupted/truncated JPEG upload (HTTP 400)
- Non-image file upload (HTTP 400)
- Oversized file upload (HTTP 400)
"""
import io
import pytest
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from unittest.mock import MagicMock
from main import app
from app.db.connection import get_db

client = TestClient(app)

# Mock DB dependency for testing when Postgres is offline
def override_get_db():
    mock_db = MagicMock()
    mock_db.query.return_value.join.return_value.filter.return_value.first.return_value = None
    mock_db.query.return_value.first.return_value = None
    yield mock_db

app.dependency_overrides[get_db] = override_get_db


def create_valid_green_leaf_image(width=300, height=300) -> bytes:
    """Create a valid leaf image (uses real dataset leaf if available or textured synthetic leaf)."""
    import glob
    from pathlib import Path
    dataset_dir = Path(__file__).parent.parent / "datasets"
    found_images = glob.glob(str(dataset_dir / "**" / "*.jpg"), recursive=True)
    for img_p in found_images:
        try:
            with Image.open(img_p) as pil_img:
                pil_img.convert("RGB")
            with open(img_p, "rb") as f:
                return f.read()
        except Exception:
            continue

    # Synthetic textured leaf image
    img_array = np.random.randint(50, 200, (height, width, 3), dtype=np.uint8)
    img_array[:, :, 0] = np.clip(img_array[:, :, 0] * 0.2, 0, 50).astype(np.uint8)
    img_array[:, :, 1] = np.clip(img_array[:, :, 1] + 80, 100, 255).astype(np.uint8)
    img_array[:, :, 2] = np.clip(img_array[:, :, 2] * 0.2, 0, 50).astype(np.uint8)
    pil_img = Image.fromarray(img_array)
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG")
    return buf.getvalue()


def test_scan_valid_leaf_image():
    """Test /api/v1/scan with a valid leaf image."""
    img_bytes = create_valid_green_leaf_image()

    response = client.post(
        "/api/scan",
        files={"file": ("valid_leaf.jpg", img_bytes, "image/jpeg")},
        data={"notes": "Test valid leaf scan"}
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()

    assert "label" in data
    assert "confidence" in data
    assert "top3" in data
    assert isinstance(data["top3"], list)
    assert len(data["top3"]) == 3
    assert "severity_estimate" in data
    assert "severity_pct" in data
    assert "gradcam_image_base64" in data
    assert "low_confidence" in data
    assert "status" in data
    assert data["status"] in ["confident", "uncertain"]


def test_scan_corrupted_jpeg():
    """Test /api/v1/scan with corrupted/truncated JPEG bytes."""
    corrupted_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00corrupted_invalid_data_stream_truncation"

    response = client.post(
        "/api/scan",
        files={"file": ("corrupt.jpg", corrupted_bytes, "image/jpeg")}
    )

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "Unable to decode image file" in detail or "corrupted" in detail.lower()


def test_scan_non_image_file():
    """Test /api/v1/scan with a non-image file (e.g. text file)."""
    text_bytes = b"Hello world, this is a plain text file, not an image!"

    response = client.post(
        "/api/scan",
        files={"file": ("document.txt", text_bytes, "text/plain")}
    )

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "Invalid file type" in detail or "image" in detail.lower()


def test_scan_oversized_file():
    """Test /api/v1/scan with a file exceeding maximum allowed size (10MB)."""
    oversized_bytes = b"0" * (11 * 1024 * 1024)  # 11 MB

    response = client.post(
        "/api/scan",
        files={"file": ("large_file.jpg", oversized_bytes, "image/jpeg")}
    )

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "exceeds maximum allowed limit" in detail or "10MB" in detail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
