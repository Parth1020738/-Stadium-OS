# Performance Optimization Report

This report outlines the bundle sizing, render, and caching strategies.

---

## 1. Caching & Memory Allocations

*   **React Query Caching**: Configured with a default staleTime of 5 minutes (`300,000 ms`) to prevent redundant API queries. Mutating records invalidates active cache keys, refreshing views without full page reloads.
*   **Zustand Subscriptions**: Store updates only trigger re-renders for components that explicitly subscribe to slice selectors, avoiding full-page cascade updates.

---

## 2. Compilation Bundling

*   **Static Pre-rendering**: Page layouts compile to static files during the build phase. Hydration happens seamlessly on the client.
*   **Lucide Icon Splitting**: Tree-shaking is enabled by Next.js, meaning only the icons imported in the pages are compiled into the final JS bundle.
