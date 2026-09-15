import { expect, test } from '@playwright/test';
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';

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
  const audioUrl = await page.locator('audio').getAttribute('src');
  expect(audioUrl).toBeTruthy();
  const expectedHash = createHash('sha256').update(await (await page.request.get(audioUrl!)).body()).digest('hex');
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('link', { name: 'Download WAV' }).click();
  const download = await downloadEvent;
  const downloadPath = await download.path();
  expect(downloadPath).toBeTruthy();
  const downloadedHash = createHash('sha256').update(await readFile(downloadPath!)).digest('hex');
  expect(downloadedHash).toBe(expectedHash);
  await page.reload();
  await expect(page.locator('audio')).toHaveCount(1);
  await expect(page.getByRole('region', { name: 'Generated result' })).toBeVisible();
  await page.screenshot({ path: test.info().outputPath('d03-real-playback.png'), fullPage: true });
});
