# Phase 12D - GenAI Model & Prompting Strategy Report

## 1. Predictive Prompting Context
The predictive AI collects live telemetry arrays:
- turnstiles scan throughput velocity, GPS tracking of metro shuttles, alerts history, and weather.
- It parses these into standard prompt files (e.g. `system.md`, `copilot.md`) to evaluate crowd flow patterns and estimate density curves.

## 2. Simulation Triggers
Queries starting with `Simulate:` bypass standard conversation modes and load simulation structures, returning chronological timelines detailing required overrides and expected restoration.
