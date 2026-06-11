"""
Curated font pairing suggestions for stamp album pages.

Each pairing includes:
- name: display name
- heading_font: font ID for headings/titles
- body_font: font ID for body text
- description: why this pairing works
- style: general style category
"""

FONT_PAIRINGS = [
    {
        "id": "classic_serif",
        "name": "Classic Serif",
        "heading_font": "TB",
        "body_font": "TN",
        "description": "Traditional and authoritative. Perfect for historical collections.",
        "style": "Classic",
    },
    {
        "id": "modern_sans",
        "name": "Modern Sans-Serif",
        "heading_font": "HB",
        "body_font": "HN",
        "description": "Clean and contemporary. Great for modern stamp issues.",
        "style": "Modern",
    },
    {
        "id": "elegant_contrast",
        "name": "Elegant Contrast",
        "heading_font": "TS",
        "body_font": "HN",
        "description": "Bold headings with readable body text. Excellent for competition pages.",
        "style": "Elegant",
    },
    {
        "id": "uniform_helvetica",
        "name": "Uniform Helvetica",
        "heading_font": "HB",
        "body_font": "HN",
        "description": "Consistent family feel. Clean and professional.",
        "style": "Modern",
    },
    {
        "id": "uniform_times",
        "name": "Uniform Times",
        "heading_font": "TB",
        "body_font": "TN",
        "description": "Classic newspaper style. Highly readable for dense text.",
        "style": "Classic",
    },
    {
        "id": "mono_accent",
        "name": "Monospace Accent",
        "heading_font": "CB",
        "body_font": "TN",
        "description": "Typewriter-style headings with serif body. Unique character.",
        "style": "Creative",
    },
    {
        "id": "bold_impact",
        "name": "Bold Impact",
        "heading_font": "HS",
        "body_font": "HN",
        "description": "Strong headlines with neutral body. Makes titles stand out.",
        "style": "Bold",
    },
    {
        "id": "italic_emphasis",
        "name": "Italic Emphasis",
        "heading_font": "TI",
        "body_font": "TN",
        "description": "Elegant italic headings with roman body. Sophisticated look.",
        "style": "Elegant",
    },
    {
        "id": "vintage_typewriter",
        "name": "Vintage Typewriter",
        "heading_font": "CS",
        "body_font": "CN",
        "description": "Full monospace. Evokes early 20th century documentation.",
        "style": "Vintage",
    },
    {
        "id": "minimal_light",
        "name": "Minimal Light",
        "heading_font": "HN",
        "body_font": "HN",
        "description": "Light, airy, and minimal. Lets the stamps be the focus.",
        "style": "Minimal",
    },
]

# Map of font IDs to human-readable names
FONT_NAMES = {
    "CN": "Courier",
    "CB": "Courier Bold",
    "CI": "Courier Italic",
    "CS": "Courier Bold Italic",
    "TN": "Times Roman",
    "TB": "Times Bold",
    "TI": "Times Italic",
    "TS": "Times Bold Italic",
    "HN": "Helvetica",
    "HB": "Helvetica Bold",
    "HI": "Helvetica Italic",
    "HS": "Helvetica Bold Italic",
}


def get_pairing(pairing_id):
    """Get a font pairing by ID."""
    for p in FONT_PAIRINGS:
        if p["id"] == pairing_id:
            return p
    return None


def get_pairings_by_style(style):
    """Get all font pairings for a given style category."""
    return [p for p in FONT_PAIRINGS if p["style"].lower() == style.lower()]


def get_all_styles():
    """Get all available style categories."""
    return sorted(set(p["style"] for p in FONT_PAIRINGS))
