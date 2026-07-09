"""Run with: python seed.py  (creates a few demo HCPs so the UI has data to show)."""
from app.database import Base, engine, SessionLocal
from app.models import HCP

Base.metadata.create_all(bind=engine)

db = SessionLocal()

demo_hcps = [
    dict(name="Dr. Anjali Mehta", specialty="Cardiology", institution="Fortis Hospital, Bengaluru", segment="A"),
    dict(name="Dr. Ravi Shankar", specialty="Endocrinology", institution="Apollo Hospitals, Chennai", segment="B"),
    dict(name="Dr. Priya Nair", specialty="Oncology", institution="Tata Memorial, Mumbai", segment="A"),
    dict(name="Dr. Karthik Rao", specialty="General Medicine", institution="Manipal Hospital, Bengaluru", segment="C"),
]

for h in demo_hcps:
    exists = db.query(HCP).filter(HCP.name == h["name"]).first()
    if not exists:
        db.add(HCP(**h))

db.commit()
print(f"Seeded {len(demo_hcps)} demo HCPs (skipping any that already existed).")
db.close()

{
    "hcp_id": "HCP001",
    "name": "Dr. Mehta",
    "speciality": "Cardiology",
    "hospital": "Apollo Hospital"
}