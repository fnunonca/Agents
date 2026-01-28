# Benchmark Candidates Report: {{SOLUTION_NAME}}

**Fecha de Escaneo**: {{SCAN_DATE}}
**Framework Target**: {{DOTNET_VERSION}}
**Umbral de Severidad**: {{SEVERITY_THRESHOLD}}

---

## Resumen Ejecutivo

| Métrica | Valor |
|---------|-------|
| Total archivos escaneados | {{TOTAL_FILES}} |
| Métodos analizados | {{TOTAL_METHODS}} |
| Candidatos identificados | {{TOTAL_CANDIDATES}} |
| Candidatos CRITICAL | {{CRITICAL_COUNT}} |
| Candidatos HIGH | {{HIGH_COUNT}} |
| Candidatos MEDIUM | {{MEDIUM_COUNT}} |
| Candidatos LOW | {{LOW_COUNT}} |

### Distribución por Severidad

```
CRITICAL: {{CRITICAL_BAR}}
HIGH:     {{HIGH_BAR}}
MEDIUM:   {{MEDIUM_BAR}}
LOW:      {{LOW_BAR}}
```

---

## Top Candidatos para Benchmark

{{#CANDIDATES}}
### {{RANK}}. {{CLASS_NAME}}.{{METHOD_NAME}} (Score: {{SCORE}} - {{SEVERITY}})

**Archivo**: `{{FILE_PATH}}:{{START_LINE}}`
**Hot Path**: {{IS_HOT_PATH}}

#### Code Smells Detectados

| Pattern | Descripción | Línea | Puntos |
|---------|-------------|-------|--------|
{{#CODE_SMELLS}}
| {{PATTERN_NAME}} | {{DESCRIPTION}} | {{LINE_NUMBER}} | {{FINAL_SCORE}} |
{{/CODE_SMELLS}}

#### Fragmento de Código

```csharp
{{METHOD_CODE_PREVIEW}}
```

#### Comando para Invocar Benchmark Analyzer

```yaml
# Parámetros para benchmark-analyzer sub-agente
dotnet_version: "{{DOTNET_VERSION}}"
method_name: "{{CLASS_NAME}}.{{METHOD_NAME}}"
method_context: "{{METHOD_CONTEXT}}"
focus_area: "both"
baseline_exists: false

# El method_code debe extraerse del archivo:
# {{FILE_PATH}} líneas {{START_LINE}}-{{END_LINE}}
```

**Invocación Manual**:
```bash
# Extraer método y enviarlo al benchmark-analyzer
# Ver benchmark-analyzer-subagent-prompt.md para detalles
```

---

{{/CANDIDATES}}

## Métodos por Archivo

{{#FILES_SUMMARY}}
### {{FILE_PATH}}

| Método | Score | Severidad | Issues |
|--------|-------|-----------|--------|
{{#METHODS}}
| {{METHOD_NAME}} | {{SCORE}} | {{SEVERITY}} | {{ISSUES_COUNT}} |
{{/METHODS}}

{{/FILES_SUMMARY}}

---

## Resumen de Patterns Detectados

| Pattern | Ocurrencias | Impacto Total |
|---------|-------------|---------------|
{{#PATTERN_SUMMARY}}
| {{PATTERN_NAME}} | {{COUNT}} | {{TOTAL_SCORE}} |
{{/PATTERN_SUMMARY}}

---

## Recomendaciones

### Acciones Inmediatas (CRITICAL)

{{#CRITICAL_RECOMMENDATIONS}}
1. **{{METHOD_NAME}}**: {{RECOMMENDATION}}
{{/CRITICAL_RECOMMENDATIONS}}

### Acciones a Corto Plazo (HIGH)

{{#HIGH_RECOMMENDATIONS}}
1. **{{METHOD_NAME}}**: {{RECOMMENDATION}}
{{/HIGH_RECOMMENDATIONS}}

### Consideraciones (MEDIUM/LOW)

Los métodos con severidad MEDIUM y LOW deben evaluarse según:
- Frecuencia de ejecución real en producción
- Impacto en la experiencia del usuario
- Esfuerzo de optimización vs beneficio

---

## Próximos Pasos

1. **Revisar candidatos CRITICAL y HIGH** - Estos tienen mayor probabilidad de impacto real
2. **Ejecutar benchmark-analyzer** en los top 3-5 candidatos
3. **Validar con profiling de producción** - Confirmar que los hot paths teóricos son reales
4. **Implementar optimizaciones** - Basándose en resultados de benchmark

---

## Notas

- Los puntajes son indicativos y deben validarse con profiling real
- Algunos patterns pueden ser false positives (ver `references/detection_patterns.md`)
- Los multiplicadores de hot path se aplican basándose en heurísticas, no en datos reales de tráfico

---

**Generado por**: dotnet-benchmark-scanner skill
**Versión**: 1.0
