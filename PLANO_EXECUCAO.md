# Plano de Execução - Protocol-Driven Development

## Objetivo
Fechar um ciclo de produto funcional para `proto-md`, com validação ponta a ponta de protocolos Markdown e uso simples em ambiente local/CI.

## Frente 1 — Essencial para MVP

### Escopo do ciclo completo
- Usuário executa linter em arquivo ou diretório.
- Ferramenta valida frontmatter, slots e schema.
- Saída legível e saída JSON para CI.
- Exit code bloqueia pipeline em caso de erro.
- Repositório inclui exemplos e testes mínimos para garantir estabilidade.

### Checklist de implementação

#### 1) Núcleo de parsing e validação
- [x] Parser de protocolo Markdown (`parser.py`)
- [x] Frontmatter YAML com chaves normalizadas
- [x] Validação de consistência de slots declarados vs usados
- [x] Parsing de `## Schema` com suporte a code fences
- [x] SchemaValidator baseado em JSON Schema Draft 7
- [x] ProtocolValidator integrando parser + schema validator

#### 2) Produto utilizável via CLI
- [x] CLI `proto-lint` executável por arquivo e diretório
- [x] Formatos de saída: table, compact e json
- [x] Modo `--strict` (warnings viram erro)
- [x] Códigos de saída consistentes para CI

#### 3) Qualidade mínima de entrega
- [x] Suite de testes automatizados para parser/validator/CLI
- [x] Exemplos de protocolo válido e inválido
- [x] Deploy básico de documentação/site no GitHub Pages
- [x] Pipeline CI baseline (syntax + testes + smoke da CLI)

### Definition of Done do MVP
- [x] Comando de lint funciona em diretório com múltiplos arquivos `.md`
- [x] Erros críticos retornam exit code `1`
- [x] Modo sem erros retorna exit code `0`
- [x] Formato JSON pode ser consumido por pipeline
- [x] Testes automatizados passam no repositório

## Frente 2 — Improvements / Next Steps

### Produto e DX
- [ ] Configuração via `.protolint`
- [ ] Regras customizáveis por projeto
- [ ] Melhorias visuais de output (cores, tabelas ricas)
- [ ] Mensagens de erro com contexto de linha

### Ecossistema
- [ ] SDK Python completo
- [ ] SDK TypeScript completo
- [ ] VS Code Extension
- [ ] Ferramentas auxiliares (`proto-init`, `proto-generate`, `proto-test`)

### Distribuição e operação
- [ ] Publicação no PyPI
- [ ] Publicação no npm
- [ ] Publicação de extensão no VS Code Marketplace
- [ ] Pipeline de qualidade completa (lint/typecheck/test/security)

### Qualidade avançada
- [ ] Cobertura > 90%
- [ ] Benchmarks de performance
- [ ] Testes de integração com provedores LLM
- [ ] Hardening de segurança

## Próxima prioridade imediata
1. Adicionar suporte a configuração via `.protolint`.
2. Melhorar detalhamento de erro com contexto de linha e seção.
3. Evoluir pipeline de qualidade para cobertura de segurança e quality gates avançados.
