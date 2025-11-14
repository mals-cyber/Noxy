# Quick Start: Upload Document Endpoint

## Endpoint

```
POST /upload-document
```

## Quick Test

### Using cURL
```bash
curl -X POST http://localhost:8000/upload-document \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.blob.core.windows.net/container/document.json"}'
```

### Using Python
```python
import requests

url = "http://localhost:8000/upload-document"
payload = {"url": "https://example.blob.core.windows.net/container/document.json"}
response = requests.post(url, json=payload)
print(response.json())
```

## Response

**Success:**
```json
{
  "success": true,
  "documents_added": 12,
  "file_type": "json",
  "message": "Successfully injected 12 chunks from JSON file"
}
```

**Error:**
```json
{
  "success": false,
  "documents_added": 0,
  "file_type": null,
  "message": "Error: File size exceeds 10MB limit"
}
```

## Supported File Types

- ✅ `.json` - Knowledge base JSON files
- ✅ `.pdf` - PDF documents
- ✅ `.md` - Markdown documentation
- ❌ Everything else

## File Requirements

- Must be publicly accessible (HTTP/HTTPS)
- Maximum 10 MB
- Valid format (proper JSON structure, readable PDF, or valid Markdown)

## Files Modified

| File | Changes |
|------|---------|
| `vector/inject.py` | **NEW** - Document injection logic |
| `vector/store.py` | Added `add_documents_to_db()` function |
| `Services/main.py` | Added `/upload-document` endpoint |

## Flow Diagram

```
Client Request (URL)
    ↓
validate URL format
    ↓
download file (requests library)
    ↓
detect file type (.json, .pdf, or .md)
    ↓
parse content (existing loaders)
    ↓
chunk documents (existing chunker)
    ↓
add to ChromaDB (incremental)
    ↓
cleanup temp file
    ↓
return response
```

## API Documentation

Full API documentation available at:
```
http://localhost:8000/docs
```

Look for the `/upload-document` endpoint under POST methods.

## Testing

```bash
python test_upload_endpoint.py
```

## Troubleshooting

**"ModuleNotFoundError: requests"**
→ Activate virtual environment: `.\venv\Scripts\activate`

**"File size exceeds 10MB limit"**
→ Use a smaller file or split into multiple files

**"Failed to download file"**
→ Verify URL is publicly accessible (no authentication required)

**"Unsupported file type"**
→ Only `.json`, `.pdf`, and `.md` files are supported
