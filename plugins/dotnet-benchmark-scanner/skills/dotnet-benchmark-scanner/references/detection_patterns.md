# Detection Patterns - .NET Benchmark Scanner

Este documento detalla todos los patterns de detección utilizados por el scanner para identificar "performance code smells" en código .NET.

## Tabla de Contenidos

1. [LINQ Code Smells](#linq-code-smells)
2. [String Operations](#string-operations)
3. [Boxing/Unboxing](#boxingunboxing)
4. [Allocations](#allocations)
5. [Collections](#collections)
6. [Marcadores Explícitos](#marcadores-explícitos)
7. [Hot Path Indicators](#hot-path-indicators)
8. [False Positives Conocidos](#false-positives-conocidos)

---

## LINQ Code Smells

### Pattern: `linq_multiple_iteration`

**Descripción**: Múltiples operaciones LINQ encadenadas que causan iteraciones múltiples sobre la colección.

**Regex**:
```regex
\.(Where|Select|OrderBy|GroupBy|Join|Distinct)\s*\([^)]*\)\s*\.(Where|Select|OrderBy|GroupBy|Join|Distinct|ToList|ToArray|ToDictionary|Count|First|Last|Any|All)
```

**Puntos Base**: 3
**Multiplicador Hot Path**: x1.5

**Ejemplo Problemático**:
```csharp
// Múltiples iteraciones
var result = items
    .Where(x => x.IsActive)      // Iteración 1
    .Select(x => x.Value)        // Iteración 2
    .OrderBy(x => x)             // Iteración 3
    .ToList();                   // Materialización
```

**Solución Recomendada**:
```csharp
// Single pass con bucle manual
var result = new List<int>(items.Count);
foreach (var item in items.OrderBy(x => x.Value))
{
    if (item.IsActive)
        result.Add(item.Value);
}
```

---

### Pattern: `linq_tolist_unnecessary`

**Descripción**: `ToList()` seguido de otra operación LINQ, lo que causa materialización innecesaria.

**Regex**:
```regex
\.ToList\(\)\s*\.(Where|Select|FirstOrDefault|First|Last|LastOrDefault|Any|All|Count)
```

**Puntos Base**: 3
**Multiplicador Hot Path**: x1.5

**Ejemplo Problemático**:
```csharp
// ToList() innecesario antes de otra operación
var count = items
    .Where(x => x.IsValid)
    .ToList()                    // Allocación innecesaria
    .Count(x => x.Score > 50);   // Podría hacerse sin materializar
```

**Solución Recomendada**:
```csharp
// Sin materialización intermedia
var count = items
    .Where(x => x.IsValid)
    .Count(x => x.Score > 50);
```

---

## String Operations

### Pattern: `string_concat_loop`

**Descripción**: Concatenación de strings con `+=` dentro de loops, causando múltiples allocaciones.

**Regex**:
```regex
(for|foreach|while)\s*\([^)]*\)\s*\{[^}]*\+\s*=\s*[^;]*string|[^}]*\+\s*=\s*["\'][^}]*\}
```

**Puntos Base**: 4
**Multiplicador Hot Path**: x1.5

**Ejemplo Problemático**:
```csharp
string result = "";
foreach (var item in items)
{
    result += item.ToString();   // Nueva allocación en cada iteración
    result += ", ";              // Otra allocación
}
```

**Solución Recomendada**:
```csharp
var sb = new StringBuilder(items.Count * 20); // Pre-size estimado
foreach (var item in items)
{
    sb.Append(item);
    sb.Append(", ");
}
return sb.ToString();
```

---

### Pattern: `string_concat_multiple`

**Descripción**: Múltiples concatenaciones de string con `+` en una sola expresión.

**Regex**:
```regex
"[^"]*"\s*\+\s*[^+]+\s*\+\s*"[^"]*"\s*\+
```

**Puntos Base**: 2
**Multiplicador Hot Path**: x1.5

**Ejemplo Problemático**:
```csharp
var message = "User " + userName + " has " + count + " items in " + category;
```

**Solución Recomendada**:
```csharp
var message = $"User {userName} has {count} items in {category}";
// O para performance extrema:
var message = string.Create(null, stackalloc char[128],
    $"User {userName} has {count} items in {category}");
```

---

## Boxing/Unboxing

### Pattern: `boxing_to_object`

**Descripción**: Conversión explícita o implícita de value types a `object`, causando boxing.

**Regex**:
```regex
\(object\)\s*\w+|\bobject\b\s+\w+\s*=\s*[^;]*\b(int|long|double|float|bool|char|byte|short|decimal)\b
```

**Puntos Base**: 2
**Multiplicador Hot Path**: x1.5

**Ejemplo Problemático**:
```csharp
object boxed = 42;                    // Boxing implícito
object result = (object)myInt;        // Boxing explícito
ArrayList list = new ArrayList();
list.Add(123);                        // Boxing al agregar
```

**Solución Recomendada**:
```csharp
List<int> list = new List<int>();     // Generic, sin boxing
list.Add(123);
```

---

### Pattern: `legacy_collections`

**Descripción**: Uso de colecciones legacy (ArrayList, Hashtable) que requieren boxing.

**Regex**:
```regex
\b(ArrayList|Hashtable)\b
```

**Puntos Base**: 3
**Multiplicador Hot Path**: x1.5

**Ejemplo Problemático**:
```csharp
ArrayList items = new ArrayList();
items.Add(1);    // Boxing
items.Add(2);    // Boxing

Hashtable table = new Hashtable();
table["key"] = 123;  // Boxing
```

**Solución Recomendada**:
```csharp
List<int> items = new List<int> { 1, 2 };
Dictionary<string, int> table = new Dictionary<string, int>
{
    ["key"] = 123
};
```

---

## Allocations

### Pattern: `allocation_in_loop`

**Descripción**: Creación de objetos con `new` dentro de loops.

**Regex**:
```regex
(for|foreach|while)\s*\([^)]*\)\s*\{[^}]*\bnew\s+\w+\s*[\[\(][^}]*\}
```

**Puntos Base**: 3
**Multiplicador Hot Path**: x1.5

**Ejemplo Problemático**:
```csharp
for (int i = 0; i < 1000; i++)
{
    var temp = new StringBuilder();  // 1000 allocaciones
    temp.Append(data[i]);
    results.Add(temp.ToString());
}
```

**Solución Recomendada**:
```csharp
var temp = new StringBuilder();      // Una sola allocación
for (int i = 0; i < 1000; i++)
{
    temp.Clear();
    temp.Append(data[i]);
    results.Add(temp.ToString());
}
```

---

### Pattern: `lambda_in_loop`

**Descripción**: Lambdas/closures dentro de loops que capturan variables, causando allocaciones de delegates.

**Regex**:
```regex
(for|foreach|while)\s*\([^)]*\)\s*\{[^}]*=>\s*[^}]*\}
```

**Puntos Base**: 3
**Multiplicador Hot Path**: x1.5

**Ejemplo Problemático**:
```csharp
for (int i = 0; i < items.Count; i++)
{
    // Closure captura 'i', nueva allocación cada iteración
    results.Add(items.Where(x => x.Id == i).FirstOrDefault());
}
```

**Solución Recomendada**:
```csharp
// Usar variable local para evitar closure
for (int i = 0; i < items.Count; i++)
{
    int localI = i;  // Captura explícita
    results.Add(items.Where(x => x.Id == localI).FirstOrDefault());
}
// O mejor aún, usar un Dictionary para O(1) lookup
```

---

### Pattern: `buffer_allocation`

**Descripción**: Allocación repetida de buffers byte[] sin usar ArrayPool.

**Regex**:
```regex
new\s+byte\s*\[\s*\d+\s*\]
```

**Puntos Base**: 3
**Multiplicador Hot Path**: x1.5

**Ejemplo Problemático**:
```csharp
public void ProcessData()
{
    byte[] buffer = new byte[4096];  // Nueva allocación cada llamada
    // ... usar buffer
}
```

**Solución Recomendada**:
```csharp
public void ProcessData()
{
    byte[] buffer = ArrayPool<byte>.Shared.Rent(4096);
    try
    {
        // ... usar buffer
    }
    finally
    {
        ArrayPool<byte>.Shared.Return(buffer);
    }
}
```

---

## Collections

### Pattern: `list_contains_loop`

**Descripción**: Uso de `List<T>.Contains()` dentro de loops, que tiene O(n) complejidad.

**Regex**:
```regex
(for|foreach|while)[^{]*\{[^}]*List<[^>]+>\s*\w+[^}]*\.Contains\s*\(
```

**Puntos Base**: 2
**Multiplicador Hot Path**: x1.0

**Ejemplo Problemático**:
```csharp
List<int> allowedIds = GetAllowedIds();
foreach (var item in items)
{
    if (allowedIds.Contains(item.Id))  // O(n) cada iteración
    {
        Process(item);
    }
}
```

**Solución Recomendada**:
```csharp
HashSet<int> allowedIds = GetAllowedIds().ToHashSet();
foreach (var item in items)
{
    if (allowedIds.Contains(item.Id))  // O(1) cada iteración
    {
        Process(item);
    }
}
```

---

### Pattern: `frequent_parse`

**Descripción**: Uso frecuente de métodos Parse/TryParse que pueden ser costosos.

**Regex**:
```regex
(int|long|double|float|decimal|DateTime)\.(Parse|TryParse)\s*\(
```

**Puntos Base**: 1
**Multiplicador Hot Path**: x1.5

**Nota**: Este pattern tiene bajo peso base porque el parsing es a veces necesario. Solo es problemático en hot paths con alta frecuencia.

---

### Pattern: `regex_not_compiled`

**Descripción**: Uso de Regex sin precompilar, que incurre overhead de compilación cada vez.

**Regex**:
```regex
Regex\.(Match|IsMatch|Replace|Split)\s*\([^,]+,\s*[^,]+\)
```

**Puntos Base**: 2
**Multiplicador Hot Path**: x1.5

**Ejemplo Problemático**:
```csharp
foreach (var line in lines)
{
    // Compila el regex cada iteración
    if (Regex.IsMatch(line, @"\d{4}-\d{2}-\d{2}"))
    {
        ProcessDate(line);
    }
}
```

**Solución Recomendada**:
```csharp
private static readonly Regex DatePattern =
    new Regex(@"\d{4}-\d{2}-\d{2}", RegexOptions.Compiled);

foreach (var line in lines)
{
    if (DatePattern.IsMatch(line))
    {
        ProcessDate(line);
    }
}
```

---

## Marcadores Explícitos

### Pattern: `todo_optimize`

**Descripción**: Comentarios TODO/FIXME que mencionan optimización.

**Regex**:
```regex
//\s*(TODO|FIXME):\s*optimi[zs]e
```

**Puntos Base**: 5
**Multiplicador Hot Path**: x2.0

**Ejemplo**:
```csharp
// TODO: optimize this method for large datasets
public void ProcessLargeData(IEnumerable<Item> items) { ... }
```

---

### Pattern: `perf_marker`

**Descripción**: Comentarios con marcador PERF: indicando concern de performance.

**Regex**:
```regex
//\s*PERF:
```

**Puntos Base**: 4
**Multiplicador Hot Path**: x2.0

**Ejemplo**:
```csharp
// PERF: This method is called 10k times per request
public int Calculate(int input) { ... }
```

---

### Pattern: `slow_marker`

**Descripción**: Comentarios con marcador SLOW indicando código lento conocido.

**Regex**:
```regex
//\s*SLOW
```

**Puntos Base**: 4
**Multiplicador Hot Path**: x2.0

---

### Pattern: `obsolete_performance`

**Descripción**: Atributo [Obsolete] mencionando performance como razón.

**Regex**:
```regex
\[Obsolete\s*\([^)]*[Pp]erformance[^)]*\)\]
```

**Puntos Base**: 5
**Multiplicador Hot Path**: x2.0

**Ejemplo**:
```csharp
[Obsolete("Performance: Use FastProcess instead")]
public void SlowProcess() { ... }
```

---

## Hot Path Indicators

Los siguientes patterns identifican contextos de "hot path" que multiplican los puntajes:

| Pattern | Descripción |
|---------|-------------|
| `class\s+\w*(Controller\|Handler\|Processor\|Service)\b` | Clases con sufijos típicos de hot paths |
| `\[(HttpGet\|HttpPost\|HttpPut\|HttpDelete\|HttpPatch\|Route)\s*[\(\]]` | Endpoints HTTP |
| `\basync\s+Task` | Métodos async (típicamente I/O bound) |
| `\[ApiController\]` | Controllers de API |

---

## False Positives Conocidos

### 1. LINQ en código de inicialización
```csharp
// Esto NO es un problema - solo se ejecuta una vez
private static readonly List<string> AllowedValues =
    Enum.GetValues<MyEnum>().Select(x => x.ToString()).ToList();
```

### 2. StringBuilder en métodos de uso infrecuente
```csharp
// Esto NO es un problema si el método se llama raramente
public string GenerateReport()
{
    var sb = new StringBuilder();
    // ...
}
```

### 3. Allocaciones en código de test
```csharp
// Los tests no son hot paths - ignorar
[Fact]
public void TestMethod()
{
    var items = new List<int> { 1, 2, 3 };  // OK en tests
}
```

### 4. Regex.IsMatch con pattern constante en inicialización
```csharp
// El pattern se compila una vez si es estático
private static readonly bool HasDigits =
    Regex.IsMatch(SomeConstant, @"\d+");  // OK si es estático
```

### Mitigación de False Positives

El scanner intenta mitigar false positives mediante:

1. **Contexto de Hot Path**: Solo aplica multiplicadores si está cerca de indicators de hot path
2. **Umbral de Severidad**: Permite filtrar candidatos de bajo puntaje
3. **Revisión Manual**: El reporte está diseñado para revisión humana antes de actuar

---

## Extensibilidad

Para agregar nuevos patterns, editar la lista `DETECTION_PATTERNS` en `scan_solution.py`:

```python
PatternConfig(
    name="new_pattern_name",
    regex=r'your_regex_here',
    base_score=3,
    hot_path_multiplier=1.5,
    description="Descripción del pattern"
)
```
