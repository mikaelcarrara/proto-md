# Plano de Execução — intent-compiler

## Posicionamento do produto

> **intent-compiler é um compilador de intenção humana em Markdown.**
> Markdown进来了 → estruturas determinísticas出去了.

O produto resolve um problema real: **Markdown virou interface universal de dev** (READMEs, specs, docs, prompts), mas não tem governança. intent-compiler transforma Markdown em **artefatos determinísticos validados** — não é editor, não é "IA interpretando texto", é um **resolvedor de intenção**.

### Frases de posicionamento (usar em todo lugar)
- "Markdown that compiles to X"
- "Intent compiler for structured protocols"
- "Deterministic Markdown → structured artifacts"

### Conceito central: Resolver
> **Resolver** = engine que transforma Markdown em artefato executável/validável, de forma determinística.

### Modelo de output atual
- **JSON Schema validado** (SchemaValidator)
- **Relatório de lint** (table/compact/json via CLI, colorido)
- **Artefatos estruturados** via `intent resolve` (JSON, YAML, TypeScript, prompt)
- **Exit codes** (0 = válido, 1 = erro, 2 = argumento inválido)

---

## MVP — Entregue ✅

### Checklist de implementação

#### 1) Núcleo de parsing e validação
- [x] Parser de protocolo Markdown (`parser.py`)
- [x] Frontmatter YAML com chaves normalizadas (case-insensitive)
- [x] Validação de consistência de slots declarados vs usados
- [x] Parsing de `## Schema` com suporte a code fences
- [x] SchemaValidator baseado em JSON Schema Draft 7
- [x] ProtocolValidator integrando parser + schema validator
- [x] Validação determinística de schema com `check_schema`

#### 2) CLI do resolvedor (`intent lint` + `intent resolve`)
- [x] `intent lint` — validação por arquivo e diretório
- [x] Formatos de saída: table, compact e json (coloridos)
- [x] Modo `--strict` (warnings viram erro)
- [x] Códigos de saída consistentes para CI
- [x] `intent resolve` — emite artefato em JSON, YAML, TypeScript
- [x] `intent resolve --prompt` — gera prompt estruturado a partir de slots

#### 3) Qualidade e entrega
- [x] Suite de testes automatizados (parser/validator/CLI)
- [x] Exemplos de protocolo válido e inválido
- [x] Site estático no GitHub Pages (index.html)
- [x] Pipeline CI de qualidade (syntax + testes + smoke)
- [x] Live demo interativa no index.html (parsing client-side)
- [x] Configuração via `.intent.yaml` com regras customizáveis

---

## Próximos passos

### Output model
- [x] Geração de mocks de API a partir de schema
- [x] UI renderizada (componentes) a partir de protocolo

### Produto e DX
- [ ] CLI mais intuitiva com commands alias (`intent lint` → `intent check`)
- [ ] Mensagens de erro com contexto de linha e seção
- [ ] `intent init` — scaffold de novo protocolo
- [ ] `intent generate` — emite código/mocks/prompts a partir de protocolo

### Ecossistema
- [ ] SDK Python (publicação em PyPI)
- [ ] SDK TypeScript (publicação em npm)
- [ ] VS Code Extension com hover, autocomplete e lint inline

### Qualidade e hardening
- [ ] Cobertura de testes > 90%
- [ ] Pipeline de qualidade completo (lint/typecheck/test/security)
- [ ] Testes de integração com provedores LLM
- [ ] Hardening de segurança (SAST, dependabot)

### Posicionamento
- [ ] Avaliar rename de `intent-compiler` para algo que transmita "compilador de intenção" mais claramente
- [ ] Atualizar tagline em todos os pontos de contato para foco em "compilação" não "lint"
