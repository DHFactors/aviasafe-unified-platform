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

import os
import json
import re
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from loguru import logger

# Initialize Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.0-pro-exp-02-05')
else:
    logger.warning("GEMINI_API_KEY not set. AI features will use mock data.")
    model = None

def sanitize_prompt(narrative: str) -> str:
    """Sanitize input for prompt injection prevention."""
    # Remove script tags
    narrative = narrative.replace('<script>', '').replace('</script>', '')
    # Remove potential injection patterns
    narrative = re.sub(r'[{}<>]', '', narrative)
    # Limit length
    narrative = narrative[:5000]
    return narrative

def analyze_report(narrative: str) -> Dict[str, Any]:
    """Analyze a safety report using Gemini API."""
    if not model:
        return mock_analysis(narrative)
    
    try:
        # Sanitize input
        clean_narrative = sanitize_prompt(narrative)
        
        # Build prompt
        prompt = f"""
You are an aviation safety analyst. Analyze the following safety report and classify it according to ICAO standards.

REPORT NARRATIVE:
{clean_narrative}

Return ONLY valid JSON with the following structure:
{{
    "occurrence_type": "One of: Runway Excursion, Runway Incursion, Airborne Conflict, Abnormal Runway Contact, Ground Collision, System/Component Failure, Powerplant Failure, Weather Encounter, Bird Strike, Cabin Safety Event, Procedural Deviation, ATC Operational Incident, Other",
    "human_factors": ["Array of applicable factors"],
    "risk_level": "One of: Low, Medium, High, Critical",
    "phase_of_flight": "One of: Standing, Pushback, Taxi, Takeoff, Initial Climb, En-route, Holding, Approach, Landing, Go-Around",
    "summary": "Brief 1-2 sentence summary",
    "recommendations": ["2-3 brief recommendations"]
}}
"""
        
        # Call Gemini API
        response = model.generate_content(prompt)
        
        # Extract JSON from response
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
    """Mock analysis for when Gemini API is not available."""
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
    
    return {
        "occurrence_type": occurrence_type,
        "human_factors": human_factors,
        "risk_level": "Medium",
        "phase_of_flight": "Landing",
        "summary": "Safety report analyzed using mock classification.",
        "recommendations": [
            "Review standard operating procedures.",
            "Consider additional training on identified risk areas."
        ]
    }
