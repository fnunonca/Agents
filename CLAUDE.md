# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

`code-craft` — a **Claude Code plugin marketplace** that distributes a personal collection of agents and skills for .NET 8/9/10 (C# 12/13/14) development workflows: automated code review, backend implementation on internal stack, performance benchmarking, git history investigation, benchmark scanning, and architecture documentation.

This repo contains no application code — only plugin manifests, agent prompts, skill definitions, and a few Python scripts. There is no build, lint, or test step for the marketplace itself. Validation is done by JSON parsing the manifests and by installing the marketplace locally in Claude Code.

Users consume this repo via:
```
/plugin marketplace add github.com/<user>/code-craft
/plugin install <plugin-name>@code-craft
```

## Prerequisites

- Claude Code (VS Code extension or CLI)
- Python 3.8+ (for skills that use scripts)
- .NET SDK 8.0+ (only when running benchmarks)

## Repository Layout

```
.claude-plugin/marketplace.json      # Marketplace catalog (6 plugins)
plugins/
├── dotnet-code-review/              # Agent plugin
├── dotnet-backend-senior/           # Agent plugin (implementer for internal stack)
├── dotnet-benchmark-analyzer/       # Agent plugin (sub-agent)
├── git-history-investigator/        # Agent plugin
├── dotnet-benchmark-scanner/        # Skill plugin
└── architecture-html/               # Skill plugin
```

Each plugin follows the standard Claude Code layout:
- `plugins/<name>/.claude-plugin/plugin.json` — plugin manifest
- `plugins/<name>/agents/*.md` — agent prompts with YAML frontmatter (for agent plugins)
- `plugins/<name>/skills/<name>/SKILL.md` — skill definition (for skill plugins)

## Key Commands

### Validate marketplace + plugin manifests
There is no test suite. The only mechanical check is JSON validity:
```bash
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"
python3 -c "import json; json.load(open('plugins/<name>/.claude-plugin/plugin.json'))"
```

### Test the marketplace locally before publishing
Inside a Claude Code session (use an absolute path to this repo):
```
/plugin marketplace add C:/IZIPAY/code-craft
/plugin install <plugin-name>@code-craft
```
This is the canonical way to verify a new or modified plugin without pushing to GitHub.

### Run the benchmark scanner scripts directly
```bash
# Full orchestration (interactive)
python3 plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /path/to/Solution.sln

# Scanner only
python3 plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/scripts/scan_solution.py /path/to/Solution.sln --threshold medium

# Batch mode (CI/CD)
python3 plugins/dotnet-benchmark-scanner/skills/dotnet-benchmark-scanner/scripts/orchestrate_benchmark.py /path/to/Solution.sln --batch --threshold critical
```

## Agent Plugins

### dotnet-code-review (`plugins/dotnet-code-review/agents/code-reviewer.md`)
Main orchestrator for comprehensive .NET code reviews. Analyzes security (SQL injection, auth, secrets), performance (N+1 queries, async patterns), architecture (SOLID), and testing quality. Supports .NET 8 (LTS), .NET 9 (STS), and .NET 10 (LTS) with C# 12/13/14.

**Outputs**: `CODE_REVIEW_[CommitSHA]_[Date].md`

### dotnet-benchmark-analyzer (`plugins/dotnet-benchmark-analyzer/agents/benchmark-analyzer.md`)
Sub-agent for BenchmarkDotNet performance testing. Creates benchmark projects, generates 2-4 optimization variants (Span-based, ArrayPool, ValueTask, struct-based, SIMD, etc.), and produces detailed comparison reports.

**Outputs**: `BENCHMARK_REPORT.md` in `benchmark/Benchmark_[MethodName]_[Timestamp]/`

### dotnet-backend-senior (`plugins/dotnet-backend-senior/agents/dotnet-backend-senior.md`)
Senior .NET backend implementer for the team's internal stack: Clean Architecture (6 layers), Dapper + Stored Procedures, NLog via `IAppLogger`, Hangfire (MemoryStorage), `IRestClient`, Options Pattern, xUnit with manual stubs. Applies conventions consistently (naming, layering, error codes, logging format, masking of sensitive data) and proposes architectural improvements only when explicitly asked.

### git-history-investigator (`plugins/git-history-investigator/agents/git-investigator.md`)
Agent for code archaeology: bug introduction finding (git bisect), blame analysis, code evolution tracking, deleted code recovery, and impact analysis.

**Investigation types**: `bug_finder`, `blame_analysis`, `code_evolution`, `deleted_code`, `author_analysis`, `impact_analysis`, `related_commits`

## Skill Plugins

- **dotnet-benchmark-scanner** — Scans .NET solutions for performance code smells (LINQ abuse, string concat in loops, boxing, unnecessary allocations). Uses regex-based pattern detection with a scoring system and severity thresholds (Critical >= 15, High >= 10, Medium >= 6, Low >= 3).
- **architecture-html** (`plugins/architecture-html/skills/architecture-html/SKILL.md`) — Generates a self-contained `docs/architecture.html` with an interactive React Flow architecture diagram and a Mermaid UML sequence diagram (zoom/pan, PNG export, fullscreen). Analyzes the repo (CLAUDE.md, csproj/sln/package.json, controllers, repositories, appsettings) to identify layers, endpoints, external services, and stored procedures. Loads React + React Flow + Mermaid from `esm.sh` via import map — no bundler/npm. Opens with a double click.

## Prompt Structure

All agents use a consistent YAML parameter specification format inside the prompt body:

```yaml
# Required parameters
parameter_name: type           # Description

# Optional parameters
optional_param: type [opcional] # Description with default
```

When modifying prompts:
- Keep YAML frontmatter at the top of every agent `.md` file (`name`, `description`, `model`, `color`); skills require `name`, `description`
- Maintain the YAML parameter format in the "Parámetros de Entrada" section
- Preserve the markdown report templates with their emoji conventions
- Keep the checklist structures (using `- [ ]` format)
- **Language convention**: agent prompts and user-visible output are in Spanish; file names, JSON keys, and inline technical comments stay in English

## Where generated artifacts land

Agents write into the **consumer's** project directory, not into this repo:
- `dotnet-code-review` → `CODE_REVIEW_[CommitSHA]_[Date].md` at the project root
- `dotnet-benchmark-analyzer` → `benchmark/Benchmark_[MethodName]_[Timestamp]/BENCHMARK_REPORT.md`
- `dotnet-benchmark-scanner` (orchestrator) → `benchmark_params/*.yaml` + `BENCHMARK_ORCHESTRATION_*.md`
- `architecture-html` → `docs/architecture.html`

Do not commit example outputs into this marketplace repo.

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
