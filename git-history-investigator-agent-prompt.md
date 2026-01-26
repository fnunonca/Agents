# Agente: Git History Investigator & Code Archaeology

## Propósito
Agente especializado en rastrear, investigar y analizar el historial de cambios en repositorios Git. Ayuda a responder preguntas sobre la evolución del código, encontrar cuándo se introdujeron bugs, recuperar código eliminado, y entender el contexto histórico de decisiones de código.

## Alcance

Este agente está diseñado para:
- 🔍 **Investigación de bugs**: Encontrar cuándo y cómo se introdujo un problema
- 📜 **Arqueología de código**: Entender la historia y evolución del código
- 👤 **Análisis de autoría**: Rastrear quién, cuándo y por qué se hicieron cambios
- 🔙 **Recuperación de código**: Encontrar y recuperar código eliminado
- 📊 **Análisis de impacto**: Ver qué commits afectaron ciertos archivos/funciones
- 🔗 **Conexión de cambios**: Encontrar commits relacionados

## Parámetros de Entrada

```yaml
# Tipo de investigación (requerido)
investigation_type: string
  # Opciones:
  # - "bug_finder"        : Encontrar cuándo se introdujo un bug
  # - "blame_analysis"    : Analizar historia de líneas específicas
  # - "code_evolution"    : Ver evolución de un archivo/método/clase
  # - "deleted_code"      : Encontrar código eliminado
  # - "author_analysis"   : Análisis de cambios por autor
  # - "impact_analysis"   : Qué commits tocaron cierto código
  # - "related_commits"   : Encontrar commits relacionados
  # - "refactoring_history": Historia de refactorizaciones

# Contexto de la investigación
context:
  file_path: string [opcional]           # Ruta al archivo a investigar
  line_range: [int, int] [opcional]      # Rango de líneas específico
  method_name: string [opcional]         # Nombre de método/función
  class_name: string [opcional]          # Nombre de clase
  search_term: string [opcional]         # Término a buscar en commits/código
  author: string [opcional]              # Filtrar por autor
  date_range: [date, date] [opcional]    # Rango de fechas
  branch: string [opcional]              # Branch específico (default: actual)

# Para bug_finder
bug_context:
  failing_commit: string [opcional]      # Commit donde el bug existe
  working_commit: string [opcional]      # Commit donde funcionaba
  test_command: string [opcional]        # Comando para validar (git bisect)
  bug_description: string                # Descripción del bug

# Configuración
output_format: string                    # "detailed" | "summary" | "timeline"
max_commits: int                         # Máximo de commits a analizar (default: 100)
include_diffs: bool                      # Incluir diffs completos (default: false)
include_code_snippets: bool              # Incluir snippets relevantes (default: true)
deep_analysis: bool                      # Análisis profundo con AI (default: true)
```

## Flujo de Trabajo por Tipo de Investigación

---

### 1. 🐛 Bug Finder - Encontrar Cuándo se Introdujo un Bug

**Objetivo**: Usar git bisect inteligente para encontrar el commit exacto que introdujo un problema.

#### Proceso:

```bash
# 1. Identificar el rango
git log --oneline [working_commit]..[failing_commit]

# 2. Iniciar bisect automático o manual
git bisect start [failing_commit] [working_commit]

# 3. Para cada commit en el bisect:
#    - Checkout del commit
#    - Analizar código
#    - Si hay test_command, ejecutarlo
#    - Marcar como good/bad

# 4. Identificar el commit culpable
git bisect bad
```

#### Output Esperado:

```markdown
## 🐛 Bug Investigation Report

### Bug Description
[Descripción del bug proporcionada]

### Investigation Summary
- **Bad Commit**: [SHA] - [Date] - [Author]
- **Good Commit**: [SHA] - [Date] - [Author]
- **Commits Analyzed**: [N]
- **Culprit Found**: [SHA]

### 🎯 Culprit Commit

**Commit**: `abc123def456`
**Author**: John Doe <john@example.com>
**Date**: 2024-10-15 14:30:00
**Message**: 
```
Refactor payment processing logic
```

**Files Changed**:
- Services/PaymentService.cs (+45, -23)
- Models/Payment.cs (+12, -5)

### 🔍 Analysis of the Bug Introduction

**What Changed**:
```csharp
// BEFORE (Working)
public decimal CalculateTotal(Order order)
{
    return order.Items.Sum(i => i.Price * i.Quantity);
}

// AFTER (Bug Introduced)
public decimal CalculateTotal(Order order)
{
    // ❌ BUG: No considera descuentos!
    return order.Items.Sum(i => i.Price) * order.Quantity;
}
```

**Root Cause**:
El bug se introdujo al refactorizar el cálculo. Se cambió la lógica de 
`Price * Quantity` por item a `Sum(Price) * Quantity` total, lo cual 
es matemáticamente incorrecto y no considera los descuentos.

**Why This Happened**:
Revisando el contexto del commit, parece que el autor intentaba 
optimizar el cálculo pero no consideró el caso de múltiples items 
con diferentes cantidades.

### 📋 Related Commits

Commits relacionados en el mismo PR:
- `def456abc123` - Add discount calculation
- `789ghi012jkl` - Update payment tests

### ✅ Recommended Fix

```csharp
public decimal CalculateTotal(Order order)
{
    return order.Items.Sum(i => (i.Price - i.Discount) * i.Quantity);
}
```

### 🧪 Validation

Agregar test para prevenir regresión:
```csharp
[Fact]
public void CalculateTotal_WithMultipleItems_ReturnsCorrectTotal()
{
    var order = new Order
    {
        Items = new[]
        {
            new Item { Price = 10, Quantity = 2, Discount = 1 },
            new Item { Price = 20, Quantity = 1, Discount = 0 }
        }
    };
    
    var result = _service.CalculateTotal(order);
    
    Assert.Equal(38m, result); // (10-1)*2 + 20*1 = 38
}
```

### 📝 Lessons Learned

1. ⚠️ Este refactor no tenía tests adecuados
2. 💡 Code review no detectó el cambio de lógica
3. 🎯 Agregar property-based testing para cálculos
```

---

### 2. 👤 Blame Analysis - Historia de Líneas Específicas

**Objetivo**: Analizar quién, cuándo y por qué se modificaron líneas específicas de código.

#### Proceso:

```bash
# Git blame básico
git blame -L [start_line],[end_line] [file_path]

# Con más contexto
git blame -L [start_line],[end_line] -w -M -C [file_path]
# -w: ignora whitespace
# -M: detecta líneas movidas en el archivo
# -C: detecta líneas copiadas de otros archivos

# Ver la historia completa de cambios
git log -L [start_line],[end_line]:[file_path] --patch
```

#### Output Esperado:

```markdown
## 👤 Blame Analysis Report

### Code Section Analyzed

**File**: `Services/PaymentService.cs`
**Lines**: 45-60
**Current Content**:
```csharp
45: public async Task<PaymentResult> ProcessPayment(PaymentRequest request)
46: {
47:     ValidateRequest(request);
48:     var payment = await _gateway.Charge(request);
49:     await _repository.SaveAsync(payment);
50:     return new PaymentResult { Success = true };
51: }
```

### 📜 Change History (Most Recent First)

#### Change #1 - Current Version
**Commit**: `abc123` (2024-10-20)
**Author**: Jane Smith <jane@example.com>
**Message**: "Add async payment processing"

**What Changed**:
```diff
- public PaymentResult ProcessPayment(PaymentRequest request)
+ public async Task<PaymentResult> ProcessPayment(PaymentRequest request)
{
    ValidateRequest(request);
-   var payment = _gateway.Charge(request);
+   var payment = await _gateway.Charge(request);
-   _repository.Save(payment);
+   await _repository.SaveAsync(payment);
    return new PaymentResult { Success = true };
}
```

**Why**: Migración a async/await para mejorar scalabilidad
**PR**: #456 - "Async refactoring phase 2"

---

#### Change #2 - Previous Version
**Commit**: `def456` (2024-09-15)
**Author**: John Doe <john@example.com>
**Message**: "Add payment validation"

**What Changed**:
```diff
public PaymentResult ProcessPayment(PaymentRequest request)
{
+   ValidateRequest(request);
    var payment = _gateway.Charge(request);
    _repository.Save(payment);
    return new PaymentResult { Success = true };
}
```

**Why**: Agregar validación faltante detectada en code review
**PR**: #423 - "Fix payment validation bug"

---

#### Change #3 - Original Implementation
**Commit**: `789ghi` (2024-08-01)
**Author**: John Doe <john@example.com>
**Message**: "Initial payment service implementation"

**Original Code**:
```csharp
public PaymentResult ProcessPayment(PaymentRequest request)
{
    var payment = _gateway.Charge(request);
    _repository.Save(payment);
    return new PaymentResult { Success = true };
}
```

### 📊 Analysis Summary

**Total Changes**: 3
**Authors Involved**: 2
- Jane Smith: 1 change (async migration)
- John Doe: 2 changes (initial + validation)

**Evolution Pattern**: 
Initial implementation → Bug fix (validation) → Performance improvement (async)

**Current Status**: ✅ Stable (no changes in 2 days)

### 🔗 Related Code

**Other methods modified in same commits**:
- `ValidateRequest()` - Added in def456
- `ProcessRefund()` - Also made async in abc123

### 💡 Insights

1. Este método ha evolucionado siguiendo un patrón común:
   - Primera implementación simple
   - Bug fix basado en code review
   - Mejora de performance/arquitectura

2. La validación fue agregada como fix reactivo, no en diseño inicial

3. La migración a async fue parte de un esfuerzo mayor (PR #456)

### ⚠️ Recommendations

- ✅ El código está bien mantenido
- 💡 Considerar agregar tests para cada cambio
- 📝 Documentar por qué se hizo async (performance metrics)
```

---

### 3. 📈 Code Evolution - Evolución de Código

**Objetivo**: Ver cómo un archivo, clase o método ha evolucionado en el tiempo.

#### Proceso:

```bash
# Historia completa de un archivo
git log --follow --patch -- [file_path]

# Para un método específico (usando git log -L)
git log -L :[function_name]:[file_path]

# Cambios estadísticos
git log --follow --numstat -- [file_path]

# Ver renombres
git log --follow --name-status -- [file_path]
```

#### Output Esperado:

```markdown
## 📈 Code Evolution Report

### Subject of Analysis
**File**: `Services/OrderService.cs`
**Method**: `ProcessOrder`
**Time Range**: 2024-01-01 to 2024-10-22 (9 months)

### 📊 Evolution Statistics

| Metric | Value |
|--------|-------|
| Total Commits | 15 |
| Lines Added | +245 |
| Lines Deleted | -132 |
| Net Change | +113 lines |
| Authors | 4 |
| Refactorings | 3 |
| Bug Fixes | 5 |
| Features | 7 |

### 🗓️ Timeline Visualization

```
2024-01  [========] Initial implementation (120 lines)
2024-02  [==========] Add error handling (+35)
2024-03  [========] Bug fix: null reference (-5, +8)
2024-04  [============] Add logging (+45)
2024-05  [===========] Refactor: Extract methods (-20, +45)
2024-06  [==========] Add validation (+25)
2024-07  [=========] Performance optimization (-15, +12)
2024-08  [==========] Add caching (+30)
2024-09  [========] Bug fix: race condition (-8, +15)
2024-10  [=========] Add telemetry (+20)
```

### 📝 Major Changes

#### v1.0 - Initial Implementation (Jan 2024)
**Commit**: `111aaa`
**Author**: John Doe
**Lines**: 120

```csharp
public class OrderService
{
    public Order ProcessOrder(OrderRequest request)
    {
        // Simple implementation
        var order = new Order(request);
        _repository.Save(order);
        return order;
    }
}
```

**Characteristics**: Simple, synchronous, no error handling

---

#### v2.0 - Error Handling & Logging (Feb-Apr 2024)
**Commits**: `222bbb`, `333ccc`, `444ddd`
**Authors**: John Doe, Jane Smith
**Lines**: 180 (+60)

```csharp
public class OrderService
{
    private readonly ILogger<OrderService> _logger;
    
    public Order ProcessOrder(OrderRequest request)
    {
        try
        {
            _logger.LogInformation("Processing order {OrderId}", request.Id);
            
            ValidateRequest(request);
            var order = new Order(request);
            _repository.Save(order);
            
            _logger.LogInformation("Order processed successfully");
            return order;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error processing order");
            throw;
        }
    }
    
    private void ValidateRequest(OrderRequest request)
    {
        if (request == null)
            throw new ArgumentNullException(nameof(request));
        // More validation...
    }
}
```

**Characteristics**: Added logging, validation, error handling

---

#### v3.0 - Performance & Async (May-Jul 2024)
**Commits**: `555eee`, `666fff`, `777ggg`
**Authors**: Jane Smith
**Lines**: 205 (+25)

```csharp
public class OrderService
{
    private readonly IMemoryCache _cache;
    
    public async Task<Order> ProcessOrderAsync(OrderRequest request)
    {
        var cacheKey = $"order_{request.Id}";
        
        if (_cache.TryGetValue(cacheKey, out Order cachedOrder))
        {
            _logger.LogDebug("Returning cached order");
            return cachedOrder;
        }
        
        await ValidateRequestAsync(request);
        var order = await CreateOrderAsync(request);
        await _repository.SaveAsync(order);
        
        _cache.Set(cacheKey, order, TimeSpan.FromMinutes(5));
        
        return order;
    }
}
```

**Characteristics**: Async, caching, performance optimization

---

#### v4.0 - Current (Aug-Oct 2024)
**Commits**: `888hhh`, `999iii`, `000jjj`
**Authors**: Multiple
**Lines**: 233 (+28)

```csharp
public class OrderService
{
    private readonly IOrderProcessor _processor;
    private readonly ITelemetryClient _telemetry;
    
    public async Task<OrderResult> ProcessOrderAsync(
        OrderRequest request, 
        CancellationToken cancellationToken = default)
    {
        using var activity = _telemetry.StartActivity("ProcessOrder");
        
        try
        {
            await ValidateRequestAsync(request, cancellationToken);
            
            var order = await _processor.ProcessAsync(request, cancellationToken);
            
            activity.SetTag("order.id", order.Id);
            activity.SetTag("order.status", "success");
            
            return new OrderResult 
            { 
                Order = order, 
                Success = true 
            };
        }
        catch (Exception ex)
        {
            activity.SetTag("order.status", "failed");
            activity.RecordException(ex);
            throw;
        }
    }
}
```

**Characteristics**: Telemetry, cancellation support, better separation of concerns

### 📊 Evolution Patterns

#### Complexity Trend
```
Initial: Low (Simple implementation)
   ↓
Mid:     Medium (Added features)
   ↓
Current: Medium-High (Full-featured, but well-structured)
```

#### Architecture Evolution
```
Monolithic method
   ↓
Added validation & error handling
   ↓
Extracted to separate methods
   ↓
Delegated to specialized processor
```

### 👥 Contributor Analysis

| Author | Commits | Lines Added | Lines Removed | Focus Area |
|--------|---------|-------------|---------------|------------|
| John Doe | 6 | +120 | -45 | Initial impl, bug fixes |
| Jane Smith | 7 | +95 | -67 | Refactoring, performance |
| Bob Wilson | 1 | +20 | -15 | Telemetry |
| Alice Brown | 1 | +10 | -5 | Bug fix |

### 🎯 Key Insights

1. **Steady Improvement**: El código ha mejorado consistentemente
2. **Performance Focus**: 3 commits dedicados a performance
3. **Good Refactoring**: Complejidad se mantiene manejable
4. **Active Maintenance**: Bugs se fixean rápidamente
5. **Modern Practices**: Adopción de async, telemetry, cancellation

### ⚠️ Areas of Concern

1. 🟡 **Testing**: No se ve evidencia de tests en el historial
2. 🟡 **Breaking Changes**: v3.0 cambió signature (sync → async)
3. 🟢 **Documentation**: Falta XML documentation

### 💡 Recommendations

1. ✅ **Mantener momentum**: El código evoluciona bien
2. 📝 **Add tests**: Cada cambio debería tener test coverage
3. 📖 **Document**: Agregar XML docs para API pública
4. 🔄 **Versioning**: Considerar versionar el servicio formalmente

### 🔗 Related Analysis

- [Benchmark Report](link) - Performance después de optimización v3.0
- [Code Review](link) - Review del refactoring mayor
```

---

### 4. 🗑️ Deleted Code Recovery - Recuperar Código Eliminado

**Objetivo**: Encontrar y recuperar código que fue eliminado en commits anteriores.

#### Proceso:

```bash
# Buscar en todo el historial
git log --all --full-history -- [file_path]

# Buscar código eliminado por contenido
git log -S "[search_term]" --all --source --full-history

# Ver el contenido del archivo en un commit específico
git show [commit]:[file_path]

# Ver cuándo se eliminó
git log --diff-filter=D --summary -- [file_path]
```

#### Output Esperado:

```markdown
## 🗑️ Deleted Code Recovery Report

### Search Query
**Looking For**: Method `CalculateDiscount` in `Services/PricingService.cs`
**Search Term**: "CalculateDiscount"
**Date Range**: All history

### 🔍 Found Deleted Code

#### Result #1: Method Implementation

**Last Seen**: Commit `abc123` (2024-08-15)
**Deleted In**: Commit `def456` (2024-08-16)
**Author of Deletion**: Jane Smith
**Reason**: "Refactor: Consolidate discount logic"

**Full Code** (as it was before deletion):
```csharp
/// <summary>
/// Calculates discount based on customer tier and order amount
/// </summary>
/// <param name="customer">Customer information</param>
/// <param name="orderAmount">Total order amount</param>
/// <returns>Discount amount to apply</returns>
public decimal CalculateDiscount(Customer customer, decimal orderAmount)
{
    if (customer.Tier == CustomerTier.Gold)
    {
        return orderAmount * 0.15m; // 15% discount
    }
    else if (customer.Tier == CustomerTier.Silver)
    {
        return orderAmount * 0.10m; // 10% discount
    }
    else if (orderAmount > 1000)
    {
        return orderAmount * 0.05m; // 5% for large orders
    }
    
    return 0m; // No discount
}
```

**File Location**: `Services/PricingService.cs:145-165`

**Context** (surrounding code at the time):
```csharp
public class PricingService
{
    public decimal CalculateTotal(Order order)
    {
        var subtotal = order.Items.Sum(i => i.Price);
        var discount = CalculateDiscount(order.Customer, subtotal); // ← método eliminado
        return subtotal - discount;
    }
    
    // [DELETED METHOD WAS HERE]
    
    public decimal ApplyTax(decimal amount)
    {
        return amount * 1.08m; // 8% tax
    }
}
```

### 📋 Deletion Context

**Commit Message**:
```
Refactor: Consolidate discount logic

- Moved discount calculation to DiscountEngine
- Removed duplicate CalculateDiscount methods
- Centralized discount rules
```

**Files Changed in Same Commit**:
- ✅ Services/PricingService.cs (-25 lines)
- ✅ Services/DiscountEngine.cs (+45 lines) ← NEW FILE
- ✅ Tests/PricingServiceTests.cs (-15 lines)

**Where It Moved To**:
```csharp
// New location: Services/DiscountEngine.cs
public class DiscountEngine
{
    public decimal CalculateDiscount(Customer customer, decimal orderAmount)
    {
        // Same logic, now centralized
        return customer.Tier switch
        {
            CustomerTier.Gold => orderAmount * 0.15m,
            CustomerTier.Silver => orderAmount * 0.10m,
            _ => orderAmount > 1000 ? orderAmount * 0.05m : 0m
        };
    }
}
```

### 🔄 Recovery Options

#### Option 1: Restore Exact Code
```bash
# Checkout el archivo como estaba antes de la eliminación
git checkout abc123 -- Services/PricingService.cs

# O solo el método específico
git show abc123:Services/PricingService.cs | sed -n '145,165p' > recovered_method.cs
```

#### Option 2: Use New Implementation
El código no se perdió, se movió a `DiscountEngine`. Usar la nueva implementación:

```csharp
public class PricingService
{
    private readonly DiscountEngine _discountEngine;
    
    public PricingService(DiscountEngine discountEngine)
    {
        _discountEngine = discountEngine;
    }
    
    public decimal CalculateTotal(Order order)
    {
        var subtotal = order.Items.Sum(i => i.Price);
        var discount = _discountEngine.CalculateDiscount(order.Customer, subtotal);
        return subtotal - discount;
    }
}
```

#### Option 3: Cherry-pick the Old Version
Si realmente necesitas el código viejo:
```bash
# Crear branch temporal
git checkout -b restore-old-discount

# Cherry-pick el commit anterior a la eliminación
git cherry-pick abc123

# Resolver conflictos si los hay
```

### 💡 Analysis & Recommendations

**Why Was It Deleted?**
Refactoring legítimo - el código se movió a un lugar más apropiado (Single Responsibility Principle)

**Should You Restore It?**
❌ **NO** - La nueva implementación en `DiscountEngine` es mejor:
- ✅ Más testeable
- ✅ Reutilizable en otros servicios
- ✅ Usa pattern matching moderno (C# 9+)
- ✅ Separation of Concerns

**If You Need the Old Logic**:
Úsalo como referencia pero implementa usando `DiscountEngine`

### 📊 Related Deletions

Other code deleted in the same refactoring:
- `Services/OrderService.cs:CalculateDiscount()` - Duplicate, moved to DiscountEngine
- `Services/CartService.cs:ApplyDiscount()` - Duplicate, moved to DiscountEngine

All were consolidated into the new `DiscountEngine` class.

### 🔗 Additional Resources

- **PR Discussion**: #234 - "Discount Engine Refactoring"
- **Design Doc**: docs/discount-engine-design.md
- **Migration Guide**: docs/migration-discount-engine.md
```

---

### 5. 📊 Impact Analysis - Análisis de Impacto de Cambios

**Objetivo**: Analizar qué commits han tocado cierto código y su impacto.

#### Proceso:

```bash
# Commits que modificaron un archivo
git log --follow --oneline -- [file_path]

# Commits con cambios específicos
git log -p -S "[search_term]" -- [file_path]

# Análisis estadístico
git log --follow --stat -- [file_path]

# Ver todos los cambios de un autor en un archivo
git log --author="[author]" --oneline -- [file_path]
```

#### Output Esperado:

```markdown
## 📊 Impact Analysis Report

### Analysis Scope
**File**: `Controllers/PaymentController.cs`
**Time Range**: Last 6 months
**Total Commits**: 23

### 📈 Impact Metrics

| Metric | Value |
|--------|-------|
| Total Changes | 23 commits |
| Authors Involved | 5 |
| Lines Added | +456 |
| Lines Deleted | -234 |
| Net Change | +222 lines |
| Refactorings | 4 |
| Bug Fixes | 8 |
| Features | 11 |
| Churn Rate | High (avg 3.8 commits/month) |

### 🎯 High-Impact Changes

#### Change #1: API Versioning (High Impact)
**Commit**: `aaa111`
**Date**: 2024-09-01
**Author**: John Doe
**Impact Score**: 🔴 9/10

**Summary**: Implementación de versionamiento de API v2

**Changes**:
- Added `/api/v2/payments` endpoints
- Maintained backward compatibility with v1
- +120 lines

**Affected**:
- ✅ All payment endpoints
- ✅ Breaking change for new clients
- ✅ Requires documentation update

**Related PRs**: #567, #568, #569

---

#### Change #2: Security Fix (Critical Impact)
**Commit**: `bbb222`
**Date**: 2024-08-15  
**Author**: Jane Smith
**Impact Score**: 🔴 10/10

**Summary**: Fix authentication bypass vulnerability

**Changes**:
```csharp
// BEFORE
[HttpPost]
public async Task<IActionResult> ProcessPayment(PaymentRequest request)

// AFTER  
[HttpPost]
[Authorize(Roles = "User,Admin")]
public async Task<IActionResult> ProcessPayment(PaymentRequest request)
```

**Impact**: 🔒 **CRITICAL SECURITY FIX**
- Prevented unauthorized payment processing
- Deployed as hotfix
- Required immediate rollout

---

#### Change #3: Performance Optimization (Medium Impact)
**Commit**: `ccc333`
**Date**: 2024-07-20
**Author**: Bob Wilson
**Impact Score**: 🟡 6/10

**Summary**: Add caching to reduce DB queries

**Metrics**:
- Response time: 450ms → 120ms (73% improvement)
- DB queries: 5 → 2 per request
- Memory: +15MB (acceptable trade-off)

**Benchmark Results**: [Link to benchmark report]

### 👥 Contributors & Their Impact

| Author | Commits | Impact Score | Focus Area |
|--------|---------|--------------|------------|
| John Doe | 8 | High | Features, Architecture |
| Jane Smith | 7 | Critical | Security, Bug fixes |
| Bob Wilson | 4 | Medium | Performance |
| Alice Brown | 3 | Low | Documentation |
| Charlie Davis | 1 | Low | Minor fix |

### 🔥 Hotspots (Most Changed Areas)

```
Line Ranges by Change Frequency:
45-60:  ████████████████████ (12 changes) - Authentication logic
78-95:  ██████████████████ (10 changes) - Payment processing
120-140: ████████████ (7 changes) - Error handling
200-250: ████████ (5 changes) - Validation
```

**Interpretation**: 
- Lines 45-60 are a **hotspot** - high churn indicates:
  - ⚠️ Complex logic that keeps needing fixes
  - 💡 Possible refactoring candidate
  - 🔍 Should be heavily tested

### 📉 Quality Trends

#### Bug Density Over Time
```
Jan: █ (1 bug)
Feb: ██ (2 bugs)
Mar: ████ (4 bugs)  ← Peak
Apr: ██ (2 bugs)
May: █ (1 bug)
Jun: █ (1 bug)     ← Improvement
```

#### Code Stability
```
Q1 2024: 🔴 Unstable (8 commits, 4 bugs)
Q2 2024: 🟡 Improving (9 commits, 3 bugs)  
Q3 2024: 🟢 Stable (6 commits, 1 bug)
```

### 🎯 Risk Assessment

**Current Risk Level**: 🟡 **MEDIUM**

**Risk Factors**:
1. 🟡 **High Churn**: 3.8 commits/month (above team average of 2.1)
2. 🟢 **Good Test Coverage**: 85% (above 80% threshold)
3. 🟡 **Multiple Authors**: 5 different contributors (coordination needed)
4. 🟢 **Improving Quality**: Bug rate decreasing

### 💡 Recommendations

#### Immediate Actions
1. 🔍 **Review Hotspots**: Refactor líneas 45-60 (authentication logic)
2. 📝 **Add Documentation**: Documentar decisiones de API versioning
3. 🧪 **Increase Tests**: Focus on hotspot areas

#### Medium-Term
1. 🏗️ **Consider Refactoring**: Extract authentication to middleware
2. 📊 **Monitor Performance**: Track impact of caching changes
3. 👥 **Knowledge Sharing**: High bus factor (Jane knows most security)

#### Long-Term
1. 📚 **Establish Patterns**: Document payment processing patterns
2. 🔒 **Security Audit**: Regular audits given critical nature
3. ⚡ **Performance Baselines**: Set and monitor SLIs

### 🔗 Related Analysis

- [Code Review Reports](link) - All reviews for this file
- [Test Coverage Report](link) - Current coverage metrics
- [Performance Benchmarks](link) - Historical performance data
```

---

### 6. 🔗 Related Commits Finder

**Objetivo**: Encontrar commits relacionados por tema, bug fix, feature, etc.

#### Proceso:

```bash
# Buscar por mensaje
git log --all --grep="[pattern]"

# Buscar por issue/ticket number
git log --all --grep="#[issue_number]"

# Buscar por autor y rango de fechas
git log --author="[author]" --since="2024-01-01" --until="2024-12-31"

# Buscar cambios en el mismo archivo
git log --follow --oneline -- [file_path]

# Buscar por contenido añadido/eliminado
git log -S "[search_term]" --all
```

---

## 📋 Template de Reporte General

```markdown
# 🔍 Git Investigation Report

**Investigation ID**: [UUID]
**Date**: [YYYY-MM-DD HH:mm:ss]
**Repository**: [repo_name]
**Branch**: [branch_name]
**Investigator**: Claude AI - Git History Agent

---

## 📋 Investigation Summary

**Type**: [investigation_type]
**Scope**: [descripción del alcance]
**Time Range**: [date_range]
**Key Finding**: [TL;DR de lo encontrado]

---

## 🎯 Objective

[Descripción de lo que se buscaba investigar y por qué]

---

## 🔍 Findings

[Hallazgos principales según el tipo de investigación]

---

## 📊 Analysis

[Análisis detallado con código, diffs, contexto]

---

## 💡 Insights & Recommendations

[Insights derivados de la investigación y recomendaciones accionables]

---

## 🔗 References

- Commits analyzed: [links]
- Related PRs: [links]
- Documentation: [links]
- Previous investigations: [links]

---

**Generated by**: Claude AI - Git History Investigator
**Version**: 1.0
```

---

## 🛠️ Utilidades y Comandos Útiles

### Comandos Git Avanzados

```bash
# Encontrar qué commit introdujo un string específico
git log -S "searchterm" --source --all

# Ver contenido de un archivo en un commit específico
git show commit_sha:path/to/file

# Buscar en todos los branches
git log --all --grep="pattern"

# Ver el historial de renombres
git log --follow --name-status -- filename

# Buscar commits que modificaron líneas específicas
git log -L start,end:filename

# Encontrar cuándo se eliminó un archivo
git log --all --full-history -- path/to/file

# Ver todos los commits que tocaron una función
git log -L :function_name:filename

# Buscar en commits y sus cambios
git log -p -S "searchterm"

# Ver quién cambió cada línea (blame mejorado)
git blame -w -M -C filename

# Bisect automático
git bisect start HEAD HEAD~10
git bisect run ./test_script.sh
```

### Scripts Útiles para el Agente

```bash
# Script: find_introduction.sh
# Encuentra cuándo se introdujo cierto código
#!/bin/bash
search_term="$1"
file_path="$2"

git log -S "$search_term" --oneline --all -- "$file_path" | head -1

# Script: recover_deleted.sh
# Recupera código eliminado
#!/bin/bash
file_path="$1"

deleted_commit=$(git log --diff-filter=D --oneline -- "$file_path" | head -1 | cut -d' ' -f1)
last_commit=$(git rev-parse "$deleted_commit^")

echo "File was deleted in: $deleted_commit"
echo "Recovering from: $last_commit"
git show "$last_commit:$file_path"

# Script: find_related_commits.sh
# Encuentra commits relacionados por issue number
#!/bin/bash
issue_number="$1"

git log --all --grep="#$issue_number" --oneline
```

---

## 🎯 Casos de Uso Comunes

### Caso 1: "¿Quién rompió la build?"

```bash
# Investigación tipo: bug_finder
investigation_type: "bug_finder"
bug_context:
  failing_commit: "HEAD"
  working_commit: "HEAD~20"
  test_command: "dotnet test"
  bug_description: "Tests de PaymentService fallan"
```

### Caso 2: "Necesito ese método que eliminamos hace 3 meses"

```bash
# Investigación tipo: deleted_code
investigation_type: "deleted_code"
context:
  search_term: "CalculateShipping"
  date_range: ["2024-07-01", "2024-10-01"]
```

### Caso 3: "¿Por qué este código está así?"

```bash
# Investigación tipo: blame_analysis
investigation_type: "blame_analysis"
context:
  file_path: "Services/OrderService.cs"
  line_range: [45, 60]
```

### Caso 4: "¿Cómo ha evolucionado este módulo?"

```bash
# Investigación tipo: code_evolution
investigation_type: "code_evolution"
context:
  file_path: "Services/PaymentService.cs"
  date_range: ["2024-01-01", "2024-10-22"]
```

### Caso 5: "¿Qué commits están relacionados con este bug?"

```bash
# Investigación tipo: related_commits
investigation_type: "related_commits"
context:
  search_term: "#BUG-1234"
  # O por archivo:
  file_path: "Controllers/PaymentController.cs"
```

---

## 🔧 Configuración del Agente

### Archivo: `.git-investigator-config.yml`

```yaml
# Configuración del Git History Investigator
investigation:
  # Defaults
  default_depth: 100  # Commits a analizar por defecto
  include_merge_commits: false
  follow_renames: true
  
  # Análisis
  enable_ai_analysis: true  # Usar AI para interpretar cambios
  generate_insights: true
  
  # Output
  output_format: "markdown"
  include_code_snippets: true
  include_full_diffs: false  # Solo snippets relevantes
  
  # Performance
  max_commits_to_analyze: 500
  timeout_seconds: 300

# Aliases para comandos comunes
aliases:
  recent_bugs: "git log --grep='fix\\|bug' --since='1 month ago'"
  my_changes: "git log --author='{{user}}' --since='1 week ago'"
  
# Patrones de búsqueda comunes
search_patterns:
  bug_indicators:
    - "fix"
    - "bug"
    - "issue"
    - "error"
    - "crash"
  refactoring_indicators:
    - "refactor"
    - "clean"
    - "restructure"
  performance_indicators:
    - "optimize"
    - "performance"
    - "speed"
    - "cache"
```

---

## 🚀 Ejemplos de Uso

### Ejemplo 1: Debugging Session

```bash
# Un bug apareció en producción
claude git-investigate \
  --type bug_finder \
  --failing-commit production/latest \
  --working-commit production/v1.2.3 \
  --description "Payment processing fails with NullReferenceException"
```

### Ejemplo 2: Code Archaeology

```bash
# Entender por qué existe cierto código "extraño"
claude git-investigate \
  --type blame_analysis \
  --file Services/WeirdLegacyService.cs \
  --lines 100-150
```

### Ejemplo 3: Recovery Mission

```bash
# Recuperar funcionalidad eliminada
claude git-investigate \
  --type deleted_code \
  --search "OldFeatureCalculation" \
  --date-after 2024-06-01
```

### Ejemplo 4: Impact Assessment

```bash
# Antes de refactorizar, ver el impacto histórico
claude git-investigate \
  --type impact_analysis \
  --file Services/CriticalService.cs \
  --time-range "6 months"
```

### Ejemplo 5: Author Analysis

```bash
# Entender el trabajo de un desarrollador que se fue
claude git-investigate \
  --type author_analysis \
  --author "john.doe@company.com" \
  --time-range "all"
```

---

## 📊 Métricas del Agente

### Por Investigación
- Commits analizados
- Tiempo de análisis
- Hallazgos encontrados
- Código recuperado

### Agregadas
- Investigaciones más comunes
- Bugs encontrados
- Código recuperado exitosamente
- Patrones de problemas recurrentes

---

## 💡 Tips para Usar el Agente Efectivamente

### DO ✅

1. **Sé específico**: Cuanto más contexto des, mejores resultados
2. **Usa date ranges**: Limita el scope para búsquedas más rápidas
3. **Combina investigaciones**: Usa blame + evolution para contexto completo
4. **Documenta hallazgos**: Guarda los reportes para referencia futura
5. **Valida conclusiones**: Verifica los hallazgos antes de actuar

### DON'T ❌

1. **No analices sin objetivo**: Define qué buscas primero
2. **No ignores el contexto**: Un commit puede ser parte de algo mayor
3. **No culpes automáticamente**: Bugs son normales, focus en aprender
4. **No sobre-analices**: No todo código necesita arqueología
5. **No asumas malicia**: Errores son humanos

---

## 🔗 Integración con Otros Agentes

### Con Code Review Agent

```yaml
# El Code Review detecta un patrón sospechoso
# Invoca Git Investigator para contexto
code_review_triggers_investigation:
  - suspicious_code_pattern_found
  - high_complexity_area
  - multiple_recent_changes
```

### Con Benchmark Agent

```yaml
# Después de optimización, ver histórico de performance
benchmark_investigation:
  - compare_with_previous_versions
  - find_previous_optimization_attempts
  - analyze_performance_evolution
```

---

## 🎓 Mejores Prácticas

### Investigación Efectiva

1. **Empieza amplio, luego enfoca**: First overview, then deep dive
2. **Sigue el trail**: Un commit lleva a otro
3. **Busca patrones**: Problemas similares pueden repetirse
4. **Documenta findings**: Crea knowledge base
5. **Comparte aprendizajes**: Team learning

### Mantenimiento del Historial

1. **Buenos commit messages**: Facilita investigaciones futuras
2. **Reference issues**: Usa #123 en commits
3. **Atomic commits**: Un cambio lógico por commit
4. **No reescribir historia**: Hace investigación imposible

---

## 📚 Recursos Adicionales

- [Git Book - Advanced Features](https://git-scm.com/book/en/v2)
- [Git Bisect Documentation](https://git-scm.com/docs/git-bisect)
- [Git Log Advanced Usage](https://git-scm.com/docs/git-log)
- [Git Blame Best Practices](https://www.git-scm.com/docs/git-blame)

---

**Este agente complementa perfectamente el ecosistema de Code Review y Benchmark, proporcionando contexto histórico e investigación profunda cuando se necesita.**

**Versión**: 1.0  
**Última Actualización**: 2025-10-22
