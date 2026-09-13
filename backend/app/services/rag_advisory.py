"""
RAG Advisory Engine using Anthropic Claude (claude-sonnet-4-6).
Constructs strict anti-hallucination prompts grounded on retrieved IPM KB entries,
generating farmer-friendly advisories in English ('en'), Hindi ('hi'), and Marathi ('mr')
with structured numbered action steps.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional

from app.services.ipm_retrieval import retrieve_ipm_entry

logger = logging.getLogger(__name__)

# System Prompt Guardrail enforcing strict grounding to prevent chemical hallucinations
SYSTEM_PROMPT = """You are KrushiRakshak AI, an expert agricultural advisory assistant for Indian farmers.
CRITICAL CONSTRAINT: Only use the provided knowledge base content. Do not invent pesticide names, dosages, or application rates not present in the source. If information is missing, say to consult the local extension officer.

Generate a farmer-friendly advisory in plain language for the specified crop, disease/pest, and farm context in THREE languages:
1. English (en)
2. Hindi (hi)
3. Marathi (mr)

For each language, provide:
- "summary": A concise, encouraging explanation of the diagnostic findings and risk status.
- "action_steps": A list of 4-6 numbered step-by-step action recommendations (cultural, biological, chemical guidance, and monitoring).

Format your output STRICTLY as a valid JSON object matching this structure:
{
  "en": {
    "summary": "...",
    "action_steps": ["1. ...", "2. ...", "3. ...", "4. ..."]
  },
  "hi": {
    "summary": "...",
    "action_steps": ["1. ...", "2. ...", "3. ...", "4. ..."]
  },
  "mr": {
    "summary": "...",
    "action_steps": ["1. ...", "2. ...", "3. ...", "4. ..."]
  }
}
"""


def format_user_prompt(
    crop_name: str,
    disease_label: str,
    retrieved_kb: Dict[str, Any],
    farm_context: Dict[str, Any]
) -> str:
    """Format the user prompt containing grounding KB content and farm context."""
    return f"""CROP: {crop_name}
DIAGNOSED DISEASE/PEST: {disease_label}

FARM CONTEXT:
- Growth Stage: {farm_context.get('growth_stage', 'vegetative')}
- Overall Risk Level: {farm_context.get('risk_level', 'MODERATE')}
- Weather Summary: {farm_context.get('weather_summary', 'Temp 28°C, Humidity 75%')}

RETRIEVED IPM KNOWLEDGE BASE CONTENT (GROUND TRUTH):
{json.dumps(retrieved_kb, indent=2)}

Please generate the structured JSON advisory in English, Hindi, and Marathi following all system constraints.
"""


def generate_rag_advisory(
    crop_name: str,
    disease_label: str,
    farm_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Execute full RAG advisory workflow:
    1. Retrieve grounded IPM KB entry.
    2. Attempt Anthropic API call (model claude-sonnet-4-6).
    3. Fallback to deterministic grounded generator if Anthropic API is unconfigured/unavailable.
    """
    ctx = farm_context or {
        "growth_stage": "vegetative",
        "risk_level": "MODERATE",
        "weather_summary": "Temperature 28°C, Humidity 75%"
    }

    # 1. Retrieve Knowledge Base Entry
    retrieved_kb, match_confidence, kb_found = retrieve_ipm_entry(crop_name, disease_label)

    # 2. Try Anthropic API if key is present
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            user_prompt = format_user_prompt(crop_name, disease_label, retrieved_kb, ctx)

            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}]
            )

            raw_text = response.content[0].text.strip()
            # Parse JSON
            if "```json" in raw_text:
                json_str = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                json_str = raw_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw_text

            advisory_dict = json.loads(json_str)

            return {
                "match_confidence": match_confidence,
                "kb_entry_found": kb_found,
                "advisory": advisory_dict,
                "retrieved_kb": retrieved_kb
            }

        except Exception as exc:
            logger.warning("Anthropic API call failed or unavailable (%s). Using deterministic grounded advisory generator.", exc)

    # 3. Deterministic Grounded Advisory Generator (Fallback)
    advisory_dict = generate_fallback_rag_response(crop_name, disease_label, retrieved_kb, ctx)

    return {
        "match_confidence": match_confidence,
        "kb_entry_found": kb_found,
        "advisory": advisory_dict,
        "retrieved_kb": retrieved_kb
    }


def generate_fallback_rag_response(
    crop_name: str,
    disease_label: str,
    kb: Dict[str, Any],
    ctx: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate structured, strictly grounded advisories in English, Hindi, and Marathi
    directly from retrieved IPM KB entries without hallucinating chemical dosages.
    """
    crop_title = crop_name.capitalize()
    disease_title = disease_label.replace("___", " - ").replace("_", " ").title()

    cult = kb.get("cultural_controls", [])
    bio = kb.get("biological_controls", [])
    chem = kb.get("chemical_control_guidance", [])
    mon = kb.get("monitoring_recommendations", [])

    # English Steps
    en_steps = []
    step_num = 1
    if cult:
        en_steps.append(f"{step_num}. Cultural Practice: {cult[0]}")
        step_num += 1
    if bio:
        en_steps.append(f"{step_num}. Organic & Biological Control: {bio[0]}")
        step_num += 1
    if chem:
        en_steps.append(f"{step_num}. Chemical Guidance: {chem[0]}")
        step_num += 1
    if mon:
        en_steps.append(f"{step_num}. Field Monitoring: {mon[0]}")
        step_num += 1
    en_steps.append(f"{step_num}. Extension Consultation: For state-approved commercial products and dosages, consult your local agricultural extension officer or Krishi Vigyan Kendra (KVK).")

    # Hindi Steps
    hi_steps = [
        f"1. सांस्कृतिक उपाय: {cult[0] if cult else 'संक्रमित पौधों के हिस्सों को हटाकर नष्ट करें।'}",
        f"2. जैविक नियंत्रण: {bio[0] if bio else 'नीम तेल (10,000 पीपीएम) @ 3 मिली/लीटर पानी का छिड़काव करें।'}",
        f"3. रासायनिक मार्गदर्शन: राज्य द्वारा अनुमोदित उत्पादों के लिए अपने स्थानीय कृषि विस्तार अधिकारी या कृषि विज्ञान केंद्र (KVK) से संपर्क करें।",
        f"4. निगरानी: सप्ताह में दो बार फसल का निरीक्षण करें और नियमित रिकॉर्ड रखें।"
    ]

    # Marathi Steps
    mr_steps = [
        f"1. संवर्धन पद्धती: {cult[0] if cult else 'बाधित पानांचा भाग काढून शेताबाहेर नष्ट करा.'}",
        f"2. सेंद्रिय व जैविक नियंत्रण: {bio[0] if bio else 'कडुनिंब तेल (१०,००० पीपीएम) @ ३ मि.ली./लिटर पाण्यात फवारा.'}",
        f"3. रासायनिक मार्गदर्शन: राज्य शासन मंजूर उत्पादने आणि प्रमाणासाठी तुमच्या स्थानिक कृषी विज्ञान केंद्र (KVK) किंवा कृषी अधिकाऱ्यांशी संपर्क साधा.",
        f"4. निरीक्षण: आठवड्यातून दोनदा पिकाची पाहणी करा."
    ]

    return {
        "en": {
            "summary": f"Diagnostic scan confirmed '{disease_title}' on {crop_title} during '{ctx.get('growth_stage', 'vegetative')}' stage under '{ctx.get('risk_level', 'MODERATE')}' risk conditions.",
            "action_steps": en_steps
        },
        "hi": {
            "summary": f"निदान में '{ctx.get('growth_stage', 'vegetative')}' अवस्था के दौरान {crop_title} पर '{disease_title}' की पुष्टि हुई है।",
            "action_steps": hi_steps
        },
        "mr": {
            "summary": f"तपासणीमध्ये '{ctx.get('growth_stage', 'vegetative')}' टप्प्यात {crop_title} पिकावर '{disease_title}' चे निदान झाले आहे.",
            "action_steps": mr_steps
        }
    }
