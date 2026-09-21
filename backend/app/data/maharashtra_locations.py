"""
Maharashtra location data for Risk Hotspot Map.
Contains lat/lng coordinates, district names, climate zones, and associated disease/pest patterns.
"""

MAHARASHTRA_LOCATIONS = [
    {
        "name": "Mumbai",
        "lat": 19.0760,
        "lng": 72.8777,
        "district": "Mumbai City",
        "climate_zone": "coastal_humid",
        "description": "Coastal, humid, high rainfall",
        "common_diseases": ["Leaf Blight", "Powdery Mildew", "Downy Mildew", "Root Rot"],
        "common_pests": ["Thrips", "Whitefly"],
        "disease_skew": "fungal",  # Higher fungal disease pressure
        "base_scan_volume": 150,  # Higher scan volume due to dense farming
    },
    {
        "name": "Nashik",
        "lat": 19.9975,
        "lng": 73.7898,
        "district": "Nashik",
        "climate_zone": "semi_arid",
        "description": "Semi-arid, grape/onion belt",
        "common_diseases": ["Powdery Mildew", "Anthracnose"],
        "common_pests": ["Thrips", "Aphids", "Mealybugs"],
        "disease_skew": "mixed",
        "base_scan_volume": 120,
    },
    {
        "name": "Mahabaleshwar",
        "lat": 17.9229,
        "lng": 73.6586,
        "district": "Satara",
        "climate_zone": "hill_station",
        "description": "Hill station, cool + very wet",
        "common_diseases": ["Strawberry Disease", "Root Rot", "Grey Mold", "Leaf Spot"],
        "common_pests": ["Mites", "Aphids"],
        "disease_skew": "fungal",  # Very high fungal disease pressure
        "base_scan_volume": 80,
    },
    {
        "name": "Pune",
        "lat": 18.5204,
        "lng": 73.8567,
        "district": "Pune",
        "climate_zone": "moderate",
        "description": "Moderate, mixed cropping",
        "common_diseases": ["Leaf Spot", "Rust", "Blight"],
        "common_pests": ["Bollworm", "Whitefly", "Aphids"],
        "disease_skew": "mixed",
        "base_scan_volume": 100,
    },
    {
        "name": "Nagpur",
        "lat": 21.1458,
        "lng": 79.0882,
        "district": "Nagpur",
        "climate_zone": "interior_dry",
        "description": "Hot, dry interior, citrus belt",
        "common_diseases": ["Citrus Canker", "Gummosis"],
        "common_pests": ["Whitefly", "Fruit Fly", "Citrus Psylla"],
        "disease_skew": "pest",  # Higher pest pressure
        "base_scan_volume": 90,
    },
    {
        "name": "Kolhapur",
        "lat": 16.7050,
        "lng": 74.2433,
        "district": "Kolhapur",
        "climate_zone": "sugarcane_belt",
        "description": "Sugarcane belt, humid",
        "common_diseases": ["Red Rot", "Smut", "Leaf Scald"],
        "common_pests": ["Borer Pests", "Shoot Borer", "Whitefly"],
        "disease_skew": "mixed",
        "base_scan_volume": 110,
    },
    {
        "name": "Aurangabad",
        "lat": 19.8762,
        "lng": 75.3433,
        "district": "Aurangabad",
        "climate_zone": "semi_arid",
        "description": "Semi-arid, cotton belt",
        "common_diseases": ["Bacterial Blight", "Fusarium Wilt"],
        "common_pests": ["Bollworm", "Pink Bollworm", "Aphids"],
        "disease_skew": "pest",  # Higher pest pressure
        "base_scan_volume": 95,
    },
    {
        "name": "Solapur",
        "lat": 17.6599,
        "lng": 75.9064,
        "district": "Solapur",
        "climate_zone": "dry_drought_prone",
        "description": "Dry, drought-prone",
        "common_diseases": ["Charcoal Rot", "Stem Rot"],
        "common_pests": ["Bollworm", "Spider Mites", "Jassids"],
        "disease_skew": "pest",
        "base_scan_volume": 70,
    },
    {
        "name": "Amravati",
        "lat": 20.9374,
        "lng": 77.7796,
        "district": "Amravati",
        "climate_zone": "interior_dry",
        "description": "Cotton/soybean, hot, Vidarbha region",
        "common_diseases": ["Alternaria Leaf Spot", "Tobacco Streak Virus"],
        "common_pests": ["Pink Bollworm", "Spodoptera", "Whitefly"],
        "disease_skew": "pest",  # Historically high pest pressure
        "base_scan_volume": 85,
    },
]

# Helper functions for demo data generation
def get_location_by_name(name: str):
    """Get location data by name."""
    for loc in MAHARASHTRA_LOCATIONS:
        if loc["name"].lower() == name.lower():
            return loc
    return None

def get_locations_by_climate_zone(climate_zone: str):
    """Get all locations matching a climate zone."""
    return [loc for loc in MAHARASHTRA_LOCATIONS if loc["climate_zone"] == climate_zone]

def get_disease_skew_for_location(location_name: str) -> str:
    """Get disease skew (fungal/pest/mixed) for a location."""
    loc = get_location_by_name(location_name)
    return loc["disease_skew"] if loc else "mixed"

def get_common_diseases_for_location(location_name: str) -> list:
    """Get common diseases for a location based on climate zone."""
    loc = get_location_by_name(location_name)
    return loc["common_diseases"] if loc else []

def get_common_pests_for_location(location_name: str) -> list:
    """Get common pests for a location based on climate zone."""
    loc = get_location_by_name(location_name)
    return loc["common_pests"] if loc else []
