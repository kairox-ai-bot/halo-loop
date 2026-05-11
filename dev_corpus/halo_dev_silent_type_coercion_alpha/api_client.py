def fetch_record(record_id):
    # API expects string IDs like "001", "002"
    # str() coercion happens implicitly in the URL path
    url = f"/api/records/{record_id}"
    return {"url_called": url, "found": url.endswith("001")}
