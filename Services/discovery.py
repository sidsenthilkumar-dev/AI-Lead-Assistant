import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

OVERPASS_URLS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]


def geocode_location(location):
    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": location,
            "format": "json",
            "limit": 1,
        },
        headers={
            "User-Agent": "AI-Lead-Assistant/1.0",
        },
        timeout=15,
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    return {
        "lat": float(results[0]["lat"]),
        "lon": float(results[0]["lon"]),
    }


def search_nominatim(target_business, location):
    response = requests.get(
        NOMINATIM_URL,
        params={
            "q": f"{target_business} in {location}",
            "format": "json",
            "addressdetails": 1,
            "limit": 50,
            "dedupe": 1,
        },
        headers={
            "User-Agent": "AI-Lead-Assistant/1.0",
        },
        timeout=20,
    )

    response.raise_for_status()

    results = response.json()

    businesses = []
    seen = set()

    ignored_types = {
        "school",
        "place_of_worship",
        "residential",
        "road",
        "park",
        "neighbourhood",
        "city",
        "town",
        "village",
        "hamlet",
        "county",
        "state",
        "suburb",
        "building",
        "house",
    }

    for result in results:
        name = result.get("name", "").strip()

        if not name:
            continue

        result_type = result.get("type", "").lower()

        if result_type in ignored_types:
            continue

        key = name.lower()

        if key in seen:
            continue

        seen.add(key)

        address = result.get("display_name", "")

        address_data = result.get("address", {})

        industry = (
            result_type
            or result.get("class", "")
            or target_business
        )

        businesses.append(
            {
                "company": name,
                "industry": industry,
                "website": "",
                "phone": "",
                "address": address,
                "source": "OpenStreetMap",
            }
        )

    return businesses


def search_overpass(target_business, location):
    coordinates = geocode_location(location)

    if not coordinates:
        return []

    lat = coordinates["lat"]
    lon = coordinates["lon"]

    query = f"""
    [out:json][timeout:15];

    (
      nwr(around:5000,{lat},{lon})["name"]["shop"];
      nwr(around:5000,{lat},{lon})["name"]["office"];
      nwr(around:5000,{lat},{lon})["name"]["craft"];
      nwr(around:5000,{lat},{lon})["name"]["amenity"];
    );

    out center tags;
    """

    for overpass_url in OVERPASS_URLS:
        try:
            response = requests.post(
                overpass_url,
                data=query,
                headers={
                    "User-Agent": "AI-Lead-Assistant/1.0",
                },
                timeout=20,
            )

            if response.status_code != 200:
                continue

            data = response.json()

            businesses = []
            seen = set()

            for element in data.get("elements", []):
                tags = element.get("tags", {})

                name = tags.get("name", "").strip()

                if not name:
                    continue

                key = name.lower()

                if key in seen:
                    continue

                seen.add(key)

                address_parts = []

                for field in [
                    "addr:housenumber",
                    "addr:street",
                    "addr:city",
                    "addr:state",
                    "addr:postcode",
                ]:
                    value = tags.get(field)

                    if value:
                        address_parts.append(value)

                businesses.append(
                    {
                        "company": name,
                        "industry": (
                            tags.get("shop")
                            or tags.get("office")
                            or tags.get("craft")
                            or tags.get("amenity")
                            or target_business
                        ),
                        "website": (
                            tags.get("website")
                            or tags.get("contact:website")
                            or ""
                        ),
                        "phone": (
                            tags.get("phone")
                            or tags.get("contact:phone")
                            or ""
                        ),
                        "address": ", ".join(address_parts),
                        "source": "OpenStreetMap",
                    }
                )

                if len(businesses) >= 50:
                    break

            return businesses

        except requests.RequestException:
            continue

    return []


def search_businesses(target_business, location):
    # try the simple search first
    businesses = search_nominatim(
        target_business,
        location,
    )

    if businesses:
        return businesses

    # use Overpass if the direct search finds nothing
    return search_overpass(
        target_business,
        location,
    )