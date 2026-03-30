#!/usr/bin/env python3
"""
.NET Benchmark Orchestrator - Orquesta el flujo completo de scanner + benchmark-analyzer

Coordina el proceso de:
1. Escanear solución con scan_solution.py
2. Presentar candidatos al usuario (modo interactivo) o seleccionar automáticamente (modo batch)
3. Extraer código de métodos seleccionados
4. Generar archivos YAML con parámetros para benchmark-analyzer
5. Opcionalmente ejecutar benchmarks
6. Generar reporte consolidado

Usage:
    orchestrate_benchmark.py <solution_path> [options]

Examples:
    # Modo interactivo (default)
    orchestrate_benchmark.py /path/to/MySolution.sln

    # Modo batch (CI/CD)
    orchestrate_benchmark.py /path/to/MySolution.sln --batch --threshold critical

    # Solo generar YAMLs sin ejecutar benchmarks
    orchestrate_benchmark.py /path/to/MySolution.sln --no-execute
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


# =============================================================================
# CONFIGURACIÓN
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
SCANNER_SCRIPT = SCRIPT_DIR / "scan_solution.py"
DEFAULT_PARAMS_DIR = "benchmark_params"
DEFAULT_BENCHMARK_DIR = "benchmark"

# Colores ANSI para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def supports_color() -> bool:
    """Detecta si la terminal soporta colores."""
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

def color(text: str, color_code: str) -> str:
    """Aplica color si la terminal lo soporta."""
    if supports_color():
        return f"{color_code}{text}{Colors.ENDC}"
    return text


# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class Candidate:
    """Candidato a benchmark."""
    rank: int
    class_name: str
    method_name: str
    file_path: str
    start_line: int
    end_line: int
    score: float
    severity: str
    is_hot_path: bool
    code_smells: list
    method_code: str = ""


@dataclass
class BenchmarkParams:
    """Parámetros para invocar benchmark-analyzer."""
    dotnet_version: str
    method_name: str
    method_file: str
    method_lines: str
    method_code: str
    method_context: str
    focus_area: str = "both"
    baseline_exists: bool = False


@dataclass
class OrchestratorResult:
    """Resultado del orquestador."""
    solution_name: str
    scan_date: str
    candidates_total: int
    candidates_selected: int
    yaml_files_generated: list = field(default_factory=list)
    benchmark_reports: list = field(default_factory=list)
    summary_file: str = ""


# =============================================================================
# FUNCIONES DE ESCANEO
# =============================================================================

def run_scanner(solution_path: Path, dotnet_version: str, threshold: str) -> dict:
    """Ejecuta el scanner y retorna los resultados como dict."""
    cmd = [
        sys.executable,
        str(SCANNER_SCRIPT),
        str(solution_path),
        "--version", dotnet_version,
        "--threshold", threshold
    ]

    print(f"\n{color('🔍 Escaneando solución...', Colors.CYAN)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"{color('Error ejecutando scanner:', Colors.RED)} {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"{color('Error parseando JSON del scanner:', Colors.RED)} {e}", file=sys.stderr)
        sys.exit(1)


def parse_candidates(scan_result: dict) -> list[Candidate]:
    """Convierte resultados del scanner a lista de Candidate."""
    candidates = []

    for i, c in enumerate(scan_result.get("candidates", []), 1):
        severity = get_severity(c.get("total_score", 0))

        candidate = Candidate(
            rank=i,
            class_name=c.get("class_name", "Unknown"),
            method_name=c.get("method_name", "Unknown"),
            file_path=c.get("file_path", ""),
            start_line=c.get("start_line", 0),
            end_line=c.get("end_line", 0),
            score=c.get("total_score", 0),
            severity=severity,
            is_hot_path=c.get("is_hot_path", False),
            code_smells=c.get("code_smells", []),
            method_code=c.get("method_code", "")
        )
        candidates.append(candidate)

    return candidates


def get_severity(score: float) -> str:
    """Determina la severidad basada en el puntaje."""
    if score >= 15:
        return "CRITICAL"
    elif score >= 10:
        return "HIGH"
    elif score >= 6:
        return "MEDIUM"
    else:
        return "LOW"


# =============================================================================
# PRESENTACIÓN DE CANDIDATOS
# =============================================================================

def print_candidates_table(candidates: list[Candidate]) -> None:
    """Muestra tabla de candidatos en terminal."""
    if not candidates:
        print(f"\n{color('No se encontraron candidatos.', Colors.YELLOW)}")
        return

    # Calcular anchos de columna
    max_method = max(len(f"{c.class_name}.{c.method_name}") for c in candidates)
    max_method = min(max_method, 45)  # Limitar ancho

    # Header
    header = f"{'#':>3} │ {'Método':<{max_method}} │ {'Score':>6} │ {'Severidad':^10} │ {'Hot Path':^9}"
    separator = "─" * (len(header) + 5)

    print(f"\n{separator}")
    print(f" {color(header, Colors.BOLD)}")
    print(f"{separator}")

    # Filas
    for c in candidates:
        method_name = f"{c.class_name}.{c.method_name}"
        if len(method_name) > max_method:
            method_name = method_name[:max_method-3] + "..."

        # Color por severidad
        if c.severity == "CRITICAL":
            sev_color = Colors.RED
        elif c.severity == "HIGH":
            sev_color = Colors.YELLOW
        elif c.severity == "MEDIUM":
            sev_color = Colors.CYAN
        else:
            sev_color = Colors.DIM

        hot = color("✓", Colors.GREEN) if c.is_hot_path else " "
        severity_str = color(f"{c.severity:^10}", sev_color)

        print(f" {c.rank:>3} │ {method_name:<{max_method}} │ {c.score:>6.1f} │ {severity_str} │ {hot:^9}")

    print(f"{separator}\n")


def print_summary(scan_result: dict) -> None:
    """Muestra resumen del escaneo."""
    total_files = scan_result.get("total_files", 0)
    total_methods = scan_result.get("total_methods", 0)
    candidates = len(scan_result.get("candidates", []))

    print(f"   Archivos: {color(str(total_files), Colors.CYAN)} | "
          f"Métodos: {color(str(total_methods), Colors.CYAN)} | "
          f"Candidatos: {color(str(candidates), Colors.GREEN)}")


# =============================================================================
# SELECCIÓN DE CANDIDATOS
# =============================================================================

def select_candidates_interactive(candidates: list[Candidate]) -> list[Candidate]:
    """Permite al usuario seleccionar candidatos interactivamente."""
    if not candidates:
        return []

    print(f"Selecciona candidatos para benchmark:")
    print(f"  - Números separados por coma (ej: {color('1,2,3', Colors.CYAN)})")
    print(f"  - {color('critical', Colors.CYAN)} para todos los CRITICAL")
    print(f"  - {color('high', Colors.CYAN)} para CRITICAL + HIGH")
    print(f"  - {color('all', Colors.CYAN)} para todos")
    print(f"  - {color('q', Colors.CYAN)} para cancelar")

    while True:
        try:
            user_input = input(f"\n{color('>', Colors.GREEN)} ").strip().lower()

            if user_input == 'q':
                print("Cancelado.")
                return []

            if user_input == 'all':
                return candidates

            if user_input == 'critical':
                return [c for c in candidates if c.severity == "CRITICAL"]

            if user_input == 'high':
                return [c for c in candidates if c.severity in ["CRITICAL", "HIGH"]]

            # Parse numbers
            indices = []
            for part in user_input.split(','):
                part = part.strip()
                if part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(candidates):
                        indices.append(idx)
                    else:
                        print(f"{color('Índice fuera de rango:', Colors.YELLOW)} {idx}")

            if indices:
                return [c for c in candidates if c.rank in indices]

            print(f"{color('Entrada no válida. Intenta de nuevo.', Colors.YELLOW)}")

        except EOFError:
            print("\nCancelado.")
            return []
        except KeyboardInterrupt:
            print("\nCancelado.")
            return []


def select_candidates_batch(candidates: list[Candidate], threshold: str) -> list[Candidate]:
    """Selecciona candidatos automáticamente según umbral."""
    if threshold == "critical":
        return [c for c in candidates if c.severity == "CRITICAL"]
    elif threshold == "high":
        return [c for c in candidates if c.severity in ["CRITICAL", "HIGH"]]
    elif threshold == "medium":
        return [c for c in candidates if c.severity in ["CRITICAL", "HIGH", "MEDIUM"]]
    else:
        return candidates


# =============================================================================
# EXTRACCIÓN DE CÓDIGO
# =============================================================================

def extract_method_code(file_path: str, start_line: int, end_line: int) -> str:
    """Extrae el código del método del archivo fuente."""
    try:
        path = Path(file_path)
        if not path.exists():
            return f"// Error: Archivo no encontrado: {file_path}"

        content = path.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')

        # Ajustar índices (1-based a 0-based)
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line)

        return '\n'.join(lines[start_idx:end_idx])

    except Exception as e:
        return f"// Error extrayendo código: {e}"


def generate_method_context(candidate: Candidate) -> str:
    """Genera contexto del método basado en el análisis."""
    context_parts = []

    # Hot path info
    if candidate.is_hot_path:
        context_parts.append("Hot path detectado (Service/Controller/Handler con async)")

    # Code smells summary
    smells_by_type = {}
    for smell in candidate.code_smells:
        name = smell.get("pattern_name", "unknown")
        smells_by_type[name] = smells_by_type.get(name, 0) + 1

    if smells_by_type:
        smell_summary = ", ".join(f"{name} (x{count})" if count > 1 else name
                                   for name, count in smells_by_type.items())
        context_parts.append(f"Code smells: {smell_summary}")

    context_parts.append(f"Score: {candidate.score:.1f} ({candidate.severity})")

    return "\n".join(context_parts)


# =============================================================================
# GENERACIÓN DE YAML
# =============================================================================

def generate_yaml_params(candidate: Candidate, dotnet_version: str, output_dir: Path) -> Path:
    """Genera archivo YAML con parámetros para benchmark-analyzer."""
    # Extraer código si no está disponible
    method_code = candidate.method_code
    if not method_code or len(method_code) < 10:
        method_code = extract_method_code(
            candidate.file_path,
            candidate.start_line,
            candidate.end_line
        )

    # Generar contexto
    context = generate_method_context(candidate)

    # Crear nombre de archivo seguro
    safe_name = re.sub(r'[^\w\-_]', '_', f"{candidate.class_name}_{candidate.method_name}")
    yaml_path = output_dir / f"{safe_name}.yaml"

    # Generar contenido YAML (sin usar biblioteca externa)
    content = f'''# Parámetros para benchmark-analyzer sub-agente
# Generado por: orchestrate_benchmark.py
# Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Candidato: #{candidate.rank} (Score: {candidate.score:.1f} - {candidate.severity})

dotnet_version: "{dotnet_version}"
method_name: "{candidate.class_name}.{candidate.method_name}"
method_file: "{candidate.file_path}"
method_lines: "{candidate.start_line}-{candidate.end_line}"
method_code: |
{indent_code(method_code, 2)}

method_context: |
{indent_code(context, 2)}

focus_area: "both"
baseline_exists: false

# ─────────────────────────────────────────────────────────────────────
# Para invocar el benchmark-analyzer, usa estos parámetros con Claude:
#
# "Ejecuta el benchmark-analyzer con los parámetros del archivo:
#  {yaml_path.name}"
#
# O copia los parámetros directamente en tu prompt al sub-agente.
# ─────────────────────────────────────────────────────────────────────
'''

    output_dir.mkdir(parents=True, exist_ok=True)
    yaml_path.write_text(content, encoding='utf-8')

    return yaml_path


def indent_code(code: str, spaces: int) -> str:
    """Indenta código para YAML."""
    prefix = " " * spaces
    lines = code.split('\n')
    return '\n'.join(prefix + line for line in lines)


# =============================================================================
# REPORTE CONSOLIDADO
# =============================================================================

def generate_summary_report(
    scan_result: dict,
    selected_candidates: list[Candidate],
    yaml_files: list[Path],
    output_path: Path
) -> None:
    """Genera reporte consolidado de la orquestación."""

    solution_name = scan_result.get("solution_name", "Unknown")
    scan_date = datetime.now().strftime("%Y-%m-%d")

    content = f'''# Benchmark Orchestration Summary: {solution_name}

**Fecha**: {scan_date}
**Framework**: {scan_result.get("dotnet_version", "net8.0")}
**Umbral**: {scan_result.get("severity_threshold", "medium")}

---

## Resumen del Escaneo

| Métrica | Valor |
|---------|-------|
| Archivos escaneados | {scan_result.get("total_files", 0)} |
| Métodos analizados | {scan_result.get("total_methods", 0)} |
| Candidatos encontrados | {len(scan_result.get("candidates", []))} |
| Candidatos seleccionados | {len(selected_candidates)} |

---

## Candidatos Seleccionados para Benchmark

| # | Método | Score | Severidad | Hot Path | YAML |
|---|--------|-------|-----------|----------|------|
'''

    for i, (c, yaml_file) in enumerate(zip(selected_candidates, yaml_files), 1):
        hot = "✓" if c.is_hot_path else ""
        yaml_name = yaml_file.name if yaml_file else "-"
        content += f"| {i} | {c.class_name}.{c.method_name} | {c.score:.1f} | {c.severity} | {hot} | `{yaml_name}` |\n"

    content += f'''
---

## Archivos YAML Generados

Los siguientes archivos contienen los parámetros para invocar el benchmark-analyzer:

```
{DEFAULT_PARAMS_DIR}/
'''

    for yaml_file in yaml_files:
        content += f"├── {yaml_file.name}\n"

    content += f'''```

---

## Próximos Pasos

1. **Revisar los archivos YAML** en `{DEFAULT_PARAMS_DIR}/`
2. **Para cada candidato**, invocar el benchmark-analyzer:
   ```
   "Ejecuta el benchmark-analyzer con los parámetros de benchmark_params/[archivo].yaml"
   ```
3. **Revisar reportes de benchmark** generados en `{DEFAULT_BENCHMARK_DIR}/`
4. **Implementar optimizaciones** según recomendaciones

---

## Invocación Rápida

Para ejecutar benchmark en todos los candidatos seleccionados:

'''

    for yaml_file in yaml_files:
        content += f'- `{yaml_file.name}`\n'

    content += f'''
---

**Generado por**: orchestrate_benchmark.py
**Versión**: 1.0
'''

    output_path.write_text(content, encoding='utf-8')


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Orquesta el flujo de scanner + benchmark-analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
  %(prog)s /path/to/Solution.sln                    # Modo interactivo
  %(prog)s /path/to/Solution.sln --batch            # Auto-selecciona CRITICAL
  %(prog)s /path/to/Solution.sln --batch --threshold high
  %(prog)s /path/to/Solution.sln --no-execute       # Solo genera YAMLs
        '''
    )

    parser.add_argument('solution_path', help='Ruta a archivo .sln o .csproj')
    parser.add_argument('--version', default='net8.0',
                        help='Versión de .NET (default: net8.0)')
    parser.add_argument('--threshold', default='medium',
                        choices=['critical', 'high', 'medium', 'low'],
                        help='Umbral de severidad para escaneo (default: medium)')
    parser.add_argument('--batch', action='store_true',
                        help='Modo batch: selecciona automáticamente según threshold')
    parser.add_argument('--select-threshold', default='critical',
                        choices=['critical', 'high', 'medium', 'low'],
                        help='Umbral para auto-selección en modo batch (default: critical)')
    parser.add_argument('--output-dir', type=Path, default=None,
                        help='Directorio de salida (default: directorio de la solución)')
    parser.add_argument('--no-execute', action='store_true',
                        help='Solo generar YAMLs, no ejecutar benchmarks')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Modo silencioso (menos output)')

    args = parser.parse_args()

    solution_path = Path(args.solution_path)

    # Validar entrada
    if not solution_path.exists():
        print(f"{color('Error:', Colors.RED)} No se encontró {solution_path}", file=sys.stderr)
        sys.exit(1)

    if solution_path.suffix not in ['.sln', '.csproj']:
        print(f"{color('Error:', Colors.RED)} Se esperaba un archivo .sln o .csproj", file=sys.stderr)
        sys.exit(1)

    # Configurar directorio de salida
    output_dir = args.output_dir or solution_path.parent
    params_dir = output_dir / DEFAULT_PARAMS_DIR

    # Banner
    if not args.quiet:
        print(f"\n{color('═' * 60, Colors.CYAN)}")
        print(f"{color('  .NET Benchmark Orchestrator', Colors.BOLD)}")
        print(f"{color('═' * 60, Colors.CYAN)}")
        print(f"\n  Solución: {color(str(solution_path), Colors.GREEN)}")
        print(f"  Versión:  {args.version}")
        print(f"  Umbral:   {args.threshold}")
        print(f"  Modo:     {'Batch' if args.batch else 'Interactivo'}")

    # Fase 1: Escanear
    scan_result = run_scanner(solution_path, args.version, args.threshold)

    if not args.quiet:
        print_summary(scan_result)

    candidates = parse_candidates(scan_result)

    if not candidates:
        print(f"\n{color('No se encontraron candidatos con el umbral especificado.', Colors.YELLOW)}")
        print(f"Intenta con --threshold low para ver más candidatos.")
        sys.exit(0)

    # Mostrar tabla
    if not args.quiet:
        print_candidates_table(candidates)

    # Fase 2: Selección
    if args.batch:
        selected = select_candidates_batch(candidates, args.select_threshold)
        if not args.quiet:
            print(f"\n{color('Modo batch:', Colors.CYAN)} Seleccionados {len(selected)} candidatos ({args.select_threshold})")
    else:
        selected = select_candidates_interactive(candidates)

    if not selected:
        print(f"\n{color('No se seleccionaron candidatos.', Colors.YELLOW)}")
        sys.exit(0)

    # Fase 3: Generar YAMLs
    print(f"\n{color('📦 Preparando benchmarks...', Colors.CYAN)}")

    yaml_files = []
    for i, candidate in enumerate(selected, 1):
        print(f"\n[{i}/{len(selected)}] {color(f'{candidate.class_name}.{candidate.method_name}', Colors.GREEN)}")
        print(f"  {color('✓', Colors.GREEN)} Código extraído: {candidate.file_path}:{candidate.start_line}-{candidate.end_line}")

        context = generate_method_context(candidate)
        print(f"  {color('✓', Colors.GREEN)} Contexto generado: {context.split(chr(10))[0][:50]}...")

        yaml_path = generate_yaml_params(candidate, args.version, params_dir)
        yaml_files.append(yaml_path)
        print(f"  {color('✓', Colors.GREEN)} YAML guardado: {yaml_path.relative_to(output_dir)}")

    # Fase 4: Generar reporte consolidado
    summary_path = output_dir / f"BENCHMARK_ORCHESTRATION_{datetime.now().strftime('%Y%m%d')}.md"
    generate_summary_report(scan_result, selected, yaml_files, summary_path)

    # Resumen final
    print(f"\n{color('═' * 60, Colors.GREEN)}")
    print(f"{color('✅ Completado', Colors.GREEN)}")
    print(f"{color('═' * 60, Colors.GREEN)}")
    print(f"\n  Candidatos preparados: {color(str(len(selected)), Colors.CYAN)}")
    print(f"  Archivos YAML: {color(str(params_dir), Colors.CYAN)}/")
    print(f"  Reporte: {color(str(summary_path.name), Colors.CYAN)}")

    print(f"\n{color('Próximos pasos:', Colors.BOLD)}")
    print(f"  1. Revisa los archivos YAML en {params_dir}/")
    print(f"  2. Invoca el benchmark-analyzer con cada archivo:")
    print(f"     \"Ejecuta benchmark-analyzer con benchmark_params/[archivo].yaml\"")
    print(f"  3. Los reportes se generarán en benchmark/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
