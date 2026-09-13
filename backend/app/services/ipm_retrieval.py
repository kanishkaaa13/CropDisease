"""
IPM Knowledge Retrieval Engine.
Loads structured Integrated Pest Management guidance for crops
(cotton, soybean, onion, tomato, chilli, grapes, pomegranate).
Performs exact match lookup, fuzzy string similarity fallback (difflib),
or safe generic fallback to prevent LLM hallucinations.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import difflib

logger = logging.getLogger(__name__)

KB_PATH = Path(__file__).parent.parent / "db" / "ipm_knowledge_base.json"

_IPM_KB_CACHE: Optional[Dict[str, Any]] = None


def load_ipm_knowledge_base() -> Dict[str, Any]:
    """Load cached IPM knowledge base JSON from disk."""
    global _IPM_KB_CACHE
    if _IPM_KB_CACHE is not None:
        return _IPM_KB_CACHE

    if not KB_PATH.exists():
        logger.warning("IPM knowledge base file not found at %s. Using empty dict.", KB_PATH)
        return {}

    try:
        with open(KB_PATH, "r", encoding="utf-8") as f:
            _IPM_KB_CACHE = json.load(f)
            logger.info("Successfully loaded IPM Knowledge Base with %d crops.", len(_IPM_KB_CACHE))
            return _IPM_KB_CACHE
    except Exception as exc:
        logger.error("Failed to load IPM knowledge base JSON: %s", exc)
        return {}


def normalize_token(text: str) -> str:
    """Clean and normalize crop or pathogen string tokens."""
    if not text:
        return ""
    # Handle class labels like "Tomato___Early_blight" -> "early blight"
    cleaned = text.replace("___", " ").replace("_", " ").strip().lower()
    return cleaned


def retrieve_ipm_entry(crop_name: str, disease_or_pest: str) -> Tuple[Dict[str, Any], str, bool]:
    """
    Retrieve IPM Knowledge Base entry for a given crop and disease/pest.

    Returns:
        - kb_entry (dict): IPM knowledge structure
        - match_confidence (str): "exact_match", "fuzzy_match", or "generic_fallback"
        - kb_found (bool): True if exact or fuzzy match was found
    """
    kb = load_ipm_knowledge_base()

    norm_crop = normalize_token(crop_name)
    norm_pathogen = normalize_token(disease_or_pest)

    # 1. Exact Match Check
    for kb_crop_key, crop_entries in kb.items():
        if normalize_token(kb_crop_key) in norm_crop or norm_crop in normalize_token(kb_crop_key):
            # Crop matched, check disease/pest key
            for pest_key, entry_data in crop_entries.items():
                norm_pest_key = normalize_token(pest_key)
                norm_disease_or_pest = normalize_token(entry_data.get("disease_or_pest", ""))

                if (norm_pest_key in norm_pathogen or norm_pathogen in norm_pest_key or
                        norm_disease_or_pest in norm_pathogen or norm_pathogen in norm_disease_or_pest):
                    return entry_data, "exact_match", True

    # 2. Fuzzy Match Fallback (using difflib.SequenceMatcher)
    best_match_entry = None
    best_score = 0.0

    for kb_crop_key, crop_entries in kb.items():
        crop_sim = difflib.SequenceMatcher(None, norm_crop, normalize_token(kb_crop_key)).ratio()
        # Allow crop match if similarity > 0.4 or if token overlap
        if crop_sim > 0.40 or normalize_token(kb_crop_key) in norm_crop:
            for pest_key, entry_data in crop_entries.items():
                pest_sim = difflib.SequenceMatcher(None, norm_pathogen, normalize_token(pest_key)).ratio()
                full_sim = difflib.SequenceMatcher(None, norm_pathogen, normalize_token(entry_data.get("disease_or_pest", ""))).ratio()
                score = max(pest_sim, full_sim)

                if score > best_score:
                    best_score = score
                    best_match_entry = entry_data

    if best_match_entry and best_score > 0.35:
        logger.info("Fuzzy match found for crop='%s', pathogen='%s' (score=%.2f)", crop_name, disease_or_pest, best_score)
        return best_match_entry, "fuzzy_match", True

    # 3. Generic Safe Fallback (Prevent Hallucinations)
    logger.info("No KB match for crop='%s', pathogen='%s'. Returning safe generic fallback.", crop_name, disease_or_pest)
    generic_entry = {
        "crop": crop_name.capitalize(),
        "disease_or_pest": disease_or_pest.replace("___", " - ").replace("_", " ").title(),
        "symptoms": [
            "Leaf spot, foliage discoloration, chlorosis, or pest feeding damage observed on crop canopy."
        ],
        "cultural_controls": [
            "Remove and safely destroy heavily infected leaves and crop debris away from field.",
            "Avoid overhead sprinkler irrigation; use drip lines to keep leaf foliage dry.",
            "Ensure proper weed management along field perimeters to eliminate vector harbors."
        ],
        "biological_controls": [
            "Apply Neem Oil extract (10,000 ppm) @ 3 ml/L of water as a natural bio-repellent.",
            "Foliar spray of Trichoderma viride or Pseudomonas fluorescens bio-agents @ 5 g/L."
        ],
        "chemical_control_guidance": [
            "Consult your local Krishi Vigyan Kendra (KVK) or district agricultural extension officer for government-approved commercial products registered for your state under CIBRC.",
            "Never apply unverified chemical mixtures or illegal pesticide dosages."
        ],
        "monitoring_recommendations": [
            "Inspect crops twice weekly and consult local extension officers for state-approved commercial products."
        ]
    }

    return generic_entry, "generic_fallback", False
