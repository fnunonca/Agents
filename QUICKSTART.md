# Quick Start: .NET Benchmark Tools

Guía rápida para usar las herramientas de análisis de performance en proyectos .NET.

## Prerequisitos

- Python 3.8+
- .NET SDK 8.0+ (para ejecutar benchmarks)
- Claude Code (VS Code extension o CLI)

## Estructura del Repositorio

```
Agents/
├── .claude/skills/dotnet-benchmark-scanner/   # Skill de escaneo
│   ├── scripts/
│   │   ├── scan_solution.py                   # Scanner de candidatos
│   │   └── orchestrate_benchmark.py           # Orquestador completo
│   └── SKILL.md                               # Documentación de la skill
├── benchmark-analyzer-subagent-prompt.md      # Sub-agente de benchmarking
└── QUICKSTART.md                              # Esta guía
```

## Uso Rápido (3 Pasos)

### Paso 1: Escanear tu Proyecto

Desde este directorio (Agents), ejecuta:

```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py \
  /ruta/a/tu/MiProyecto.sln
```

### Paso 2: Seleccionar Candidatos

El orquestador mostrará una tabla interactiva:

```
 #  │ Método                         │ Score │ Severidad │ Hot Path
────┼────────────────────────────────┼───────┼───────────┼─────────
 1  │ OrderService.ProcessOrders     │  22.0 │ CRITICAL  │    ✓
 2  │ DataProcessor.Transform        │  15.0 │ CRITICAL  │    ✓

> Escribe: 1,2 (números) o "critical" o "all"
```

### Paso 3: Ejecutar Benchmark

Con los YAMLs generados, pide a Claude:

```
"Ejecuta benchmark-analyzer con benchmark_params/OrderService_ProcessOrders.yaml"
```

## Comandos Disponibles

### Scanner Solo (sin orquestación)
```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/scan_solution.py \
  /ruta/a/MiProyecto.sln \
  --threshold medium
```

### Orquestador Modo Batch (CI/CD)
```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py \
  /ruta/a/MiProyecto.sln \
  --batch \
  --threshold critical
```

## Archivos Generados

Después de ejecutar el orquestador:

```
/ruta/a/tu/proyecto/
├── benchmark_params/                    # YAMLs para benchmark-analyzer
│   └── OrderService_ProcessOrders.yaml
└── BENCHMARK_ORCHESTRATION_*.md         # Reporte consolidado
```

## Copiar Herramientas a tu Proyecto (Opcional)

Si prefieres tener las herramientas en tu propio proyecto:

```bash
cd /ruta/a/tu/proyecto
mkdir -p .claude/skills
cp -r /home/liamred/Escritorio/Agents/.claude/skills/dotnet-benchmark-scanner .claude/skills/
cp /home/liamred/Escritorio/Agents/benchmark-analyzer-subagent-prompt.md .
```

## FAQ

**¿Necesito hacer `init` o instalar algo?**
No. Son scripts Python que se ejecutan directamente.

**¿Dónde se crean los benchmarks?**
En `./benchmark/` del directorio donde ejecutes el orquestador.

**¿Los scores son precisos?**
Son heurísticos. Valida con profiling real en producción.
