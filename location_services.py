import os
from typing import List, Dict, Optional

try:
    import googlemaps
except ImportError:
    print("Please install googlemaps: pip install googlemaps")

class LocationServices:
    """
    Service for integrating Google Maps and Places API to discover local providers.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LocationServices with a Google Maps API Key.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("Google Maps API Key is required. Set GOOGLE_MAPS_API_KEY environment variable.")
        
        self.gmaps = googlemaps.Client(key=self.api_key)

    def geocode_address(self, address: str) -> Optional[Dict[str, float]]:
        """
        Converts an address string (e.g., "DHA Phase 5, Lahore") into coordinates.
        """
        try:
            geocode_result = self.gmaps.geocode(address)
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                return {
                    "lat": location['lat'],
                    "lng": location['lng']
                }
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None

    def discover_local_providers(self, lat: float, lng: float, service_type: str, radius: int = 5000) -> List[Dict]:
        """
        Discovers local service providers based on coordinates using Google Places API.
        
        Args:
            lat (float): Latitude
            lng (float): Longitude
            service_type (str): Type of service (e.g., 'plumber', 'electrician', 'ac repair')
            radius (int): Search radius in meters (default 5km)
            
        Returns:
            List of dictionaries containing provider details (name, rating, address, location).
        """
        try:
            # We use places_nearby to search for businesses matching the service_type
            places_result = self.gmaps.places_nearby(
                location=(lat, lng),
                radius=radius,
                keyword=service_type
            )
            
            providers = []
            if places_result and 'results' in places_result:
                for place in places_result['results']:
                    provider = {
                        "name": place.get("name"),
                        "rating": place.get("rating", 0.0),
                        "user_ratings_total": place.get("user_ratings_total", 0),
                        "address": place.get("vicinity"),
                        "location": place.get("geometry", {}).get("location", {}),
                        "place_id": place.get("place_id"),
                        "business_status": place.get("business_status")
                    }
                    providers.append(provider)
                    
            # Sort providers by rating and number of reviews
            providers.sort(key=lambda x: (x["rating"], x["user_ratings_total"]), reverse=True)
            return providers
            
        except Exception as e:
            print(f"Error discovering providers: {e}")
            return []

# Example Usage
if __name__ == "__main__":
    # Ensure you have GOOGLE_MAPS_API_KEY set in your environment variables.
    try:
        location_service = LocationServices()
        
        # 1. First, get coordinates for a location (this would typically come from the NLU module's output)
        address = "F-8 Markaz, Islamabad, Pakistan"
        print(f"Geocoding address: {address}")
        coords = location_service.geocode_address(address)
        
        if coords:
            print(f"Coordinates found: {coords}")
            
            # 2. Discover providers (e.g., plumbers) near these coordinates
            service_needed = "plumber"
            print(f"\nSearching for '{service_needed}' within 5km of {coords}...")
            
            providers = location_service.discover_local_providers(
                lat=coords['lat'], 
                lng=coords['lng'], 
                service_type=service_needed
            )
            
            print(f"\nFound {len(providers)} providers:")
            for idx, p in enumerate(providers[:5], 1): # Show top 5
                print(f"{idx}. {p['name']} - Rating: {p['rating']} ({p['user_ratings_total']} reviews) - Address: {p['address']}")
        else:
            print("Could not geocode the address.")
            
    except ValueError as e:
        print(f"Setup Error: {e}")
