import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("iterations, exact lyrics, metadata and saved selection", async ({
  page,
}, testInfo) => {
  test.setTimeout(150000);
  await page.goto("/create");
  await page.getByLabel("Music brief").fill("Responsive workspace acceptance");
  await page.getByRole("button", { name: "Generate", exact: true }).click();
  const result = page.getByRole("region", { name: "Generated result" });
  await expect(result).toBeVisible({ timeout: 45000 });
  await expect(page.locator("audio")).toHaveCount(1);
  await page.getByRole("button", { name: "Play", exact: true }).click();
  await expect
    .poll(() =>
      page.locator("audio").evaluate((a: HTMLAudioElement) => a.currentTime),
    )
    .toBeGreaterThan(0.1);
  await page.getByRole("button", { name: "Pause", exact: true }).click();
  await page.getByLabel("Seek", { exact: true }).fill("3");
  expect(
    await page
      .locator("audio")
      .evaluate((a: HTMLAudioElement) => a.currentTime),
  ).toBeCloseTo(3, 0);
  await page
    .getByRole("button", { name: "Refine Lyrics", exact: true })
    .click();
  const text =
    "  [अंतरा]\nहवा 🎵\n\n[பல்லவி]\n" + "வானம் தமிழ் இசை ".repeat(80) + "\t\n";
  await page.getByLabel("Refine lyrics", { exact: true }).fill(text);
  await page.getByRole("button", { name: "Apply lyrics", exact: true }).click();
  await expect(result).toContainText("Audio unchanged", { timeout: 45000 });
  expect(await page.locator("pre.lyrics").textContent()).toBe(text);
  const history = page
    .locator("details")
    .filter({ has: page.getByText(/^Version History/) });
  if ((await history.getAttribute("open")) === null)
    await history.locator("summary").click();
  await page.getByRole("button", { name: "Favorite", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Unfavorite", exact: true }),
  ).toBeVisible();
  await page
    .getByLabel("Version label", { exact: true })
    .fill("My exact lyric edit");
  await page
    .getByRole("button", { name: "Rename version", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "My exact lyric edit", exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Create Variation", exact: true })
    .click();
  await expect(
    page.getByText("Version History (3)", { exact: true }),
  ).toBeVisible({ timeout: 45000 });
  await page
    .getByRole("combobox", { name: "Completed versions", exact: true })
    .selectOption({ label: "1. Version 1" });
  await expect(
    page.getByRole("heading", { name: "Version 1", exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Version 1", exact: true }),
  ).toBeVisible();
  expect(
    await page.locator("audio").evaluate((a: HTMLAudioElement) => a.paused),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: testInfo.outputPath("workspace.png"),
    fullPage: true,
  });
});

test("breakpoint and zoom layout keeps controls and semantic order", async ({
  page,
}, testInfo) => {
  await page.goto("/create");
  await page.getByLabel("Music brief").fill("Zoom and keyboard draft");
  for (const width of [320, 360, 390, 768, 1199, 1200, 1399, 1440, 1600]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () =>
          document.documentElement.scrollWidth <=
          document.documentElement.clientWidth,
      ),
    ).toBe(true);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.evaluate(() => {
    document.documentElement.style.fontSize = "200%";
  });
  await page
    .getByRole("button", { name: "Save Project", exact: true })
    .scrollIntoViewIfNeeded();
  const button = await page
    .getByRole("button", { name: "Save Project", exact: true })
    .boundingBox();
  const nav = await page.getByRole("navigation").boundingBox();
  expect(button!.y + button!.height).toBeLessThan(nav!.y);
  await page.screenshot({
    path: testInfo.outputPath("large-text.png"),
    fullPage: true,
  });
});

test("focused actions, clipboard failure, offline draft and conditional save", async ({
  page,
  context,
}, testInfo) => {
  test.skip(
    testInfo.project.name !== "desktop",
    "Behavior is shared; viewport coverage is in the workspace test.",
  );
  test.setTimeout(150000);
  await page.goto("/create");
  await page.getByLabel("Music brief").fill("Focused action acceptance");
  await page.getByRole("button", { name: "Generate", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Generated result" }),
  ).toBeVisible({ timeout: 45000 });
  await page.getByRole("button", { name: "Change Mood", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Iteration mood", exact: true })
    .selectOption("Epic");
  const accepted = page.waitForResponse(
    (r) => r.url().endsWith("/iterations") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Apply Changes", exact: true })
    .click();
  const identity = await (await accepted).json();
  await expect(
    page.getByText("Version History (2)", { exact: true }),
  ).toBeVisible({ timeout: 45000 });
  const job = await (await page.request.get(identity.status_url)).json();
  const version = await (await page.request.get(job.version_url)).json();
  expect(version.inputs.mood).toBe("Epic");
  expect(version.inputs.iteration_instruction).toBe("Change the mood");
  await page
    .getByRole("button", { name: "Try New Instruments", exact: true })
    .click();
  await page
    .getByRole("group", { name: "Iteration instruments", exact: true })
    .getByRole("button", { name: "Guitar", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Apply Changes", exact: true })
    .click();
  await expect(
    page.getByText("Version History (3)", { exact: true }),
  ).toBeVisible({ timeout: 45000 });
  await page.getByRole("button", { name: "Regenerate", exact: true }).click();
  await page.getByRole("combobox",{name:"Completed versions",exact:true}).selectOption({index:0});
  await expect(
    page.getByText("Version History (4)", { exact: true }),
  ).toBeVisible({ timeout: 45000 });
  await expect(page.getByRole("heading",{name:"Version 1",exact:true})).toBeVisible();
  await page.evaluate(() => {
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: () => Promise.reject(new Error("denied")) },
    });
  });
  await page.getByRole("button", { name: "Copy lyrics", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Copy failed." }),
  ).toBeVisible();
  await context.setOffline(true);
  await expect(
    page.getByRole("button", { name: "Save Project", exact: true }),
  ).toBeDisabled();
  await page.getByLabel("Music brief").fill("Offline unsent edit survives");
  await context.setOffline(false);
  await expect(
    page.getByRole("button", { name: "Save Project", exact: true }),
  ).toBeEnabled();
  await page
    .getByLabel("Project title", { exact: true })
    .fill("Saved workspace title");
  await page.getByRole("button", { name: "Save Project", exact: true }).click();
  await expect(
    page.getByRole("status").filter({ hasText: "Saved to server" }),
  ).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Music brief")).toHaveValue(
    "Offline unsent edit survives",
  );
  await expect(page.getByLabel("Project title", { exact: true })).toHaveValue(
    "Saved workspace title",
  );
  await page.getByRole("button", { name: "Shuffle", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Shuffle", exact: true }),
  ).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Repeat: off", exact: true }).click();
  await page.getByRole("button", { name: "Repeat: one", exact: true }).click();
  await page.getByRole("button", { name: "Play", exact: true }).click();
  await page.locator("audio").evaluate((a: HTMLAudioElement) => {
    a.currentTime = a.duration - 0.05;
  });
  await expect
    .poll(() =>
      page
        .locator("audio")
        .evaluate(
          (a: HTMLAudioElement) =>
            !a.paused && a.currentTime > 0.1 && a.currentTime < 2,
        ),
    )
    .toBe(true);
});

test('cancellation and stale save keep the editable draft',async({page},testInfo)=>{
 test.skip(testInfo.project.name!=='desktop','Shared state behavior is verified once.');test.setTimeout(90000);
 await page.goto('/create');await page.getByLabel('Music brief').fill('Cancellation and save conflict acceptance');
 await page.getByRole('button',{name:'Generate',exact:true}).click();await page.getByRole('button',{name:'Cancel generation',exact:true}).click();
 await expect(page.getByRole('region',{name:'Generation status'})).toContainText('cancelled',{timeout:45000});await expect(page.getByRole('region',{name:'Generated result'})).toHaveCount(0);
 await page.getByRole('button',{name:'Generate again',exact:true}).click();await expect(page.getByRole('region',{name:'Generated result'})).toBeVisible({timeout:45000});
 const projectPath='/api/v1/projects/'+page.url().split('/').at(-1);const project=await(await page.request.get(projectPath)).json();
 const changed=await page.request.patch(projectPath,{data:{title:'A newer server title'},headers:{'If-Match':`"${project.revision}"`}});expect(changed.status()).toBe(200);
 await page.getByLabel('Music brief').fill('Keep this local text after a stale save');await page.getByRole('button',{name:'Save Project',exact:true}).click();
 await expect(page.getByRole('alert')).toContainText('Save conflict');await expect(page.getByLabel('Music brief')).toHaveValue('Keep this local text after a stale save');
 expect((await(await page.request.get(projectPath)).json()).title).toBe('A newer server title');
 await expect(page.getByRole('button',{name:'Keep local',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Keep local',exact:true}).click();
 await page.getByRole('button',{name:'Save Project',exact:true}).click();await expect(page.getByRole('status').filter({hasText:'Saved to server'})).toBeVisible();
});
