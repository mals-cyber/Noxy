import requests
import tempfile
import os
from pathlib import Path
from langchain_core.documents import Document
from .loaders import load_json_kb, extract_pdf_text, load_md_kb
from .chunker import chunk_documents
from .store import get_vector_db


def download_file_from_url(url: str, timeout: int = 30) -> str:
    """
    Download file from public URL and save to temporary file.

    Args:
        url: Public file URL (http/https)
        timeout: Request timeout in seconds

    Returns:
        Path to temporary file

    Raises:
        ValueError: If download fails or invalid URL
        requests.RequestException: If network error occurs
    """
    try:
        # Validate URL format
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")

        # Download file
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        # Check content length if available
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            raise ValueError("File size exceeds 10MB limit")

        # Save to temp file with proper extension
        file_extension = Path(url).suffix or ".bin"
        temp_file = tempfile.NamedTemporaryFile(
            suffix=file_extension,
            delete=False,
            mode="wb"
        )

        # Stream download to file
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                temp_file.write(chunk)

        temp_file.close()
        return temp_file.name

    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to download file: {str(e)}")


def get_file_type(url: str) -> str:
    """
    Determine file type from URL extension.

    Args:
        url: File URL

    Returns:
        "json", "pdf", or "md"

    Raises:
        ValueError: If unsupported file type
    """
    extension = Path(url).suffix.lower()

    if extension == ".json":
        return "json"
    elif extension == ".pdf":
        return "pdf"
    elif extension == ".md":
        return "md"
    else:
        raise ValueError(f"Unsupported file type: {extension}. Only .json, .pdf, and .md are supported.")


def inject_document_from_url(url: str) -> dict:
    """
    Download document from URL and inject into ChromaDB.

    Args:
        url: Public file URL to document

    Returns:
        dict with:
            - success: bool
            - documents_added: int (number of chunks added)
            - file_type: str ("json", "pdf", or "md")
            - message: str (success or error message)

    Raises:
        ValueError: If validation or processing fails
    """
    temp_file = None

    try:
        # Validate file type
        file_type = get_file_type(url)

        # Download file
        temp_file = download_file_from_url(url)

        # Load documents based on file type
        if file_type == "json":
            docs = load_json_kb(temp_file)
        elif file_type == "md":
            docs = load_md_kb(temp_file)
        else:  # pdf
            text = extract_pdf_text(temp_file)
            if text:
                # Create document with PDF filename in content
                filename = Path(url).name
                docs = [Document(page_content=f"PDF FILE: {filename}\n{text}")]
            else:
                docs = []

        if not docs:
            raise ValueError("No content extracted from file")

        # Chunk documents
        chunks = chunk_documents(docs)

        if not chunks:
            raise ValueError("No chunks created from document")

        # Add metadata to each chunk
        for c in chunks:
            c.metadata = {
                "source": url,
                "file_type": file_type,
                "original_filename": Path(url).name
            }

        # Add to ChromaDB
        vector_db = get_vector_db()
        vector_db.add_documents(chunks)

        return {
            "success": True,
            "documents_added": len(chunks),
            "file_type": file_type,
            "message": f"Successfully injected {len(chunks)} chunks from {file_type.upper()} file"
        }

    except Exception as e:
        return {
            "success": False,
            "documents_added": 0,
            "file_type": None,
            "message": f"Error: {str(e)}"
        }

    finally:
        # Clean up temp file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
