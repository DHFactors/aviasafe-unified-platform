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
app = firebase_admin.initialize_app(creds, name="capcheck")
beta_db = firestore.client(app=app, database_id="sms-db-beta")
import app.firebase as fb
fb._db = beta_db
fb._firebase_app = app

from app.services.can_cap_service import CanCapService

svc = CanCapService("tara-air")
user = {"role": "AIRLINE_ADMIN", "tenant_id": "tara-air"}
caps = svc.list_all_caps(user, {})
print(f"total CAPs: {len(caps)}")
for c in caps:
    print(f"  {c.get('cap_reference')} | CAN={c.get('can_reference')} | can_issued_at={c.get('can_issued_at')} | status={c.get('status')} | priority={c.get('priority')} | hazard={c.get('hazard_id')} | submitted_at={c.get('submitted_at')} | plan={(c.get('action_plan') or '')[:50]}")

print("\n--- filter status=Completed ---")
caps2 = svc.list_all_caps(user, {"status": "Completed"})
print(f"completed: {len(caps2)} -> {[c.get('cap_reference') for c in caps2]}")

print("\n--- filter search=wildlife ---")
caps3 = svc.list_all_caps(user, {"search": "wildlife"})
print(f"search 'wildlife': {len(caps3)} -> {[c.get('cap_reference') for c in caps3]}")
