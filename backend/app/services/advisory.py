"""
Advisory Service
----------------
Generates human-readable treatment/prevention advisories based on
detected disease + severity. In production, this can call an LLM or a
pre-built rule database.
"""

ADVISORIES: dict[str, dict] = {
    "Wheat Rust": {
        "low": "Monitor crop closely. Ensure proper spacing for air circulation.",
        "medium": "Apply fungicide (Propiconazole 25% EC) at recommended dose. Remove infected leaves.",
        "high": "Urgent: Apply systemic fungicide immediately. Alert district agriculture officer. Consider crop insurance claim.",
    },
    "Rice Blast": {
        "low": "Avoid excess nitrogen fertilization. Monitor daily.",
        "medium": "Spray Tricyclazole 75% WP at 0.6 g/L. Drain and re-irrigate after 3 days.",
        "high": "Immediate fungicide application required. Report to block-level officer for area assessment.",
    },
    "Early Blight": {
        "low": "Remove and destroy infected leaves. Apply copper-based fungicide.",
        "medium": "Spray Mancozeb 75% WP every 7 days. Improve drainage.",
        "high": "Intensive spray schedule needed. Consider replanting with resistant variety.",
    },
    "Late Blight": {
        "low": "Remove infected tissue. Apply preventive Metalaxyl + Mancozeb.",
        "medium": "Weekly fungicide application. Avoid overhead irrigation.",
        "high": "Emergency: High spread risk. Notify district office. Apply Cymoxanil 8% + Mancozeb 64% WP.",
    },
    "Healthy": {
        "none": "No disease detected. Continue regular monitoring and good agricultural practices.",
    },
}

DEFAULT_ADVISORY = "Consult your local Krishi Vigyan Kendra (KVK) for tailored advice."


def generate_advisory(disease_name: str, severity: str, crop_type: str) -> str:
    """Return a plain-text advisory for the given disease/severity combination."""
    disease_advisories = ADVISORIES.get(disease_name, {})
    return disease_advisories.get(severity, DEFAULT_ADVISORY)
