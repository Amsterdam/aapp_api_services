# Contact Service

The contact service provides contact and service map data for the Amsterdam App. It is used by multiple frontend modules:

- **Contact** (city offices, links)
- **Handig in de stad** (service maps)
- **Koningsdag** (service maps)

## API Endpoints

**Contact:**
- `GET /contact/api/v1/city-offices` — Returns a list of city offices with address, coordinates, opening hours, and related info. Data is serialized using `CityOfficeResultSerializer`.
- `GET /contact/api/v1/links` - Returns a list of links that are used in the app.
- `GET /contact/api/v1/health-check` — Simple health check endpoint.

**Service Maps:**
- `GET /service/api/v1/maps` — Returns available services for a given module source (e.g., 'Handig in de stad', 'Koningsdag').
- `GET /service/api/v1/maps/<service_id>` — Returns all relevant data for a specific service, including:
    - `layers`: UI-visible layer definitions (label + filtering + icon label)
    - `filters`: how the client can filter features
    - `icons_to_include`: icon definitions used by the client
    - `properties_to_include` / `silent_properties`: feature property handling
    - `data`: GeoJSON FeatureCollection
- Serializers for these endpoints are built dynamically based on the data structure using `build_map_response_serializer`.

## Implementation Notes

- Endpoints use caching for performance.
- OpenAPI schema extensions are used for documentation and API key handling.
- The service is designed to be modular and extensible for new modules or data types.

## How to add a new service (checklist)

A “service” is an entry that shows up in `GET /service/api/v1/maps?module_source=...` and can be fetched via `GET /service/api/v1/maps/<service_id>`.

1. Create (or reuse) a DataService implementation:
    - Add a new service class under services.
    - Implement a get_full_data method returning:
        - layers, filters, icons_to_include (optional), properties_to_include, silent_properties, list_property, data (GeoJSON FeatureCollection)
2. Register the service in the Services enum:
    - Edit `services.py`.
    - Add a new `ServiceClass(...)` entry with:
        - Unique id (becomes <service_id>)
        - title (shown to client)
        - icon (an IconPath key)
        - dataservice (your new service class)
        - input_module (e.g., ModuleSourceChoices.KONINGSDAG.value)
3. Add/confirm icons:
    - If needed, add to icons.py (`IconPath["<key>"] = "<svg path>"`).
    - Reference in your Services entry.
4. Add/update tests:
    - Edit `test_service_views.py`.
    - Test service discovery and service map payloads.
    - If your service calls external APIs, add mock fixtures under mock_data and patch/mock as needed.

## Dynamic Serializer
The service map endpoints use a dynamic serializer to construct the API response based on the service's configuration. This is handled by the `build_map_response_serializer` function in `service_serializers.py.`

**How it works:**
- The backend receives lists of properties, silent properties, filters, layers, and other metadata from the service definition.
- The dynamic serializer is built at runtime to match these fields, ensuring the API response always matches the service's data structure.
- This makes it easy to add new services or change data structures without writing new serializers for each case.

**Benefits:**
- No need to manually update serializers for each new service or property.
- Ensures strict validation and OpenAPI documentation for all fields.