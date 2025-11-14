# Upload Document to Vector DB Endpoint

## Overview

A new FastAPI endpoint `/upload-document` has been added to enable dynamic injection of JSON, PDF, and Markdown documents from public Azure Blob Storage URLs into the ChromaDB vector database, without requiring server restart or manual file placement.

## Endpoint Details

### POST `/upload-document`

**Description:** Upload and inject a document (JSON, PDF, or Markdown) into the vector database for semantic search.

**Request:**
```json
{
  "url": "https://example.blob.core.windows.net/container/document.json"
}
```

**Response (Success):**
```json
{
  "success": true,
  "documents_added": 12,
  "file_type": "json",
  "message": "Successfully injected 12 chunks from JSON file"
}
```

**Response (Error):**
```json
{
  "success": false,
  "documents_added": 0,
  "file_type": null,
  "message": "Error: File size exceeds 10MB limit"
}
```

### Supported File Types

- **JSON** (`.json`)
  - Uses existing JSON knowledge base format
  - Structure: `{ "knowledgeBase": { "categories": [...] } }`
  - Each entry becomes a document with question, answer, and keywords

- **PDF** (`.pdf`)
  - Text extracted via PyMuPDF (fitz)
  - Entire PDF becomes one document (pre-chunked internally)

- **Markdown** (`.md`)
  - Splits by header levels (`#`, `##`, `###`, etc.)
  - Expands bullet points into full sentences
  - Each section becomes a document

### Validation & Constraints

| Constraint | Value |
|-----------|-------|
| Max file size | 10 MB |
| Supported formats | `.json`, `.pdf`, `.md` |
| URL scheme | `http://` or `https://` |
| Request timeout | 30 seconds |
| File accessibility | Must be publicly downloadable |

## Implementation

### New Files

**`vector/inject.py`** - Core document injection logic
- `download_file_from_url(url, timeout)` - Downloads file from public URL
- `get_file_type(url)` - Determines file type from extension
- `inject_document_from_url(url)` - Orchestrates download, process, and inject

### Modified Files

**`vector/store.py`** - Added helper function
- `add_documents_to_db(documents, metadatas)` - Adds documents to existing ChromaDB

**`Services/main.py`** - Added endpoint
- `UploadDocumentRequest` - Pydantic model for request validation
- `POST /upload-document` - FastAPI endpoint handler

## Usage Examples

### Example 1: Upload JSON FAQ

```bash
curl -X POST http://localhost:8000/upload-document \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.blob.core.windows.net/kb/faq.json"
  }'
```

Response:
```json
{
  "success": true,
  "documents_added": 24,
  "file_type": "json",
  "message": "Successfully injected 24 chunks from JSON file"
}
```

### Example 2: Upload PDF Form

```bash
curl -X POST http://localhost:8000/upload-document \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.blob.core.windows.net/forms/application.pdf"
  }'
```

### Example 3: Upload Markdown Documentation

```bash
curl -X POST http://localhost:8000/upload-document \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.blob.core.windows.net/docs/employee-handbook.md"
  }'
```

Response:
```json
{
  "success": true,
  "documents_added": 18,
  "file_type": "md",
  "message": "Successfully injected 18 chunks from MD file"
}
```

### Example 4: Using Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/upload-document",
    json={
        "url": "https://example.blob.core.windows.net/docs/handbook.pdf"
    }
)

result = response.json()
if result["success"]:
    print(f"Added {result['documents_added']} chunks to vector DB")
else:
    print(f"Error: {result['message']}")
```

## How It Works

1. **Receive URL** - Client sends public file URL via POST request
2. **Validate** - Verify URL format and file type (JSON/PDF/MD)
3. **Download** - Stream file from public Azure Blob Storage or any public URL
4. **Parse** - Load content using existing loaders:
   - JSON: Uses `load_json_kb()` from `vector/loaders.py`
   - PDF: Uses `extract_pdf_text()` from `vector/loaders.py`
   - Markdown: Uses `load_md_kb()` from `vector/loaders.py`
5. **Chunk** - Apply existing chunking logic via `chunk_documents()`
6. **Embed** - ChromaDB automatically embeds using configured embedding function
7. **Store** - Add chunks to existing ChromaDB (incremental, no rebuild needed)
8. **Cleanup** - Delete temporary downloaded file
9. **Return** - Send success/error response with statistics

## Key Benefits

✅ **Dynamic updates** - No need to restart server or manually manage files
✅ **Azure Blob Storage ready** - Works with public Azure Blob Storage URLs
✅ **Reuses existing code** - Leverages current loaders, chunkers, and embedders
✅ **Incremental injection** - Adds documents without rebuilding entire vector DB
✅ **Error handling** - Validates files and returns informative error messages
✅ **Metadata tracking** - Stores source URL, file type, and filename with documents

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `URL must start with http:// or https://` | Invalid URL scheme | Use public HTTP(S) URL |
| `Unsupported file type: .txt` | Wrong file extension | Only `.json`, `.pdf`, and `.md` supported |
| `File size exceeds 10MB limit` | File too large | Use smaller files or split into parts |
| `Failed to download file` | URL not accessible | Verify URL is publicly accessible |
| `No content extracted from file` | File is empty or corrupted | Check file content and format |

## Database Impact

- **Non-destructive** - Adds to existing ChromaDB, doesn't rebuild or delete
- **Metadata** - Each chunk stores source URL and original filename
- **Searchability** - Immediately available for chatbot semantic search
- **Persistence** - Changes persisted to disk in ChromaDB directory

## Testing

Run the test suite:
```bash
python test_upload_endpoint.py
```

Tests verify:
- Module imports
- File type detection
- JSON injection structure
- Request model validation

## Integration with Existing System

The endpoint integrates seamlessly with existing Noxy components:

- **Chatbot search** - Injected documents immediately available for `/chat` semantic search
- **User conversations** - No impact on conversation history or user data
- **Vector database** - Uses same ChromaDB instance and embedding model
- **Error handling** - Follows existing API error response patterns

## Development Notes

### Limitations

- Public URLs only (no authentication support yet)
- Single-threaded injection (sequential processing)
- No duplicate detection (same content can be added multiple times)
- No download resume on network failure

### Future Enhancements

- Add authentication support (SAS tokens, API keys)
- Batch upload multiple documents
- Duplicate detection and deduplication
- Document versioning and updates
- Progress tracking for large files
- Automatic refresh of vector embeddings

## Security Considerations

✅ **File validation** - Type and size checking
✅ **URL validation** - HTTP(S) scheme verification
✅ **Safe temp handling** - Temp files cleaned up in finally block
✅ **Error messages** - Don't expose internal paths
⚠️ **No authentication** - Public endpoint (add auth if needed)
⚠️ **No malware scanning** - Consider adding if handling untrusted files

## Related Documentation

- See `CLAUDE.md` for architecture overview
- See `Services/main.py` for endpoint implementation
- See `vector/inject.py` for injection logic
- See `vector/loaders.py` for file format handlers
- See `vector/chunker.py` for document chunking strategy
