# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains AI agent prompt templates (written in Spanish) for .NET 8 / C# 12 development workflows. These prompts define specialized agents for LLMs to perform automated code review, performance benchmarking, and git history investigation.

## Agent Prompts

### Code Review Agent (`dotnet-code-review-agent-prompt.md`)
Main orchestrator for comprehensive .NET 8 code reviews. Analyzes security (SQL injection, auth, secrets), performance (N+1 queries, async patterns), architecture (SOLID), and testing quality.

**Outputs**: `CODE_REVIEW_[CommitSHA]_[Date].md`

### Benchmark Analyzer (`benchmark-analyzer-subagent-prompt.md`)
Sub-agent for BenchmarkDotNet performance testing. Creates benchmark projects, generates 2-4 optimization variants, and produces detailed comparison reports.

**Outputs**: `BENCHMARK_REPORT.md` in `benchmark/Benchmark_[MethodName]_[Timestamp]/`

### Git History Investigator (`git-history-investigator-agent-prompt.md`)
Agent for code archaeology: bug introduction finding (git bisect), blame analysis, code evolution tracking, deleted code recovery, and impact analysis.

**Investigation types**: `bug_finder`, `blame_analysis`, `code_evolution`, `deleted_code`, `author_analysis`, `impact_analysis`, `related_commits`

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

## Agent Integration

The agents work as a system:
- **Code Review → Benchmark**: Code Review invokes Benchmark Analyzer when detecting performance-critical methods (configurable via `benchmark_threshold`)
- **Code Review → Git Investigator**: Provides historical context for review findings
- **Configuration files**: `.code-review-config.yml`, `.git-investigator-config.yml`
