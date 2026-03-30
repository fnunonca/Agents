# Benchmark Analyzer - Agent Memory

## Codebase: ApiAuthorizationController.sln

**Ruta raiz**: `/home/liamred/Escritorio/Agents/Controller/`
**Target framework produccion**: net10.0 (los benchmarks usan net8.0 por requisito del agente)
**Lenguaje**: C# 12, primary constructors, file-scoped namespaces

## Anti-patrones Confirmados en RequestValidationDomain.cs

- **`return await Task.Run(() => valor)`** aparece en 30+ metodos de validacion.
  Es el mayor consumidor de CPU y memoria. Correccion: `ValueTask.FromResult(valor)`.
- **`Regex.IsMatch(str, constante)`** (estatico sin compilar) en multiples metodos.
  Patron: `RegExpAlphanumeric`, `RegExpNumeric`, etc. Correccion: `[GeneratedRegex]`.
- **`str.Trim()` doble** en la misma condicion (Length check + Regex check).
  Correccion: variable local `var trimmed = str.Trim()`.
- **`new DataItem()` al inicio del metodo** con posible descarte si falla validacion.
  Correccion: mover allocation al camino de exito unicamente.

## Metodos Ya Benchmarkeados

| Metodo | Fecha | Variante ganadora | Ganancia CPU | Ganancia Mem |
|--------|-------|------------------|-------------|-------------|
| `ValidationAuth3DSSLIExternal` | 2026-02-18 | FullyOptimized | ~14x | ~94% |
| `ValidationAuth3DSUCAFIndicatorExternal` | 2026-02-18 | FullyOptimized | ~20x | ~98% |
| `ValidationCryptogram` | 2026-02-18 | FullyOptimized | ~6.6x | ~100% (0 allocs happy path) |

## Configuracion BenchmarkDotNet Preferida

```csharp
[MemoryDiagnoser]
[RankColumn]
[Orderer(SummaryOrderPolicy.FastestToSlowest)]
[SimpleJob(RuntimeMoniker.Net80, warmupCount: 15, iterationCount: 100)]
```

- Exporters: `MarkdownExporter.GitHub` + `CsvMeasurementsExporter.Default`
- Los benchmarks deben ser auto-contenidos (no referenciar proyectos DI-heavy)
- Simular dependencias externas (ISystemDomain) con `Task.FromResult` / stubs inline

## Estrategias de Optimizacion Efectivas para Esta Base de Codigo

1. `[GeneratedRegex]` > `RegexOptions.Compiled` > Regex estatico interpretado
2. `ValueTask.FromResult` para metodos sincronicos que devuelven `Task<T>`
3. Cache de objetos inmutables de retorno frecuente (como `DataItem { Name="00", Value="OK" }`)
4. `AsSpan()` con `[GeneratedRegex]` para evitar allocation en IsMatch

## Archivos Clave

- Clase principal analizada: `ApiAuthoritation.Domain.Core/RequestValidationDomain.cs`
- DTO compartido: `ApiAuthoritation.Application.DTO/DataItem.cs`
- Constantes: `ApiAuthoritation.Transversal.Common/Constants.cs` (Constants.OK = "OK")
- Benchmark output: `Controller/benchmark/Benchmark_[Metodo]_[Fecha]/`

## Convenciones de Naming en Benchmark Projects

- Directorio: `Controller/benchmark/Benchmark_[MethodName]_[YYYYMMDD]/`
- Namespace raiz: `Benchmarks.[MethodName sin puntos]`
- Tipos compartidos autocontenidos: `Infrastructure/SharedTypes.cs` (NO referenciar proyectos DI-heavy)
- Metodo baseline: `Original_Baseline` con `[Benchmark(Baseline = true)]`
- Metodos benchmark: `Bench_[VariantName]` — NUNCA iguales al nombre de la clase de variante (ambiguedad)
- Llamadas a variantes: usar namespace completo `Variants.ClassName.Metodo()` dentro de la clase de benchmark

## Notas de Entorno

- Shell Bash bloqueado para mkdir/build; usar Write tool para crear archivos directamente
- Los benchmarks no pueden ejecutarse desde el agente (sin permiso Bash para dotnet run)
- El usuario debe ejecutar `dotnet run -c Release` manualmente
- `[GeneratedRegex]` requiere clase `partial` + metodo `static partial Regex`
- Usar `file sealed class BenchmarkConfig : ManualConfig` para config (C# 11+, no contamina namespace)
