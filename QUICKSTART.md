# Quick Start: .NET Benchmark Tools

Guía rápida para usar las herramientas de análisis de performance en proyectos .NET.

## Prerequisitos

- Python 3.8+
- .NET SDK 8.0+ (para ejecutar benchmarks)
- Claude Code (VS Code extension o CLI)

## Opción A — Instalar como plugin (recomendado)

```
/plugin marketplace add github.com/<tu-usuario>/Agents
/plugin install dotnet-benchmark-scanner@fernando-agents
/plugin install dotnet-benchmark-analyzer@fernando-agents
```

Una vez instalados, podés invocar la skill y el agente directamente desde Claude Code sin clonar este repo.

## Opción B — Ejecutar scripts directamente

Desde este repo (o un clon):

```
Agents/
└── plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/
    ├── scripts/
    │   ├── scan_solution.py           # Scanner de candidatos
    │   └── orchestrate_benchmark.py   # Orquestador completo
    └── SKILL.md
```

## Uso Rápido (3 Pasos)

### Paso 1: Escanear tu Proyecto

Desde este directorio (Agents), ejecuta:

```bash
python3 plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py \
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

Con los YAMLs generados, pedí a Claude:

```
"Ejecuta benchmark-analyzer con benchmark_params/OrderService_ProcessOrders.yaml"
```

## Comandos Disponibles

### Scanner Solo (sin orquestación)
```bash
python3 plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/scripts/scan_solution.py \
  /ruta/a/MiProyecto.sln \
  --threshold medium
```

### Orquestador Modo Batch (CI/CD)
```bash
python3 plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py \
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

## FAQ

**¿Necesito hacer `init` o instalar algo?**
Si instalaste los plugins vía `/plugin install`, no. Si ejecutás los scripts directamente, solo necesitás Python 3.8+.

**¿Dónde se crean los benchmarks?**
En `./benchmark/` del directorio donde ejecutes el orquestador.

**¿Los scores son precisos?**
Son heurísticos. Valida con profiling real en producción.
