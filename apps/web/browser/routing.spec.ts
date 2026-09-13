import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('API-served shell supports navigation, refresh, and accessible placeholders', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Create', exact: true })).toBeVisible();
  await expect(page.getByRole('status')).toHaveText('Storage is ready.');
  for (const name of ['Library', 'Projects', 'Settings', 'Templates', 'Create']) {
    await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('link', { name, exact: true }).click();
    await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
    await page.reload();
    await expect(page.getByRole('heading', { name, exact: true })).toBeVisible();
  }
  await page.goto('/projects/00000000-0000-4000-8000-000000000001');
  await expect(page.getByRole('heading', { name: 'Project workspace', exact: true })).toBeVisible();
  await expect(page.getByRole('alert')).toContainText('not found');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  expect(errors).toEqual([]);
  await page.screenshot({ path: `../../test-results/foundation-${test.info().project.name}.png`, fullPage: true });
});
