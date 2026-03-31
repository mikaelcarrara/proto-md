"""
Protocol Markdown Parser
Lê arquivos .md de protocolo e extrai metadados, slots e validações
"""

import re
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class SlotType(Enum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    ARRAY = "array"
    OBJECT = "object"

@dataclass
class Slot:
    name: str
    type: SlotType
    constraints: Optional[str] = None
    description: Optional[str] = None
    
    @classmethod
    def from_string(cls, slot_str: str) -> 'Slot':
        """
        Parse slot de string como: {{nome}} string(1..100) — descrição
        """
        # Regex para extrair {{nome}} tipo(constraints) — descrição
        pattern = r'\{\{(\w+)\}\}\s+(\w+)(?:\(([^)]+)\))?\s*(?:—\s*(.+))?'
        match = re.match(pattern, slot_str.strip())
        
        if not match:
            raise ValueError(f"Slot inválido: {slot_str}")
        
        name, type_str, constraints, description = match.groups()
        
        # Mapear tipo string para SlotType
        type_mapping = {
            'string': SlotType.STRING,
            'int': SlotType.INT,
            'float': SlotType.FLOAT,
            'bool': SlotType.BOOL,
            'array': SlotType.ARRAY,
            'object': SlotType.OBJECT
        }
        
        slot_type = type_mapping.get(type_str.lower())
        if not slot_type:
            raise ValueError(f"Tipo de slot desconhecido: {type_str}")
        
        return cls(
            name=name,
            type=slot_type,
            constraints=constraints,
            description=description.strip() if description else None
        )

@dataclass
class ProtocolMetadata:
    version: str
    model: str
    author: str
    schema: Dict[str, Any]
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 4096
    metadata: Optional[Dict[str, Any]] = None

class ProtocolParser:
    def __init__(self):
        self.frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
        self.slot_pattern = re.compile(r'\{\{(\w+)\}\}')
        self.last_slot_warnings: List[str] = []
        
    def parse_file(self, filepath: str) -> Dict[str, Any]:
        """
        Parse arquivo .md completo e retorna estrutura parseada
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> Dict[str, Any]:
        """
        Parse conteúdo markdown e extrai todas as informações
        """
        result = {
            'frontmatter': {},
            'slots': [],
            'constraints': [],
            'context': '',
            'raw_content': content,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Extrair frontmatter
            frontmatter_match = self.frontmatter_pattern.search(content)
            if not frontmatter_match:
                result['errors'].append("Frontmatter não encontrado")
                return result
            
            frontmatter_text = frontmatter_match.group(1)
            frontmatter = self._parse_frontmatter(frontmatter_text)
            result['frontmatter'] = frontmatter
            
            # Extrair conteúdo sem frontmatter
            main_content = content[frontmatter_match.end():]
            
            # Extrair seções
            sections = self._parse_sections(main_content)
            result.update(sections)
            result['warnings'].extend(sections.get('slot_warnings', []))

            if 'schema' not in frontmatter and result.get('schema') is not None:
                result['frontmatter']['schema'] = result['schema']

            if (
                'schema' not in result['frontmatter']
                and '## Schema' in main_content
                and result.get('schema') is None
            ):
                result['errors'].append("Seção ## Schema presente, mas inválida")
            
            # Validar slots
            declared_slots = {slot.name: slot for slot in result['slots']}
            used_slots = set(self.slot_pattern.findall(main_content))
            
            # Verificar slots não declarados
            undeclared = used_slots - set(declared_slots.keys())
            if undeclared:
                result['errors'].append(f"Slots usados mas não declarados: {undeclared}")
            
            # Verificar slots declarados mas não usados
            unused = set(declared_slots.keys()) - used_slots
            if unused:
                result['warnings'].append(f"Slots declarados mas não usados: {unused}")
            
            # Validar campos obrigatórios do frontmatter
            required_fields = ['version', 'model', 'author', 'schema']
            missing_fields = [field for field in required_fields if field not in frontmatter]
            if missing_fields:
                result['errors'].append(f"Campos obrigatórios faltando: {missing_fields}")
            else:
                if not self._is_valid_semver(str(frontmatter.get('version', '')).strip()):
                    result['errors'].append("Campo 'version' deve seguir formato semver X.Y.Z")
                if not str(frontmatter.get('model', '')).strip():
                    result['errors'].append("Campo 'model' não pode estar vazio")
                if not str(frontmatter.get('author', '')).strip():
                    result['errors'].append("Campo 'author' não pode estar vazio")
                if not isinstance(frontmatter.get('schema'), dict):
                    result['errors'].append("Campo 'schema' deve ser um objeto JSON/YAML válido")
            
        except Exception as e:
            result['errors'].append(f"Erro ao parsear: {str(e)}")
        
        return result

    def _is_valid_semver(self, value: str) -> bool:
        return bool(re.match(r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$', value))
    
    def _parse_frontmatter(self, text: str) -> Dict[str, Any]:
        """
        Parse YAML frontmatter
        """
        try:
            # O frontmatter pode ter o formato # [Protocol] Name no início
            lines = text.split('\n')
            if lines[0].startswith('# [Protocol]'):
                protocol_name = lines[0].replace('# [Protocol]', '').strip()
                yaml_content = '\n'.join(lines[1:])
            else:
                protocol_name = None
                yaml_content = text
            
            frontmatter = yaml.safe_load(yaml_content) or {}
            if not isinstance(frontmatter, dict):
                raise ValueError("Frontmatter YAML deve ser um objeto")
            frontmatter = {str(key).lower(): value for key, value in frontmatter.items()}
            
            if protocol_name:
                frontmatter['protocol_name'] = protocol_name
            
            return frontmatter
            
        except yaml.YAMLError as e:
            raise ValueError(f"YAML inválido no frontmatter: {e}")
    
    def _parse_sections(self, content: str) -> Dict[str, Any]:
        """
        Parse seções do markdown usando AST seguro
        """
        sections = {
            'context': '',
            'slots': [],
            'constraints': [],
            'schema': None,
            'slot_warnings': []
        }
        
        from markdown_it import MarkdownIt
        md = MarkdownIt("commonmark")
        tokens = md.parse(content)
        
        h2_headings = []
        for i, token in enumerate(tokens):
            if token.type == "heading_open" and token.tag == "h2":
                if i + 1 < len(tokens):
                    title = tokens[i+1].content.strip().lower()
                    start_line = token.map[0] if token.map else 0
                    h2_headings.append((title, start_line))
        
        lines = content.split('\n')
        for idx, (title, start_line) in enumerate(h2_headings):
            if title not in ['context', 'slots', 'constraints', 'schema']:
                continue
            
            next_start_line = h2_headings[idx+1][1] if idx + 1 < len(h2_headings) else len(lines)
            section_content = '\n'.join(lines[start_line+1:next_start_line]).strip()
            
            if title == 'context':
                sections['context'] = section_content
            elif title == 'slots':
                self.last_slot_warnings = []
                sections['slots'] = self._parse_slots(section_content)
                sections['slot_warnings'].extend(self.last_slot_warnings)
            elif title == 'constraints':
                sections['constraints'] = self._parse_constraints(section_content)
            elif title == 'schema':
                sections['schema'] = self._parse_schema(section_content)
        
        return sections
    
    def _parse_slots(self, content: str) -> List[Slot]:
        """
        Parse declarações de slots
        """
        slots = []
        
        # Procurar por linhas que contenham {{slot_name}}
        lines = content.split('\n')
        for line in lines:
            if '{{' in line and '}}' in line:
                try:
                    slot = Slot.from_string(line.strip())
                    slots.append(slot)
                except ValueError as e:
                    self.last_slot_warnings.append(str(e))
        
        return slots
    
    def _parse_constraints(self, content: str) -> List[str]:
        """
        Parse lista de constraints
        """
        # Procurar por linhas que começam com número ou bullet
        lines = content.split('\n')
        constraints = []
        
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line) or line.startswith('-') or line.startswith('*'):
                constraint = re.sub(r'^\d+\.\s*|^[-*]\s*', '', line)
                if constraint:
                    constraints.append(constraint)
            elif line and not line.startswith('#'):
                constraints.append(line)
        
        return constraints
    
    def _parse_schema(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse schema JSON/YAML
        """
        content = content.strip()
        fence_match = re.match(r'^```(?:json|yaml|yml)?\s*(.*?)\s*```$', content, re.DOTALL)
        if fence_match:
            content = fence_match.group(1).strip()

        try:
            # Tentar parsear como JSON primeiro
            import json
            return json.loads(content)
        except json.JSONDecodeError:
            try:
                # Tentar YAML
                return yaml.safe_load(content)
            except yaml.YAMLError:
                return None

def main():
    """
    Exemplo de uso do parser
    """
    parser = ProtocolParser()
    
    # Exemplo de conteúdo markdown
    example_md = """---
# [Protocol] Performance Analyst
Version: 2.1.0
Model: anthropic/claude-sonnet-4
Author: platform-team
Schema:
  type: object
  properties:
    score: {type: number, minimum: 0, maximum: 100}
    issues: {type: array, items: {type: object}}
    summary: {type: string}
  required: [score, issues, summary]
---

## Context
You are a static analysis engine operating via semantic inference. You do not guess. You measure.

## Slots
{{code_snippet}}  string — the code to analyze
{{strictness}}   int(1..10) — enforcement level
{{language}}     string — programming language

## Constraints
1. Output MUST be valid JSON matching ## Schema
2. Never suggest external libraries unless asked
3. Strictness < 5: report only critical issues
4. Strictness ≥ 5: report all issues found

## Schema
{
  "score": "number(0..100)",
  "issues": "Issue[]",
  "summary": "string"
}
"""
    
    result = parser.parse_content(example_md)
    
    print("=== PROTOCOL PARSER RESULT ===")
    print(f"Version: {result['frontmatter'].get('version')}")
    print(f"Model: {result['frontmatter'].get('model')}")
    print(f"Author: {result['frontmatter'].get('author')}")
    print(f"Slots encontrados: {len(result['slots'])}")
    for slot in result['slots']:
        print(f"  - {slot.name}: {slot.type.value} {slot.constraints or ''}")
    print(f"Constraints: {len(result['constraints'])}")
    print(f"Erros: {result['errors']}")
    if 'warnings' in result:
        print(f"Avisos: {result['warnings']}")

if __name__ == "__main__":
    main()
