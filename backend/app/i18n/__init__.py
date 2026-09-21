# i18n package for KrushiRakshak AI
from app.i18n.catalog import (
    get_locale_from_request,
    translate_disease,
    translate_severity,
    translate_risk_level,
    DISEASE_CATALOG,
    SEVERITY_CATALOG,
    RISK_CATALOG,
)

__all__ = [
    "get_locale_from_request",
    "translate_disease",
    "translate_severity",
    "translate_risk_level",
    "DISEASE_CATALOG",
    "SEVERITY_CATALOG",
    "RISK_CATALOG",
]
