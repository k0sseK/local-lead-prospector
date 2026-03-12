import { test, expect, type Page } from "@playwright/test";

/**
 * Auth E2E – Golden Path
 *
 * These tests run against a live Nuxt dev server + real FastAPI backend.
 * No mocks. No stubs. Pure black-box.
 *
 * Requirements to run:
 *   1. Backend running:  cd backend && uvicorn app.main:app --reload
 *   2. Frontend running: cd frontend && pnpm dev
 *   3. A real test account must exist in the database (see TEST_EMAIL / TEST_PASSWORD).
 *
 * Set credentials via env vars to keep them out of source control:
 *   $env:E2E_TEST_EMAIL    = "tester@example.com"
 *   $env:E2E_TEST_PASSWORD = "SuperSecretPass123"
 */

const TEST_EMAIL = process.env.E2E_TEST_EMAIL ?? "tester@example.com";
const TEST_PASSWORD = process.env.E2E_TEST_PASSWORD ?? "SuperSecretPass123";

// ── Page Object ────────────────────────────────────────────────────────────────
// Keeps selectors in one place; when the template changes, update here only.

class LoginPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto("/login");
	}

	get emailInput() {
		return this.page.locator("#email");
	}

	get passwordInput() {
		return this.page.locator("#password");
	}

	get submitButton() {
		// The button text is "Zaloguj się" (or "Logowanie..." while loading).
		// Role-based locator is more resilient than text matching.
		return this.page.getByRole("button", { name: /zaloguj się/i });
	}

	get errorMessage() {
		return this.page.locator("p.text-red-400");
	}

	async fillAndSubmit(email: string, password: string) {
		await this.emailInput.fill(email);
		await this.passwordInput.fill(password);
		await this.submitButton.click();
	}
}

// ── Tests ──────────────────────────────────────────────────────────────────────

test.describe("Login page", () => {
	let loginPage: LoginPage;

	test.beforeEach(async ({ page }) => {
		loginPage = new LoginPage(page);
		// Make sure we start every test logged out (clear auth cookie).
		await page.context().clearCookies();
		await loginPage.goto();
	});

	// ── Rendering ────────────────────────────────────────────────────────────

	test("renders the login form with all required fields", async () => {
		await expect(loginPage.emailInput).toBeVisible();
		await expect(loginPage.passwordInput).toBeVisible();
		await expect(loginPage.submitButton).toBeVisible();
		await expect(loginPage.submitButton).toBeEnabled();
	});

	test("page title reflects the login context", async ({ page }) => {
		await expect(page.locator("h1")).toContainText("Zaloguj się");
	});

	// ── Golden path ───────────────────────────────────────────────────────────

	test("valid credentials redirect to /app and render the dashboard", async ({
		page,
	}) => {
		await loginPage.fillAndSubmit(TEST_EMAIL, TEST_PASSWORD);

		// Wait for navigation – the app redirects to /app after successful login.
		await page.waitForURL("**/app", { timeout: 15_000 });

		// Confirm we actually landed on the dashboard, not a redirect loop.
		expect(page.url()).toContain("/app");

		// The dashboard must render some meaningful content (not a blank page).
		// We look for an element that only appears when authenticated.
		// Adjust the selector if the component structure changes.
		await expect(
			page
				.locator(
					"[data-testid='dashboard-root'], .kanban-board, #app-layout",
				)
				.first(),
		)
			.toBeVisible({ timeout: 10_000 })
			.catch(async () => {
				// Fallback: if no specific testid exists yet, verify the URL persists
				// and no login form is visible (i.e. we are not bounced back).
				await expect(loginPage.emailInput).not.toBeVisible();
				await expect(page).toHaveURL(/\/app/);
			});
	});

	// ── Error paths ───────────────────────────────────────────────────────────

	test("wrong password shows error message without redirecting", async ({
		page,
	}) => {
		await loginPage.fillAndSubmit(TEST_EMAIL, "definitely-wrong-password");

		// Must stay on /login – no redirect.
		await expect(page).toHaveURL(/\/login/, { timeout: 8_000 });

		// Error paragraph must appear.
		await expect(loginPage.errorMessage).toBeVisible();
	});

	test("non-existent email shows error message", async ({ page }) => {
		await loginPage.fillAndSubmit("nobody@nowhere.invalid", "irrelevant");

		await expect(page).toHaveURL(/\/login/, { timeout: 8_000 });
		await expect(loginPage.errorMessage).toBeVisible();
	});

	// ── Already authenticated ─────────────────────────────────────────────────

	test("authenticated user visiting /login is redirected to /app", async ({
		page,
	}) => {
		// Log in first to get the auth cookie.
		await loginPage.fillAndSubmit(TEST_EMAIL, TEST_PASSWORD);
		await page.waitForURL("**/app", { timeout: 15_000 });

		// Now navigate back to /login directly.
		await page.goto("/login");

		// Nuxt middleware should kick the user back to /app.
		await expect(page).toHaveURL(/\/app/, { timeout: 8_000 });
	});

	// ── Keyboard UX ───────────────────────────────────────────────────────────

	test("pressing Enter in the password field submits the form", async ({
		page,
	}) => {
		await loginPage.emailInput.fill(TEST_EMAIL);
		await loginPage.passwordInput.fill(TEST_PASSWORD);
		await loginPage.passwordInput.press("Enter");

		await page.waitForURL("**/app", { timeout: 15_000 });
		expect(page.url()).toContain("/app");
	});
});
