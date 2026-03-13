const FRONTEND_BASE_URL =
	process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";
const API_BASE_URL =
	process.env.E2E_API_BASE_URL ??
	process.env.NUXT_PUBLIC_API_BASE ??
	"http://localhost:8000/api";
const BACKEND_HEALTH_URL =
	process.env.E2E_BACKEND_HEALTH_URL ??
	`${API_BASE_URL.replace(/\/api\/?$/, "")}/health`;
const TEST_EMAIL = process.env.E2E_TEST_EMAIL;
const TEST_PASSWORD = process.env.E2E_TEST_PASSWORD;

const CHECK_TIMEOUT_MS = Number(process.env.E2E_PRECHECK_TIMEOUT_MS ?? 60000);
const RETRY_DELAY_MS = Number(process.env.E2E_PRECHECK_RETRY_MS ?? 1000);

function sleep(ms) {
	return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForHttpOk(url, label, timeoutMs) {
	const startedAt = Date.now();
	let lastError = "unknown error";

	while (Date.now() - startedAt < timeoutMs) {
		try {
			const response = await fetch(url);
			if (response.ok) {
				console.log(`[e2e-precheck] ${label} ready: ${url}`);
				return;
			}
			lastError = `${label} returned HTTP ${response.status}`;
		} catch (error) {
			lastError = `${label} is unreachable (${String(error)})`;
		}

		await sleep(RETRY_DELAY_MS);
	}

	throw new Error(
		`${label} was not ready within ${timeoutMs}ms. Last error: ${lastError}`,
	);
}

async function probeLogin() {
	if (!TEST_EMAIL || !TEST_PASSWORD) {
		throw new Error(
			"Missing E2E_TEST_EMAIL or E2E_TEST_PASSWORD. Configure both before running E2E tests.",
		);
	}

	let response;
	try {
		response = await fetch(`${API_BASE_URL}/auth/login`, {
			method: "POST",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({
				email: TEST_EMAIL,
				password: TEST_PASSWORD,
				cf_turnstile_response: "e2e-smoke-token",
			}),
		});
	} catch (error) {
		throw new Error(
			`Cannot reach login API at ${API_BASE_URL}/auth/login. ${String(error)}`,
		);
	}

	let detail = "";
	try {
		const body = await response.json();
		if (typeof body?.detail === "string") {
			detail = body.detail;
		}
	} catch {
		detail = "";
	}

	if (response.status !== 200) {
		const reason =
			response.status === 401
				? "Invalid E2E credentials"
				: response.status === 403
					? "E2E account is not verified"
					: `Unexpected status ${response.status}`;

		throw new Error(
			`Login precheck failed: ${reason}${detail ? ` (${detail})` : ""}.`,
		);
	}

	console.log(`[e2e-precheck] Login probe succeeded for ${TEST_EMAIL}`);
}

async function main() {
	console.log("[e2e-precheck] Starting service and credential checks...");
	await waitForHttpOk(FRONTEND_BASE_URL, "Frontend", CHECK_TIMEOUT_MS);
	await waitForHttpOk(
		BACKEND_HEALTH_URL,
		"Backend health endpoint",
		CHECK_TIMEOUT_MS,
	);
	await probeLogin();
	console.log("[e2e-precheck] All checks passed.");
}

main().catch((error) => {
	console.error(`[e2e-precheck] ${error.message}`);
	process.exit(1);
});
