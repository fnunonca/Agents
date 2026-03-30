---
name: dotnet-benchmark-scanner
description: Escanea soluciones .NET completas para identificar métodos candidatos a benchmarking de rendimiento. Detecta "performance code smells" como LINQ excesivo, concatenación de strings en loops, boxing/unboxing, y allocaciones innecesarias. Genera un reporte con puntuaciones y comandos preparados para invocar el benchmark-analyzer sub-agente. Usar cuando se quiera hacer un análisis proactivo de performance en una solución .NET antes de optimizar.
---

# .NET Benchmark Scanner

## Overview

Este skill escanea una solución .NET completa para identificar métodos que son candidatos a benchmarking y optimización de rendimiento. Analiza el código buscando patrones problemáticos ("performance code smells") y genera un reporte priorizado con recomendaciones para invocar el sub-agente de benchmark.

## Parámetros de Entrada

```yaml
# Requeridos
solution_path: string         # Ruta a archivo .sln o .csproj

# Opcionales
dotnet_version: string        # "net8.0" (default), "net9.0", "net10.0"
severity_threshold: string    # "critical", "high", "medium" (default), "low"
```

## Workflow

```
1. Recibir ruta a solución/proyecto
           ↓
2. Escanear todos los archivos *.cs
           ↓
3. Para cada archivo:
   - Parsear métodos y clases
   - Buscar performance code smells
   - Identificar hot paths
   - Calcular puntuación
           ↓
4. Ordenar métodos por puntuación
           ↓
5. Generar reporte BENCHMARK_CANDIDATES_[SolutionName]_[Date].md
           ↓
6. Incluir comandos para invocar benchmark-analyzer
```

## Ejecución del Skill

### Paso 1: Validar Entrada

Verificar que la ruta proporcionada existe y es un archivo `.sln` o `.csproj` válido.

### Paso 2: Ejecutar Script de Escaneo

```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/scan_solution.py <solution_path> --version <dotnet_version> --threshold <severity_threshold>
```

El script genera un archivo JSON con los resultados del análisis.

### Paso 3: Generar Reporte

Usar el template en `assets/report_template.md` para generar el reporte final con:
- Resumen ejecutivo
- Lista de candidatos ordenados por prioridad
- Detalles de cada método con code smells detectados
- Comandos preparados para invocar el benchmark-analyzer

### Paso 4: Guardar Reporte

Guardar el reporte como `BENCHMARK_CANDIDATES_[SolutionName]_[YYYY-MM-DD].md` en el directorio de la solución.

## Sistema de Puntuación

| Pattern | Puntos Base | Multiplicador Hot Path |
|---------|-------------|------------------------|
| LINQ múltiple iteración | 3 | x1.5 |
| String concat en loop | 4 | x1.5 |
| Boxing/Unboxing | 2 | x1.5 |
| Allocation en loop | 3 | x1.5 |
| Colección incorrecta | 2 | x1.0 |
| Buffer no reutilizado | 3 | x1.5 |
| Marcador `// TODO: optimize` | 5 | x2.0 |
| Marcador `// PERF:` | 4 | x2.0 |
| Marcador `// SLOW` | 4 | x2.0 |

### Umbrales de Severidad

- **critical**: ≥15 puntos - Optimización urgente requerida
- **high**: ≥10 puntos - Optimización altamente recomendada
- **medium**: ≥6 puntos - Considerar optimización
- **low**: ≥3 puntos - Optimización opcional

### Indicadores de Hot Path

Los siguientes indicadores multiplican la puntuación base:

- Clases: `*Controller`, `*Handler`, `*Processor`, `*Service`
- Atributos: `[HttpGet]`, `[HttpPost]`, `[HttpPut]`, `[HttpDelete]`, `[HttpPatch]`
- Métodos `async` con operaciones I/O
- Métodos públicos en clases registradas como servicios DI

## Ejemplo de Uso

### Invocación Básica

```
Usuario: Escanea la solución en /path/to/MySolution.sln buscando candidatos a benchmark
```

### Invocación con Parámetros

```
Usuario: Escanea /path/to/MyProject.csproj para .NET 9 mostrando solo issues críticos
```

### Ejemplo de Salida

El skill genera un reporte markdown con estructura similar a:

```markdown
# Benchmark Candidates Report: MySolution

## Resumen Ejecutivo
- Total archivos escaneados: 45
- Métodos analizados: 312
- Candidatos identificados: 8
- Severidad promedio: High

## Top Candidatos

### 1. DataProcessor.ProcessLargeDataSet (Score: 18 - CRITICAL)
**Archivo**: src/Services/DataProcessor.cs:45
**Code Smells**:
- LINQ múltiple iteración (x2)
- Allocation en loop

**Comando para benchmark**:
invoke-benchmark --method "DataProcessor.ProcessLargeDataSet" ...
```

## Resources

### scripts/
- `scan_solution.py` - Script principal de análisis estático que detecta patterns y calcula puntuaciones

### references/
- `detection_patterns.md` - Documentación detallada de todos los patterns de detección con regex y ejemplos

### assets/
- `report_template.md` - Template markdown para el reporte de candidatos

## Integración con benchmark-analyzer

El reporte generado incluye comandos preparados para invocar el sub-agente `benchmark-analyzer` definido en `/benchmark-analyzer-subagent-prompt.md`. Cada comando incluye:

- `dotnet_version`: Versión de .NET del proyecto
- `method_code`: Código del método candidato
- `method_name`: Nombre del método
- `method_context`: Contexto inferido del análisis (hot path, frecuencia estimada)
- `focus_area`: "both" (memoria y velocidad)

---

## Orquestación Automatizada

Para un flujo de trabajo completo (escaneo → selección → benchmark), usar el script de orquestación:

### Modo Interactivo

```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /path/to/Solution.sln
```

### Modo Batch (CI/CD)

```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /path/to/Solution.sln \
    --batch \
    --threshold critical
```

### Flags Disponibles

| Flag | Descripción |
|------|-------------|
| `--batch` | Ejecuta sin interacción |
| `--threshold` | Umbral para escaneo: `critical`, `high`, `medium`, `low` |
| `--select-threshold` | Umbral para auto-selección en batch |
| `--output-dir` | Directorio de salida |
| `--quiet`, `-q` | Modo silencioso |

### Output del Orquestador

```
proyecto/
├── benchmark_params/                         # YAMLs para benchmark-analyzer
│   ├── OrderService_ProcessBulkOrders.yaml
│   └── ReportGenerator_BuildReport.yaml
└── BENCHMARK_ORCHESTRATION_20260127.md       # Reporte consolidado
```

### Invocación del Benchmark-Analyzer

Después de generar los YAMLs:

```
"Ejecuta el benchmark-analyzer con los parámetros del archivo:
 benchmark_params/[nombre_metodo].yaml"
```

Ver `references/orchestration_guide.md` para documentación completa del flujo de trabajo.
