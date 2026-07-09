import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from validator import DataValidator, Field, ValidationResult


def test_define_schema():
    v = DataValidator()
    v.define("user", {"name": Field("string", required=True)})
    assert "user" in v.schemas

def test_valid_data():
    v = DataValidator()
    v.define("user", {"name": Field("string"), "age": Field("integer")})
    result = v.validate("user", {"name": "Alice", "age": 30})
    assert result.valid
    assert result.data["name"] == "Alice"

def test_missing_required():
    v = DataValidator()
    v.define("user", {"name": Field("string", required=True)})
    result = v.validate("user", {})
    assert not result.valid
    assert any(e.code == "required" for e in result.errors)

def test_optional_field():
    v = DataValidator()
    v.define("user", {"name": Field("string", required=True), "bio": Field("string", required=False)})
    result = v.validate("user", {"name": "Alice"})
    assert result.valid

def test_default_value():
    v = DataValidator()
    v.define("user", {"name": Field("string"), "active": Field("boolean", required=False, default=True)})
    result = v.validate("user", {"name": "Alice"})
    assert result.data["active"] is True

def test_type_check():
    v = DataValidator()
    v.define("user", {"age": Field("integer")})
    result = v.validate("user", {"age": "not_a_number"})
    assert not result.valid
    assert any(e.code == "type" for e in result.errors)

def test_coerce_integer():
    v = DataValidator()
    v.define("user", {"age": Field("integer", coerce=True)})
    result = v.validate("user", {"age": "25"})
    assert result.valid
    assert result.data["age"] == 25

def test_coerce_boolean():
    v = DataValidator()
    v.define("user", {"active": Field("boolean", coerce=True)})
    result = v.validate("user", {"active": "true"})
    assert result.valid
    assert result.data["active"] is True

def test_choices():
    v = DataValidator()
    v.define("user", {"role": Field("string", choices=["admin", "user", "guest"])})
    r1 = v.validate("user", {"role": "admin"})
    assert r1.valid
    r2 = v.validate("user", {"role": "superadmin"})
    assert not r2.valid

def test_min_max():
    v = DataValidator()
    v.define("user", {"age": Field("integer", min_val=18, max_val=120)})
    assert v.validate("user", {"age": 25}).valid
    assert not v.validate("user", {"age": 10}).valid
    assert not v.validate("user", {"age": 200}).valid

def test_string_length():
    v = DataValidator()
    v.define("user", {"name": Field("string", min_length=2, max_length=50)})
    assert v.validate("user", {"name": "Alice"}).valid
    assert not v.validate("user", {"name": "A"}).valid

def test_pattern():
    v = DataValidator()
    v.define("user", {"email": Field("string", pattern=r"^[^@]+@[^@]+\.[a-z]+$")})
    assert v.validate("user", {"email": "test@example.com"}).valid
    assert not v.validate("user", {"email": "invalid"}).valid

def test_custom_rule():
    v = DataValidator()
    v.define("user", {"age": Field("integer", custom=lambda x: x >= 18)})
    assert v.validate("user", {"age": 25}).valid
    assert not v.validate("user", {"age": 15}).valid

def test_nested_object():
    v = DataValidator()
    v.define("user", {
        "profile": Field("dict", nested_schema={
            "bio": Field("string", required=True),
            "avatar": Field("string", required=False),
        })
    })
    assert v.validate("user", {"profile": {"bio": "Hello"}}).valid
    assert not v.validate("user", {"profile": {}}).valid

def test_nested_error_path():
    v = DataValidator()
    v.define("user", {
        "profile": Field("dict", nested_schema={
            "bio": Field("string", required=True),
        })
    })
    result = v.validate("user", {"profile": {}})
    assert any("profile.bio" in e.field for e in result.errors)

def test_validate_list():
    v = DataValidator()
    v.define("user", {"name": Field("string", required=True)})
    valid, results = v.validate_list("user", [{"name": "Alice"}, {"name": "Bob"}, {}])
    assert not valid
    assert results[0].valid
    assert not results[2].valid

def test_schema_not_found():
    v = DataValidator()
    result = v.validate("nonexistent", {})
    assert not result.valid

def test_add_custom_rule():
    v = DataValidator()
    v.add_rule("even", lambda x: x % 2 == 0)
    assert "even" in v.custom_rules

def test_coerce_list():
    v = DataValidator()
    v.define("user", {"tags": Field("list", coerce=True)})
    result = v.validate("user", {"tags": "a,b,c"})
    assert result.valid
    assert result.data["tags"] == ["a", "b", "c"]

def test_default_on_missing():
    v = DataValidator()
    v.define("user", {"name": Field("string", required=False, default="Anonymous")})
    result = v.validate("user", {})
    assert result.data["name"] == "Anonymous"
