# Agents

Coleccion personal de agentes de IA y skills de Claude Code que uso en mi dia a dia para desarrollo .NET.

## Agentes

| Agente | Archivo | Descripcion |
|--------|---------|-------------|
| **Code Review** | `dotnet-code-review-agent-prompt.md` | Revision integral de codigo .NET 8/9/10: seguridad, performance, arquitectura (SOLID), testing |
| **Benchmark Analyzer** | `benchmark-analyzer-subagent-prompt.md` | Sub-agente de BenchmarkDotNet. Genera 2-4 variantes de optimizacion y reportes comparativos |
| **Git History Investigator** | `git-history-investigator-agent-prompt.md` | Arqueologia de codigo: bisect, blame, evolucion, recuperacion de codigo eliminado |

## Skills

| Skill | Directorio | Descripcion |
|-------|-----------|-------------|
| **Benchmark Scanner** | `.claude/skills/dotnet-benchmark-scanner/` | Escanea soluciones .NET buscando code smells de performance (LINQ, boxing, allocaciones, etc.) |
| **Skill Creator** | `.claude/skills/skill-creator/` | Meta-skill para crear nuevas skills de Claude Code |
| **PDF Processing Pro** | `.claude/skills/pdf-processing-pro/` | Procesamiento de PDFs: formularios, tablas, OCR, operaciones batch |
| **Context7 Auto-Research** | `.claude/skills/context7-auto-research/` | Busqueda automatica de documentacion actualizada de librerias/frameworks |

## Como funciona

```
Code Review Agent
├── Detecta metodos criticos en performance → invoca Benchmark Scanner/Analyzer
└── Necesita contexto historico → invoca Git History Investigator

Benchmark Scanner (scan_solution.py)
└── Genera YAMLs con candidatos → Benchmark Analyzer crea proyecto BenchmarkDotNet
```

## Uso rapido

### Escanear una solucion .NET
```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /ruta/a/Solucion.sln
```

### Escaneo sin orquestacion
```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/scan_solution.py /ruta/a/Solucion.sln --threshold medium
```

### Modo batch (CI/CD)
```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /ruta/a/Solucion.sln --batch --threshold critical
```

Ver [QUICKSTART.md](QUICKSTART.md) para mas detalles.

## Prerequisitos

- Python 3.8+
- .NET SDK 8.0+ (para ejecutar benchmarks)
- [Claude Code](https://claude.ai/code) (extension VS Code o CLI)

## Estructura

```
Agents/
├── dotnet-code-review-agent-prompt.md      # Agente de code review
├── benchmark-analyzer-subagent-prompt.md   # Sub-agente de benchmarking
├── git-history-investigator-agent-prompt.md # Agente de historia git
├── QUICKSTART.md                           # Guia rapida benchmark tools
├── .claude/
│   ├── agents/                             # Definiciones de sub-agentes
│   └── skills/                             # Skills de Claude Code
│       ├── dotnet-benchmark-scanner/
│       ├── skill-creator/
│       ├── pdf-processing-pro/
│       └── context7-auto-research/
└── CLAUDE.md                               # Instrucciones para Claude Code
```
