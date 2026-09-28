"""
Seed script for populating the Firestore 'plants' collection for Plant & Greenhouse Concierge.
"""
from google.cloud import firestore

# CRITICAL: Hardcode the GCP Project ID string
PROJECT_ID = "qwiklabs-gcp-01-68d0c980599a"

def seed_firestore():
    db = firestore.Client(project=PROJECT_ID)
    plants_ref = db.collection("plants")

    seed_plants = [
        {
            "id": "monstera-deliciosa",
            "name": "Monstera Deliciosa",
            "species": "Monstera deliciosa",
            "care_level": "Easy",
            "watering_schedule": "Every 7-10 days",
            "light_requirement": "Bright indirect light",
            "price": 34.99,
            "stock": 12,
            "description": "Popular tropical houseplant with dramatic perforated leaves (fenestrations).",
            "care_notes": ["Prefers warm, humid environments.", "Wipe dust off broad leaves periodically."]
        },
        {
            "id": "snake-plant",
            "name": "Snake Plant (Sansevieria)",
            "species": "Dracaena trifasciata",
            "care_level": "Easy",
            "watering_schedule": "Every 2-3 weeks",
            "light_requirement": "Low to bright indirect light",
            "price": 24.99,
            "stock": 20,
            "description": "Extremely hardy succulent with upright architectural sword-like leaves.",
            "care_notes": ["Allow soil to dry out completely between waterings.", "Tolerates low light."]
        },
        {
            "id": "fiddle-leaf-fig",
            "name": "Fiddle Leaf Fig",
            "species": "Ficus lyrata",
            "care_level": "Moderate",
            "watering_schedule": "Every 7 days",
            "light_requirement": "Bright direct/indirect sunlight",
            "price": 49.99,
            "stock": 8,
            "description": "Stunning violin-shaped foliage plant that makes a bold interior statement.",
            "care_notes": ["Avoid drafts or sudden temperature changes.", "Water when top 2 inches of soil feel dry."]
        },
        {
            "id": "pothos-golden",
            "name": "Golden Pothos",
            "species": "Epipremnum aureum",
            "care_level": "Easy",
            "watering_schedule": "Every 7-10 days",
            "light_requirement": "Low to medium indirect light",
            "price": 18.99,
            "stock": 25,
            "description": "Trailing vine with heart-shaped variegated green and yellow leaves.",
            "care_notes": ["Easy to propagate in water.", "Great for hanging baskets or high shelves."]
        },
        {
            "id": "calathea-orbifolia",
            "name": "Calathea Orbifolia",
            "species": "Goeppertia orbifolia",
            "care_level": "Expert",
            "watering_schedule": "Every 4-5 days",
            "light_requirement": "Medium indirect light",
            "price": 39.99,
            "stock": 5,
            "description": "Prayer plant with large round leaves featuring distinct silver stripes.",
            "care_notes": ["Requires high humidity and distilled/filtered water.", "Keep soil consistently moist."]
        }
    ]

    print(f"Seeding Firestore collection 'plants' in project '{PROJECT_ID}'...")
    for plant in seed_plants:
        doc_id = plant["id"]
        plants_ref.document(doc_id).set(plant)
        print(f"  ✓ Seeded plant document: '{doc_id}' ({plant['name']})")

    print("✅ Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_firestore()
