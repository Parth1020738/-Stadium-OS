# Accessibility Management Service

The Accessibility Management Service manages wheelchair-accessible path mapping, maps elevator/escalator outages from BMS alerts, and computes customized, voice-guided routes optimized for disabled, elderly, or sensory-sensitive fans in the Aegis Smart Stadium OS.

## Features
- **Barrier Lifecycle Management:** Track and resolve active obstacles (e.g. elevator outages, ramp blocks).
- **Access Control:** Enforce role checks (`accessibility:read`, `accessibility:write`) and JWT validation.
- **Route Calculation:** Impairment-aware route generation avoiding active barriers.
- **BMS Event Integration:** Process elevator/ramp statuses changes and propagate updates to the Kafka bus.

## API References
- `GET /venues/{venueId}/accessibility/map`
- `GET /venues/{venueId}/accessibility/barriers`
- `POST /venues/{venueId}/accessibility/barriers`
- `PUT /venues/{venueId}/accessibility/barriers/{id}`
- `DELETE /venues/{venueId}/accessibility/barriers/{id}`
- `GET /venues/{venueId}/accessibility/routes`
- `POST /venues/{venueId}/accessibility/routes`
- `GET /venues/{venueId}/accessibility/routes/{id}`
- `GET /venues/{venueId}/accessibility/facilities`
- `GET /venues/{venueId}/accessibility/alerts`
