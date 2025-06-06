import typesense
from typesense.exceptions import ObjectAlreadyExists

client = typesense.Client(
    {
        "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
        "api_key": "conscious-field",
        "connection_timeout_seconds": 10,
    }
)

rename_map = {
    "chapters_data_sourcing": "data_sourcing",
    "chapters_data_preparation": "data_preparation",
    "chapters_data_analysis": "data_analysis",
    "chapters_data_visualization": "data_visualization",
    "chapters_large_language_models": "large_language_models",
    "chapters_development_tools": "development_tools",
    "chapters_deployment_tools": "deployment_tools",
    "chapters_project-1": "project-1",
    "chapters_project-2": "project-2",
    "chapters_misc": "misc",
}

for old_name, new_name in rename_map.items():
    print(f"Copying {old_name} → {new_name}")
    try:
        # Check if old collection exists
        try:
            old_schema = client.collections[old_name].retrieve()
        except Exception as e:
            print(f"Source collection {old_name} does not exist. Skipping.")
            continue
        old_schema["name"] = new_name

        # Create new collection if it doesn't exist
        try:
            client.collections.create(old_schema)
        except (AttributeError, KeyError):
            print(f"Could not create collection {new_name}: invalid schema.")
            continue
        except ObjectAlreadyExists:
            print(f"Collection {new_name} already exists. Skipping creation.")

        # Determine if content_length should be string
        content_length_type = None
        for field in old_schema.get("fields", []):
            if field.get("name") == "content_length":
                content_length_type = field.get("type")
                break

        # Export from old collection (with pagination)
        page = 1
        per_page = 250
        query_by = old_schema.get("default_sorting_field")
        if not query_by:
            fields = old_schema.get("fields", [])
            if fields:
                query_by = fields[0].get("name") or next(
                    (k for k in fields[0] if k), None
                )
            else:
                print(f"No fields found in schema for {old_name}. Skipping.")
                continue
        if not isinstance(query_by, str) or not query_by:
            print(f"No valid query_by field for {old_name}. Skipping.")
            continue
        while True:
            results = client.collections[old_name].documents.search(
                {
                    "q": "*",
                    "query_by": query_by,
                    "per_page": per_page,
                    "page": page,
                }
            )
            hits = results.get("hits", [])
            if not hits:
                break
            for hit in hits:
                record = dict(hit["document"])  # Ensure it's a mutable dict
                # Patch content_length type if needed
                if "content_length" in record and content_length_type == "string":
                    record["content_length"] = str(record["content_length"])
                client.collections[new_name].documents.create(record)
            if len(hits) < per_page:
                break
            page += 1
    except Exception as e:
        print(f"Error processing {old_name}: {e}")
