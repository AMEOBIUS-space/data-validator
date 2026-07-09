# Data Validator

> Schema-based validation with type coercion, custom rules, and nested objects

## Features

- 6 types: string, integer, float, boolean, list, dict
- Type coercion (string "25" → int 25, "true" → bool True, "a,b,c" → list)
- Required/optional fields with defaults
- Numeric min/max, string min_length/max_length
- Regex pattern validation
- Enum choices
- Custom validation rules (callable)
- Nested object validation with dot-notation error paths
- List validation (validate multiple objects)
- Detailed error codes (required, type, choices, min, max, pattern, custom)

## Quick Start

```python
from validator import DataValidator, Field

v = DataValidator()
v.define("user", {
    "name": Field("string", min_length=2, max_length=50),
    "email": Field("string", pattern=r"^[^@]+@[^@]+\.[a-z]+$"),
    "age": Field("integer", min_val=18, max_val=120, coerce=True),
    "role": Field("string", choices=["admin", "user"]),
    "profile": Field("dict", nested_schema={
        "bio": Field("string", required=True),
    })
})

result = v.validate("user", {"name": "Alice", "email": "a@b.com", "age": "25", "role": "admin", "profile": {"bio": "Hi"}})
print(result.valid, result.errors)
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
