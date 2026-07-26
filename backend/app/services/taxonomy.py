# ============================================================================ 
# FILE: taxonomy.py 
# PATH: backend/app/services/taxonomy.py 
# VERSION: 1.0.0 
# DATE CREATED: 2026-07-03 
# PURPOSE: ICAO/ECCAIRS hazard taxonomy definitions. 
# AUTHOR: Ghanshyam Acharya 
# CODE OWNER: AviaSafeSystems 
# ============================================================================ 
 
TAXONOMY = { 
    "occurrence_types": [ 
        "Runway Excursion", 
        "Runway Incursion", 
        "Airborne Conflict", 
        "Abnormal Runway Contact", 
        "Ground Collision", 
        "System/Component Failure", 
        "Powerplant Failure", 
        "Weather Encounter", 
        "Bird Strike", 
        "Cabin Safety Event", 
        "Procedural Deviation", 
        "ATC Operational Incident" 
    ], 
    "human_factors": [ 
        "Situational Awareness (Loss of)", 
        "Decision Making Error", 
        "Skill-Based Error", 
        "Procedural Deviation", 
        "Communication Issue", 
        "CRM Breakdown", 
        "Fatigue", 
        "Pressure", 
        "Distraction", 
        "Workload Management" 
    ], 
    "risk_levels": ["Low", "Medium", "High"], 
    "phases_of_flight": [ 
        "Standing", "Pushback", "Taxi", "Takeoff", 
        "Initial Climb", "En-route", "Holding", 
        "Approach", "Landing", "Go-Around" 
    ] 
} 
