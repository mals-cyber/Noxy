import requests
from Services.config import storage_name

AZURE_PDF_ENDPOINT = "http://localhost:5164/api/onboarding/materials/blobs"

def fetch_pdf_links():
    try:
        resp = requests.get(AZURE_PDF_ENDPOINT)

        print("STATUS CODE:", resp.status_code)
        print("RAW TEXT:", resp.text[:300])

        if resp.status_code != 200:
            print("ERROR: Non-200 status")
            return []

        # Parse JSON
        try:
            data = resp.json()
        except Exception as e:
            print("JSON PARSE ERROR:", e)
            return []

        print("PARSED JSON:", data)

        # Backend returns LIST -> data = [ "file1.pdf", "file2.pdf", ... ]
        if isinstance(data, list):
            blobs = data
        elif isinstance(data, dict):
            blobs = data.get("blobs", [])
        else:
            print("Unknown response format")
            return []

        print("FOUND BLOBS:", blobs)

        # Build full Azure URLs
        results = [
            {
                "name": blob.split("/")[-1],  # keep only filename
                "url": f"https://{storage_name}.blob.core.windows.net/onboarding-materials/{blob}"
            }
            for blob in blobs
            if blob.lower().endswith(".pdf")
        ]

        print("PDF RESULTS:", results)
        return results

    except Exception as e:
        print("REQUEST ERROR:", e)
        return []
