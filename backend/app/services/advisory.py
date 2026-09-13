"""
Multilingual Agronomic Advisory Service.
Generates localized chemical, organic, and cultural treatment plans
in English ('en'), Hindi ('hi'), and Marathi ('mr') based on disease label,
severity percentage, crop type, and growth stage.
"""
from typing import Dict, Any, List, Optional

# Advisory Treatment Knowledge Base
ADVISORY_DATABASE: Dict[str, Dict[str, Dict[str, List[str]]]] = {
    "Tomato___Bacterial_spot": {
        "en": {
            "chemical": [
                "Spray Copper Oxychloride 50% WP @ 2.5 g/L of water.",
                "In severe infection, mix Streptocycline @ 0.1 g/L with Copper fungicide.",
                "Maintain 10-14 days safety interval before harvest."
            ],
            "organic": [
                "Apply Neem Oil extract (10,000 ppm) @ 3 ml/L of water.",
                "Spray Pseudomonas fluorescens bio-bactericide @ 5 g/L."
            ],
            "cultural": [
                "Avoid overhead sprinkler irrigation; use drip lines to keep foliage dry.",
                "Prune lower infected leaves and destroy them away from the field.",
                "Rotate crops with non-solanaceous crops (e.g., maize, beans) for 2 seasons."
            ]
        },
        "hi": {
            "chemical": [
                "कॉपर ऑक्सीक्लोराइड 50% डब्ल्यूपी @ 2.5 ग्राम/लीटर पानी में घोलकर छिड़कें।",
                "गंभीर संक्रमण में, कॉपर कवकनाशी के साथ स्ट्रेप्टोसाइक्लिन @ 0.1 ग्राम/लीटर मिलाएं।",
                "फसल कटाई से पहले 10-14 दिनों का सुरक्षा अंतर रखें।"
            ],
            "organic": [
                "नीम का तेल (10,000 पीपीएम) @ 3 मिली/लीटर पानी में मिलाकर प्रयोग करें।",
                "स्यूडोमोनास फ्लोरेसेंस जैव-जीवाणुनाशी @ 5 ग्राम/लीटर छिड़कें।"
            ],
            "cultural": [
                "पत्तियों को गीला होने से बचाने के लिए ड्रिप सिंचाई का उपयोग करें।",
                "संक्रमित निचली पत्तियों को काटें और उन्हें खेत से दूर नष्ट कर दें।"
            ]
        },
        "mr": {
            "chemical": [
                "कॉपर ऑक्सिक्लोराईड ५०% डब्ल्यूपी @ २.५ ग्रॅम/लिटर पाण्यात मिसळून फवारा.",
                "तीव्र संसर्गासाठी कॉपर बुरशीनाशकासोबत स्ट्रिप्टोसायक्लिन @ ०.१ ग्रॅम/लिटर मिसळा.",
                "काढणीपूर्वी १०-१४ दिवसांचा सुरक्षित कालावधी ठेवा."
            ],
            "organic": [
                "कडुनिंब तेल (१०,००० पीपीएम) @ ३ मि.ली./लिटर पाण्यात मिसळून वापरा.",
                "स्युडोमोनास फ्लोरेसेन्स जैविक जिवाणूनाशक @ ५ ग्रॅम/लिटर फवारा."
            ],
            "cultural": [
                "पाने ओली होण्यापासून वाचवण्यासाठी ठिबक सिंचनाचा वापर करा.",
                "खालील बाधित पाने काढून शेताबाहेर नष्ट करा."
            ]
        }
    },
    "Tomato___Late_blight": {
        "en": {
            "chemical": [
                "Spray Mancozeb 75% WP @ 2.0 g/L as preventive measure.",
                "If symptoms appear, spray Metalaxyl 8% + Mancozeb 64% WP @ 2.5 g/L.",
                "Alternate with Azoxystrobin 23% SC @ 1 ml/L to prevent resistance."
            ],
            "organic": [
                "Spray Trichoderma viride bio-fungicide @ 5 g/L in morning hours.",
                "Apply sour buttermilk solution (1 L in 10 L water) every 7 days."
            ],
            "cultural": [
                "Ensure proper row spacing (60 cm x 45 cm) for sunlight and ventilation.",
                "Remove and burn blighted plants immediately."
            ]
        },
        "hi": {
            "chemical": [
                "बचाव के लिए मैंकोजेब 75% डब्ल्यूपी @ 2.0 ग्राम/लीटर का छिड़काव करें।",
                "लक्षण दिखने पर मेटालेक्सिल 8% + मैंकोजेब 64% @ 2.5 ग्राम/लीटर छिड़कें।",
                "प्रतिरोध से बचने के लिए एज़ोक्सीस्ट्रोबिन 23% एससी @ 1 मिली/लीटर का प्रयोग करें।"
            ],
            "organic": [
                "सुबह के समय ट्राइकोडर्मा विरिडे @ 5 ग्राम/लीटर का छिड़काव करें।",
                "खट्टा छाछ का घोल (1 लीटर 10 लीटर पानी में) हर 7 दिन में छिड़कें।"
            ],
            "cultural": [
                "हवा और धूप के लिए पौधों के बीच उचित दूरी (60 सेमी x 45 सेमी) रखें।",
                "झुलसे हुए पौधों को तुरंत उखाड़कर जला दें।"
            ]
        },
        "mr": {
            "chemical": [
                "प्रतिबंधात्मक उपाय म्हणून मँकोझेब ७५% डब्ल्यूपी @ २.० ग्रॅम/लिटर फवारा.",
                "लक्षणे दिसल्यास मेटाॅलॅक्सिल ८% + मँकोझेब ६४% @ २.५ ग्रॅम/लिटर फवारा.",
                "किड प्रतिकार टाळण्यासाठी ॲझॉक्सीस्ट्रॉबिन २३% एससी @ १ मि.ली./लिटर बदला."
            ],
            "organic": [
                "सकाळी ट्रायकोडर्मा व्हिरिडे @ ५ ग्रॅम/लिटर फवारा.",
                "आंबट ताकाचे द्रावण (१ लिटर १० लिटर पाण्यात) दर ७ दिवसांनी फवारा."
            ],
            "cultural": [
                "हवा आणि सूर्यप्रकाशासाठी योग्य अंतर (६० सेमी x ४५ सेमी) ठेवा.",
                "बाधित झाडे तात्काळ उपटून नष्ट करा."
            ]
        }
    },
    "Cotton___Pink_bollworm": {
        "en": {
            "chemical": [
                "Install Pheromone traps @ 5 traps/acre for monitoring.",
                "Spray Profenofos 50% EC @ 2 ml/L or Emamectin Benzoate 5% SG @ 0.5 g/L if moth counts exceed threshold.",
                "Do not repeat synthetic pyrethroids to prevent pest flare-up."
            ],
            "organic": [
                "Release Trichogramma bactrae egg parasitoids @ 60,000/acre weekly.",
                "Spray Neem seed kernel extract (NSKE 5%) @ 50 ml/L."
            ],
            "cultural": [
                "Destroy rosette flowers and early fallen bolls manually.",
                "Maintain strict crop termination by December end."
            ]
        },
        "hi": {
            "chemical": [
                "निगरानी के लिए फेरोमोन ट्रैप @ 5 ट्रैप/एकड़ स्थापित करें।",
                "पतंगों की संख्या अधिक होने पर प्रोफेनोफॉस 50% ईसी @ 2 मिली/लीटर छिड़कें।",
                "कीटों के प्रकोप से बचने के लिए सिंथेटिक पाइरेथ्रॉइड्स को दोबारा न दोहराएं।"
            ],
            "organic": [
                "ट्राइकोग्रामा बैक्ट्रे परजीवी @ 60,000/एकड़ साप्ताहिक रूप से छोड़ें।",
                "नीम की निंबोली का अर्क (NSKE 5%) @ 50 मिली/लीटर छिड़कें।"
            ],
            "cultural": [
                "गुलाब की पंखुड़ियों जैसे फूल और झड़े हुए गोलों को हाथ से नष्ट करें।"
            ]
        },
        "mr": {
            "chemical": [
                "पाहाणीसाठी कामगंध सापळे @ ५ सापळे/एकड लावा.",
                "पतंगांची संख्या वाढल्यास प्रोफेनोफॉस ५०% ईसी @ २ मि.ली./लिटर फवारा.",
                "किडींचा उद्रेक टाळण्यासाठी सिंथेटिक पायरिथ्रॉइड्स पुन्हा वापरू नका."
            ],
            "organic": [
                "ट्रायकोग्रामा बॅक्ट्रे परोपजीवी मित्रकीटक @ ६०,०००/एकड सोडा.",
                "निंबोळी अर्क (NSKE ५%) @ ५० मि.ली./लिटर फवारा."
            ],
            "cultural": [
                "गुलाबी रंगाचे बाधित फुले व गळलेली बोंडे गोळा करून नष्ट करा."
            ]
        }
    },
    "Rice___Blast": {
        "en": {
            "chemical": [
                "Spray Tricyclazole 75% WP @ 0.6 g/L of water at early leaf blast stage.",
                "In neck blast risk, apply Isoprothiolane 40% EC @ 1.5 ml/L at booting stage."
            ],
            "organic": [
                "Apply Pseudomonas fluorescens seed treatment @ 10 g/kg and foliar spray @ 5 g/L.",
                "Spray vermicompost wash (10% solution)."
            ],
            "cultural": [
                "Avoid excessive Nitrogen fertilizer application (split N dosage into 3 doses).",
                "Maintain standing water level (2-3 cm) during tillering stage."
            ]
        },
        "hi": {
            "chemical": [
                "पत्ती के झुलसा रोग में ट्राइसाइक्लाज़ोल 75% डब्ल्यूपी @ 0.6 ग्राम/लीटर छिड़कें।",
                "गर्दन के झुलसे (नेक ब्लास्ट) में आइसोप्रोथियोलेन 40% ईसी @ 1.5 मिली/लीटर छिड़कें।"
            ],
            "organic": [
                "स्यूडोमोनास फ्लोरेसेंस @ 5 ग्राम/लीटर का पर्णीय छिड़काव करें।"
            ],
            "cultural": [
                "अत्यधिक नाइट्रोजन उर्वरक का उपयोग न करें (नाइट्रोजन को 3 भागों में दें)।"
            ]
        },
        "mr": {
            "chemical": [
                "पानावरील करपा रोगासाठी ट्रायसायक्लाझोल ७५% डब्ल्यूपी @ ०.६ ग्रॅम/लिटर फवारा.",
                "मानमोडी (नेक ब्लास्ट) रोगासाठी आयसोप्रोथिओलेन ४०% ईसी @ १.५ मि.ली./लिटर फवारा."
            ],
            "organic": [
                "स्युडोमोनास फ्लोरेसेन्स @ ५ ग्रॅम/लिटर पाण्यात फवारा."
            ],
            "cultural": [
                "नत्र खताचा अतिवापर टाळा (नत्र खत ३ हप्त्यांमध्ये द्या)."
            ]
        }
    }
}

# Default Healthy Crop Advisory
HEALTHY_ADVISORY = {
    "en": {
        "chemical": ["No chemical pesticide required. Crop appears healthy."],
        "organic": ["Apply Jeevamrut / Vermicompost tea every 15 days to enhance soil biodiversity."],
        "cultural": ["Maintain regular drip irrigation scheduling and weed-free field borders."]
    },
    "hi": {
        "chemical": ["किसी रासायनिक कीटनाशक की आवश्यकता नहीं है। फसल स्वस्थ दिखाई दे रही है।"],
        "organic": ["मृदा जैव विविधता बढ़ाने के लिए हर 15 दिन में जीवामृत/वर्मीकम्पोस्ट चाय दें।"],
        "cultural": ["नियमित ड्रिप सिंचाई और खरपतवार रहित खेत की सीमाएं बनाए रखें।"]
    },
    "mr": {
        "chemical": ["कोणत्याही रासायनिक कीटकनाशकाची गरज नाही. पीक निरोगी दिसत आहे."],
        "organic": ["मातीची सुपीकता वाढवण्यासाठी दर १५ दिवसांनी जिवामृत किंवा गांडूळ खत ताक वापरा."],
        "cultural": ["नियमित ठिबक सिंचन आणि तणमुक्त शेतबांध ठेवा."]
    }
}


def generate_advisory_plan(
    disease_label: str,
    severity_pct: float = 0.0,
    crop_name: str = "Crop",
    growth_stage: str = "vegetative",
    language_pref: str = "en"
) -> Dict[str, Any]:
    """
    Generate agronomic advisory action plan based on disease label, severity, crop, stage, and language.
    Languages supported: 'en' (English), 'hi' (Hindi), 'mr' (Marathi).
    """
    lang = (language_pref or "en").lower()
    if lang not in ("en", "hi", "mr"):
        lang = "en"

    is_healthy = "healthy" in disease_label.lower()

    if is_healthy:
        treatment_plan = HEALTHY_ADVISORY.get(lang, HEALTHY_ADVISORY["en"])
        severity_category = "Healthy (0%)"
    else:
        adv_entry = ADVISORY_DATABASE.get(disease_label, ADVISORY_DATABASE["Tomato___Bacterial_spot"])
        treatment_plan = adv_entry.get(lang, adv_entry.get("en"))

        if severity_pct >= 50.0:
            severity_category = "Severe High (>50%)"
        elif severity_pct >= 25.0:
            severity_category = "Moderate (25-50%)"
        else:
            severity_category = "Mild / Early Spot (<25%)"

    formatted_disease = disease_label.replace("___", " - ").replace("_", " ")

    return {
        "disease_label": disease_label,
        "disease_name_formatted": formatted_disease,
        "severity_pct": severity_pct,
        "severity_category": severity_category,
        "crop_name": crop_name,
        "growth_stage": growth_stage,
        "language": lang,
        "treatments": {
            "chemical": treatment_plan.get("chemical", []),
            "organic": treatment_plan.get("organic", []),
            "cultural": treatment_plan.get("cultural", []),
        },
        "urgency_level": "IMMEDIATE ACTION" if severity_pct > 40.0 else ("MONITOR" if is_healthy else "PREVENTATIVE SPRAY")
    }


def generate_advisory(disease_name: str, severity: str = "medium", crop_type: str = "crop") -> str:
    """Legacy helper returning plain string advisory summary."""
    plan = generate_advisory_plan(disease_label=disease_name, crop_name=crop_type, language_pref="en")
    chem = " ".join(plan["treatments"]["chemical"][:2])
    org = " ".join(plan["treatments"]["organic"][:1])
    return f"{chem} {org}"

