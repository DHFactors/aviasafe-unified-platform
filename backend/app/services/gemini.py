# ============================================================================
# FILE: gemini.py
# PATH: backend/app/services/gemini.py
# VERSION: 1.0.0
# DATE CREATED: 2026-07-03
# DATE REVISED: 2026-07-03
# PURPOSE: Google Gemini 2.5 Pro integration for safety report analysis.
# AUTHOR: Ghanshyam Acharya
# CODE OWNER: AviaSafeSystems
# ============================================================================

import json
import re
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from loguru import logger

from app.core.config import settings
from app.services.risk_matrix import (
    compute_risk_index,
    get_risk_level,
    THRESHOLDS_DEFAULT,
)

GEMINI_API_KEY = settings.AI_API_KEY or settings.GEMINI_API_KEY
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(settings.AI_MODEL)
else:
    logger.warning("AI_API_KEY not set. AI features will use mock data.")
    model = None


def sanitize_prompt(narrative: str) -> str:
    narrative = narrative.replace('<script>', '').replace('</script>', '')
    narrative = re.sub(r'[{}<>]', '', narrative)
    narrative = narrative[:settings.AI_NARRATIVE_TRUNCATE]
    return narrative


def _build_icao_risk_prompt_section() -> str:
    return f"""
ASSESSMENT — ICAO Safety Risk Severity and Probability
You MUST assign ICAO severity (1-5) and probability (1-5) using this scale:

SEVERITY (1-5):
1 = Negligible — No injuries, minor system degradation
2 = Minor — Slight injuries, operational delay, minor damage
3 = Major — Serious injury, major equipment damage, significant operational disruption
4 = Hazardous — Life-threatening injuries, loss of primary systems, near CFIT/near LOC-I
5 = Catastrophic — Fatalities, hull loss, collision with terrain or obstacle

PROBABILITY (1-5):
1 = Extremely Improbable — Almost inconceivable; <10^-8 per flight hour
2 = Improbable — Very unlikely to occur; <10^-6 per flight hour
3 = Remote — Unlikely but possible; <10^-5 per flight hour
4 = Occasional — Likely to occur occasionally; <10^-3 per flight hour
5 = Frequent — Likely to occur many times; >10^-3 per flight hour

For EACH severity and probability assignment, you MUST provide an "explanation" field
that cites real-world aviation incident or accident precedents to justify the rating.
Draw on well-known investigation findings:
- CFIT: Turkish 1951 (2009), Air France 447 (2009), Helios 522 (2005)
- Runway incursion: Tenerife (1977), Linate (2001), Comair 5191 (2006)
- Engine failure: Qantas 32 (2010), British Airtours 28M (1985)
- Bird strike: US Airways 1549 (2009), Ethiopian 604 (1988)
- Weather: Air France 358 (2005), Delta 191 (1985), ATR 72 Rio Doce (2023)
- Fatigue: Colgan 3407 (2009), UPS 1354 (2013)
- LOC-I: ATR 72 (2018, Nepal), Yeti Airlines 691 (2023, Nepal)
- Maintenance: Alaska 261 (2000), Japan 123 (1985), SilkAir 185 (1997)
- Cargo safety: UPS 6 (2010), National 102 (2013)
- Regional/STOL/helicopter: Cougar Helicopters 91 (2009), CHC Helikopter 241 (2016)

Your explanation should be 1-2 sentences that anchor the assigned level to an actual
investigation outcome or industry statistical precedent.

RISK INDEX is then computed automatically as Severity x Probability.
Risk Level thresholds (ICAO-aligned):
  <= {THRESHOLDS_DEFAULT['low_max']} = Low
  <= {THRESHOLDS_DEFAULT['medium_max']} = Medium
  <= {THRESHOLDS_DEFAULT['high_max']} = High
  > {THRESHOLDS_DEFAULT['high_max']} = Very High
"""


def analyze_report(narrative: str) -> Dict[str, Any]:
    """Analyze a safety report using Gemini API."""
    if not model:
        return mock_analysis(narrative)

    try:
        clean_narrative = sanitize_prompt(narrative)

        prompt = f"""You are an aviation safety analyst. Analyze the following safety report and classify it according to ICAO standards.

REPORT NARRATIVE:
{clean_narrative}

{_build_icao_risk_prompt_section()}

Return ONLY valid JSON with the following structure:
{{
    "occurrence_type": "One of: Runway Excursion, Runway Incursion, Airborne Conflict, Abnormal Runway Contact, Ground Collision, System/Component Failure, Powerplant Failure, Weather Encounter, Bird Strike, Cabin Safety Event, Procedural Deviation, ATC Operational Incident, Other",
    "human_factors": ["Array of applicable factors"],
    "phase_of_flight": "One of: Standing, Pushback, Taxi, Takeoff, Initial Climb, En-route, Holding, Approach, Landing, Go-Around",
    "summary": "Brief 1-2 sentence summary",
    "recommendations": ["2-3 brief recommendations"],
    "suggested_severity": <int 1-5>,
    "severity_explanation": "<1-2 sentence citing real precedent>",
    "suggested_probability": <int 1-5>,
    "probability_explanation": "<1-2 sentence citing real precedent>"
}}
Do NOT include risk_index or risk_level in the JSON. Those are computed server-side.
"""

        response = model.generate_content(prompt)

        response_text = response.text
        json_match = re.search(r'\{[\s\S]*\}', response_text)

        if json_match:
            result = json.loads(json_match.group())
            return result
        else:
            logger.error(f"Failed to parse Gemini response: {response_text}")
            return mock_analysis(narrative)

    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return mock_analysis(narrative)

def classify_mandatory(narrative: str) -> Dict[str, Any]:
    """Classify if a report is mandatory under ICAO/EASA regulations."""
    narrative_lower = narrative.lower()
    
    # Category A: Immediate mandatory (72 hours)
    category_a_keywords = {
        'accident': ['accident', 'crash', 'fatal', 'serious injury', 'death'],
        'serious_incident': ['near miss', 'loss of separation', 'TCAS RA', 'RA'],
        'engine_failure': ['engine failure', 'flameout', 'engine shutdown'],
        'fire': ['fire', 'smoke in cockpit', 'smoke in cabin'],
        'structural': ['structural damage', 'airframe damage', 'crack'],
        'CFIT': ['CFIT', 'terrain warning', 'GPWS'],
        'LOCI': ['loss of control', 'upset', 'stall'],
        'runway_excursion': ['runway excursion', 'veer-off', 'overrun'],
        'security': ['hijack', 'sabotage', 'breach', 'security']
    }
    
    # Category B: Timely mandatory
    category_b_keywords = {
        'bird_strike': ['bird strike', 'birdstrike', 'wildlife'],
        'weather': ['turbulence', 'hail', 'microburst', 'windshear'],
        'system_failure': ['system failure', 'avionics', 'hydraulic failure'],
        'atc_incident': ['runway incursion', 'airspace violation', 'ATC error'],
        'maintenance': ['maintenance error', 'installation error'],
        'ground_incident': ['ground handling', 'ramp', 'stand collision']
    }
    
    # Check Category A
    matched_a = []
    for category, keywords in category_a_keywords.items():
        for keyword in keywords:
            if keyword in narrative_lower:
                matched_a.append({category: keyword})
                break
    
    if len(matched_a) >= 1:
        return {
            "is_mandatory": True,
            "category": "A",
            "reason": f"Matched {len(matched_a)} Category A criteria",
            "matched_criteria": matched_a,
            "confidence": 0.95
        }
    
    # Check Category B
    matched_b = []
    for category, keywords in category_b_keywords.items():
        for keyword in keywords:
            if keyword in narrative_lower:
                matched_b.append({category: keyword})
                break
    
    if len(matched_b) >= 2:
        return {
            "is_mandatory": True,
            "category": "B",
            "reason": f"Matched {len(matched_b)} Category B criteria",
            "matched_criteria": matched_b,
            "confidence": 0.80
        }
    
    return {
        "is_mandatory": False,
        "category": None,
        "reason": "No mandatory criteria matched",
        "matched_criteria": [],
        "confidence": 0.90
    }

def mock_analysis(narrative: str) -> Dict[str, Any]:
    """Mock analysis with ICAO risk assessment when Gemini API is not available."""
    narrative_lower = narrative.lower()

    # Simple keyword-based classification
    occurrence_type = "Other"
    if "runway" in narrative_lower and ("excursion" in narrative_lower or "veer" in narrative_lower or "dirt" in narrative_lower):
        occurrence_type = "Runway Excursion"
    elif "incursion" in narrative_lower:
        occurrence_type = "Runway Incursion"
    elif "hard landing" in narrative_lower or "bounce" in narrative_lower:
        occurrence_type = "Abnormal Runway Contact"
    elif "engine" in narrative_lower and ("fail" in narrative_lower or "problem" in narrative_lower):
        occurrence_type = "Powerplant Failure"

    # Human factors
    human_factors = []
    if "decision" in narrative_lower or "attempt" in narrative_lower:
        human_factors.append("Decision Making Error")
    if "pressur" in narrative_lower or "rush" in narrative_lower or "quickly" in narrative_lower:
        human_factors.append("Pressure")
    if "awareness" in narrative_lower or "didn't realize" in narrative_lower:
        human_factors.append("Situational Awareness (Loss of)")
    if "speed" in narrative_lower or "bounce" in narrative_lower:
        human_factors.append("Skill-Based Error")

    if not human_factors:
        human_factors.append("Skill-Based Error")

    # ICAO risk assessment based on severity keywords
    if any(word in narrative_lower for word in ['fatal', 'death', 'crash', 'collision', 'catastrophic', 'hull loss']):
        sev_val = 5
    elif any(word in narrative_lower for word in ['serious', 'severe', 'hospital', 'intensive', 'major', 'fire', 'emergency']):
        sev_val = 4
    elif any(word in narrative_lower for word in ['injured', 'damage', 'delay', 'failure', 'incident']):
        sev_val = 3
    else:
        sev_val = 2

    if any(word in narrative_lower for word in ['repeated', 'common', 'frequent', 'multiple', 'ongoing', 'systemic']):
        prob_val = 5
    elif any(word in narrative_lower for word in ['likely', 'probable', 'expected', 'tend']):
        prob_val = 4
    elif any(word in narrative_lower for word in ['unlikely', 'remote', 'rare', 'hardly']):
        prob_val = 3
    elif any(word in narrative_lower for word in ['extremely unlikely', 'improbable']):
        prob_val = 2
    else:
        prob_val = 4

    risk_index = compute_risk_index(sev_val, prob_val)
    risk_level = get_risk_level(risk_index)

    return {
        "occurrence_type": occurrence_type,
        "human_factors": human_factors,
        "risk_level": risk_level,
        "phase_of_flight": "Landing",
        "summary": "Safety report analyzed using mock classification.",
        "recommendations": [
            "Review standard operating procedures.",
            "Consider additional training on identified risk areas."
        ],
        "suggested_severity": sev_val,
        "severity_explanation": f"Severity {sev_val} based on keyword indicators. In aviation operations, this level corresponds to outcomes documented in NTSB/EASA accident databases.",
        "suggested_probability": prob_val,
        "probability_explanation": f"Probability {prob_val} based on recurrence keywords. Industry safety reports indicate events at this level are documented in IATA Safety Report benchmarks.",
    }
