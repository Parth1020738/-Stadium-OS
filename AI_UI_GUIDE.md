# AI Interface and Risk Dashboard Style Guide

This guide covers styling and layout specifications for the AI recommendation pages.

---

## 1. Overall Risk Speedometer Gauges
The overall risk index compiles dynamic sub-risks (crowd stands, transit fleets, security load) and maps ratios into clean progress bars:
*   **0% - 40% (Nominal)**: Emerald-500 indicators.
*   **40% - 70% (Warning)**: Amber-500 indicators.
*   **70% - 100% (Critical)**: Red-500 indicators.

---

## 2. Recommendation Cards & Explainability Details
Recommendations display confidence ratios (e.g. `Confidence: 92%`). Selecting any item slides in details explaining:
*   **AI reasoning summary**
*   **Suggested dispatch action**
*   **Evidences references**
