"""Shared translation catalog for API-facing agricultural labels."""

from __future__ import annotations

import re
from typing import Mapping, Optional

SUPPORTED_LOCALES = ("en", "hi", "mr")
DEFAULT_LOCALE = "en"


def _entry(en: str, hi: str, mr: str) -> dict[str, str]:
    return {"en": en, "hi": hi, "mr": mr}


DISEASE_CATALOG: dict[str, dict[str, str]] = {
    "tomato_bacterial_spot": _entry("Tomato bacterial spot", "टमाटर बैक्टीरियल स्पॉट", "टोमॅटो बॅक्टेरियल स्पॉट"),
    "tomato_early_blight": _entry("Tomato early blight", "टमाटर अर्ली ब्लाइट", "टोमॅटो अर्ली ब्लाइट"),
    "tomato_late_blight": _entry("Tomato late blight", "टमाटर लेट ब्लाइट", "टोमॅटो लेट ब्लाइट"),
    "tomato_leaf_mold": _entry("Tomato leaf mold", "टमाटर लीफ मोल्ड", "टोमॅटो लीफ मोल्ड"),
    "tomato_septoria_leaf_spot": _entry("Tomato Septoria leaf spot", "टमाटर सेप्टोरिया लीफ स्पॉट", "टोमॅटो सेप्टोरिया लीफ स्पॉट"),
    "tomato_spider_mites": _entry("Tomato spider mites", "टमाटर स्पाइडर माइट्स", "टोमॅटो स्पायडर माइट्स"),
    "tomato_target_spot": _entry("Tomato target spot", "टमाटर टार्गेट स्पॉट", "टोमॅटो टार्गेट स्पॉट"),
    "tomato_yellow_leaf_curl_virus": _entry("Tomato yellow leaf curl virus", "टमाटर येलो लीफ कर्ल वायरस", "टोमॅटो यलो लीफ कर्ल विषाणू"),
    "tomato_mosaic_virus": _entry("Tomato mosaic virus", "टमाटर मोज़ेक वायरस", "टोमॅटो मोझॅक विषाणू"),
    "tomato_healthy": _entry("Healthy tomato", "स्वस्थ टमाटर", "निरोगी टोमॅटो"),
    "cotton_bacterial_blight": _entry("Cotton bacterial blight", "कपास बैक्टीरियल ब्लाइट", "कापूस बॅक्टेरियल ब्लाइट"),
    "cotton_pink_bollworm": _entry("Cotton pink bollworm", "कपास गुलाबी सुंडी", "कापूस गुलाबी बोंडअळी"),
    "cotton_healthy": _entry("Healthy cotton", "स्वस्थ कपास", "निरोगी कापूस"),
    "rice_blast": _entry("Rice blast", "धान का ब्लास्ट", "भाताचा ब्लास्ट"),
    "rice_brown_spot": _entry("Rice brown spot", "धान का ब्राउन स्पॉट", "भाताचा ब्राउन स्पॉट"),
    "rice_healthy": _entry("Healthy rice", "स्वस्थ धान", "निरोगी भात"),
}

SEVERITY_CATALOG: dict[str, dict[str, str]] = {
    "low": _entry("Low", "कम", "कमी"),
    "moderate": _entry("Moderate", "मध्यम", "मध्यम"),
    "high": _entry("High", "उच्च", "जास्त"),
    "critical": _entry("Critical", "गंभीर", "अत्यंत गंभीर"),
}

RISK_CATALOG = SEVERITY_CATALOG


def _normalize_locale(value: Optional[str]) -> str:
    if not value:
        return DEFAULT_LOCALE
    candidate = value.strip().lower().replace("_", "-").split("-", 1)[0]
    return candidate if candidate in SUPPORTED_LOCALES else DEFAULT_LOCALE


def get_locale_from_request(lang: Optional[str] = None, accept_language: Optional[str] = None) -> str:
    """Resolve an API locale from an explicit query/body value or HTTP header."""
    if lang:
        return _normalize_locale(lang)
    if accept_language:
        for candidate in accept_language.split(","):
            locale = _normalize_locale(candidate.split(";", 1)[0])
            if locale in SUPPORTED_LOCALES:
                return locale
    return DEFAULT_LOCALE


def disease_key(disease_name: str) -> str:
    """Convert model labels such as ``Tomato___Early_blight`` to a stable key."""
    normalized = re.sub(r"[^a-z0-9]+", "_", (disease_name or "unknown").lower()).strip("_")
    return normalized


def translate_disease(disease_name: str, lang: str = DEFAULT_LOCALE) -> str:
    key = disease_key(disease_name)
    return DISEASE_CATALOG.get(key, {}).get(_normalize_locale(lang), _format_label(disease_name))


def translate_severity(severity: str, lang: str = DEFAULT_LOCALE) -> str:
    key = (severity or "moderate").lower().strip()
    return SEVERITY_CATALOG.get(key, {}).get(_normalize_locale(lang), severity)


def translate_risk_level(risk_level: str, lang: str = DEFAULT_LOCALE) -> str:
    return translate_severity((risk_level or "moderate").lower(), lang)


def _format_label(value: str) -> str:
    return (value or "Unknown").replace("___", " - ").replace("_", " ").strip().title()


__all__ = [
    "DEFAULT_LOCALE",
    "SUPPORTED_LOCALES",
    "DISEASE_CATALOG",
    "SEVERITY_CATALOG",
    "RISK_CATALOG",
    "disease_key",
    "get_locale_from_request",
    "translate_disease",
    "translate_severity",
    "translate_risk_level",
]
