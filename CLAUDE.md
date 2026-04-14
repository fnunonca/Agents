# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

`fernando-agents` — a **Claude Code plugin marketplace** that distributes a personal collection of agents and skills for .NET 8/9/10 (C# 12/13/14) development workflows: automated code review, performance benchmarking, git history investigation, and benchmark scanning. All agent prompts and output are in Spanish.

Users consume this repo via:
```
/plugin marketplace add github.com/<user>/Agents
/plugin install <plugin-name>@fernando-agents
```

## Prerequisites

- Claude Code (VS Code extension or CLI)
- Python 3.8+ (for skills that use scripts)
- .NET SDK 8.0+ (only when running benchmarks)

## Repository Layout

```
.claude-plugin/marketplace.json      # Marketplace catalog (4 plugins)
plugins/
├── dotnet-code-review/              # Agent plugin
├── dotnet-benchmark-analyzer/       # Agent plugin (sub-agent)
├── git-history-investigator/        # Agent plugin
└── dotnet-benchmark-scanner/        # Skill plugin
```

Each plugin follows the standard Claude Code layout:
- `plugins/<name>/.claude-plugin/plugin.json` — plugin manifest
- `plugins/<name>/agents/*.md` — agent prompts with YAML frontmatter (for agent plugins)
- `plugins/<name>/skills/<name>/SKILL.md` — skill definition (for skill plugins)

## Key Commands (running scripts directly from this repo)

### Scan a .NET solution for performance candidates
```bash
python3 plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /path/to/Solution.sln
```

### Scanner only (no orchestration)
```bash
python3 plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/scripts/scan_solution.py /path/to/Solution.sln --threshold medium
```

### Batch mode (CI/CD)
```bash
python3 plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /path/to/Solution.sln --batch --threshold critical
```

## Agent Plugins

### dotnet-code-review (`plugins/dotnet-code-review/agents/code-reviewer.md`)
Main orchestrator for comprehensive .NET code reviews. Analyzes security (SQL injection, auth, secrets), performance (N+1 queries, async patterns), architecture (SOLID), and testing quality. Supports .NET 8 (LTS), .NET 9 (STS), and .NET 10 (LTS) with C# 12/13/14.

**Outputs**: `CODE_REVIEW_[CommitSHA]_[Date].md`

### dotnet-benchmark-analyzer (`plugins/dotnet-benchmark-analyzer/agents/benchmark-analyzer.md`)
Sub-agent for BenchmarkDotNet performance testing. Creates benchmark projects, generates 2-4 optimization variants (Span-based, ArrayPool, ValueTask, struct-based, SIMD, etc.), and produces detailed comparison reports.

**Outputs**: `BENCHMARK_REPORT.md` in `benchmark/Benchmark_[MethodName]_[Timestamp]/`

### git-history-investigator (`plugins/git-history-investigator/agents/git-investigator.md`)
Agent for code archaeology: bug introduction finding (git bisect), blame analysis, code evolution tracking, deleted code recovery, and impact analysis.

**Investigation types**: `bug_finder`, `blame_analysis`, `code_evolution`, `deleted_code`, `author_analysis`, `impact_analysis`, `related_commits`

## Skill Plugins

- **dotnet-benchmark-scanner** — Scans .NET solutions for performance code smells (LINQ abuse, string concat in loops, boxing, unnecessary allocations). Uses regex-based pattern detection with a scoring system and severity thresholds (Critical >= 15, High >= 10, Medium >= 6, Low >= 3).

## Prompt Structure

All agents use a consistent YAML parameter specification format inside the prompt body:

```yaml
# Required parameters
parameter_name: type           # Description

# Optional parameters
optional_param: type [opcional] # Description with default
```

When modifying prompts:
- Keep YAML frontmatter at the top of every agent `.md` file (`name`, `description`, `model`, `color`)
- Maintain the YAML parameter format in the "Parámetros de Entrada" section
- Preserve the markdown report templates with their emoji conventions
- Keep the checklist structures (using `- [ ]` format)
- All documentation and agent output is in Spanish

## Agent Integration

The agents work as a system:
- **Code Review → Benchmark**: `dotnet-code-review` invokes `dotnet-benchmark-analyzer` when detecting performance-critical methods (configurable via `benchmark_threshold`)
- **Code Review → Git Investigator**: Provides historical context for review findings
- **Benchmark Scanner → Benchmark Analyzer**: Scanner generates YAML param files in `benchmark_params/` that feed into the analyzer
- **Configuration files**: `.code-review-config.yml`, `.git-investigator-config.yml`

## Adding a new plugin

1. Create `plugins/<name>/.claude-plugin/plugin.json`
2. Add `plugins/<name>/agents/<name>.md` (agent with YAML frontmatter) OR `plugins/<name>/skills/<name>/SKILL.md` (skill)
3. Register it in `.claude-plugin/marketplace.json` under `plugins[]`
4. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.
