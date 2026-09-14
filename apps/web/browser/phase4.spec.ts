import { expect, test } from "@playwright/test";

const draft = {
  brief: "Phase four saved draft",
  instruments: ["Piano"],
  mood: "Calm",
  language: "English",
  genre: "Indie Pop",
  tempo: "Medium",
  vocal_type: "Instrumental",
  lyrics: { mode: "mock" },
  duration_seconds: 8,
};

test("projects, library, duplicate, archive, settings, and templates work", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Stateful lifecycle flow runs once.");
  test.setTimeout(150000);

  await page.goto("/settings");
  await expect(page.getByRole("heading", { name: "Settings", exact: true })).toBeVisible();
  await page.getByRole("combobox", { name: "Mood", exact: true }).selectOption("Happy");
  await page.getByLabel("Default volume", { exact: false }).fill("0.65");
  await page.getByRole("combobox", { name: "Repeat", exact: true }).selectOption("one");
  await page.getByRole("button", { name: "Save workspace settings" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Workspace settings saved." })).toBeVisible();
  await page.getByRole("link", { name: "Create", exact: true }).click();
  await expect(page.getByRole("radio", { name: "Happy" })).toBeChecked();
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await page.getByRole("combobox", { name: "Mood", exact: true }).selectOption("Calm");
  await page.getByRole("button", { name: "Save workspace settings" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Workspace settings saved." })).toBeVisible();

  await page.getByRole("link", { name: "Templates", exact: true }).click();
  await page.getByLabel("Find a template").fill("Tabla");
  await page.getByRole("button", { name: "Apply to draft" }).click();
  await expect(page.getByLabel("Music brief")).toHaveValue(
    "A relaxed evening instrumental with a soft tabla pulse.",
  );
  await expect(page.getByRole("region", { name: "Generated result" })).toHaveCount(0);
  await expect(page.getByRole("status").filter({ hasText: "Template applied" })).toBeVisible();
  await page.getByLabel("Project title", { exact: true }).fill("Phase 4 library song");
  await page.getByRole("button", { name: "Save Project", exact: true }).click();
  await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/);
  await expect(page.getByRole("status").filter({ hasText: "Saved to server" })).toBeVisible();
  await page.getByRole("button", { name: "Generate", exact: true }).click();
  await expect(page.getByRole("region", { name: "Generated result" })).toBeVisible({ timeout: 45000 });
  await expect(page.getByRole("button", { name: "Repeat: one", exact: true })).toBeVisible();
  await expect(page.getByLabel("Volume", { exact: true })).toHaveValue("0.65");
  await page.getByLabel("Project title", { exact: true }).fill("Phase 4 library song");
  await page.getByRole("button", { name: "Save Project", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Saved to server" })).toBeVisible();
  const projectId = new URL(page.url()).pathname.split("/").at(-1)!;
  await page.reload();
  await expect(page.getByLabel("Project title", { exact: true })).toHaveValue("Phase 4 library song");
  await expect(page.getByLabel("Music brief")).toHaveValue(
    "A relaxed evening instrumental with a soft tabla pulse.",
  );

  await page.getByRole("link", { name: "Library", exact: true }).click();
  await page.getByLabel("Search titles and labels").fill("Phase 4 library song");
  const row = page.locator(".record-card").filter({ hasText: "Phase 4 library song" }).first();
  await expect(row).toBeVisible();
  await expect(row).toContainText("Version 1");
  await row.getByRole("button", { name: "☆ Favorite" }).click();
  await expect(row.getByRole("button", { name: "★ Favorited" })).toBeVisible();
  await page.getByLabel("Favorites only").check();
  await expect(page.locator(".record-card")).toHaveCount(1);
  await page.getByRole("link", { name: "Open version" }).click();
  await expect(page).toHaveURL(new RegExp(`/projects/${projectId}\\?version=`));
  await expect(page.getByRole("region", { name: "Generated result" })).toBeVisible();

  await page.getByRole("link", { name: "Projects", exact: true }).click();
  await page.getByLabel("Search projects").fill("Phase 4 library song");
  const projectRow = page.locator(".record-card").filter({ hasText: "Phase 4 library song" }).first();
  await expect(projectRow).toBeVisible();
  await projectRow.getByRole("button", { name: "Duplicate" }).click();
  await expect(page.getByLabel("Project title", { exact: true })).toHaveValue("Copy of Phase 4 library song");
  await page.getByRole("link", { name: "Projects", exact: true }).click();
  await page.getByLabel("Search projects").fill("Phase 4 library song");
  const original = page.locator(".record-card").filter({ hasText: "Phase 4 library song" }).first();
  await original.getByRole("button", { name: "Archive" }).click();
  await page.getByRole("combobox", { name: "Project archive filter" }).selectOption("archived");
  const archived = page.locator(".record-card").filter({ hasText: "Phase 4 library song" }).first();
  await expect(archived).toBeVisible();
  await archived.getByRole("button", { name: "Unarchive" }).click();
  await page.getByRole("combobox", { name: "Project archive filter" }).selectOption("active");
  await expect(page.locator(".record-card").filter({ hasText: "Phase 4 library song" })).toHaveCount(2);
  await page.screenshot({ path: testInfo.outputPath("phase4-projects.png"), fullPage: true });
  await page.getByRole("link", { name: "Settings", exact: true }).click();
  await page.getByLabel("Default volume", { exact: false }).fill("0.8");
  await page.getByRole("combobox", { name: "Repeat", exact: true }).selectOption("off");
  await page.getByRole("button", { name: "Save workspace settings" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Workspace settings saved." })).toBeVisible();
});

test("offline and two-tab draft conflicts keep explicit recovery choices", async ({ page, context }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Two-tab save behavior runs once.");
  test.setTimeout(90000);
  const created = await page.request.post("/api/v1/projects", {
    data: { title: "Two tab recovery", draft },
  });
  expect(created.status()).toBe(201);
  const project = await created.json();
  await page.goto(`/projects/${project.id}`);
  const secondTab = await context.newPage();
  await secondTab.goto(`/projects/${project.id}`);
  await expect(secondTab.getByLabel("Music brief")).toHaveValue(draft.brief);
  await page.getByLabel("Music brief").fill("Offline local recovery draft");
  await page.waitForTimeout(350);
  await context.setOffline(true);
  await page.getByLabel("Music brief").fill("Offline edit saved locally");
  await page.waitForTimeout(350);
  await context.setOffline(false);
  await page.reload();
  await expect(page.getByLabel("Music brief")).toHaveValue("Offline edit saved locally");

  await secondTab.getByLabel("Project title", { exact: true }).fill("Server tab title");
  await secondTab.getByRole("button", { name: "Save Project", exact: true }).click();
  await expect(secondTab.getByRole("status").filter({ hasText: "Saved to server" })).toBeVisible();
  await page.getByRole("button", { name: "Save Project", exact: true }).click();
  await expect(page.getByRole("button", { name: "Use server", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Use server", exact: true }).click();
  await expect(page.getByLabel("Project title", { exact: true })).toHaveValue("Server tab title");

  await page.getByLabel("Music brief").fill("Keep this second local edit");
  let latest = await (await page.request.get(`/api/v1/projects/${project.id}`)).json();
  const changed = await page.request.patch(`/api/v1/projects/${project.id}`, {
    data: { title: "Changed by another writer" },
    headers: { "If-Match": `"${latest.revision}"` },
  });
  expect(changed.status()).toBe(200);
  await page.getByRole("button", { name: "Save Project", exact: true }).click();
  await expect(page.getByRole("button", { name: "Keep local", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Keep local", exact: true }).click();
  await page.getByRole("button", { name: "Save Project", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Saved to server" })).toBeVisible();
  await expect(page.getByLabel("Music brief")).toHaveValue("Keep this second local edit");

  await page.getByLabel("Music brief").fill("Save this conflict as a copy");
  latest = await (await page.request.get(`/api/v1/projects/${project.id}`)).json();
  const changedAgain = await page.request.patch(`/api/v1/projects/${project.id}`, {
    data: { title: "One more server revision" },
    headers: { "If-Match": `"${latest.revision}"` },
  });
  expect(changedAgain.status()).toBe(200);
  await page.getByRole("button", { name: "Save Project", exact: true }).click();
  await page.getByRole("button", { name: "Save copy", exact: true }).click();
  await expect(page).toHaveURL(/\/projects\/[0-9a-f-]+$/);
  await expect(page.getByLabel("Project title", { exact: true })).toHaveValue("Copy of Server tab title");
  await expect(page.getByLabel("Music brief")).toHaveValue("Save this conflict as a copy");
  await secondTab.close();
  await page.screenshot({ path: testInfo.outputPath("phase4-draft-recovery.png"), fullPage: true });
});

test("IndexedDB failure keeps edits in memory and reports unsaved local recovery", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Browser storage failure runs once.");
  await page.addInitScript(() => {
    Object.defineProperty(window, "indexedDB", {
      configurable: true,
      get() {
        throw new DOMException("Blocked", "SecurityError");
      },
    });
  });
  await page.goto("/create");
  await page.getByLabel("Music brief").fill("In-memory draft despite blocked IndexedDB");
  await expect(page.getByRole("alert")).toContainText("Local draft storage");
  await page.getByLabel("Project title", { exact: true }).fill("IndexedDB failure project");
  await page.getByRole("button", { name: "Save Project", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "local recovery unavailable" })).toBeVisible();
  await expect(page.getByLabel("Music brief")).toHaveValue("In-memory draft despite blocked IndexedDB");
  await expect(page.getByRole("alert")).toContainText("Project saved to the server");
});

test("failed jobs can be retried explicitly as linked jobs", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop", "Retry action runs once.");
  test.setTimeout(90000);
  await page.goto("/create");
  await page.getByLabel("Music brief").fill("Explicit retry acceptance");
  await page.getByText("Advanced Options", { exact: true }).click();
  await page.getByLabel("Seed (optional)").fill("4294967201");
  await page.getByRole("button", { name: "Generate", exact: true }).click();
  await expect(page.getByRole("region", { name: "Generation status" })).toContainText("failed", { timeout: 45000 });
  const path = `/api/v1/projects/${new URL(page.url()).pathname.split("/").at(-1)}`;
  const project = await (await page.request.get(path)).json();
  const original = project.jobs.find((item: { state: string }) => item.state === "failed");
  expect(original).toBeTruthy();
  await page.getByRole("button", { name: "Retry failed job", exact: true }).click();
  await expect(page.getByText("Retry queued as a new linked job.")).toBeVisible();
  await expect(page.getByText(`Explicit retry of job ${original.id}`)).toBeVisible();
  const currentProject = await (await page.request.get(path)).json();
  expect(currentProject.jobs.some((item: { retry_of_job_id: string }) => item.retry_of_job_id === original.id)).toBe(true);
  await testInfo.attach("retry-jobs", { body: JSON.stringify(currentProject.jobs, null, 2), contentType: "application/json" });
});
