"""
Utility to generate Pydantic models from JSON schemas.
"""
import os
import json
from typing import Dict, Any, Optional, List, Union
import importlib.util
from pydantic import create_model, Field, validator
import datetime

SCHEMA_DIR = os.path.dirname(os.path.abspath(__file__))

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema file from the schemas directory.
    
    Args:
        schema_name: Name of the schema file (without .json extension)
        
    Returns:
        Dict containing the schema
        
    Raises:
        FileNotFoundError: If schema file not found
    """
    schema_path = os.path.join(SCHEMA_DIR, f"{schema_name}.json")
    with open(schema_path, 'r') as f:
        return json.load(f)

def _convert_type(json_type: str, format_type: Optional[str] = None) -> type:
    """
    Convert JSON schema type to Python type.
    
    Args:
        json_type: JSON schema type
        format_type: Optional format specifier
        
    Returns:
        Python type
    """
    type_mapping = {
        'string': str,
        'integer': int,
        'number': float,
        'boolean': bool,
        'object': dict,
        'array': list,
        'null': type(None)
    }
    
    # Handle date-time format
    if json_type == 'string' and format_type == 'date-time':
        return datetime.datetime
    
    return type_mapping.get(json_type, Any)

def _create_field(property_schema: Dict[str, Any], required: bool = False) -> Dict[str, Any]:
    """
    Create a Pydantic field from a JSON schema property.
    
    Args:
        property_schema: JSON schema for the property
        required: Whether the property is required
        
    Returns:
        Dict with field attributes for Pydantic model creation
    """
    field_args = {}
    
    # Handle type
    json_type = property_schema.get('type')
    format_type = property_schema.get('format')
    
    # Handle enums
    if 'enum' in property_schema:
        field_args['enum_values'] = property_schema['enum']
    
    # Set description if available
    if 'description' in property_schema:
        field_args['description'] = property_schema['description']
    
    # Handle required fields
    if required:
        field_args['required'] = True
    else:
        field_args['default'] = None
    
    # Convert type
    if json_type:
        if json_type == 'array' and 'items' in property_schema:
            # Handle array types
            item_type = _convert_type(property_schema['items'].get('type', 'string'))
            field_type = List[item_type]
        else:
            field_type = _convert_type(json_type, format_type)
        
        return (field_type, Field(**field_args))
    
    # Default to Any if type not specified
    return (Any, Field(**field_args))

def generate_model_from_schema(schema_name: str, model_name: Optional[str] = None) -> type:
    """
    Generate a Pydantic model from a JSON schema.
    
    Args:
        schema_name: Name of the schema file (without .json extension)
        model_name: Optional name for the generated model
        
    Returns:
        Pydantic model class
        
    Raises:
        ValueError: If schema generation fails
    """
    try:
        schema = load_schema(schema_name)
        
        # Use provided model name or extract from schema title
        if not model_name:
            model_name = schema.get('title', schema_name.capitalize())
        
        # Get properties and required fields
        properties = schema.get('properties', {})
        required_fields = set(schema.get('required', []))
        
        # Build field definitions
        fields = {}
        
        for prop_name, prop_schema in properties.items():
            # Handle nested objects
            if prop_schema.get('type') == 'object' and 'properties' in prop_schema:
                nested_required = set(prop_schema.get('required', []))
                nested_fields = {}
                
                for nested_prop_name, nested_prop_schema in prop_schema['properties'].items():
                    nested_fields[nested_prop_name] = _create_field(
                        nested_prop_schema, 
                        nested_prop_name in nested_required
                    )
                
                # Create nested model
                nested_model_name = f"{model_name}{prop_name.capitalize()}"
                nested_model = create_model(nested_model_name, **nested_fields)
                
                # Add to parent fields
                fields[prop_name] = (
                    nested_model, 
                    Field(
                        description=prop_schema.get('description', ''),
                        required=prop_name in required_fields
                    )
                )
            else:
                # Regular field
                fields[prop_name] = _create_field(prop_schema, prop_name in required_fields)
        
        # Create model
        return create_model(model_name, **fields)
    
    except Exception as e:
        raise ValueError(f"Failed to generate model from schema {schema_name}: {e}")

def generate_all_models() -> Dict[str, type]:
    """
    Generate Pydantic models for all JSON schemas in the schema directory.
    
    Returns:
        Dict mapping schema names to Pydantic model classes
    """
    models = {}
    
    # Find all JSON schema files
    for filename in os.listdir(SCHEMA_DIR):
        if filename.endswith('.json'):
            schema_name = filename[:-5]  # Remove .json extension
            try:
                model = generate_model_from_schema(schema_name)
                models[schema_name] = model
            except Exception as e:
                print(f"Error generating model for {schema_name}: {e}")
    
    return models 