"""
Firestore, Image Generation, Botany, Google Maps, and Artifact tools for Plant & Greenhouse Concierge agent.
"""
import base64
import json
import os
import re
import urllib.parse
import urllib.request
import uuid
from google import genai
from google.genai import types
from google.cloud import firestore, storage
from google.adk.tools import ToolContext

# CRITICAL: Hardcode the GCP Project ID string to prevent Agent Platform project number issues
PROJECT_ID = "qwiklabs-gcp-01-68d0c980599a"
BUCKET_NAME = "plant-greenhouse-images-qwiklabs-gcp-01-68d0c980599a"

# Initialize clients with hardcoded project ID string
db = firestore.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)
genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="us-central1")
global_genai_client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")


def _get_maps_api_key() -> str:
    """Helper to retrieve GOOGLE_MAPS_API_KEY from environment or .env file."""
    key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not key and os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("GOOGLE_MAPS_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    return key


def list_plants(care_level: str = "") -> list[dict]:
    """
    List all plants available in the greenhouse inventory.
    Optionally filter by care_level (e.g. 'Easy', 'Moderate', 'Expert').
    """
    plants_ref = db.collection("plants")
    if care_level:
        query = plants_ref.where("care_level", "==", care_level.strip().capitalize())
        docs = query.stream()
    else:
        docs = plants_ref.stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        results.append(data)
    
    return results


def get_plant_details(plant_name_or_id: str) -> dict | str:
    """
    Get detailed information about a plant by ID or name substring.
    """
    plants_ref = db.collection("plants")
    query_str = plant_name_or_id.strip().lower()

    # Try direct document ID lookup
    doc = plants_ref.document(query_str).get()
    if doc.exists:
        return doc.to_dict()

    # Substring search by name
    docs = plants_ref.stream()
    for doc in docs:
        data = doc.to_dict()
        if query_str in data.get("name", "").lower() or query_str in data.get("species", "").lower():
            return data

    return f"No plant found matching '{plant_name_or_id}'."


def update_plant_stock(plant_id: str, new_stock: int) -> str:
    """
    Update the inventory stock level for a specific plant by plant_id.
    """
    doc_ref = db.collection("plants").document(plant_id.strip().lower())
    doc = doc_ref.get()
    if not doc.exists:
        return f"Plant document '{plant_id}' does not exist."

    doc_ref.update({"stock": int(new_stock)})
    return f"Successfully updated stock for '{plant_id}' to {new_stock} units."


def add_care_note(plant_id: str, note: str) -> str:
    """
    Add a new care note or tip to a plant's care history in Firestore.
    """
    doc_ref = db.collection("plants").document(plant_id.strip().lower())
    doc = doc_ref.get()
    if not doc.exists:
        return f"Plant document '{plant_id}' does not exist."

    doc_ref.update({"care_notes": firestore.ArrayUnion([note.strip()])})
    return f"Successfully added care note to '{plant_id}'."


def generate_plant_image(plant_name: str, style_description: str = "") -> str:
    """
    Generates a visual preview photo of a plant using AI image generation,
    uploads it to public Cloud Storage, and returns its public URL.

    Args:
        plant_name: Name of the plant (e.g., 'Monstera Deliciosa', 'Snake Plant').
        style_description: Optional styling details (e.g., 'in a terracotta pot on a wooden table').

    Returns:
        Public HTTP URL of the generated image.
    """
    prompt = f"A vibrant high quality photograph of a healthy {plant_name} plant"
    if style_description:
        prompt += f", {style_description}"

    response = genai_client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    image_bytes = None
    mime_type = "image/png"
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/png"
                break

    if not image_bytes:
        return f"Failed to generate image for '{plant_name}'."

    ext = "jpg" if "jpeg" in mime_type else "png"
    slug = re.sub(r"[^\w\-]", "_", plant_name.lower().strip())
    filename = f"plant_images/{slug}_{uuid.uuid4().hex[:8]}.{ext}"

    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    return f"Image generated successfully! Public URL: {public_url}"


def generate_domain_image(plant_name: str, tool_context: ToolContext, style: str = "") -> str:
    """
    Generates a photo of a plant or greenhouse item using gemini-3.1-flash-lite-image in global region.
    Saves the image to the session artifacts panel via tool_context.save_artifact,
    uploads the image bytes directly to public Cloud Storage, and returns its public HTTPS URL.

    Args:
        plant_name: Name of the plant or item (e.g. 'Monstera Deliciosa', 'Fiddle Leaf Fig').
        tool_context: ADK ToolContext supplied by runtime.
        style: Optional aesthetic style description.

    Returns:
        Public Cloud Storage HTTPS URL of the generated image.
    """
    prompt = f"A high quality photograph of a {plant_name}"
    if style:
        prompt += f", {style}"

    response = global_genai_client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    image_bytes = None
    mime_type = "image/jpeg"
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return f"Failed to generate image for '{plant_name}'."

    ext = "jpg" if "jpeg" in mime_type else "png"
    slug = re.sub(r"[^\w\-]", "_", plant_name.lower().strip())
    filename = f"{slug}_{uuid.uuid4().hex[:8]}.{ext}"

    # 1. Save artifact using tool_context.save_artifact
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes directly to public Cloud Storage bucket
    object_path = f"plant_images/{filename}"
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_path)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_path}"
    return public_url


def generate_domain_video(item_name: str, tool_context: ToolContext, prompt_details: str = "") -> str:
    """
    Generates a short video clip for a plant or greenhouse item using Google's Omni model (gemini-omni-flash-preview) in the global region.
    Saves the video to the session artifacts panel via tool_context.save_artifact,
    uploads the video bytes directly to public Cloud Storage, and returns its public HTTPS URL.

    Args:
        item_name: Name of the plant or greenhouse item (e.g. 'Monstera Deliciosa', 'Fiddle Leaf Fig').
        tool_context: ADK ToolContext supplied by runtime.
        prompt_details: Optional additional scene description details.

    Returns:
        Public Cloud Storage HTTPS URL of the generated video.
    """
    prompt = f"A short video clip of {item_name}"
    if prompt_details:
        prompt += f", {prompt_details}"

    interaction = global_genai_client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt,
    )

    video_bytes = None
    mime_type = "video/mp4"

    if hasattr(interaction, "output_video") and interaction.output_video and hasattr(interaction.output_video, "data"):
        raw_data = interaction.output_video.data
        if isinstance(raw_data, str):
            video_bytes = base64.b64decode(raw_data)
        elif isinstance(raw_data, bytes):
            video_bytes = raw_data
        
        if hasattr(interaction.output_video, "mime_type") and interaction.output_video.mime_type:
            mime_type = interaction.output_video.mime_type

    if not video_bytes:
        return f"Failed to generate video for '{item_name}'."

    slug = re.sub(r"[^\w\-]", "_", item_name.lower().strip())
    filename = f"{slug}_{uuid.uuid4().hex[:8]}.mp4"

    # 1. Save artifact using tool_context.save_artifact
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload video bytes directly to public Cloud Storage bucket
    object_path = f"plant_videos/{filename}"
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(object_path)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{object_path}"
    return public_url


def search_botany_database(query: str) -> str:
    """
    Search the free public iNaturalist Botany API for plant species taxonomy,
    common names, scientific names, Wikipedia URLs, and wild observations.

    Args:
        query: Plant name or species query (e.g., 'Monstera', 'Golden Pothos', 'Ficus').

    Returns:
        JSON string containing matching botanical records.
    """
    api_key = os.environ.get("INATURALIST_API_KEY", "")
    encoded_query = urllib.parse.quote(query.strip())
    url = f"https://api.inaturalist.org/v1/taxa?q={encoded_query}&iconic_taxa=Plantae&per_page=3"
    
    headers = {"User-Agent": "PlantGreenhouseConcierge/1.0"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            results = data.get("results", [])
            if not results:
                return f"No botanical species records found for '{query}'."

            plants = []
            for item in results:
                photo = item.get("default_photo") or {}
                plants.append({
                    "common_name": item.get("preferred_common_name", item.get("name")),
                    "scientific_name": item.get("name"),
                    "wikipedia_url": item.get("wikipedia_url"),
                    "photo_url": photo.get("medium_url") or photo.get("square_url"),
                    "total_observations": item.get("observations_count"),
                })
            return json.dumps(plants, indent=2)
    except Exception as e:
        return f"Error querying public botany API: {e}"


def geocode_address(address: str) -> str:
    """
    Converts a human-readable street address or city into geographical coordinates (latitude and longitude)
    using the Google Maps Geocoding API.

    Args:
        address: Full address or location string (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA' or 'San Francisco, CA').

    Returns:
        JSON string containing latitude, longitude, and formatted address.
    """
    api_key = _get_maps_api_key()
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not set in environment or .env."

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("status") != "OK" or not data.get("results"):
                return f"Geocoding failed for '{address}': {data.get('status')} - {data.get('error_message', 'No results')}"

            result = data["results"][0]
            loc = result["geometry"]["location"]
            return json.dumps({
                "formatted_address": result.get("formatted_address"),
                "latitude": loc.get("lat"),
                "longitude": loc.get("lng"),
            }, indent=2)
    except Exception as e:
        return f"Error calling Geocoding API: {e}"


def search_nearby_places(latitude: float, longitude: float, place_type: str = "florist", radius_meters: float = 5000.0) -> str:
    """
    Finds nearby places of a specified type (e.g., 'florist', 'park', 'greenhouse') around given coordinates
    using the Google Places API (New) searchNearby REST endpoint.

    Args:
        latitude: Latitude of center search point.
        longitude: Longitude of center search point.
        place_type: Type of place to search for (e.g. 'florist', 'garden_center', 'park').
        radius_meters: Radius in meters around coordinates to search (default: 5000m).

    Returns:
        JSON string containing list of nearby places with name, address, and location.
    """
    api_key = _get_maps_api_key()
    if not api_key:
        return "Error: GOOGLE_MAPS_API_KEY is not set in environment or .env."

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
    }
    payload = {
        "includedTypes": [place_type.strip().lower()],
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": float(latitude),
                    "longitude": float(longitude),
                },
                "radius": float(radius_meters),
            }
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            places = data.get("places", [])
            if not places:
                return f"No nearby places of type '{place_type}' found within {radius_meters}m."

            results = []
            for item in places:
                disp_name = item.get("displayName", {})
                loc = item.get("location", {})
                results.append({
                    "name": disp_name.get("text", "Unknown"),
                    "address": item.get("formattedAddress"),
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                    }
                })
            return json.dumps(results, indent=2)
    except Exception as e:
        return f"Error calling Places API (New): {e}"
