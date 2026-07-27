"""
AviaSAFE SMS Platform — Demo Dataset Seeder

Seeds ICAO Annex 19 / CAR-19 aligned Safety Management System data:
- Survey:  12 ICAO SMS Elements across 4 Pillars (930 responses)
- VSR:     Voluntary hazard reports classified per ICAO taxonomy (620)
- MOR:     Mandatory occurrence reports with investigation state (245)
- Users:   21 demo users with JWT claims and tenant isolation

Usage:
    python -m seed.runner              # Idempotent seed
    python -m seed.runner --force      # Re-seed
    python -m seed.runner --dry-run    # Preview counts
"""
