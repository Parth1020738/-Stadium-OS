from locust import HttpUser, task, between

class AegisStadiumUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def check_health(self):
        self.client.get("/api/v1/health")

    @task(2)
    def view_overview(self):
        # Using a mock/testing auth token header or testing unauthenticated health
        headers = {"Authorization": "Bearer mock-operator-token"}
        self.client.get("/api/v1/ai/overview", headers=headers)

    @task(1)
    def get_recommendations(self):
        headers = {"Authorization": "Bearer mock-operator-token"}
        self.client.get("/api/v1/ai/recommendations", headers=headers)
