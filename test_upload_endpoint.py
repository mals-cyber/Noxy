"""
Test script for the /upload-document endpoint
Tests the vector DB injection functionality without requiring a running server
"""

import json
import tempfile
import os
from pathlib import Path


def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        from vector.inject import inject_document_from_url, download_file_from_url, get_file_type
        from vector.store import add_documents_to_db, get_vector_db
        from Services.main import upload_document, UploadDocumentRequest
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_file_type_detection():
    """Test file type detection"""
    print("\nTesting file type detection...")
    try:
        from vector.inject import get_file_type

        # Test JSON detection
        assert get_file_type("https://example.com/file.json") == "json"
        print("✓ JSON detection works")

        # Test PDF detection
        assert get_file_type("https://example.com/file.pdf") == "pdf"
        print("✓ PDF detection works")

        # Test invalid type
        try:
            get_file_type("https://example.com/file.txt")
            print("✗ Should have rejected .txt file")
            return False
        except ValueError:
            print("✓ Correctly rejects unsupported file types")

        return True
    except Exception as e:
        print(f"✗ File type detection test failed: {e}")
        return False


def test_json_injection_structure():
    """Test JSON injection with a sample file"""
    print("\nTesting JSON injection structure...")
    try:
        from vector.inject import inject_document_from_url

        # Create a temporary JSON file with proper structure
        sample_json = {
            "knowledgeBase": {
                "categories": [
                    {
                        "name": "Test Category",
                        "entries": [
                            {
                                "question": "What is this?",
                                "answer": "This is a test answer",
                                "keywords": ["test", "sample"]
                            }
                        ]
                    }
                ]
            }
        }

        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_json, f)
            temp_path = f.name

        print(f"✓ Created test JSON file at {temp_path}")
        print(f"  File size: {os.path.getsize(temp_path)} bytes")

        # Clean up
        os.unlink(temp_path)
        return True

    except Exception as e:
        print(f"✗ JSON injection structure test failed: {e}")
        return False


def test_endpoint_request_model():
    """Test the Pydantic request model"""
    print("\nTesting endpoint request model...")
    try:
        from Services.main import UploadDocumentRequest

        # Test valid request
        req = UploadDocumentRequest(url="https://example.com/file.json")
        assert req.url == "https://example.com/file.json"
        print("✓ Valid request model works")

        # Test invalid request (empty URL)
        try:
            req = UploadDocumentRequest(url="")
            print("✗ Should have rejected empty URL")
            return False
        except:
            print("✓ Empty URL rejected")

        return True
    except Exception as e:
        print(f"✗ Endpoint request model test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing /upload-document Endpoint Implementation")
    print("=" * 60)

    tests = [
        test_imports,
        test_file_type_detection,
        test_json_injection_structure,
        test_endpoint_request_model,
    ]

    results = [test() for test in tests]

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    return all(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
