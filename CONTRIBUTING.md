# Contributing

Guía para agregar un nuevo plugin (agente o skill) al marketplace `fernando-agents`.

## Estructura de un plugin

Cada plugin vive bajo `plugins/<nombre>/` y debe seguir este layout:

### Plugin de agente

```
plugins/<nombre>/
├── .claude-plugin/
│   └── plugin.json
└── agents/
    └── <nombre>.md         # Prompt del agente con YAML frontmatter
```

### Plugin de skill

```
plugins/<nombre>/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── <nombre>/
        ├── SKILL.md        # Definición con YAML frontmatter
        ├── scripts/        # Opcional
        ├── references/     # Opcional
        └── assets/         # Opcional
```

## Pasos para agregar un plugin

### 1. Crear el directorio y el manifiesto

```bash
mkdir -p plugins/mi-plugin/.claude-plugin
mkdir -p plugins/mi-plugin/agents    # o skills/mi-plugin
```

Crea `plugins/mi-plugin/.claude-plugin/plugin.json`:

```json
{
  "name": "mi-plugin",
  "version": "0.1.0",
  "description": "Descripción breve (una línea) de qué hace el plugin.",
  "author": "Tu Nombre",
  "license": "MIT",
  "keywords": ["tag1", "tag2"],
  "agents": "./agents"
}
```

Para un skill, cambiá `"agents": "./agents"` por `"skills": "./skills"`.

### 2. Escribir el agente o skill

**Agente** (`plugins/mi-plugin/agents/mi-agente.md`):

```markdown
---
name: mi-agente
description: "Use this agent when... [ejemplos y casos de uso]"
model: sonnet
color: blue
---

You are an expert in ...

## Your Mission
...
```

**Skill** (`plugins/mi-plugin/skills/mi-plugin/SKILL.md`):

```markdown
---
name: mi-plugin
description: "Qué hace este skill, cuándo usarlo"
---

# Mi Plugin

Instrucciones detalladas del skill...
```

### 3. Registrarlo en el marketplace

Edita `.claude-plugin/marketplace.json` y agregá una entrada al array `plugins`:

```json
{
  "name": "mi-plugin",
  "source": "./plugins/mi-plugin",
  "description": "Descripción breve.",
  "version": "0.1.0",
  "category": "tu-categoria",
  "keywords": ["tag1", "tag2"]
}
```

### 4. Validar

```bash
# JSON válido
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"
python3 -c "import json; json.load(open('plugins/mi-plugin/.claude-plugin/plugin.json'))"

# Probar instalación local
# En Claude Code:
#   /plugin marketplace add /ruta/absoluta/a/este/repo
#   /plugin install mi-plugin@fernando-agents
```

### 5. Abrir un PR

Incluí:
- El nuevo directorio `plugins/mi-plugin/`
- La entrada en `marketplace.json`
- Una breve descripción del plugin en el PR

## Convenciones

- **Idioma**: las prompts de agentes y outputs están en español. Los nombres de archivos, keys de JSON y comentarios técnicos en inglés.
- **Versionado**: seguí [semver](https://semver.org/). Empezá en `0.1.0`.
- **Frontmatter YAML**: obligatorio en todos los agentes (`name`, `description`, `model`, `color`) y en los skills (`name`, `description`).
- **Keywords**: usalos para que el plugin sea descubrible. Máx 5-6.
- **Licencia**: MIT por defecto (consistente con el resto del marketplace).

## Nombres reservados

No uses estos nombres de marketplace/plugin (reservados por Anthropic):
- `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`
- `anthropic-marketplace`, `anthropic-plugins`
- `agent-skills`, `knowledge-work-plugins`, `life-sciences`

## Referencias

- [Create plugins](https://code.claude.com/docs/en/plugins)
- [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)
- [Plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Skills](https://code.claude.com/docs/en/skills)
