import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration – black-box tests against a running Nuxt dev
 * server (or production build). We do NOT integrate with Vitest or
 * @nuxt/test-utils; Playwright is the sole runner here.
 *
 * Usage:
 *   pnpm test:e2e          – headless run
 *   pnpm test:e2e:ui       – Playwright UI mode (interactive, recommended)
 *   pnpm test:e2e:debug    – headed + Playwright Inspector
 *
 * Prerequisites: Nuxt dev server must be running on http://localhost:3000
 * and the FastAPI backend must be running on http://localhost:8000.
 */
export default defineConfig({
	// ── Discovery ────────────────────────────────────────────────────────────
	testDir: "./tests/e2e",
	testMatch: "**/*.spec.ts",

	// ── Parallelism ──────────────────────────────────────────────────────────
	// Single worker so tests share one real backend (no data races between
	// parallel tests writing to the same DB).
	workers: 1,
	fullyParallel: false,

	// ── Retries ──────────────────────────────────────────────────────────────
	// Retry once on CI to absorb transient timing issues; no retries locally.
	retries: process.env.CI ? 1 : 0,

	// ── Timeouts ─────────────────────────────────────────────────────────────
	timeout: 30_000, // per test
	expect: { timeout: 8_000 }, // per assertion (generous for slow API calls)

	// ── Shared settings ───────────────────────────────────────────────────────
	use: {
		baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000",

		// Always collect traces and screenshots on first retry so failures are
		// diagnosable without having to reproduce locally.
		trace: "on-first-retry",
		screenshot: "only-on-failure",
		video: "retain-on-failure",
	},

	// ── Projects (browsers) ──────────────────────────────────────────────────
	// Desktop Chromium is the primary target; add others when the suite is stable.
	projects: [
		{
			name: "chromium",
			use: { ...devices["Desktop Chrome"] },
		},
	],

	// ── Output ───────────────────────────────────────────────────────────────
	reporter: process.env.CI
		? [["github"], ["html", { open: "never" }]]
		: [["list"], ["html", { open: "on-failure" }]],

	outputDir: "test-results/",
});
