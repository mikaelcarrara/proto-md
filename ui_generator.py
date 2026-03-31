"""
UI Component Generator
Gera componentes UI HTML a partir de schemas JSON Schema
"""

from typing import Any, Dict, List, Optional


class UIGenerator:
    def __init__(self, title: str = "Generated Form", theme: str = "dark"):
        self.title = title
        self.theme = theme
        self.component_id = 0

    def generate(self, schema: Dict[str, Any], slot_values: Optional[Dict[str, Any]] = None) -> str:
        """
        Gera HTML de componentes UI a partir de schema JSON Schema
        """
        if slot_values is None:
            slot_values = {}

        schema_type = schema.get("type", "object")

        if schema_type == "object":
            return self._generate_object(schema, slot_values)
        elif schema_type == "array":
            return self._generate_array(schema, slot_values)
        else:
            return self._generate_field(schema, "root", slot_values)

    def _generate_object(self, schema: Dict[str, Any], slot_values: Dict[str, Any]) -> str:
        """Gera campos de formulário para objeto"""
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        fields_html = []
        for prop_name, prop_schema in properties.items():
            is_required = prop_name in required
            field_html = self._generate_field(prop_schema, prop_name, slot_values.get(prop_name), is_required)
            fields_html.append(field_html)

        return "\n".join(fields_html)

    def _generate_array(self, schema: Dict[str, Any], slot_values: Any) -> str:
        """Gera campo de array (lista de itens)"""
        items_schema = schema.get("items", {"type": "string"})
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", 10)

        field_id = self._next_id()
        return f"""
    <div class="field array-field" data-min="{min_items}" data-max="{max_items}">
      <label class="label">Items</label>
      <div class="array-items" id="{field_id}">
        <div class="array-item">
          {self._generate_field(items_schema, "item", None, True).strip()}
          <button type="button" class="btn-remove" onclick="removeItem(this)">×</button>
        </div>
      </div>
      <button type="button" class="btn-add" onclick="addItem('{field_id}', {min_items}, {max_items})">+ Add item</button>
    </div>"""

    def _generate_field(self, schema: Dict[str, Any], name: str, value: Any = None, required: bool = False) -> str:
        """Gera campo de formulário individual"""
        field_type = schema.get("type", "string")
        description = schema.get("description", "")
        enum_values = schema.get("enum")

        if enum_values:
            return self._generate_select(name, enum_values, value, required, description)

        if field_type == "boolean":
            return self._generate_checkbox(name, value, required, description)

        if field_type == "number" or field_type == "integer":
            return self._generate_number(name, schema, value, required, description)

        if field_type == "array":
            return self._generate_array(schema, value)

        if field_type == "object":
            return self._generate_object(schema, value or {})

        return self._generate_text(name, schema, value, required, description)

    def _generate_text(self, name: str, schema: Dict[str, Any], value: Any, required: bool, description: str) -> str:
        """Gera campo de texto"""
        min_length = schema.get("minLength")
        max_length = schema.get("maxLength")
        pattern = schema.get("pattern")
        format_type = schema.get("format")
        placeholder = schema.get("examples", [schema.get("default", "")])[0] if schema.get("examples") else ""

        input_type = "text"
        if format_type == "email":
            input_type = "email"
        elif format_type == "uri":
            input_type = "url"
        elif format_type == "date":
            input_type = "date"
        elif format_type == "date-time":
            input_type = "datetime-local"
        elif format_type == "time":
            input_type = "time"

        attrs = []
        if min_length:
            attrs.append(f'minlength="{min_length}"')
        if max_length:
            attrs.append(f'maxlength="{max_length}"')
        if pattern:
            attrs.append(f'pattern="{pattern}"')
        if placeholder:
            attrs.append(f'placeholder="{placeholder}"')
        if required:
            attrs.append('required')

        attrs_str = " ".join(attrs)
        display_value = value if value is not None else ""

        return f"""
    <div class="field">
      <label class="label" for="{name}">{name}{'<span class="required">*</span>' if required else ''}</label>
      {'<span class="hint">' + description + '</span>' if description else ''}
      <input type="{input_type}" id="{name}" name="{name}" value="{display_value}" {attrs_str} class="input">
    </div>"""

    def _generate_number(self, name: str, schema: Dict[str, Any], value: Any, required: bool, description: str) -> str:
        """Gera campo numérico"""
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        step = schema.get("multipleOf", 1)

        attrs = [f'step="{step}"']
        if minimum is not None:
            attrs.append(f'min="{minimum}"')
        if maximum is not None:
            attrs.append(f'max="{maximum}"')
        if required:
            attrs.append('required')

        attrs_str = " ".join(attrs)
        display_value = value if value is not None else ""

        return f"""
    <div class="field">
      <label class="label" for="{name}">{name}{'<span class="required">*</span>' if required else ''}</label>
      {'<span class="hint">' + description + '</span>' if description else ''}
      <input type="number" id="{name}" name="{name}" value="{display_value}" {attrs_str} class="input">
    </div>"""

    def _generate_checkbox(self, name: str, value: Any, required: bool, description: str) -> str:
        """Gera checkbox"""
        checked = 'checked' if value else ''
        req_attr = 'required' if required else ''

        return f"""
    <div class="field checkbox-field">
      <label class="checkbox-label">
        <input type="checkbox" id="{name}" name="{name}" {checked} {req_attr} class="checkbox">
        <span class="checkbox-text">{name}{'<span class="required">*</span>' if required else ''}</span>
      </label>
      {'<span class="hint">' + description + '</span>' if description else ''}
    </div>"""

    def _generate_select(self, name: str, options: List[Any], value: Any, required: bool, description: str) -> str:
        """Gera select dropdown"""
        required_attr = 'required' if required else ''
        options_html = []
        for opt in options:
            selected = 'selected' if opt == value else ''
            options_html.append(f'<option value="{opt}" {selected}>{opt}</option>')

        return f"""
    <div class="field">
      <label class="label" for="{name}">{name}{'<span class="required">*</span>' if required else ''}</label>
      {'<span class="hint">' + description + '</span>' if description else ''}
      <select id="{name}" name="{name}" class="select" {required_attr}>
        {'<option value="">Select...</option>' if not required else ''}
        {"".join(options_html)}
      </select>
    </div>"""

    def _next_id(self) -> str:
        """Gera próximo ID único"""
        self.component_id += 1
        return f"field_{self.component_id}"

    def generate_full_html(self, schema: Dict[str, Any], slot_values: Optional[Dict[str, Any]] = None) -> str:
        """Gera documento HTML completo com CSS e JS"""
        fields = self.generate(schema, slot_values)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{self.title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'JetBrains Mono', monospace;
      background: #0d0d0f;
      color: #e0e0e0;
      min-height: 100vh;
      padding: 2rem;
    }}

    .container {{
      max-width: 600px;
      margin: 0 auto;
      background: #16161a;
      border: 0.5px solid #2a2a30;
      border-radius: 8px;
      padding: 2rem;
    }}

    .title {{
      font-size: 1.25rem;
      font-weight: 600;
      color: #e8c46a;
      margin-bottom: 0.5rem;
    }}

    .subtitle {{
      font-size: 0.75rem;
      color: #666;
      margin-bottom: 2rem;
    }}

    .field {{
      margin-bottom: 1.25rem;
    }}

    .label {{
      display: block;
      font-size: 0.875rem;
      font-weight: 500;
      color: #a0a0a0;
      margin-bottom: 0.5rem;
    }}

    .required {{
      color: #c07070;
      margin-left: 4px;
    }}

    .hint {{
      display: block;
      font-size: 0.75rem;
      color: #666;
      margin-bottom: 0.5rem;
    }}

    .input, .select {{
      width: 100%;
      padding: 0.75rem 1rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.875rem;
      background: #1e1e24;
      border: 0.5px solid #2a2a30;
      border-radius: 4px;
      color: #e0e0e0;
      outline: none;
      transition: border-color 0.2s;
    }}

    .input:focus, .select:focus {{
      border-color: #e8c46a;
    }}

    .checkbox-field {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }}

    .checkbox-label {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      cursor: pointer;
    }}

    .checkbox {{
      width: 18px;
      height: 18px;
      accent-color: #e8c46a;
    }}

    .checkbox-text {{
      font-size: 0.875rem;
      color: #e0e0e0;
    }}

    .array-field .array-items {{
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      margin-bottom: 0.5rem;
    }}

    .array-item {{
      display: flex;
      gap: 0.5rem;
      align-items: center;
    }}

    .array-item .input {{
      flex: 1;
    }}

    .btn-add, .btn-remove {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      padding: 0.5rem 0.75rem;
      border: 0.5px solid #2a2a30;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.2s;
    }}

    .btn-add {{
      background: #1e1e24;
      color: #e8c46a;
    }}

    .btn-add:hover {{
      background: #2a2a30;
    }}

    .btn-remove {{
      background: transparent;
      color: #c07070;
      padding: 0.5rem;
    }}

    .btn-remove:hover {{
      background: rgba(192, 112, 112, 0.1);
    }}

    .submit-btn {{
      width: 100%;
      padding: 1rem;
      margin-top: 1.5rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.875rem;
      font-weight: 600;
      background: #e8c46a;
      color: #0d0d0f;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      transition: opacity 0.2s;
    }}

    .submit-btn:hover {{
      opacity: 0.85;
    }}

    .output {{
      margin-top: 1.5rem;
      padding: 1rem;
      background: #1e1e24;
      border: 0.5px solid #2a2a30;
      border-radius: 4px;
      font-size: 0.75rem;
      white-space: pre-wrap;
      display: none;
    }}

    .output.visible {{
      display: block;
    }}

    .output-label {{
      font-size: 0.625rem;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: #666;
      margin-bottom: 0.5rem;
    }}
  </style>
</head>
<body>
  <div class="container">
    <h1 class="title">{self.title}</h1>
    <p class="subtitle">Generated from JSON Schema</p>

    <form id="generatedForm" onsubmit="handleSubmit(event)">
{fields}
      <button type="submit" class="submit-btn">Submit</button>
    </form>

    <div class="output" id="output">
      <div class="output-label">JSON Output</div>
      <pre id="outputContent"></pre>
    </div>
  </div>

  <script>
    function addItem(containerId, min, max) {{
      const container = document.getElementById(containerId);
      const itemCount = container.children.length;
      if (itemCount >= max) return;

      const firstItem = container.children[0];
      const newItem = firstItem.cloneNode(true);
      newItem.querySelector('input').value = '';
      container.appendChild(newItem);
    }}

    function removeItem(btn) {{
      const container = btn.parentElement.parentElement;
      if (container.children.length > 1) {{
        btn.parentElement.remove();
      }}
    }}

    function handleSubmit(e) {{
      e.preventDefault();
      const form = document.getElementById('generatedForm');
      const formData = new FormData(form);
      const data = Object.fromEntries(formData.entries());

      document.getElementById('outputContent').textContent = JSON.stringify(data, null, 2);
      document.getElementById('output').classList.add('visible');
    }}
  </script>
</body>
</html>"""


def generate_ui(schema: Dict[str, Any], title: str = "Generated Form", slot_values: Optional[Dict[str, Any]] = None) -> str:
    """
    Função de conveniência para gerar UI a partir de schema
    """
    generator = UIGenerator(title=title)
    return generator.generate_full_html(schema, slot_values)


def generate_ui_fields_only(schema: Dict[str, Any], slot_values: Optional[Dict[str, Any]] = None) -> str:
    """
    Gera apenas os campos HTML (sem documento completo)
    """
    generator = UIGenerator()
    return generator.generate(schema, slot_values)
