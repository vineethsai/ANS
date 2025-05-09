"""
Test script to isolate JSON schema date-time validation issues.
"""
import sys
import os
import json
import datetime
import jsonschema
from jsonschema import validate

# Add the parent directory to the Python path so we can import ANS modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ans.schemas.validator import ensure_iso_format

# Define a simple schema with a date-time format field
SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "dateTime": {
            "type": "string",
            "format": "date-time"
        }
    },
    "required": ["dateTime"]
}

def test_various_date_formats():
    """Test various date-time formats against the JSON Schema."""
    # Get current time
    now = datetime.datetime.utcnow()
    
    # Test different formats
    formats = [
        now.isoformat(),                    # Basic ISO format
        now.strftime("%Y-%m-%dT%H:%M:%SZ"), # ISO format with Z
        now.strftime("%Y-%m-%dT%H:%M:%S"),  # ISO format without Z
        now.strftime("%Y-%m-%d %H:%M:%S"),  # ISO format with space instead of T
        now.strftime("%Y-%m-%dT%H:%M:%S.%fZ"), # ISO format with microseconds and Z
        str(now)                            # String representation
    ]
    
    print("Testing date-time formats against JSON Schema validation:")
    print("-" * 50)
    
    for i, date_format in enumerate(formats, 1):
        test_data = {"dateTime": date_format}
        print(f"Format {i}: {date_format}")
        try:
            validate(instance=test_data, schema=SCHEMA)
            print("  ✓ VALID")
        except jsonschema.exceptions.ValidationError as e:
            print(f"  ✗ INVALID: {e.message}")
    
    # Test with datetime object directly
    test_data = {"dateTime": now}
    print("\nDirect datetime object:")
    try:
        validate(instance=test_data, schema=SCHEMA)
        print("  ✓ VALID")
    except jsonschema.exceptions.ValidationError as e:
        print(f"  ✗ INVALID: {e.message}")
    
    # Test with ensure_iso_format function
    print("\nUsing ensure_iso_format:")
    test_data = {"dateTime": now}
    test_data = ensure_iso_format(test_data)
    print(f"Converted: {test_data}")
    try:
        validate(instance=test_data, schema=SCHEMA)
        print("  ✓ VALID")
    except jsonschema.exceptions.ValidationError as e:
        print(f"  ✗ INVALID: {e.message}")

if __name__ == "__main__":
    test_various_date_formats() 