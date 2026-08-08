import os, sys
os.environ["FIREBASE_DATABASE_ID"] = "sms-db-beta"

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

from dotenv import load_dotenv
load_dotenv(override=False)

from firebase_admin import credentials, firestore
import firebase_admin

creds = credentials.Certificate({
    "type": "service_account",
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n"),
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
    "token_uri": os.environ.get("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
})
beta_app = firebase_admin.initialize_app(creds, name="backfill")
beta_db = firestore.client(app=beta_app, database_id="sms-db-beta")

import app.firebase as fb
fb._db = beta_db
fb._firebase_app = beta_app

from app.routes.reports import _auto_create_hazard_from_report

TENANT = "tara-air"
ten = beta_db.collection("tenants").document(TENANT)

reports = list(ten.collection("reports").stream())
hazards = list(ten.collection("hazards").stream())
linked = {h.to_dict().get("source_id") for h in hazards}
print(f"reports={len(reports)} | hazards={len(hazards)} | already_linked={len(linked)}")

created = 0
skipped = 0
errors = 0
for rep in reports:
    if rep.id in linked:
        skipped += 1
        continue
    d = rep.to_dict()
    stored = {
        "id": rep.id,
        "tenant_id": TENANT,
        "report_type": d.get("report_type"),
        "narrative": d.get("narrative", ""),
        "severity_level": d.get("severity_level"),
        "probability_level": d.get("probability_level"),
        "occurrence_category": d.get("occurrence_category"),
        "occurrence_type": d.get("occurrence_type"),
    }
    user = {"uid": d.get("created_by") or "sm-tara-air-001"}
    try:
        _auto_create_hazard_from_report(stored, user)
        created += 1
        occ = d.get("occurrence_date")
        if occ:
            refs = list(ten.collection("hazards").where("source_id", "==", rep.id).limit(1).get())
            if refs:
                refs[0].reference.update({"created_at": occ, "updated_at": occ})
    except Exception as e:
        errors += 1
        print(f"ERROR for {rep.id}: {e}")

print(f"\ncreated={created} | skipped={skipped} | errors={errors}")

after = sum(1 for _ in ten.collection("hazards").stream())
print(f"total hazards now={after}")
