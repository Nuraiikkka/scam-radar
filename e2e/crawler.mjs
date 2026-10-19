import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const baseUrl = process.env.E2E_BASE_URL || 'http://localhost:8080';
const channel = process.env.E2E_CHANNEL || undefined;
const routes = ['/home', '/history', '/stats', '/settings', '/login', '/register', '/onboarding'];
const skipLabels = ['Upload a video file', 'Log out', 'Confirm', 'Clear history', 'Show the introduction again'];
const ROLES = ['button', 'tab', 'link', 'checkbox', 'radio', 'switch', 'menuitem'];
const CONTROL_SELECTOR = ROLES.map((role) => 'flt-semantics[role="' + role + '"]').join(', ');
const outDir = path.resolve('screenshots', 'crawler');
fs.mkdirSync(outDir, { recursive: true });

function isExpected(line) {
  return line.includes('status of 401') && line.includes('/api/v1/auth/');
}

async function enableAccessibility(page) {
  await page.waitForFunction(() => document.querySelector('flt-semantics-placeholder') !== null, null, { timeout: 60000 });
  await page.evaluate(() => document.querySelector('flt-semantics-placeholder').click());
  await page.waitForFunction(() => document.querySelector('flt-semantics[role]') !== null, null, { timeout: 60000 });
}

async function prepare(context) {
  const page = await context.newPage();
  await page.goto(baseUrl + '/');
  await enableAccessibility(page);
  await page.getByRole('button', { name: 'Skip' }).click();
  await page.getByRole('button', { name: 'I understand, start' }).click();
  await page.waitForURL(/\/home$/);
  return page;
}

async function openRoute(page, route) {
  await page.goto(baseUrl + route);
  await enableAccessibility(page);
  await page.waitForTimeout(1200);
  if (route !== '/onboarding' && page.url().includes('/onboarding')) {
    await page.getByRole('button', { name: 'Skip' }).click();
    await page.getByRole('button', { name: 'I understand, start' }).click();
    await page.waitForURL(/\/home$/);
    await page.goto(baseUrl + route);
    await enableAccessibility(page);
    await page.waitForTimeout(1200);
  }
}

async function visibleControls(page) {
  const locator = page.locator(CONTROL_SELECTOR);
  const count = await locator.count();
  const labels = [];
  for (let index = 0; index < count; index += 1) {
    const item = locator.nth(index);
    if (!(await item.isVisible())) {
      continue;
    }
    const label = ((await item.getAttribute('aria-label')) || (await item.textContent()) || '').trim();
    if (label && !labels.includes(label)) {
      labels.push(label);
    }
  }
  return labels;
}

async function main() {
  const browser = await chromium.launch({ channel, headless: true });
  const context = await browser.newContext({ viewport: { width: 412, height: 915 } });
  const problems = [];
  const deadEnds = [];
  let clicks = 0;
  const page = await prepare(context);
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Upload a video file' }).click();
  await (await chooser).setFiles(path.resolve('..', 'data', 'samples', 'scam_job_ru.mp4'));
  await page.waitForURL(/\/result\//, { timeout: 240000 });
  routes.push(new URL(page.url()).pathname);
  page.on('console', (message) => {
    if (message.type() === 'error') {
      problems.push('console: ' + message.text() + ' @ ' + message.location().url + ' on ' + page.url());
    }
  });
  page.on('pageerror', (error) => problems.push('page error: ' + error.message + ' on ' + page.url()));
  page.on('requestfailed', (request) => {
    const reason = request.failure() ? request.failure().errorText : 'unknown';
    if (reason !== 'net::ERR_ABORTED') {
      problems.push('request failed: ' + request.url() + ' ' + reason);
    }
  });
  page.on('response', (response) => {
    if (response.status() >= 500) {
      problems.push('server error ' + response.status() + ': ' + response.url());
    }
  });

  for (const route of routes) {
    await openRoute(page, route);
    const labels = await visibleControls(page);
    console.log(route + ': ' + labels.length + ' controls: ' + labels.join(' | '));
    for (const label of labels) {
      if (skipLabels.includes(label)) {
        continue;
      }
      await openRoute(page, route);
      const target = page.locator(CONTROL_SELECTOR)
        .filter({ hasText: label })
        .or(page.locator('flt-semantics[aria-label="' + label.replace(/"/g, '\\"') + '"]'))
        .first();
      if (!(await target.isVisible().catch(() => false))) {
        continue;
      }
      await target.click({ timeout: 5000 }).catch((error) => problems.push('click failed: ' + label + ' ' + error.message));
      clicks += 1;
      await page.waitForTimeout(1200);
      const after = await visibleControls(page);
      const canGoBack = after.length > 0;
      if (!canGoBack) {
        deadEnds.push(route + ' -> ' + label + ' -> ' + page.url());
        await page.screenshot({ path: path.join(outDir, 'dead-end-' + clicks + '.png') });
      }
      await page.keyboard.press('Escape').catch(() => {});
    }
  }
  await browser.close();
  const unexpected = problems.filter((line) => !isExpected(line));
  console.log('clicked ' + clicks + ' controls on ' + routes.length + ' screens');
  console.log('problems: ' + unexpected.length + ', dead ends: ' + deadEnds.length);
  for (const line of unexpected) {
    console.log('  ' + line);
  }
  for (const line of deadEnds) {
    console.log('  dead end: ' + line);
  }
  if (unexpected.length > 0 || deadEnds.length > 0) {
    process.exit(1);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
