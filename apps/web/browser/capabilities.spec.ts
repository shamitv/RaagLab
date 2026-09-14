import { expect, test } from "@playwright/test";

test("composer uses the configured provider capability limits", async ({ page }) => {
  await page.route("**/health/ready", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "ready",
        dependencies: { database: "ready", schema: "ready", artifacts: "ready" },
        services: { dispatcher: "ready", worker: "ready", broker: "ready", provider: "ready" },
        generation: "ready",
      }),
    }),
  );
  await page.route("**/api/v1/settings", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        revision: 1,
        generation_defaults: {
          instruments: ["Piano"],
          mood: "Calm",
          language: "Hindi",
          genre: "Folk",
          tempo: "Medium",
          vocal_type: "Instrumental",
          duration_seconds: 8,
          lyrics_mode: "mock",
        },
        volume: 0.8,
        repeat_mode: "off",
        export_format: "wav",
      }),
    }),
  );
  await page.route("**/api/v1/capabilities", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        provider_id: "yue2",
        provider_revision: "yue2-infer-0.1.5",
        provider_route: "museforge.yue2.v1",
        model_id: "m-a-p/YuE2-3B",
        model_revision: "29b3558dd46954a0cd9021dc76d5c91864a0f1c7",
        decoder_revision: "9a94e1d0ea9f8087e98f77fa88df4a4068104d2a",
        is_demo: false,
        capability_matrix: {
          lyrics_text_input: {
            state: "supported",
            evidence: "Supplied lyrics are retained.",
            limits: [],
          },
          instrumental_music_generation: {
            state: "unknown",
            evidence: "Instrumental-only output is unverified.",
            limits: ["Output may include vocals."],
          },
          duration_control: {
            state: "unsupported",
            evidence: "Output duration is model-determined.",
            limits: [],
          },
        },
        lyrics_modes: ["user"],
        lyrics_text: true,
        text_to_instrumental: null,
        vocals: null,
        exact_lyrics_vocals: null,
        instruments: ["Guitar", "Piano"],
        moods: ["Calm", "Happy"],
        languages: ["English"],
        genres: ["Folk", "Pop"],
        vocal_types: ["Instrumental"],
        operations: ["generate"],
        duration: { min: 5, max: 30, default: 8 },
        sample_rates: [48000],
        channels: [2],
        seed_behavior: "Passed to the model; reproducibility is unverified.",
        cooperative_cancel: true,
        progress_mode: "stage",
        warnings: ["Vocal behavior is unverified."],
        default_lyrics_mode: "user",
        readiness: { state: "ready", last_observed_at: null },
      }),
    }),
  );

  await page.goto("/create");
  await expect(page.getByLabel("Lyrics source")).toHaveValue("user");
  await expect(page.getByRole("textbox", { name: "Your lyrics" })).toBeVisible();
  await expect(page.getByRole("radio", { name: "English" })).toBeChecked();
  await expect(page.getByRole("radio", { name: "Hindi" })).toHaveCount(0);
  await expect(page.getByText("YuE2 may include vocals", { exact: false })).toBeVisible();

  await page.getByText("Advanced Options", { exact: true }).click();
  await expect(page.getByLabel("Duration (seconds)")).toBeDisabled();
  await expect(page.getByRole("list", { name: "Provider capability status" }))
    .toContainText("unknown");
  await expect(page.getByText("Real provider audio may not follow", { exact: false }))
    .toBeVisible();
});
