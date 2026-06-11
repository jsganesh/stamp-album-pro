"""
Stamp collection data model and storage.

Stamps are stored as JSON in ~/StampAlbum/collection.json.
Each stamp has: id, country, year, description, catalog_number, catalog_type,
denomination, condition, purchase_price, image_path, notes, created_at, updated_at.
"""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

COLLECTION_FILE = Path.home() / "StampAlbum" / "collection.json"


@dataclass
class StampEntry:
    id: str
    country: str
    year: int
    description: str
    catalog_number: str
    catalog_type: str  # SG, Scott, Michel, Yvert, Other
    denomination: str
    condition: str  # Mint, Used, MH, MLH, FDC, Other
    purchase_price: float
    image_path: str
    notes: str
    created_at: str
    updated_at: str

    @classmethod
    def from_dict(cls, d: dict) -> "StampEntry":
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            country=d.get("country", ""),
            year=d.get("year", 0),
            description=d.get("description", ""),
            catalog_number=d.get("catalog_number", ""),
            catalog_type=d.get("catalog_type", "SG"),
            denomination=d.get("denomination", ""),
            condition=d.get("condition", ""),
            purchase_price=d.get("purchase_price", 0.0),
            image_path=d.get("image_path", ""),
            notes=d.get("notes", ""),
            created_at=d.get("created_at", datetime.now(timezone.utc).isoformat()),
            updated_at=d.get("updated_at", datetime.now(timezone.utc).isoformat()),
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "country": self.country,
            "year": self.year,
            "description": self.description,
            "catalog_number": self.catalog_number,
            "catalog_type": self.catalog_type,
            "denomination": self.denomination,
            "condition": self.condition,
            "purchase_price": self.purchase_price,
            "image_path": self.image_path,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def load_collection() -> list[dict]:
    """Load the stamp collection from JSON file."""
    if not COLLECTION_FILE.exists():
        return []
    try:
        with open(COLLECTION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_collection(stamps: list[dict]) -> None:
    """Save the stamp collection to JSON file."""
    COLLECTION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COLLECTION_FILE, "w", encoding="utf-8") as f:
        json.dump(stamps, f, indent=2, ensure_ascii=False)


def add_stamp(data: dict) -> dict:
    """Add a new stamp to the collection."""
    stamps = load_collection()
    stamp_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "id": stamp_id,
        "country": data.get("country", ""),
        "year": data.get("year", 0),
        "description": data.get("description", ""),
        "catalog_number": data.get("catalog_number", ""),
        "catalog_type": data.get("catalog_type", "SG"),
        "denomination": data.get("denomination", ""),
        "condition": data.get("condition", ""),
        "purchase_price": data.get("purchase_price", 0.0),
        "image_path": data.get("image_path", ""),
        "notes": data.get("notes", ""),
        "created_at": now,
        "updated_at": now,
    }
    stamps.append(entry)
    save_collection(stamps)
    return entry


def update_stamp(stamp_id: str, data: dict) -> Optional[dict]:
    """Update an existing stamp."""
    stamps = load_collection()
    for i, s in enumerate(stamps):
        if s.get("id") == stamp_id:
            stamps[i].update(data)
            stamps[i]["updated_at"] = datetime.now(timezone.utc).isoformat()
            stamps[i]["id"] = stamp_id  # Ensure ID doesn't change
            save_collection(stamps)
            return stamps[i]
    return None


def delete_stamp(stamp_id: str) -> bool:
    """Delete a stamp from the collection."""
    stamps = load_collection()
    original_len = len(stamps)
    stamps = [s for s in stamps if s.get("id") != stamp_id]
    if len(stamps) < original_len:
        save_collection(stamps)
        return True
    return False


def search_stamps(
    query: str = "",
    country: str = "",
    year_from: int = 0,
    year_to: int = 0,
    catalog_type: str = "",
    condition: str = "",
    sort_by: str = "country",
    sort_order: str = "asc",
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[dict], int]:
    """Search and filter stamps. Returns (results, total_count)."""
    stamps = load_collection()

    # Filter
    if query:
        q = query.lower()
        stamps = [
            s for s in stamps
            if q in s.get("description", "").lower()
            or q in s.get("catalog_number", "").lower()
            or q in s.get("country", "").lower()
            or q in s.get("notes", "").lower()
        ]
    if country:
        stamps = [s for s in stamps if s.get("country", "").lower() == country.lower()]
    if year_from:
        stamps = [s for s in stamps if s.get("year", 0) >= year_from]
    if year_to:
        stamps = [s for s in stamps if s.get("year", 0) <= year_to]
    if catalog_type:
        stamps = [s for s in stamps if s.get("catalog_type", "") == catalog_type]
    if condition:
        stamps = [s for s in stamps if s.get("condition", "") == condition]

    # Sort
    reverse = sort_order == "desc"
    if sort_by == "year":
        stamps.sort(key=lambda s: s.get("year", 0), reverse=reverse)
    elif sort_by == "price":
        stamps.sort(key=lambda s: s.get("purchase_price", 0.0), reverse=reverse)
    elif sort_by == "updated":
        stamps.sort(key=lambda s: s.get("updated_at", ""), reverse=reverse)
    else:
        stamps.sort(key=lambda s: s.get(sort_by, "").lower(), reverse=reverse)

    total = len(stamps)
    # Paginate
    start = (page - 1) * per_page
    end = start + per_page
    return stamps[start:end], total


def import_csv(csv_text: str) -> tuple[int, list[str]]:
    """
    Import stamps from CSV text.
    Expected columns: country, year, description, catalog_number, catalog_type,
                      denomination, condition, purchase_price, image_path, notes
    Returns (count_imported, list_of_errors).
    """
    import csv
    import io

    errors = []
    count = 0
    stamps = load_collection()

    reader = csv.DictReader(io.StringIO(csv_text))
    for row_num, row in enumerate(reader, start=2):
        try:
            entry = {
                "id": str(uuid.uuid4()),
                "country": row.get("country", "").strip(),
                "year": int(row.get("year", 0) or 0),
                "description": row.get("description", "").strip(),
                "catalog_number": row.get("catalog_number", "").strip(),
                "catalog_type": row.get("catalog_type", "SG").strip() or "SG",
                "denomination": row.get("denomination", "").strip(),
                "condition": row.get("condition", "").strip(),
                "purchase_price": float(row.get("purchase_price", 0) or 0),
                "image_path": row.get("image_path", "").strip(),
                "notes": row.get("notes", "").strip(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            stamps.append(entry)
            count += 1
        except (ValueError, KeyError) as e:
            errors.append(f"Row {row_num}: {e}")

    if count > 0:
        save_collection(stamps)

    return count, errors


def get_collection_stats() -> dict:
    """Get summary statistics about the collection."""
    stamps = load_collection()
    countries = set(s.get("country", "") for s in stamps if s.get("country"))
    total_value = sum(s.get("purchase_price", 0.0) for s in stamps)
    catalog_types = {}
    for s in stamps:
        ct = s.get("catalog_type", "Other")
        catalog_types[ct] = catalog_types.get(ct, 0) + 1

    return {
        "total_stamps": len(stamps),
        "countries": sorted(countries),
        "total_value": round(total_value, 2),
        "catalog_types": catalog_types,
    }
