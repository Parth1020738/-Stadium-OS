import { test, expect } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

const LOG_DIR = "c:/Users/Asus/OneDrive/Desktop/hackthon challnge 4/browser_logs";
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

test("Aegis Browser Automation Verification", async ({ page }) => {
  test.setTimeout(120000);
  
  // Setup logging
  const consoleLogs: Array<{ type: string; text: string; location: Record<string, unknown> }> = [];
  const networkLogs: Array<{ url: string; method: string; status: number | null; error: string | null }> = [];
  const wsConnections: Array<{ url: string; status: string }> = [];
  const pageErrors: Array<string> = [];

  page.on("console", (msg) => {
    consoleLogs.push({ type: msg.type(), text: msg.text(), location: msg.location() });
  });

  page.on("pageerror", (err) => {
    pageErrors.push(err.message);
  });

  page.on("response", (res) => {
    networkLogs.push({
      url: res.url(),
      method: res.request().method(),
      status: res.status(),
      error: null,
    });
  });

  page.on("requestfailed", (req) => {
    networkLogs.push({
      url: req.url(),
      method: req.method(),
      status: null,
      error: req.failure()?.errorText || "Unknown error",
    });
  });

  page.on("websocket", (ws) => {
    wsConnections.push({ url: ws.url(), status: "Connected" });
    ws.on("close", () => {
      const found = wsConnections.find(w => w.url === ws.url());
      if (found) found.status = "Closed";
    });
    ws.on("socketerror", (err) => {
      const found = wsConnections.find(w => w.url === ws.url());
      if (found) found.status = `Error: ${err}`;
    });
  });

  // 1. Visit login page
  await page.goto("/login");
  await expect(page).toHaveURL(/\/login/);
  await page.screenshot({ path: path.join(LOG_DIR, "01_login_page.png") });

  // 2. Perform Login
  await page.fill("#email", "operator@aegis.com");
  await page.fill("#password", "password");
  await page.click('button[type="submit"]');

  await page.waitForURL("**/");
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(LOG_DIR, "02_dashboard_home.png") });

  const pagesToTest = [
    { path: "/crowd", name: "crowd", screenshot: "03_crowd_heatmap.png" },
    { path: "/incidents", name: "incidents", screenshot: "04_incidents.png" },
    { path: "/volunteers", name: "volunteers", screenshot: "05_volunteers.png" },
    { path: "/transit", name: "transit", screenshot: "06_transit.png" },
    { path: "/accessibility", name: "accessibility", screenshot: "07_accessibility.png" },
    { path: "/knowledge", name: "knowledge", screenshot: "08_knowledge.png" },
    { path: "/ai", name: "ai", screenshot: "09_ai_playbooks.png" },
    { path: "/command-center", name: "command_center", screenshot: "10_command_center.png" },
    { path: "/reports", name: "reports", screenshot: "11_reports.png" },
    { path: "/settings", name: "settings", screenshot: "12_settings.png" },
    { path: "/health", name: "health", screenshot: "13_health.png" }
  ];

  const results: Record<string, { status: string; error: string | null }> = {};

  for (const p of pagesToTest) {
    try {
      await page.goto(p.path);
      await page.waitForTimeout(2000);
      await page.screenshot({ path: path.join(LOG_DIR, p.screenshot) });

      if (p.path === "/incidents") {
        const titleInput = page.locator('input[placeholder*="Title" i], input[name*="title" i], input[id*="title" i]');
        if (await titleInput.count() > 0) {
          await titleInput.first().fill("Security Guard dispatch request");
          const descInput = page.locator('textarea[placeholder*="Description" i], textarea[name*="description" i]');
          if (await descInput.count() > 0) await descInput.first().fill("Gate 3 crowd build up reporting");
          const submitBtn = page.locator('button[type="submit"], button:has-text("Create"), button:has-text("Submit")');
          if (await submitBtn.count() > 0) {
            await submitBtn.first().click();
            await page.waitForTimeout(1000);
            await page.screenshot({ path: path.join(LOG_DIR, "04_incidents_submitted.png") });
          }
        }
      } else if (p.path === "/volunteers") {
        const volunteerBtn = page.locator('button:has-text("Assign"), button:has-text("Add"), button:has-text("Schedule")');
        if (await volunteerBtn.count() > 0) {
          await volunteerBtn.first().click();
          await page.waitForTimeout(1000);
          await page.screenshot({ path: path.join(LOG_DIR, "05_volunteers_interacted.png") });
        }
      } else if (p.path === "/transit") {
        const dispatchBtn = page.locator('button:has-text("Dispatch"), button:has-text("Send"), button:has-text("Route")');
        if (await dispatchBtn.count() > 0) {
          await dispatchBtn.first().click();
          await page.waitForTimeout(1000);
          await page.screenshot({ path: path.join(LOG_DIR, "06_transit_dispatched.png") });
        }
      } else if (p.path === "/settings") {
        const saveBtn = page.locator('button:has-text("Save"), button:has-text("Update"), button[type="submit"]');
        if (await saveBtn.count() > 0) {
          await saveBtn.first().click();
          await page.waitForTimeout(1000);
          await page.screenshot({ path: path.join(LOG_DIR, "12_settings_saved.png") });
        }
      }

      results[p.name] = { status: "PASS", error: null };
    } catch (err: unknown) {
      results[p.name] = { status: "FAIL", error: err instanceof Error ? err.message : String(err) };
    }
  }

  fs.writeFileSync(
    path.join(LOG_DIR, "verification_results.json"),
    JSON.stringify({
      timestamp: new Date().toISOString(),
      results,
      consoleLogs,
      networkLogs: networkLogs.filter(n => !n.url.startsWith("data:")),
      wsConnections,
      pageErrors
    }, null, 2)
  );
});