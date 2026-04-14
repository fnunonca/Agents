#!/usr/bin/env python3
"""
.NET Benchmark Scanner - Escanea soluciones .NET para identificar candidatos a benchmarking

Usage:
    scan_solution.py <solution_path> [--version <dotnet_version>] [--threshold <severity>]

Examples:
    scan_solution.py /path/to/MySolution.sln
    scan_solution.py /path/to/MyProject.csproj --version net9.0 --threshold critical
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# =============================================================================
# CONFIGURACIÓN DE PATTERNS
# =============================================================================

@dataclass
class PatternConfig:
    """Configuración de un pattern de detección."""
    name: str
    regex: str
    base_score: int
    hot_path_multiplier: float
    description: str


# Patterns de detección de performance code smells
DETECTION_PATTERNS = [
    # LINQ múltiple iteración
    PatternConfig(
        name="linq_multiple_iteration",
        regex=r'\.(Where|Select|OrderBy|GroupBy|Join|Distinct)\s*\([^)]*\)\s*\.(Where|Select|OrderBy|GroupBy|Join|Distinct|ToList|ToArray|ToDictionary|Count|First|Last|Any|All)',
        base_score=3,
        hot_path_multiplier=1.5,
        description="LINQ con múltiples iteraciones encadenadas"
    ),
    # ToList() innecesario
    PatternConfig(
        name="linq_tolist_unnecessary",
        regex=r'\.ToList\(\)\s*\.(Where|Select|FirstOrDefault|First|Last|LastOrDefault|Any|All|Count)',
        base_score=3,
        hot_path_multiplier=1.5,
        description="ToList() seguido de otra operación LINQ"
    ),
    # String concatenation en loop
    PatternConfig(
        name="string_concat_loop",
        regex=r'(for|foreach|while)\s*\([^)]*\)\s*\{[^}]*\+\s*=\s*[^;]*string|[^}]*\+\s*=\s*["\'][^}]*\}',
        base_score=4,
        hot_path_multiplier=1.5,
        description="Concatenación de strings dentro de loop"
    ),
    # String concat con + en lugar de interpolación (múltiples)
    PatternConfig(
        name="string_concat_multiple",
        regex=r'"[^"]*"\s*\+\s*[^+]+\s*\+\s*"[^"]*"\s*\+',
        base_score=2,
        hot_path_multiplier=1.5,
        description="Múltiples concatenaciones de string con +"
    ),
    # Boxing/Unboxing - conversión a object
    PatternConfig(
        name="boxing_to_object",
        regex=r'\(object\)\s*\w+|\bobject\b\s+\w+\s*=\s*[^;]*\b(int|long|double|float|bool|char|byte|short|decimal)\b',
        base_score=2,
        hot_path_multiplier=1.5,
        description="Boxing: conversión de value type a object"
    ),
    # ArrayList o Hashtable (legacy)
    PatternConfig(
        name="legacy_collections",
        regex=r'\b(ArrayList|Hashtable)\b',
        base_score=3,
        hot_path_multiplier=1.5,
        description="Uso de colecciones legacy sin generics"
    ),
    # new dentro de loop
    PatternConfig(
        name="allocation_in_loop",
        regex=r'(for|foreach|while)\s*\([^)]*\)\s*\{[^}]*\bnew\s+\w+\s*[\[\(][^}]*\}',
        base_score=3,
        hot_path_multiplier=1.5,
        description="Allocación (new) dentro de loop"
    ),
    # Lambda/closure en loop
    PatternConfig(
        name="lambda_in_loop",
        regex=r'(for|foreach|while)\s*\([^)]*\)\s*\{[^}]*=>\s*[^}]*\}',
        base_score=3,
        hot_path_multiplier=1.5,
        description="Lambda/closure capturando variables en loop"
    ),
    # new byte[] repetido (sin ArrayPool)
    PatternConfig(
        name="buffer_allocation",
        regex=r'new\s+byte\s*\[\s*\d+\s*\]',
        base_score=3,
        hot_path_multiplier=1.5,
        description="Allocación de buffer byte[] (considerar ArrayPool)"
    ),
    # List cuando podría ser HashSet (Contains en loop)
    PatternConfig(
        name="list_contains_loop",
        regex=r'(for|foreach|while)[^{]*\{[^}]*List<[^>]+>\s*\w+[^}]*\.Contains\s*\(',
        base_score=2,
        hot_path_multiplier=1.0,
        description="List.Contains en loop (considerar HashSet)"
    ),
    # Parse/Convert frecuente
    PatternConfig(
        name="frequent_parse",
        regex=r'(int|long|double|float|decimal|DateTime)\.(Parse|TryParse)\s*\(',
        base_score=1,
        hot_path_multiplier=1.5,
        description="Parse/TryParse (verificar si es en hot path)"
    ),
    # Regex sin compilar en hot path
    PatternConfig(
        name="regex_not_compiled",
        regex=r'Regex\.(Match|IsMatch|Replace|Split)\s*\([^,]+,\s*[^,]+\)',
        base_score=2,
        hot_path_multiplier=1.5,
        description="Regex sin precompilar"
    ),
    # TODO: optimize marker
    PatternConfig(
        name="todo_optimize",
        regex=r'//\s*(TODO|FIXME):\s*optimi[zs]e',
        base_score=5,
        hot_path_multiplier=2.0,
        description="Marcador TODO: optimize"
    ),
    # PERF: marker
    PatternConfig(
        name="perf_marker",
        regex=r'//\s*PERF:',
        base_score=4,
        hot_path_multiplier=2.0,
        description="Marcador PERF:"
    ),
    # SLOW marker
    PatternConfig(
        name="slow_marker",
        regex=r'//\s*SLOW',
        base_score=4,
        hot_path_multiplier=2.0,
        description="Marcador SLOW"
    ),
    # Obsolete con Performance
    PatternConfig(
        name="obsolete_performance",
        regex=r'\[Obsolete\s*\([^)]*[Pp]erformance[^)]*\)\]',
        base_score=5,
        hot_path_multiplier=2.0,
        description="Atributo [Obsolete] mencionando performance"
    ),
]

# Patterns para identificar hot paths
HOT_PATH_PATTERNS = [
    r'class\s+\w*(Controller|Handler|Processor|Service)\b',  # Clases hot path
    r'\[(HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch|Route)\s*[\(\]]',  # Endpoints HTTP
    r'\basync\s+Task',  # Métodos async
    r'\[ApiController\]',  # API Controllers
]


# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class CodeSmell:
    """Representa un code smell detectado."""
    pattern_name: str
    description: str
    line_number: int
    line_content: str
    base_score: int
    multiplier: float
    final_score: float


@dataclass
class MethodCandidate:
    """Representa un método candidato a benchmark."""
    class_name: str
    method_name: str
    file_path: str
    start_line: int
    end_line: int
    is_hot_path: bool
    code_smells: list = field(default_factory=list)
    total_score: float = 0.0
    method_code: str = ""


@dataclass
class ScanResult:
    """Resultado del escaneo completo."""
    solution_name: str
    solution_path: str
    dotnet_version: str
    scan_date: str
    total_files: int
    total_methods: int
    candidates: list = field(default_factory=list)
    severity_threshold: str = "medium"


# =============================================================================
# FUNCIONES DE ESCANEO
# =============================================================================

def find_cs_files(solution_path: Path) -> list[Path]:
    """Encuentra todos los archivos .cs en la solución."""
    if solution_path.suffix == '.sln':
        search_dir = solution_path.parent
    elif solution_path.suffix == '.csproj':
        search_dir = solution_path.parent
    else:
        search_dir = solution_path

    cs_files = []
    for root, dirs, files in os.walk(search_dir):
        # Excluir directorios comunes
        dirs[:] = [d for d in dirs if d not in ['bin', 'obj', 'node_modules', '.git', 'packages']]
        for file in files:
            if file.endswith('.cs') and not file.endswith('.Designer.cs'):
                cs_files.append(Path(root) / file)

    return cs_files


def is_hot_path_context(content: str, line_number: int, context_lines: int = 50) -> bool:
    """Determina si una línea está en contexto de hot path."""
    lines = content.split('\n')
    start = max(0, line_number - context_lines)
    end = min(len(lines), line_number + context_lines)
    context = '\n'.join(lines[start:end])

    for pattern in HOT_PATH_PATTERNS:
        if re.search(pattern, context, re.IGNORECASE):
            return True
    return False


def extract_methods(content: str) -> list[dict]:
    """Extrae métodos del código fuente."""
    methods = []

    # Pattern para detectar métodos (simplificado pero efectivo)
    method_pattern = r'''
        (?:public|private|protected|internal|static|\s)*  # Modificadores
        (?:async\s+)?                                      # async opcional
        (?:[\w<>\[\],\s]+)\s+                             # Tipo de retorno
        (\w+)\s*                                           # Nombre del método
        \(([^)]*)\)\s*                                    # Parámetros
        (?:where\s+[^{]+)?                                # Constraints genéricos
        \{                                                 # Inicio del cuerpo
    '''

    # Pattern para detectar clases
    class_pattern = r'class\s+(\w+)'

    current_class = "UnknownClass"
    lines = content.split('\n')

    # Encontrar clases
    for i, line in enumerate(lines):
        class_match = re.search(class_pattern, line)
        if class_match:
            current_class = class_match.group(1)

    # Encontrar métodos
    for match in re.finditer(method_pattern, content, re.VERBOSE | re.MULTILINE):
        method_name = match.group(1)
        start_pos = match.start()
        start_line = content[:start_pos].count('\n') + 1

        # Encontrar el final del método (contar llaves)
        brace_count = 1
        end_pos = match.end()
        while brace_count > 0 and end_pos < len(content):
            if content[end_pos] == '{':
                brace_count += 1
            elif content[end_pos] == '}':
                brace_count -= 1
            end_pos += 1

        end_line = content[:end_pos].count('\n') + 1
        method_code = content[match.start():end_pos]

        # Obtener clase del contexto
        class_context = content[:match.start()]
        class_matches = list(re.finditer(class_pattern, class_context))
        if class_matches:
            current_class = class_matches[-1].group(1)

        methods.append({
            'class_name': current_class,
            'method_name': method_name,
            'start_line': start_line,
            'end_line': end_line,
            'method_code': method_code
        })

    return methods


def detect_code_smells(content: str, method_info: dict, is_hot_path: bool) -> list[CodeSmell]:
    """Detecta code smells en un método."""
    smells = []
    method_code = method_info['method_code']
    method_start = method_info['start_line']

    for pattern in DETECTION_PATTERNS:
        for match in re.finditer(pattern.regex, method_code, re.IGNORECASE | re.DOTALL):
            # Calcular línea relativa al método
            relative_line = method_code[:match.start()].count('\n')
            absolute_line = method_start + relative_line

            # Obtener línea de código
            lines = method_code.split('\n')
            line_content = lines[relative_line].strip() if relative_line < len(lines) else ""

            multiplier = pattern.hot_path_multiplier if is_hot_path else 1.0
            final_score = pattern.base_score * multiplier

            smell = CodeSmell(
                pattern_name=pattern.name,
                description=pattern.description,
                line_number=absolute_line,
                line_content=line_content[:100],  # Truncar líneas largas
                base_score=pattern.base_score,
                multiplier=multiplier,
                final_score=final_score
            )
            smells.append(smell)

    return smells


def scan_file(file_path: Path) -> list[MethodCandidate]:
    """Escanea un archivo .cs y retorna candidatos."""
    candidates = []

    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return candidates

    methods = extract_methods(content)

    for method_info in methods:
        is_hot = is_hot_path_context(content, method_info['start_line'])
        smells = detect_code_smells(content, method_info, is_hot)

        if smells:
            total_score = sum(s.final_score for s in smells)

            candidate = MethodCandidate(
                class_name=method_info['class_name'],
                method_name=method_info['method_name'],
                file_path=str(file_path),
                start_line=method_info['start_line'],
                end_line=method_info['end_line'],
                is_hot_path=is_hot,
                code_smells=[asdict(s) for s in smells],
                total_score=total_score,
                method_code=method_info['method_code']
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


def get_threshold_score(threshold: str) -> float:
    """Obtiene el puntaje mínimo para un umbral."""
    thresholds = {
        "critical": 15,
        "high": 10,
        "medium": 6,
        "low": 3
    }
    return thresholds.get(threshold.lower(), 6)


def scan_solution(solution_path: Path, dotnet_version: str, threshold: str) -> ScanResult:
    """Escanea una solución completa."""
    solution_name = solution_path.stem
    cs_files = find_cs_files(solution_path)

    print(f"Escaneando {len(cs_files)} archivos .cs...", file=sys.stderr)

    all_candidates = []
    total_methods = 0
    threshold_score = get_threshold_score(threshold)

    for file_path in cs_files:
        candidates = scan_file(file_path)
        total_methods += len(candidates)

        # Filtrar por umbral
        filtered = [c for c in candidates if c.total_score >= threshold_score]
        all_candidates.extend(filtered)

    # Ordenar por puntaje descendente
    all_candidates.sort(key=lambda x: x.total_score, reverse=True)

    result = ScanResult(
        solution_name=solution_name,
        solution_path=str(solution_path),
        dotnet_version=dotnet_version,
        scan_date=datetime.now().isoformat(),
        total_files=len(cs_files),
        total_methods=total_methods,
        candidates=[asdict(c) for c in all_candidates],
        severity_threshold=threshold
    )

    return result


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='.NET Benchmark Scanner - Identifica métodos candidatos a benchmarking'
    )
    parser.add_argument('solution_path', help='Ruta a archivo .sln o .csproj')
    parser.add_argument('--version', default='net8.0', help='Versión de .NET (default: net8.0)')
    parser.add_argument('--threshold', default='medium',
                       choices=['critical', 'high', 'medium', 'low'],
                       help='Umbral de severidad (default: medium)')
    parser.add_argument('--output', '-o', help='Archivo de salida JSON (default: stdout)')

    args = parser.parse_args()

    solution_path = Path(args.solution_path)

    if not solution_path.exists():
        print(f"Error: No se encontró {solution_path}", file=sys.stderr)
        sys.exit(1)

    if solution_path.suffix not in ['.sln', '.csproj']:
        print(f"Error: Se esperaba un archivo .sln o .csproj", file=sys.stderr)
        sys.exit(1)

    print(f"Iniciando escaneo de: {solution_path}", file=sys.stderr)
    print(f"Versión .NET: {args.version}", file=sys.stderr)
    print(f"Umbral: {args.threshold}", file=sys.stderr)

    result = scan_solution(solution_path, args.version, args.threshold)

    print(f"\nResultados:", file=sys.stderr)
    print(f"  - Archivos escaneados: {result.total_files}", file=sys.stderr)
    print(f"  - Métodos analizados: {result.total_methods}", file=sys.stderr)
    print(f"  - Candidatos encontrados: {len(result.candidates)}", file=sys.stderr)

    # Generar JSON
    output_json = json.dumps(asdict(result), indent=2, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output_json, encoding='utf-8')
        print(f"\nResultados guardados en: {args.output}", file=sys.stderr)
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    sys.exit(main())
