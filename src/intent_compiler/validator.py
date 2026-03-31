"""
Protocol Schema Validator
Valida outputs do modelo contra schemas JSON Schema definidos nos protocolos
"""

import json
from typing import Dict, Any, List, Optional
from jsonschema import Draft7Validator
from dataclasses import dataclass, field

@dataclass
class LintRule:
    id: str
    severity: str  # "error" | "warning"
    message: str

@dataclass
class LintResult:
    rule_id: str
    severity: str
    message: str
    line: Optional[int] = None
    col: Optional[int] = None

@dataclass
class LintConfig:
    rules: List[LintRule] = field(default_factory=list)
    fail_on: str = "error"  # "error" | "warning" | "off"

DEFAULT_LINT_CONFIG = LintConfig(
    rules=[
        LintRule("PM001", "error", "Frontmatter obrigatório faltando"),
        LintRule("PM002", "error", "Campo obrigatório faltando: {field}"),
        LintRule("PM003", "error", "Slots usados mas não declarados: {slots}"),
        LintRule("PM004", "error", "Schema inválido: {reason}"),
        LintRule("PM005", "warning", "Slots declarados mas não usados: {slots}"),
        LintRule("PM006", "warning", "Version não segue semver"),
        LintRule("PM007", "warning", "Model não especificado"),
    ],
    fail_on="error",
)

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    data: Optional[Any] = None

class SchemaValidator:
    def __init__(self):
        self.validator = Draft7Validator
        
    def validate_output(self, output_data: Any, schema: Dict[str, Any]) -> ValidationResult:
        """
        Valida output do modelo contra o schema definido
        """
        errors = []
        warnings = []
        
        try:
            # Se for string JSON, tentar parsear
            if isinstance(output_data, str):
                try:
                    output_data = json.loads(output_data)
                except json.JSONDecodeError as e:
                    return ValidationResult(
                        is_valid=False,
                        errors=[f"JSON inválido: {str(e)}"],
                        warnings=warnings
                    )
            
            # Validar contra o schema
            validator = self.validator(schema)
            validation_errors = list(validator.iter_errors(output_data))
            
            if validation_errors:
                errors.extend([str(error) for error in validation_errors])
                return ValidationResult(
                    is_valid=False,
                    errors=errors,
                    warnings=warnings,
                    data=output_data
                )
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                data=output_data
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Erro na validação: {str(e)}"],
                warnings=warnings,
                data=output_data
            )
    

    
    def generate_schema_from_example(self, example_data: Any, title: str = "Generated Schema") -> Dict[str, Any]:
        """
        Gera schema JSON Schema a partir de exemplo de dados
        """
        if isinstance(example_data, dict):
            properties = {}
            required = []
            
            for key, value in example_data.items():
                properties[key] = self._infer_schema_type(value)
                required.append(key)
            
            return {
                "type": "object",
                "title": title,
                "properties": properties,
                "required": required
            }
        
        elif isinstance(example_data, list):
            if example_data:
                item_schema = self._infer_schema_type(example_data[0])
            else:
                item_schema = {"type": "string"}  # Default para array vazio
            
            return {
                "type": "array",
                "title": title,
                "items": item_schema
            }
        
        else:
            return {
                "type": self._infer_json_type(example_data),
                "title": title
            }
    
    def _infer_schema_type(self, value: Any) -> Dict[str, Any]:
        """
        Inferir schema para um valor específico
        """
        if isinstance(value, dict):
            properties = {}
            required = []
            
            for key, val in value.items():
                properties[key] = self._infer_schema_type(val)
                required.append(key)
            
            return {
                "type": "object",
                "properties": properties,
                "required": required
            }
        
        elif isinstance(value, list):
            if value:
                item_schema = self._infer_schema_type(value[0])
            else:
                item_schema = {"type": "string"}
            
            return {
                "type": "array",
                "items": item_schema
            }
        
        else:
            json_type = self._infer_json_type(value)
            schema = {"type": json_type}
            
            # Adicionar constraints baseadas no valor
            if json_type == "string":
                schema["minLength"] = 0
                schema["maxLength"] = max(100, len(str(value)) * 2)
            
            elif json_type == "number":
                if isinstance(value, int):
                    schema["type"] = "integer"
                
                # Adicionar range baseado no valor
                abs_value = abs(value) if value != 0 else 1
                schema["minimum"] = -abs_value * 10
                schema["maximum"] = abs_value * 10
            
            return schema
    
    def _infer_json_type(self, value: Any) -> str:
        """
        Inferir tipo JSON para um valor
        """
        if isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "string"  # Default fallback
    
    def validate_schema_syntax(self, schema: Dict[str, Any]) -> ValidationResult:
        """
        Valida se o schema JSON Schema é sintaticamente correto
        """
        errors = []
        warnings = []
        
        try:
            # Tentar criar um validator com o schema
            self.validator.check_schema(schema)
            self.validator(schema)
            
            # Verificar se há referências circulares
            # (Isso é uma verificação simplificada)
            if "$ref" in str(schema):
                warnings.append("Schema contém referências $ref - verifique por ciclos")
            
            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Schema inválido: {str(e)}"],
                warnings=warnings
            )

class ProtocolValidator:
    """
    Validador completo de protocolos - integra parser e schema validation
    """
    
    def __init__(self):
        self.parser = None  # Será importado do parser.py
        self.schema_validator = SchemaValidator()
    
    def validate_protocol_file(self, filepath: str) -> ValidationResult:
        """
        Valida arquivo de protocolo completo
        """
        try:
            # Importar parser dinamicamente para evitar dependência circular
            from intent_compiler.parser import ProtocolParser
            self.parser = ProtocolParser()
            
            # Parsear o arquivo
            parsed = self.parser.parse_file(filepath)
            
            errors = []
            warnings = []
            
            # Verificar erros de parsing
            if parsed['errors']:
                errors.extend(parsed['errors'])
            
            if 'warnings' in parsed:
                warnings.extend(parsed['warnings'])
            
            # Validar schema do frontmatter
            if 'schema' in parsed['frontmatter']:
                schema_validation = self.schema_validator.validate_schema_syntax(
                    parsed['frontmatter']['schema']
                )
                if not schema_validation.is_valid:
                    errors.extend(schema_validation.errors)
                warnings.extend(schema_validation.warnings)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Erro ao validar protocolo: {str(e)}"],
                warnings=[]
            )

def main():
    """
    Exemplos de uso do validador
    """
    validator = SchemaValidator()
    
    # Exemplo 1: Validar output contra schema
    schema = {
        "type": "object",
        "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 100},
            "issues": {"type": "array", "items": {"type": "object"}},
            "summary": {"type": "string", "minLength": 10, "maxLength": 500}
        },
        "required": ["score", "issues", "summary"]
    }
    
    # Output válido
    valid_output = {
        "score": 85,
        "issues": [{"type": "performance", "severity": "medium"}],
        "summary": "Código com boa performance mas com algumas otimizações possíveis"
    }
    
    result = validator.validate_output(valid_output, schema)
    print("=== VALIDAÇÃO VÁLIDA ===")
    print(f"Válido: {result.is_valid}")
    print(f"Erros: {result.errors}")
    print(f"Avisos: {result.warnings}")
    
    # Output inválido
    invalid_output = {
        "score": 150,  # Acima do máximo
        "issues": "não é um array",  # Tipo errado
        # Falta o campo "summary"
    }
    
    result = validator.validate_output(invalid_output, schema)
    print("\n=== VALIDAÇÃO INVÁLIDA ===")
    print(f"Válido: {result.is_valid}")
    print(f"Erros: {result.errors}")
    print(f"Avisos: {result.warnings}")
    
    # Exemplo 2: Gerar schema a partir de exemplo
    example_data = {
        "name": "John Doe",
        "age": 30,
        "skills": ["Python", "JavaScript"]
    }
    
    generated_schema = validator.generate_schema_from_example(example_data, "User Schema")
    print("\n=== SCHEMA GERADO ===")
    print(json.dumps(generated_schema, indent=2))

if __name__ == "__main__":
    main()
