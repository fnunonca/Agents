# fernando-agents

Marketplace personal de agentes y skills para [Claude Code](https://claude.ai/code). Enfocado en flujos de desarrollo .NET 8/9/10, performance y git archaeology.

## Instalación

En cualquier sesión de Claude Code:

```
/plugin marketplace add github.com/<tu-usuario>/Agents
/plugin install dotnet-code-review@fernando-agents
```

Instalá solo los plugins que necesites — cada agente y skill se publica como plugin independiente.

## Plugins disponibles

### Agentes

| Plugin | Descripción |
|---|---|
| **[dotnet-code-review](plugins/dotnet-code-review/)** | Revisión integral de código .NET 8/9/10: seguridad (SQL injection, secrets, auth), performance (N+1, async), arquitectura SOLID y calidad de tests. |
| **[dotnet-benchmark-analyzer](plugins/dotnet-benchmark-analyzer/)** | Sub-agente de BenchmarkDotNet. Crea proyectos de benchmark, genera 2-4 variantes de optimización (Span, ArrayPool, ValueTask, SIMD) y produce reportes comparativos. |
| **[git-history-investigator](plugins/git-history-investigator/)** | Arqueología de código: bisect de bugs, blame analysis, evolución de código, recuperación de código eliminado, análisis de impacto. |

### Skills

| Plugin | Descripción |
|---|---|
| **[dotnet-benchmark-scanner](plugins/dotnet-benchmark-scanner/)** | Escanea soluciones .NET completas para identificar métodos candidatos a benchmark. Detecta LINQ excesivo, concatenación de strings en loops, boxing y allocaciones innecesarias. |

## Cómo funciona el sistema integrado

```
dotnet-code-review
├── Detecta métodos críticos en performance → invoca dotnet-benchmark-analyzer
└── Necesita contexto histórico          → invoca git-history-investigator

dotnet-benchmark-scanner (scan_solution.py)
└── Genera YAMLs con candidatos → dotnet-benchmark-analyzer crea proyecto BenchmarkDotNet
```

## Prerequisitos

- [Claude Code](https://claude.ai/code) (extensión VS Code o CLI)
- Python 3.8+ (para las skills que usan scripts)
- .NET SDK 8.0+ (solo para ejecutar benchmarks reales)

## Estructura del marketplace

```
Agents/
├── .claude-plugin/
│   └── marketplace.json          # Catálogo del marketplace
└── plugins/
    ├── dotnet-code-review/
    │   ├── .claude-plugin/plugin.json
    │   └── agents/code-reviewer.md
    ├── dotnet-benchmark-analyzer/
    │   ├── .claude-plugin/plugin.json
    │   └── agents/benchmark-analyzer.md
    ├── git-history-investigator/
    │   ├── .claude-plugin/plugin.json
    │   └── agents/git-investigator.md
    └── dotnet-benchmark-scanner/
        ├── .claude-plugin/plugin.json
        └── skills/dotnet-benchmark-scanner/
```

## Uso rápido del scanner (tras instalar `dotnet-benchmark-scanner`)

Una vez instalado, los scripts quedan accesibles desde el plugin. Para ejecutarlos manualmente desde este repo:

```bash
python3 plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /ruta/a/Solucion.sln
```

Ver [QUICKSTART.md](QUICKSTART.md) para el flujo completo del scanner.

## Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para agregar nuevos plugins al marketplace.

## Licencia

MIT — ver [LICENSE](LICENSE).
