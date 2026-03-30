# Guía de Orquestación: dotnet-benchmark-scanner + benchmark-analyzer

## Visión General

Este documento describe el flujo de trabajo completo para identificar y optimizar métodos de rendimiento crítico en soluciones .NET.

```
┌─────────────────────────────────────────────────────────────────┐
│                    FASE 1: DESCUBRIMIENTO                        │
│                   (dotnet-benchmark-scanner)                     │
├─────────────────────────────────────────────────────────────────┤
│  Ejecutar: scan_solution.py --threshold medium                   │
│  Output: Candidatos identificados con score y code smells        │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FASE 2: TRIAJE                                │
│                   (orchestrate_benchmark.py)                     │
├─────────────────────────────────────────────────────────────────┤
│  Revisar reporte y seleccionar:                                  │
│  - Top 3-5 candidatos CRITICAL/HIGH                              │
│  - Métodos en hot paths reales                                   │
│  - Quick wins: alto score + cambio simple                        │
│  Output: Archivos YAML con parámetros para benchmark-analyzer    │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FASE 3: BENCHMARK PROFUNDO                    │
│                   (benchmark-analyzer sub-agente)                │
├─────────────────────────────────────────────────────────────────┤
│  Para cada método seleccionado:                                  │
│  1. Crear proyecto benchmark con BenchmarkDotNet                 │
│  2. Implementar método original + 2-4 optimizaciones             │
│  3. Ejecutar benchmarks en Release                               │
│  Output: BENCHMARK_REPORT.md con resultados y recomendaciones    │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FASE 4: IMPLEMENTACIÓN                        │
├─────────────────────────────────────────────────────────────────┤
│  Con los reportes de benchmark:                                  │
│  1. Elegir la optimización ganadora                              │
│  2. Crear tests de regresión                                     │
│  3. Implementar cambio en código fuente                          │
│  4. Validar que produce mismos resultados                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Uso del Orquestador

### Instalación

El script `orchestrate_benchmark.py` no requiere dependencias externas más allá de Python 3.8+.

### Modo Interactivo (Recomendado)

```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /path/to/Solution.sln
```

Ejemplo de sesión:

```
═══════════════════════════════════════════════════════════════
  .NET Benchmark Orchestrator
═══════════════════════════════════════════════════════════════

  Solución: /path/to/Solution.sln
  Versión:  net8.0
  Umbral:   medium
  Modo:     Interactivo

🔍 Escaneando solución...
   Archivos: 45 | Métodos: 312 | Candidatos: 8

────────────────────────────────────────────────────────────────
  #  │ Método                                 │  Score │ Severidad  │ Hot Path
────────────────────────────────────────────────────────────────
  1  │ OrderService.ProcessBulkOrders         │   22.0 │  CRITICAL  │     ✓
  2  │ ReportGenerator.BuildReport            │   15.0 │  CRITICAL  │     ✓
  3  │ DataProcessor.TransformRecords         │   12.0 │    HIGH    │     ✓
  4  │ CacheManager.RefreshCache              │   10.0 │    HIGH    │
  5  │ UserService.ValidatePermissions        │    8.0 │   MEDIUM   │     ✓
────────────────────────────────────────────────────────────────

Selecciona candidatos para benchmark:
  - Números separados por coma (ej: 1,2,3)
  - critical para todos los CRITICAL
  - high para CRITICAL + HIGH
  - all para todos
  - q para cancelar

> 1,2

📦 Preparando benchmarks...

[1/2] OrderService.ProcessBulkOrders
  ✓ Código extraído: src/Services/OrderService.cs:145-189
  ✓ Contexto generado: Hot path detectado (Service/Controller/Handler...
  ✓ YAML guardado: benchmark_params/OrderService_ProcessBulkOrders.yaml

[2/2] ReportGenerator.BuildReport
  ✓ Código extraído: src/Reports/ReportGenerator.cs:89-145
  ✓ Contexto generado: Hot path detectado, Code smells: buffer_alloc...
  ✓ YAML guardado: benchmark_params/ReportGenerator_BuildReport.yaml

═══════════════════════════════════════════════════════════════
✅ Completado
═══════════════════════════════════════════════════════════════

  Candidatos preparados: 2
  Archivos YAML: benchmark_params/
  Reporte: BENCHMARK_ORCHESTRATION_20260127.md

Próximos pasos:
  1. Revisa los archivos YAML en benchmark_params/
  2. Invoca el benchmark-analyzer con cada archivo:
     "Ejecuta benchmark-analyzer con benchmark_params/[archivo].yaml"
  3. Los reportes se generarán en benchmark/
```

### Modo Batch (CI/CD)

```bash
python3 orchestrate_benchmark.py /path/to/Solution.sln \
    --batch \
    --threshold critical \
    --output-dir ./benchmark-results
```

Flags disponibles:

| Flag | Descripción |
|------|-------------|
| `--batch` | Ejecuta sin interacción, selecciona automáticamente |
| `--threshold` | Umbral para escaneo: `critical`, `high`, `medium`, `low` |
| `--select-threshold` | Umbral para auto-selección en batch (default: `critical`) |
| `--output-dir` | Directorio de salida (default: directorio de la solución) |
| `--no-execute` | Solo genera YAMLs, no ejecuta benchmarks |
| `--quiet`, `-q` | Modo silencioso |

---

## Archivos Generados

```
proyecto/
├── benchmark_params/                         # YAMLs para benchmark-analyzer
│   ├── OrderService_ProcessBulkOrders.yaml
│   └── ReportGenerator_BuildReport.yaml
├── benchmark/                                # Proyectos de benchmark (creados por benchmark-analyzer)
│   ├── Benchmark_ProcessBulkOrders_20260127/
│   │   ├── Program.cs
│   │   ├── Benchmark.csproj
│   │   └── BENCHMARK_REPORT.md
│   └── Benchmark_BuildReport_20260127/
│       └── ...
├── BENCHMARK_CANDIDATES_Solution_20260127.md  # Reporte del scanner
└── BENCHMARK_ORCHESTRATION_20260127.md        # Reporte consolidado
```

### Estructura del YAML Generado

```yaml
# benchmark_params/OrderService_ProcessBulkOrders.yaml
# Generado por orchestrate_benchmark.py
# Fecha: 2026-01-27 10:30:45
# Candidato: #1 (Score: 22.0 - CRITICAL)

dotnet_version: "net8.0"
method_name: "OrderService.ProcessBulkOrders"
method_file: "src/Services/OrderService.cs"
method_lines: "145-189"
method_code: |
  public async Task<List<OrderResult>> ProcessBulkOrders(List<Order> orders)
  {
      // TODO: optimize
      var results = new List<OrderResult>();
      foreach (var order in orders)
      {
          var validated = orders.Where(o => o.CustomerId == order.CustomerId)
                                .Select(o => o.Total)
                                .ToList();
          var message = "";
          foreach (var v in validated)
              message += v.ToString() + ", ";
          results.Add(new OrderResult { Message = message });
      }
      return results;
  }

method_context: |
  Hot path detectado (Service/Controller/Handler con async)
  Code smells: linq_multiple_iteration (x3), allocation_in_loop, string_concat_loop
  Score: 22.0 (CRITICAL)

focus_area: "both"
baseline_exists: false
```

---

## Estrategias de Uso

### Estrategia A: Análisis Completo (Recomendada)

**Cuándo usar**: Nueva solución, auditoría de performance, antes de release major.

```bash
# 1. Escanear toda la solución
python3 orchestrate_benchmark.py /path/to/Solution.sln --threshold medium

# 2. Seleccionar interactivamente los top candidatos
> 1,2,3

# 3. Invocar benchmark-analyzer para cada uno
# 4. Implementar ganadores
```

### Estrategia B: Análisis Focalizado

**Cuándo usar**: Optimización de microservicio específico, hotfix de performance.

```bash
# 1. Escanear solo proyecto específico
python3 orchestrate_benchmark.py /path/to/Project.csproj --threshold critical

# 2. Solo benchmarkear si score > 15
> critical

# 3. Implementar optimización más impactante
```

### Estrategia C: Validación de Cambio

**Cuándo usar**: Validar que un refactor no degradó performance.

```bash
# Skip scanner, ir directo a benchmark-analyzer con el método específico
# Comparar antes/después de refactor
```

---

## Invocando el Benchmark-Analyzer

Una vez generados los archivos YAML, hay dos formas de invocar el benchmark-analyzer:

### Opción 1: Referencia al archivo YAML

```
"Ejecuta el benchmark-analyzer con los parámetros del archivo:
 benchmark_params/OrderService_ProcessBulkOrders.yaml"
```

### Opción 2: Parámetros directos

```
Ejecuta benchmark-analyzer con estos parámetros:
- dotnet_version: "net8.0"
- method_name: "OrderService.ProcessBulkOrders"
- method_code: [copiar del YAML]
- method_context: "Hot path en API de pedidos. Procesa 100-5000 órdenes."
- focus_area: "both"
```

---

## Notas Importantes

1. **El orquestador NO ejecuta benchmarks automáticamente** - Solo prepara los parámetros. El usuario decide qué métodos benchmarkear.

2. **Los YAMLs son input para Claude** - El benchmark-analyzer es un sub-agente que debe ser invocado por Claude con los parámetros del YAML.

3. **Validar con métricas reales** - Los scores son heurísticos. Confirmar con profiling de producción que los hot paths son reales.

4. **Priorizar hot paths confirmados** - Un método con score alto pero que se ejecuta 1 vez/día no vale la pena optimizar.

5. **El directorio `benchmark/` es creado por benchmark-analyzer** - El orquestador solo crea `benchmark_params/`.

---

## Solución de Problemas

### Error: "No se encontraron candidatos"

- Verifica que la ruta a la solución es correcta
- Intenta con `--threshold low` para ver todos los candidatos
- Verifica que hay archivos `.cs` en el proyecto

### Error al parsear JSON del scanner

- Verifica que `scan_solution.py` está en la ruta correcta
- Ejecuta el scanner directamente para ver el error:
  ```bash
  python3 scan_solution.py /path/to/Solution.sln
  ```

### Los YAMLs no contienen código

- El método puede ser muy corto o tener sintaxis no reconocida
- Verifica el archivo fuente manualmente
- El código se puede agregar manualmente al YAML

---

**Versión**: 1.0
**Última actualización**: 2026-01-27
