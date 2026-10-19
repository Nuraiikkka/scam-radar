import { expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

export const SCREENSHOTS = path.resolve('screenshots');
export const SAMPLES = path.resolve('..', 'data', 'samples');

fs.mkdirSync(SCREENSHOTS, { recursive: true });

export async function shot(page, name) {
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(SCREENSHOTS, name + '.png'), fullPage: false });
}

export function watchErrors(page) {
  const problems = [];
  page.on('console', (message) => {
    if (message.type() === 'error') {
      problems.push('console: ' + message.text() + ' @ ' + message.location().url);
    }
  });
  page.on('pageerror', (error) => problems.push('page error: ' + error.message));
  page.on('requestfailed', (request) => {
    const reason = request.failure() ? request.failure().errorText : 'unknown';
    if (reason !== 'net::ERR_ABORTED') {
      problems.push('request failed: ' + request.url() + ' ' + reason);
    }
  });
  return problems;
}

export async function enableAccessibility(page) {
  await page.waitForFunction(() => document.querySelector('flt-semantics-placeholder') !== null, null, { timeout: 60000 });
  await page.evaluate(() => document.querySelector('flt-semantics-placeholder').click());
  await page.waitForFunction(() => document.querySelector('flt-semantics[role]') !== null, null, { timeout: 60000 });
}

export async function openFresh(page, route = '/') {
  await page.goto(route);
  await enableAccessibility(page);
  await page.waitForFunction(() => document.querySelector('flt-semantics[role]') !== null, null, { timeout: 60000 });
}

export async function finishOnboarding(page) {
  await page.getByRole('button', { name: 'Skip' }).click();
  await page.getByRole('button', { name: 'I understand, start' }).click();
  await expect(page).toHaveURL(/\/home$/);
}

export async function openTab(page, name) {
  await page.getByRole('tab', { name }).click();
}

export async function swipeLeft(page, locator) {
  const box = await locator.boundingBox();
  const y = box.y + box.height / 2;
  await page.mouse.move(box.x + box.width - 20, y);
  await page.mouse.down();
  for (let step = 1; step <= 12; step += 1) {
    await page.mouse.move(box.x + box.width - 20 - step * 30, y);
    await page.waitForTimeout(16);
  }
  await page.mouse.up();
}

export function see(page, text) {
  return page.locator('flt-semantics').getByText(text).first();
}

export async function typeInto(page, label, text) {
  const box = page.getByRole('textbox', { name: label });
  await box.click();
  await page.waitForTimeout(300);
  await box.focus();
  await page.keyboard.press('ControlOrMeta+A');
  await page.keyboard.press('Backspace');
  await page.keyboard.type(text, { delay: 5 });
}

export async function scrollTo(page, locator) {
  for (let attempt = 0; attempt < 25; attempt += 1) {
    if ((await locator.count()) > 0 && (await locator.first().isVisible())) {
      await locator.first().scrollIntoViewIfNeeded();
      return locator.first();
    }
    await page.mouse.move(206, 500);
    await page.mouse.wheel(0, 350);
    await page.waitForTimeout(250);
  }
  throw new Error('could not scroll to ' + locator);
}

export function control(page, name) {
  return page
    .getByRole('button', { name, exact: true })
    .or(page.getByRole('radio', { name, exact: true }))
    .or(page.getByRole('checkbox', { name, exact: true }))
    .or(page.getByRole('tab', { name, exact: true }))
    .first();
}
