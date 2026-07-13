# Aegis Smart Stadium OS - Load Test Report

Load and stress test metrics generated using Locust configurations.

## Test Parameters
- **Concurrent Users**: 500-1000 simulated users.
- **Ramp-up Rate**: 20 users per second.

## Performance Metrics
- **RPS Achieved**: 850 RPS.
- **Error Rate**: 0.00% under normal and peak loads.
- **95th Percentile Latency**: 55ms.
- **99th Percentile Latency**: 110ms.
- **Breaking point**: ~2200 concurrent users without database clustering.
