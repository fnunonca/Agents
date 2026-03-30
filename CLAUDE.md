# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Personal collection of AI agents and Claude Code skills used in day-to-day development. Currently focused on .NET 8/9/10 (C# 12/13/14) workflows: automated code review, performance benchmarking, and git history investigation. Also includes skills for benchmark scanning, PDF processing, skill creation, and documentation research. All agent prompts and output are in Spanish.

## Prerequisites

- Python 3.8+
- .NET SDK 8.0+ (for running benchmarks)
- Claude Code (VS Code extension or CLI)

## Key Commands

### Scan a .NET solution for performance candidates
```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /path/to/Solution.sln
```

### Scanner only (no orchestration)
```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/scan_solution.py /path/to/Solution.sln --threshold medium
```

### Batch mode (CI/CD)
```bash
python3 .claude/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /path/to/Solution.sln --batch --threshold critical
```

### Create a new skill
```bash
python3 .claude/skills/skill-creator/scripts/init_skill.py
```

### Package a skill for distribution
```bash
python3 .claude/skills/skill-creator/scripts/package_skill.py /path/to/skill-dir
```

## Agent Prompts

### Code Review Agent (`dotnet-code-review-agent-prompt.md`)
Main orchestrator for comprehensive .NET code reviews. Analyzes security (SQL injection, auth, secrets), performance (N+1 queries, async patterns), architecture (SOLID), and testing quality. Supports .NET 8 (LTS), .NET 9 (STS), and .NET 10 (LTS) with C# 12/13/14.

**Outputs**: `CODE_REVIEW_[CommitSHA]_[Date].md`

### Benchmark Analyzer (`benchmark-analyzer-subagent-prompt.md`)
Sub-agent for BenchmarkDotNet performance testing. Creates benchmark projects, generates 2-4 optimization variants (Span-based, ArrayPool, ValueTask, struct-based, SIMD, etc.), and produces detailed comparison reports.

**Outputs**: `BENCHMARK_REPORT.md` in `benchmark/Benchmark_[MethodName]_[Timestamp]/`

### Git History Investigator (`git-history-investigator-agent-prompt.md`)
Agent for code archaeology: bug introduction finding (git bisect), blame analysis, code evolution tracking, deleted code recovery, and impact analysis.

**Investigation types**: `bug_finder`, `blame_analysis`, `code_evolution`, `deleted_code`, `author_analysis`, `impact_analysis`, `related_commits`

## Skills (`.claude/skills/`)

- **dotnet-benchmark-scanner** — Scans .NET solutions for performance code smells (LINQ abuse, string concat in loops, boxing, unnecessary allocations). Uses regex-based pattern detection with a scoring system and severity thresholds (Critical >= 15, High >= 10, Medium >= 6, Low >= 3).
- **skill-creator** — Meta-skill for creating new Claude Code skills with proper structure (SKILL.md + scripts/references/assets).
- **pdf-processing-pro** — Production PDF processing: forms, tables, OCR (Tesseract), batch operations.
- **context7-auto-research** — Auto-fetches latest library/framework documentation via Context7 API.

## Sub-Agent Definition

`.claude/agents/dotnet-benchmark-analyzer.md` — Defines the benchmark analyzer as a Claude Code sub-agent (model: sonnet, memory: project-persistent). Invoked automatically by the code review agent or manually for standalone benchmarking.

## Prompt Structure

All agents use a consistent YAML parameter specification format:

```yaml
# Required parameters
parameter_name: type           # Description

# Optional parameters
optional_param: type [opcional] # Description with default
```

When modifying prompts:
- Maintain the YAML parameter format in the "Parámetros de Entrada" section
- Preserve the markdown report templates with their emoji conventions
- Keep the checklist structures (using `- [ ]` format)
- Update version info at the bottom when making significant changes
- All documentation and agent output is in Spanish

## Agent Integration

The agents work as a system:
- **Code Review → Benchmark**: Code Review invokes Benchmark Analyzer when detecting performance-critical methods (configurable via `benchmark_threshold`)
- **Code Review → Git Investigator**: Provides historical context for review findings
- **Benchmark Scanner → Benchmark Analyzer**: Scanner generates YAML param files in `benchmark_params/` that feed into the analyzer
- **Configuration files**: `.code-review-config.yml`, `.git-investigator-config.yml`
