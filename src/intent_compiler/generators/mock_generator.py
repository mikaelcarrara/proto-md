"""
Mock API Generator
Gera dados mock (fictícios) a partir de schemas JSON Schema
"""

import random
import string
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


class MockGenerator:
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
        self.generated_count = 0

    def generate(self, schema: Dict[str, Any]) -> Any:
        """
        Gera dado mock a partir de schema JSON Schema
        """
        schema_type = schema.get("type", "string")
        self.generated_count += 1

        if schema_type == "object":
            return self._generate_object(schema)
        elif schema_type == "array":
            return self._generate_array(schema)
        elif schema_type == "string":
            return self._generate_string(schema)
        elif schema_type == "number" or schema_type == "integer":
            return self._generate_number(schema, schema_type == "integer")
        elif schema_type == "boolean":
            return self._generate_boolean(schema)
        elif schema_type == "null":
            return None
        else:
            return self._generate_string(schema)

    def _generate_object(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Gera objeto mock a partir de schema"""
        obj = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        additional_props = schema.get("additionalProperties", True)

        for prop_name, prop_schema in properties.items():
            if prop_schema.get("type") == "object" and "properties" in prop_schema:
                obj[prop_name] = self._generate_object(prop_schema)
            elif prop_schema.get("type") == "array" and "items" in prop_schema:
                obj[prop_name] = self._generate_array(prop_schema)
            else:
                obj[prop_name] = self.generate(prop_schema)

        if additional_props and "patternProperties" in schema:
            for pattern, pattern_schema in schema["patternProperties"].items():
                pass

        return obj

    def _generate_array(self, schema: Dict[str, Any]) -> List[Any]:
        """Gera array mock a partir de schema"""
        items_schema = schema.get("items", {"type": "string"})
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", min(10, min_items + 5))

        count = random.randint(min_items, max_items)
        return [self.generate(items_schema) for _ in range(count)]

    def _generate_string(self, schema: Dict[str, Any]) -> str:
        """Gera string mock a partir de schema"""
        if "enum" in schema:
            return random.choice(schema["enum"])

        if "format" in schema:
            return self._generate_formatted_string(schema["format"], schema)

        min_length = schema.get("minLength", 1)
        max_length = schema.get("maxLength", min_length + 20)

        if max_length < min_length:
            max_length = min_length + 20

        length = random.randint(min_length, max_length)

        if "pattern" in schema:
            return self._generate_pattern_string(schema["pattern"], length)

        content_type = schema.get("contentMediaType") or schema.get("contentEncoding")
        if content_type == "base64":
            return self._generate_base64(length)

        sample = schema.get("examples", [schema.get("default", "sample")])
        sample_value = sample[0] if sample else "sample"

        if isinstance(sample_value, str):
            return sample_value[:length]
        return str(sample_value)

    def _generate_formatted_string(self, format_type: str, schema: Dict[str, Any]) -> str:
        """Gera string formatada (date-time, email, uri, etc.)"""
        min_length = schema.get("minLength", 1)
        max_length = schema.get("maxLength", min_length + 20)
        length = random.randint(min_length, max_length) if max_length > min_length else min_length

        if format_type == "date-time":
            return self._generate_datetime()
        elif format_type == "date":
            return self._generate_date()
        elif format_type == "time":
            return self._generate_time()
        elif format_type == "email":
            return self._generate_email()
        elif format_type == "uri":
            return self._generate_uri()
        elif format_type == "uuid":
            return self._generate_uuid()
        elif format_type == "hostname" or format_type == "ipv4":
            return self._generate_ipv4()
        elif format_type == "ipv6":
            return self._generate_ipv6()
        elif format_type == "password":
            chars = string.ascii_letters + string.digits + "!@#$%"
            return "".join(random.choice(chars) for _ in range(length))
        elif format_type == "byte" or format_type == "binary":
            return self._generate_base64(length)
        else:
            return self._generate_alphanumeric(length)

    def _generate_datetime(self) -> str:
        """Gera data/hora ISO 8601"""
        now = datetime.now()
        offset = timedelta(days=random.randint(-365, 365), hours=random.randint(-24, 24))
        dt = now + offset
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + random.choice([".000Z", "Z"])

    def _generate_date(self) -> str:
        """Gera data ISO 8601"""
        now = datetime.now()
        offset = timedelta(days=random.randint(-365, 365))
        return (now + offset).strftime("%Y-%m-%d")

    def _generate_time(self) -> str:
        """Gera time ISO 8601"""
        return f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"

    def _generate_email(self) -> str:
        """Gera email fake"""
        domains = ["example.com", "test.org", "demo.net", "mail.io"]
        username_length = random.randint(5, 12)
        username = self._generate_alphanumeric(username_length)
        return f"{username}@{random.choice(domains)}"

    def _generate_uri(self) -> str:
        """Gera URI/URL fake"""
        schemes = ["https", "http"]
        domains = ["api.example.com", "app.test.org", "demo.demo.net"]
        paths_count = random.randint(1, 3)
        paths = [self._generate_alphanumeric(random.randint(3, 8)) for _ in range(paths_count)]
        return f"{random.choice(schemes)}://{random.choice(domains)}/" + "/".join(paths)

    def _generate_uuid(self) -> str:
        """Gera UUID v4"""
        return (
            f"{random.randint(0, 0xFFFFFFFF):08x}-"
            f"{random.randint(0, 0xFFFF):04x}-"
            f"{random.randint(0, 0xFFFF):04x}-"
            f"{random.randint(0, 0xFFFF):04x}-"
            f"{random.randint(0, 0xFFFFFFFFFFFF):012x}"
        )

    def _generate_ipv4(self) -> str:
        """Gera IPv4"""
        return ".".join(str(random.randint(1, 254)) for _ in range(4))

    def _generate_ipv6(self) -> str:
        """Gera IPv6 simplificado"""
        groups = [f"{random.randint(0, 0xFFFF):04x}" for _ in range(8)]
        return ":".join(groups)

    def _generate_base64(self, length: int) -> str:
        """Gera string base64"""
        bytes_count = (length * 3) // 4
        sample_bytes = bytes(random.randint(0, 255) for _ in range(bytes_count))
        import base64
        return base64.b64encode(sample_bytes).decode("ascii")[:length]

    def _generate_pattern_string(self, pattern: str, length: int) -> str:
        """Gera string que corresponde a um padrão regex simplificado"""
        result = []
        i = 0
        while i < len(pattern) and len(result) < length:
            char = pattern[i]
            if char == "\\" and i + 1 < len(pattern):
                next_char = pattern[i + 1]
                if next_char == "d":
                    result.append(str(random.randint(0, 9)))
                elif next_char == "w":
                    result.append(random.choice(string.ascii_lowercase))
                elif next_char == "s":
                    result.append(" ")
                else:
                    result.append(next_char)
                i += 2
            elif char == "[":
                end_idx = pattern.find("]", i)
                if end_idx > i:
                    char_class = pattern[i + 1 : end_idx]
                    if char_class.startswith("^"):
                        char_class = char_class[1:]
                        result.append(random.choice([c for c in char_class if c != "-"]))
                    else:
                        result.append(random.choice(char_class))
                    i = end_idx + 1
                else:
                    result.append(char)
                    i += 1
            elif char in "*+?":
                if result:
                    last = result[-1]
                    if char == "*":
                        result.extend([last] * random.randint(0, 3))
                    elif char == "+":
                        result.extend([last] * random.randint(1, 3))
                i += 1
            elif char == ".":
                result.append(random.choice(string.ascii_letters + string.digits))
                i += 1
            else:
                result.append(char)
                i += 1

        while len(result) < length:
            result.append(random.choice(string.ascii_lowercase))

        return "".join(result[:length])

    def _generate_alphanumeric(self, length: int) -> str:
        """Gera string alfanumérica"""
        chars = string.ascii_lowercase + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    def _generate_number(self, schema: Dict[str, Any], is_integer: bool) -> float:
        """Gera número mock a partir de schema"""
        if "enum" in schema:
            return random.choice(schema["enum"])

        minimum = schema.get("minimum", schema.get("exclusiveMinimum", 0 if is_integer else 0.0))
        maximum = schema.get("maximum", schema.get("exclusiveMaximum", 100 if is_integer else 100.0))

        if is_integer:
            minimum = int(minimum)
            maximum = int(maximum)
            if "multipleOf" in schema:
                multiple = int(schema["multipleOf"])
                return random.randrange(minimum, maximum + 1, multiple)
            return random.randint(minimum, maximum)
        else:
            value = random.uniform(minimum, maximum)
            if "multipleOf" in schema:
                multiple = schema["multipleOf"]
                value = round(value / multiple) * multiple
            return value

    def _generate_boolean(self, schema: Dict[str, Any]) -> bool:
        """Gera booleano mock"""
        if "enum" in schema:
            return random.choice(schema["enum"])
        return random.choice([True, False])


def generate_mock(schema: Dict[str, Any], seed: Optional[int] = None) -> Any:
    """
    Função de conveniência para gerar mock a partir de schema
    """
    generator = MockGenerator(seed=seed)
    return generator.generate(schema)


def generate_multiple_mocks(schema: Dict[str, Any], count: int, seed: Optional[int] = None) -> List[Any]:
    """
    Gera múltiplos mocks a partir de schema
    """
    generator = MockGenerator(seed=seed)
    base_seed = seed
    mocks = []
    for i in range(count):
        if base_seed is not None:
            generator = MockGenerator(seed=base_seed + i)
        mocks.append(generator.generate(schema))
    return mocks
