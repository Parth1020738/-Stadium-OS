# Authentication Flow Diagram

This document illustrates the token issuance and validation loops across client devices, the NestJS API Gateway, and the FastAPI Authentication Service.

## Sequence Flow

```mermaid
sequence-diagram
    autonumber
    actor Steward as Volunteer Steward Device
    participant Gateway as NestJS API Gateway
    participant AuthService as FastAPI Authentication Service
    database DB as PostgreSQL Database
    database Cache as Redis Cache

    Steward ->> Gateway: Login request POST /api/v1/auth/login
    Gateway ->> AuthService: Forward request
    AuthService ->> DB: Query User by email
    DB -->> AuthService: User entry
    AuthService ->> AuthService: Verify password using Argon2
    AuthService ->> DB: Save RefreshToken details
    AuthService -->> Steward: Return AccessToken + RefreshToken

    Note over Steward, Gateway: Subsequent requests to protected routes
    Steward ->> Gateway: GET /api/v1/some-route with Authorization header
    Gateway ->> Gateway: Verify JWT signature (JWT_SECRET)
    Gateway ->> Cache: Check if JWT is blacklisted
    Cache -->> Gateway: Valid (not blacklisted)
    Gateway ->> Gateway: Verify User Roles
    Gateway -->> Steward: Return route resources (200 OK)
```
