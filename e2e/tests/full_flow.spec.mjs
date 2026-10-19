import { test, expect } from '@playwright/test';
import path from 'node:path';
import { SAMPLES, finishOnboarding, openFresh, openTab, control, scrollTo, see, shot, swipeLeft, typeInto, watchErrors } from './helpers.mjs';

test.describe.configure({ mode: 'serial' });

let page;
let problems;
const email = 'e2e-' + Date.now() + '@example.com';
const password = 'e2e-password-123';

test.beforeAll(async ({ browser }) => {
  page = await browser.newPage();
  problems = watchErrors(page);
});

test.beforeEach(async ({}, testInfo) => {
  problems.push('step: ' + testInfo.title);
});

test.afterAll(async () => {
  await page.close();
});

test('01 onboarding and home', async () => {
  await openFresh(page, '/');
  await expect(see(page, 'Check a TikTok video')).toBeVisible();
  await shot(page, '01-onboarding');
  await finishOnboarding(page);
  await expect(see(page, 'Is this video a scam?')).toBeVisible();
  await shot(page, '02-home');
});

test('02 link validation and a removed video fail clearly', async () => {
  await page.getByRole('button', { name: 'Check link' }).click();
  await expect(see(page, 'Paste a link first')).toBeVisible();
  await typeInto(page, 'TikTok link', 'https://example.com/video');
  await page.getByRole('button', { name: 'Check link' }).click();
  await expect(see(page, 'This is not a TikTok link')).toBeVisible();
  await shot(page, '03-link-validation');
  const link = process.env.E2E_TIKTOK_URL || 'https://www.tiktok.com/@scamradar.e2e.missing/video/7000000000000000001';
  await typeInto(page, 'TikTok link', link);
  await page.getByRole('button', { name: 'Check link' }).click();
  await expect(page).toHaveURL(/\/(progress|result)\//);
  await shot(page, '04-link-progress');
  if (process.env.E2E_TIKTOK_URL) {
    await expect(see(page, 'Why')).toBeVisible({ timeout: 300000 });
    await shot(page, '05-link-result');
  } else {
    await expect(see(page, 'The check failed')).toBeVisible({ timeout: 180000 });
    await shot(page, '05-link-failed');
  }
  await page.getByRole('button', { name: /Back to start|Check another video/ }).click();
  await expect(page).toHaveURL(/\/home$/);
});

test('03 upload a scam video and see the result', async () => {
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Upload a video file' }).click();
  const fileChooser = await chooser;
  await fileChooser.setFiles(path.join(SAMPLES, 'scam_invest_ru.mp4'));
  await expect(page).toHaveURL(/\/progress\//);
  await shot(page, '06-upload-progress');
  await expect(see(page, 'Why')).toBeVisible({ timeout: 300000 });
  await expect(page).toHaveURL(/\/result\//);
  await expect(see(page, 'Investment platform')).toBeVisible();
  await shot(page, '07-result');
  const screenTile = await scrollTo(page, page.getByRole('button', { name: /Text on screen/ }));
  await screenTile.click();
  await expect(see(page, 't.me/profit_daily')).toBeVisible();
  await shot(page, '08-result-evidence');
});

test('04 feedback on the result', async () => {
  await (await scrollTo(page, page.getByRole('button', { name: 'Wrong verdict?' }))).click();
  await control(page, 'Yes, correct').click();
  await page.getByRole('button', { name: 'Send feedback' }).click();
  await expect(see(page, 'Thank you!')).toBeVisible();
  await shot(page, '09-feedback');
});

test('05 history and delete', async () => {
  await (await scrollTo(page, page.getByRole('button', { name: 'Check another video' }))).click();
  await openTab(page, 'History');
  const item = page.getByRole('button', { name: /scam_invest_ru\.mp4/ }).first();
  await expect(item).toBeVisible();
  await shot(page, '10-history');
  const before = await page.getByRole('button', { name: /tiktok\.com|\.mp4/ }).count();
  await swipeLeft(page, item);
  await expect(see(page, 'Deleted')).toBeVisible();
  await expect(page.getByRole('button', { name: /tiktok\.com|\.mp4/ })).toHaveCount(before - 1);
  await shot(page, '11-history-deleted');
});

test('06 statistics', async () => {
  await openTab(page, 'Statistics');
  await expect(see(page, 'Checks')).toBeVisible();
  await shot(page, '12-statistics');
  await control(page, 'Everyone').click();
  await expect(see(page, 'Checks')).toBeVisible();
});

test('07 settings language and theme', async () => {
  await openTab(page, 'Settings');
  await control(page, 'Русский').click();
  await expect(see(page, 'Настройки').first()).toBeVisible();
  await shot(page, '13-settings-russian');
  await control(page, 'English').click();
  await expect(see(page, 'Settings').first()).toBeVisible();
  await control(page, 'Dark').click();
  await shot(page, '14-settings-dark');
  await control(page, 'Light').click();
});

test('08 register, log out and log in', async () => {
  await page.getByRole('button', { name: 'Log in or register' }).click();
  await page.getByRole('button', { name: 'No account? Register' }).click();
  await typeInto(page, 'Email', email);
  await typeInto(page, 'Password', password);
  await shot(page, '15-register');
  await page.getByRole('button', { name: 'Create account' }).click();
  await expect(see(page, 'Logged in as ' + email)).toBeVisible();
  await shot(page, '16-logged-in');
  await page.getByRole('button', { name: 'Log out' }).click();
  await expect(page.getByRole('button', { name: 'Log in or register' })).toBeVisible();
  await page.getByRole('button', { name: 'Log in or register' }).click();
  await typeInto(page, 'Email', email);
  await typeInto(page, 'Password', 'wrong-password');
  await page.getByRole('button', { name: 'Log in', exact: true }).click();
  await expect(see(page, 'Wrong email or password.')).toBeVisible();
  await typeInto(page, 'Password', password);
  await page.getByRole('button', { name: 'Log in', exact: true }).click();
  await expect(see(page, 'Logged in as ' + email)).toBeVisible();
  await shot(page, '17-logged-in-again');
});

test('09 no unexpected browser errors', async () => {
  const expectedWrongPassword = (line) => line.includes('status of 401') && line.includes('/api/v1/auth/login');
  const isStep = (line) => line.startsWith('step: ');
  const unexpected = problems.filter((line) => !expectedWrongPassword(line) && !isStep(line));
  if (unexpected.length > 0) {
    console.log(problems.map((line) => line.split('\n')[0]).join('\n'));
  }
  expect(unexpected, unexpected.join('\n')).toEqual([]);
});
