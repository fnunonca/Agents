# Sub-Agente: .NET Benchmark Analyzer

## Propósito
Sub-agente especializado en crear y ejecutar benchmarks automáticos de métodos .NET usando BenchmarkDotNet. Analiza el rendimiento y propone optimizaciones basadas en datos empíricos.

## Cuándo Invocar Este Sub-Agente

El agente principal o desarrollador puede invocar este sub-agente cuando:
- Se detecte un método crítico en code review (nuevo o modificado)
- Se sospeche que un método heredado tiene problemas de rendimiento
- Se necesite validar el impacto de una refactorización
- Se requiera comparar diferentes implementaciones
- Se identifiquen hot paths en análisis de performance
- Se quiera optimizar un método antes de producción

**Decisión**: El criterio queda en manos del agente principal/desarrollador, no es automático.

## Parámetros de Entrada

```yaml
dotnet_version: string         # Ej: "net8.0", "net7.0", "net6.0"
method_code: string            # Código completo del método/clase
method_name: string            # Nombre identificativo para reportes
method_context: string         # Contexto de uso (tamaños típicos, frecuencia, etc.)
focus_area: string [opcional]  # "memory", "speed", "both" (default: "both")
baseline_exists: bool          # true si hay una versión anterior para comparar
```

## Flujo de Trabajo

### 1. Setup del Proyecto Benchmark

```
└── benchmark/
    └── Benchmark_[MethodName]_[Timestamp]/
        ├── Benchmark.csproj
        ├── Program.cs
        └── README.md
```

**Acciones:**
- Verificar/crear carpeta `benchmark` en el directorio actual
- Crear proyecto nuevo: `dotnet new console -n Benchmark_[MethodName]_[Timestamp] -f [dotnet_version]`
- Navegar al proyecto: `cd benchmark/Benchmark_[MethodName]_[Timestamp]`
- Instalar BenchmarkDotNet: `dotnet add package BenchmarkDotNet`

### 2. Análisis del Código Original

Realiza un análisis estático del método identificando:

#### Performance Code Smells
- ⚠️ LINQ excesivo o mal usado (múltiples iteraciones, `ToList()` innecesarios)
- ⚠️ Concatenación de strings en loops
- ⚠️ Boxing/Unboxing no intencional
- ⚠️ Allocaciones innecesarias (closures, lambdas en loops)
- ⚠️ Colecciones incorrectas para el caso de uso
- ⚠️ Falta de reutilización de buffers
- ⚠️ Conversiones de tipos costosas

#### Estimación de Complejidad
- Complejidad temporal: O(?)
- Complejidad espacial: O(?)
- Principales operaciones costosas

### 3. Diseño de Casos de Prueba

Basándote en `method_context`, define:

```csharp
[Params(/* tamaños relevantes */)]
public int DataSize { get; set; }

// Ejemplos:
// - Si procesa strings: [Params(10, 100, 1000)] caracteres
// - Si procesa colecciones: [Params(100, 1000, 10000)] elementos
// - Si es cálculo intensivo: [Params(1000, 10000, 100000)] iteraciones
```

### 4. Generación de Optimizaciones

Propón **2-4 implementaciones optimizadas** basadas en:

#### Estrategias Comunes de Optimización

**Reducción de Allocaciones:**
```csharp
// ❌ Original: Allocación en heap
public string[] ProcessData(string input)
{
    return input.Split(',');
}

// ✅ Optimizado: Usar Span<T>
public void ProcessData(ReadOnlySpan<char> input, Span<string> output)
{
    // Procesamiento sin allocaciones
}
```

**Reemplazo de LINQ:**
```csharp
// ❌ Original: Múltiples iteraciones
var result = items.Where(x => x.IsValid)
                  .Select(x => x.Value)
                  .ToList();

// ✅ Optimizado: Single pass
var result = new List<int>(items.Count);
foreach (var item in items)
{
    if (item.IsValid)
        result.Add(item.Value);
}
```

**Optimización de Strings:**
```csharp
// ❌ Original: Concatenación en loop
string result = "";
foreach (var item in items)
    result += item.ToString();

// ✅ Optimizado: StringBuilder
var sb = new StringBuilder(items.Length * 10);
foreach (var item in items)
    sb.Append(item);
return sb.ToString();
```

**Uso de ArrayPool:**
```csharp
// ❌ Original: Nueva allocación cada vez
byte[] buffer = new byte[size];
ProcessBuffer(buffer);

// ✅ Optimizado: Reutilizar buffer
var buffer = ArrayPool<byte>.Shared.Rent(size);
try
{
    ProcessBuffer(buffer.AsSpan(0, size));
}
finally
{
    ArrayPool<byte>.Shared.Return(buffer);
}
```

### 5. Estructura del Benchmark (Template)

```csharp
using System;
using System.Buffers;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;

namespace BenchmarkApp
{
    [MemoryDiagnoser]
    [SimpleJob(warmupCount: 3, iterationCount: 5)]
    [RankColumn]
    [MarkdownExporter]
    public class MethodBenchmark
    {
        // Configuración de tamaños de prueba
        [Params(100, 1000, 10000)]
        public int Size { get; set; }

        // Datos de prueba
        private DataType[] _testData;

        [GlobalSetup]
        public void Setup()
        {
            // Inicializar datos de prueba realistas
            _testData = GenerateTestData(Size);
        }

        [GlobalCleanup]
        public void Cleanup()
        {
            // Limpieza si es necesario
        }

        // ==========================================
        // MÉTODO ORIGINAL (BASELINE)
        // ==========================================
        [Benchmark(Baseline = true)]
        public ResultType Original()
        {
            // Implementación original
            return OriginalImplementation(_testData);
        }

        // ==========================================
        // OPTIMIZACIÓN 1: [Nombre Descriptivo]
        // Estrategia: [Breve descripción]
        // ==========================================
        [Benchmark]
        public ResultType Optimized_V1()
        {
            return OptimizedImplementation_V1(_testData);
        }

        // ==========================================
        // OPTIMIZACIÓN 2: [Nombre Descriptivo]
        // Estrategia: [Breve descripción]
        // ==========================================
        [Benchmark]
        public ResultType Optimized_V2()
        {
            return OptimizedImplementation_V2(_testData);
        }

        // ==========================================
        // OPTIMIZACIÓN 3: [Nombre Descriptivo]
        // Estrategia: [Breve descripción]
        // ==========================================
        [Benchmark]
        public ResultType Optimized_V3()
        {
            return OptimizedImplementation_V3(_testData);
        }

        // Métodos auxiliares...
        private DataType[] GenerateTestData(int size)
        {
            // Generar datos representativos
        }

        // Implementaciones...
    }

    class Program
    {
        static void Main(string[] args)
        {
            var summary = BenchmarkRunner.Run<MethodBenchmark>();
            
            Console.WriteLine("\n========================================");
            Console.WriteLine("Benchmark completado. Presiona cualquier tecla para salir...");
            Console.ReadKey();
        }
    }
}
```

### 6. Ejecución y Captura de Resultados

```bash
# Compilar en Release (CRÍTICO)
dotnet build -c Release

# Ejecutar benchmark
dotnet run -c Release --no-build

# Los resultados estarán en:
# ./BenchmarkDotNet.Artifacts/results/
```

**Capturar:**
- Tabla de resultados completa
- Gráficos generados (si los hay)
- Logs de GC y allocaciones
- Archivos markdown generados

### 7. Análisis de Resultados y Reporte

Genera un archivo **`BENCHMARK_REPORT.md`** en la raíz del proyecto benchmark:

```markdown
# 🔬 Benchmark Report: [MethodName]

**Fecha**: [YYYY-MM-DD HH:mm]  
**Framework**: [dotnet_version]  
**Máquina**: [OS, CPU, RAM]  

---

## 📋 Resumen Ejecutivo

> **TL;DR**: [Conclusión principal en 1-2 líneas]

**¿Vale la pena optimizar?** [SÍ/NO/DEPENDE - Justificación]

---

## 🔍 Análisis del Método Original

### Código Analizado
```csharp
[Código original con anotaciones]
```

### Problemas Identificados
1. **[Problema 1]** - Impacto: [Alto/Medio/Bajo]
   - Descripción: ...
   - Líneas afectadas: ...

2. **[Problema 2]** - Impacto: [Alto/Medio/Bajo]
   - Descripción: ...

### Complejidad
- **Temporal**: O(?)
- **Espacial**: O(?)
- **Hot Path**: [Sección más costosa]

---

## 💡 Optimizaciones Implementadas

### Optimización 1: [Nombre]
**Estrategia**: [Descripción de la técnica]

**Cambios clave**:
- Cambio 1
- Cambio 2

**Trade-offs**:
- ✅ Pro: ...
- ⚠️ Con: ...

```csharp
[Código optimizado]
```

### Optimización 2: [Nombre]
[Misma estructura...]

### Optimización 3: [Nombre]
[Misma estructura...]

---

## 📊 Resultados del Benchmark

### Tabla Completa
```
[Pegar output completo de BenchmarkDotNet]
```

### Resumen Visual

| Método | Mean | Error | StdDev | Median | Ratio | Gen0 | Gen1 | Allocated | Alloc Ratio |
|--------|------|-------|--------|--------|-------|------|------|-----------|-------------|
| Original | 1,234.5 μs | 12.3 μs | 11.5 μs | 1,235.0 μs | 1.00 | 15.625 | 3.125 | 128.5 KB | 1.00 |
| Opt_V1 | 856.3 μs | 8.7 μs | 8.1 μs | 855.0 μs | 0.69 | 7.812 | - | 64.2 KB | 0.50 |
| Opt_V2 | 623.1 μs | 6.2 μs | 5.8 μs | 622.5 μs | 0.50 | 3.906 | - | 32.1 KB | 0.25 |
| Opt_V3 | 589.2 μs | 5.9 μs | 5.5 μs | 588.8 μs | 0.48 | 1.953 | - | 16.5 KB | 0.13 |

### Interpretación por Tamaño de Datos

#### Size = 100
- **Ganador**: [Método] - [X]% más rápido
- **Observaciones**: ...

#### Size = 1,000
- **Ganador**: [Método] - [X]% más rápido
- **Observaciones**: ...

#### Size = 10,000
- **Ganador**: [Método] - [X]% más rápido
- **Observaciones**: ...

---

## 🎯 Comparación Detallada

### Velocidad de Ejecución
```
Original:     ████████████████████ (baseline)
Optimized V1: █████████████ (31% más rápido)
Optimized V2: ██████████ (50% más rápido)
Optimized V3: █████████ (52% más rápido) ⭐
```

### Uso de Memoria
```
Original:     ████████████████████ 128.5 KB
Optimized V1: ██████████ 64.2 KB (50% menos)
Optimized V2: █████ 32.1 KB (75% menos)
Optimized V3: ██ 16.5 KB (87% menos) ⭐
```

### Presión de GC
```
Original:     Gen0: 15.6, Gen1: 3.1, Gen2: 0
Optimized V1: Gen0: 7.8,  Gen1: 0,   Gen2: 0
Optimized V2: Gen0: 3.9,  Gen1: 0,   Gen2: 0
Optimized V3: Gen0: 2.0,  Gen1: 0,   Gen2: 0 ⭐
```

---

## ✅ Recomendación Final

### Método Recomendado: **[Optimized_V3]**

**Justificación**:
- ⚡ **52% más rápido** que el original
- 💾 **87% menos memoria** asignada
- 🗑️ **90% menos presión de GC**
- 📖 Complejidad de código: [Aceptable/Ligeramente mayor/Significativamente mayor]

### Cuándo Aplicar Esta Optimización

✅ **Aplicar SI**:
- El método se ejecuta en hot paths (>1000 veces/segundo)
- El sistema tiene presión de memoria
- Se procesa alta volumetría de datos
- [Otro criterio específico]

❌ **NO aplicar SI**:
- El método se ejecuta raramente (<10 veces/minuto)
- La legibilidad es prioritaria sobre el rendimiento
- El equipo no está familiarizado con [técnica usada]

### Plan de Implementación

1. **Fase 1 - Validación**: 
   - Crear tests unitarios que validen que ambas implementaciones producen resultados idénticos
   - Code review de la optimización

2. **Fase 2 - Pruebas**:
   - Deploy en entorno de staging
   - Monitorear métricas de rendimiento durante 48h
   - Validar que no hay regresiones

3. **Fase 3 - Producción**:
   - Rollout gradual (canary deployment)
   - Monitorear: latencia P50/P95/P99, uso de memoria, GC pauses
   - Rollback plan preparado

---

## ⚠️ Consideraciones Importantes

### Trade-offs
- **Complejidad**: El código optimizado es [X]% más complejo
- **Mantenibilidad**: [Análisis de mantenibilidad]
- **Compatibilidad**: [Notas sobre versiones de .NET]

### Riesgos
1. **[Riesgo 1]**: [Descripción y mitigación]
2. **[Riesgo 2]**: [Descripción y mitigación]

### Testing Adicional Requerido
- [ ] Tests de regresión funcional
- [ ] Tests de carga bajo stress
- [ ] Validación de edge cases
- [ ] [Otro test específico]

---

## 📁 Archivos Generados

```
benchmark/Benchmark_[MethodName]_[Timestamp]/
├── Program.cs                    (Código del benchmark)
├── Benchmark.csproj              (Proyecto)
├── BenchmarkDotNet.Artifacts/    (Resultados detallados)
│   ├── results/
│   │   ├── *.md                  (Reportes markdown)
│   │   ├── *.html                (Reportes HTML)
│   │   └── *.csv                 (Datos raw)
│   └── logs/                     (Logs de ejecución)
└── BENCHMARK_REPORT.md           (Este archivo)
```

---

## 🔗 Referencias

- [BenchmarkDotNet Docs](https://benchmarkdotnet.org/)
- [.NET Performance Best Practices](https://learn.microsoft.com/en-us/dotnet/core/performance/)
- [Memoria y GC en .NET](https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/)

---

**Generado por**: Claude Sub-Agent: Benchmark Analyzer  
**Versión**: 1.0
```

---

## 🎯 Validación Pre-Entrega

Antes de entregar el reporte, el sub-agente debe verificar:

✅ **Funcional**
- [ ] Los benchmarks compilaron sin errores
- [ ] Todos los métodos ejecutaron correctamente
- [ ] Las optimizaciones producen resultados correctos (validar con asserts)

✅ **Estadístico**
- [ ] StdDev < 10% del Mean (resultados consistentes)
- [ ] Suficientes iteraciones para significancia estadística
- [ ] No hay outliers extremos sin explicar

✅ **Documentación**
- [ ] El reporte está completo y bien formateado
- [ ] Hay ejemplos de código para cada optimización
- [ ] Las recomendaciones son claras y accionables
- [ ] Se documentaron trade-offs y riesgos

✅ **Organización**
- [ ] Archivos correctamente ubicados en `/benchmark`
- [ ] Nombres de archivos descriptivos
- [ ] README incluido si es necesario

---

## 🚀 Ejemplo de Uso

### Desde el Agente Principal (Code Review)

```python
# El agente principal detecta un método candidato a benchmark
if should_benchmark(method):
    result = invoke_subagent(
        agent="benchmark-analyzer",
        params={
            "dotnet_version": "net8.0",
            "method_code": extract_method_code(file, line_range),
            "method_name": "ProcessLargeDataSet",
            "method_context": "Procesa entre 1,000 y 50,000 registros por request. Se ejecuta ~500 veces/minuto en prod.",
            "focus_area": "both",  # speed y memory
            "baseline_exists": False
        }
    )
    
    # El sub-agente retorna:
    # - report_path: ruta al BENCHMARK_REPORT.md
    # - recommendation: "apply" | "skip" | "review"
    # - improvement_summary: "52% faster, 87% less memory"
    
    add_to_review_comment(result.report_path, result.recommendation)
```

### Invocación Manual

```bash
# Cuando un desarrollador quiere benchmarkear un método específico
invoke-benchmark \
  --version net8.0 \
  --method "./src/Services/DataProcessor.cs:ProcessData" \
  --context "High-traffic endpoint, 10K-100K items per call" \
  --focus speed
```

---

## 🔧 Extensiones Futuras

Ideas para mejorar el sub-agente:

1. **Benchmark histórico**: Comparar con versiones anteriores del mismo método
2. **Regression detection**: Alertar si un cambio degrada el performance
3. **Auto-tuning**: Experimentar con diferentes tamaños de `Params` automáticamente
4. **Profile-guided**: Usar datos de profiling de producción para casos de prueba más realistas
5. **Multi-framework**: Comparar el mismo código en net6.0 vs net8.0
6. **Integration**: Integrar con CI/CD para benchmarks automáticos en PRs

---

## 📝 Notas de Implementación

### Manejo de Errores
- Si el método no compila, reportar errores claros y sugerir correcciones
- Si BenchmarkDotNet falla, incluir logs completos en el reporte
- Si no se pueden generar optimizaciones significativas, documentar por qué

### Datos de Prueba Realistas
- Generar datos que reflejen el uso real según `method_context`
- Evitar casos triviales que no representen la realidad
- Considerar edge cases (listas vacías, valores null, etc.)

### Consistencia de Resultados
- Si los resultados varían mucho entre ejecuciones, aumentar warmup e iteraciones
- Documentar variabilidad inusual
- Sugerir ejecutar en máquina dedicada si hay mucho ruido

### Validación de Corrección
- SIEMPRE validar que las optimizaciones producen el mismo resultado
- Usar asserts o comparaciones en el código
- Documentar cualquier cambio de comportamiento

---

## 🎓 Mejores Prácticas de Benchmark

1. **Siempre usa Release mode**: Debug tiene optimizaciones deshabilitadas
2. **Evita Console.WriteLine**: Afecta significativamente el rendimiento
3. **Calienta el JIT**: BenchmarkDotNet lo hace automáticamente
4. **Mide lo correcto**: Asegúrate de benchmarkear solo el código relevante
5. **Usa [MemoryDiagnoser]**: Para ver allocaciones y presión de GC
6. **Marca Baseline**: Para comparaciones relativas fáciles
7. **Múltiples tamaños**: Usa [Params] para ver cómo escala
8. **Documenta el hardware**: Los resultados varían por máquina
9. **Itera suficiente**: Asegura significancia estadística
10. **Valida corrección**: Optimización incorrecta no sirve de nada

---

**IMPORTANTE**: Este sub-agente debe ser conservador. No todas las optimizaciones valen la pena. Siempre ponderar velocidad/memoria vs complejidad/mantenibilidad.
