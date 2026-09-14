import { expect, test } from '@playwright/test';

test('D03 persisted YuE2 result plays and seeks', async ({ page }) => {
  test.skip(!process.env.D03_PROJECT_ID, 'Only run against an accepted real D03 result');
  await page.goto(`/projects/${process.env.D03_PROJECT_ID}`);
  await expect(page.locator('audio')).toHaveCount(1);
  await expect.poll(() => page.locator('audio').evaluate((a: HTMLAudioElement) => a.duration))
    .toBeGreaterThan(5);
  await page.getByRole('button', { name: 'Play', exact: true }).click();
  await expect.poll(() => page.locator('audio').evaluate((a: HTMLAudioElement) => a.currentTime))
    .toBeGreaterThan(.1);
  await page.getByRole('button', { name: 'Pause', exact: true }).click();
  await page.getByLabel('Seek', { exact: true }).fill('3');
  await expect.poll(() => page.locator('audio').evaluate((a: HTMLAudioElement) => a.currentTime))
    .toBeGreaterThan(2.5);
  await page.screenshot({ path: test.info().outputPath('d03-real-playback.png'), fullPage: true });
});
