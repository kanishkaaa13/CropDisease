"""Short, spoken-friendly farmer assistant answers."""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.i18n.catalog import get_locale_from_request
from app.models.schemas import AssistantAskRequest, AssistantAskResponse
from app.services.advisory import ADVISORY_DATABASE, generate_advisory_plan

router = APIRouter()


def _find_disease(question: str, supplied: str | None) -> str | None:
    if supplied:
        return supplied
    normalized = question.lower().replace(" ", "_")
    for disease_label in ADVISORY_DATABASE:
        tokens = disease_label.lower().replace("___", " ").replace("_", " ").split()
        if any(token in normalized for token in tokens if len(token) > 4):
            return disease_label
    return None


def _local_answer(payload: AssistantAskRequest, locale: str) -> str:
    disease_label = _find_disease(payload.question, payload.disease_label)
    if not disease_label:
        answers = {
            "en": "Please mention the crop or disease name. You can also ask a field officer for help.",
            "hi": "कृपया फसल या रोग का नाम बताएं। आप खेत अधिकारी से भी सहायता ले सकते हैं।",
            "mr": "कृपया पिकाचे किंवा रोगाचे नाव सांगा. तुम्ही कृषी अधिकाऱ्यांची मदतही घेऊ शकता.",
        }
        return answers[locale]

    plan = generate_advisory_plan(
        disease_label=disease_label,
        severity_pct=payload.severity_pct or 0.0,
        crop_name=payload.crop_name or "Crop",
        language_pref=locale,
    )
    treatments = plan["treatments"]
    summary = {
        "en": f"For {plan['disease_name_formatted']}, start with {treatments['cultural'][0] if treatments['cultural'] else 'regular field monitoring'}.",
        "hi": f"{plan['disease_name_formatted']} के लिए {treatments['cultural'][0] if treatments['cultural'] else 'नियमित खेत निरीक्षण'} से शुरुआत करें।",
        "mr": f"{plan['disease_name_formatted']} साठी {treatments['cultural'][0] if treatments['cultural'] else 'नियमित शेत तपासणी'} पासून सुरुवात करा.",
    }
    return summary[locale][:600]


def _configured_llm_answer(payload: AssistantAskRequest, locale: str) -> str | None:
    endpoint = os.getenv("ASSISTANT_LLM_URL")
    if not endpoint:
        return None
    request_body = json.dumps({"question": payload.question, "language": locale, "instruction": "Answer in two short spoken-friendly sentences; do not invent pesticide names or dosages."}).encode()
    request = urllib.request.Request(endpoint, data=request_body, headers={"Content-Type": "application/json"}, method="POST")
    api_key = os.getenv("ASSISTANT_LLM_API_KEY")
    if api_key:
        request.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            data: Any = json.loads(response.read().decode())
        answer = data.get("answer") or data.get("text")
        return str(answer).strip()[:600] if answer else None
    except Exception:
        return None


@router.post("/assistant/ask", response_model=AssistantAskResponse, summary="Answer a farmer voice question")
def ask_assistant(payload: AssistantAskRequest):
    locale = get_locale_from_request(payload.lang)
    answer = _local_answer(payload, locale)
    source = "advisory_kb"
    if answer.startswith("Please mention") or answer.startswith("कृपया"):
        llm_answer = _configured_llm_answer(payload, locale)
        if llm_answer:
            answer = llm_answer
            source = "configured_llm"
    return AssistantAskResponse(answer=answer, language=locale, source=source)
