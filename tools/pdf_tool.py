import requests
from Services.config import storage_name

AZURE_PDF_ENDPOINT = (
    "http://localhost:5164/api/AzureBlobStorage/containers/onboarding-materials/blobs/"
)

def fetch_pdf_links():
    headers = {
        "accept": "application/octet-stream"
    }

    try:
        resp = requests.get(AZURE_PDF_ENDPOINT, headers=headers)

        print("STATUS CODE:", resp.status_code)
        print("RAW TEXT:", repr(resp.text[:500]))

        # If it’s not returning JSON, show content type
        print("CONTENT-TYPE:", resp.headers.get("Content-Type"))

        # If failed, return nothing
        if resp.status_code != 200:
            print("ERROR: Server did not return 200")
            return []

        # Try parse JSON
        try:
            data = resp.json()
            print("PARSED JSON:", data)
        except Exception as e:
            print("JSON PARSE ERROR:", e)
            return []

        blobs = data.get("blobs", [])
        print("FOUND BLOBS:", blobs)

        # Build full blob URLs
        results = [
            {
                "name": blob,
                "url": f"https://{storage_name}.blob.core.windows.net/onboarding-materials/{blob}"
            }
            for blob in blobs
            if blob.lower().endswith(".pdf")
        ]

        return results
    except Exception as ex:
        return []
