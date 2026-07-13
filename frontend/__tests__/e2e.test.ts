import { test, expect } from "@playwright/test";

test.describe("Aegis Command Center E2E Flow", () => {
  test("should load unauthenticated page and redirect to login", async ({ page }) => {
    // Navigate to homepage
    await page.goto("/");

    // The shell should detect unauthenticated status and redirect to /login
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator("h2")).toContainText(/Sign In to Command Center/i);
  });
});
