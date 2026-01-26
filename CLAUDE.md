# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains AI agent prompt templates for .NET development workflows. These prompts define specialized agents that can be used by LLMs to perform automated code review, performance benchmarking, and git history investigation.

## Agent Prompts

### 1. .NET Code Review Agent (`dotnet-code-review-agent-prompt.md`)
Main orchestrator agent for comprehensive code reviews of .NET 8 applications. Covers:
- Security analysis (SQL injection, input validation, auth, secrets)
- Performance review (N+1 queries, async patterns, LINQ usage)
- Architecture and SOLID principles
- Testing quality
- C# 12 / .NET 8 best practices

Key outputs: `CODE_REVIEW_[CommitSHA]_[Date].md` reports

### 2. Benchmark Analyzer Sub-Agent (`benchmark-analyzer-subagent-prompt.md`)
Specialized agent for creating and running BenchmarkDotNet performance tests. Features:
- Automated benchmark project setup
- Multiple optimization variant generation
- Performance comparison with baseline
- Detailed reports with recommendations

Key outputs: `BENCHMARK_REPORT.md` in `benchmark/` directory

### 3. Git History Investigator (`git-history-investigator-agent-prompt.md`)
Agent for code archaeology and historical analysis:
- Bug introduction finding (git bisect)
- Blame analysis for code lines
- Code evolution tracking
- Deleted code recovery
- Impact analysis

## Working with These Prompts

These are system prompts written in Spanish, designed for .NET 8 / C# 12 codebases. When modifying:

- Maintain the YAML parameter specification format
- Keep the detailed example outputs and templates
- Preserve the checklist structures for review dimensions
- Update version info when making significant changes

## Integration Points

The agents are designed to work together:
- Code Review Agent can invoke Benchmark Analyzer for performance-critical methods
- Git Investigator provides historical context for code review findings
- Configuration via `.code-review-config.yml` and `.git-investigator-config.yml`
