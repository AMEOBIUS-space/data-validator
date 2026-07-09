"""Data Validator — schema-based validation with type coercion, custom rules, nested objects."""
import re
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class ValidationError:
    field: str
    message: str
    code: str = "invalid"
    value: Any = None


@dataclass
class ValidationResult:
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    data: Dict = field(default_factory=dict)

    def add_error(self, field: str, message: str, code: str = "invalid", value: Any = None):
        self.errors.append(ValidationError(field=field, message=message, code=code, value=value))
        self.valid = False


class Field:
    """Schema field definition."""

    def __init__(self, field_type: str, required: bool = True, default: Any = None,
                 min_val: float = None, max_val: float = None,
                 min_length: int = None, max_length: int = None,
                 pattern: str = None, choices: List = None,
                 custom: Callable = None, coerce: bool = False,
                 nested_schema: Dict[str, "Field"] = None):
        self.field_type = field_type
        self.required = required
        self.default = default
        self.min_val = min_val
        self.max_val = max_val
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.choices = choices
        self.custom = custom
        self.coerce = coerce
        self.nested_schema = nested_schema


class DataValidator:
    """Validate data against a schema with type coercion and custom rules."""

    TYPE_MAP = {
        "string": str,
        "integer": int,
        "float": (int, float),
        "boolean": bool,
        "list": list,
        "dict": dict,
    }

    COERCE_MAP = {
        "string": lambda v: str(v),
        "integer": lambda v: int(v) if isinstance(v, (int, float, str)) and str(v).lstrip("-").isdigit() else v,
        "float": lambda v: float(v) if isinstance(v, (int, float, str)) else v,
        "boolean": lambda v: str(v).lower() in ("true", "1", "yes") if isinstance(v, str) else bool(v),
        "list": lambda v: v.split(",") if isinstance(v, str) else v,
        "dict": lambda v: v if isinstance(v, dict) else v,
    }

    def __init__(self):
        self.schemas: Dict[str, Dict[str, Field]] = {}
        self.custom_rules: Dict[str, Callable] = {}

    def define(self, name: str, schema: Dict[str, Field]):
        """Define a validation schema."""
        self.schemas[name] = schema

    def add_rule(self, name: str, rule: Callable[[Any], bool]):
        """Add a custom validation rule."""
        self.custom_rules[name] = rule

    def validate(self, schema_name: str, data: Dict) -> ValidationResult:
        """Validate data against a named schema."""
        schema = self.schemas.get(schema_name)
        if not schema:
            return ValidationResult(valid=False, errors=[
                ValidationError(field="_schema", message=f"Schema '{schema_name}' not found")
            ])

        result = ValidationResult(valid=True)
        validated_data = {}

        for field_name, field_def in schema.items():
            value = data.get(field_name)
            path = field_name

            # Required check
            if value is None or value == "":
                if field_def.required:
                    if field_def.default is not None:
                        validated_data[field_name] = field_def.default
                        continue
                    result.add_error(path, f"Field '{field_name}' is required", code="required")
                    continue
                else:
                    if field_def.default is not None:
                        validated_data[field_name] = field_def.default
                    continue

            # Type coercion
            if field_def.coerce and field_def.field_type in self.COERCE_MAP:
                try:
                    value = self.COERCE_MAP[field_def.field_type](value)
                except (ValueError, TypeError):
                    pass

            # Type check
            expected_type = self.TYPE_MAP.get(field_def.field_type)
            if expected_type and not isinstance(value, expected_type):
                result.add_error(path, f"Expected {field_def.field_type}, got {type(value).__name__}",
                                 code="type", value=value)
                continue

            validated_data[field_name] = value

            # Choices
            if field_def.choices and value not in field_def.choices:
                result.add_error(path, f"Value must be one of {field_def.choices}", code="choices", value=value)
                continue

            # Numeric range
            if isinstance(value, (int, float)):
                if field_def.min_val is not None and value < field_def.min_val:
                    result.add_error(path, f"Value {value} < minimum {field_def.min_val}", code="min", value=value)
                if field_def.max_val is not None and value > field_def.max_val:
                    result.add_error(path, f"Value {value} > maximum {field_def.max_val}", code="max", value=value)

            # String length
            if isinstance(value, str):
                if field_def.min_length is not None and len(value) < field_def.min_length:
                    result.add_error(path, f"Length {len(value)} < minimum {field_def.min_length}", code="min_length")
                if field_def.max_length is not None and len(value) > field_def.max_length:
                    result.add_error(path, f"Length {len(value)} > maximum {field_def.max_length}", code="max_length")
                if field_def.pattern and not re.match(field_def.pattern, value):
                    result.add_error(path, f"Does not match pattern {field_def.pattern}", code="pattern", value=value)

            # Nested object
            if field_def.nested_schema and isinstance(value, dict):
                nested_validator = DataValidator()
                nested_validator.schemas["_nested"] = field_def.nested_schema
                nested_result = nested_validator.validate("_nested", value)
                if not nested_result.valid:
                    for err in nested_result.errors:
                        result.add_error(f"{path}.{err.field}", err.message, err.code, err.value)

            # Custom rule
            if field_def.custom:
                try:
                    if not field_def.custom(value):
                        result.add_error(path, f"Custom validation failed for '{field_name}'", code="custom", value=value)
                except Exception as e:
                    result.add_error(path, f"Custom validation error: {e}", code="custom_error", value=value)

        result.data = validated_data
        return result

    def validate_list(self, schema_name: str, items: List[Dict]) -> Tuple[bool, List[ValidationResult]]:
        """Validate a list of objects."""
        results = []
        all_valid = True
        for item in items:
            result = self.validate(schema_name, item)
            results.append(result)
            if not result.valid:
                all_valid = False
        return all_valid, results
