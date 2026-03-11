import axios, {
	type AxiosInstance,
	type AxiosResponse,
	type InternalAxiosRequestConfig,
} from "axios";
import { useToast } from "vue-toastification";

// Allow the retry counter to be attached to Axios request configs
declare module "axios" {
	interface InternalAxiosRequestConfig {
		_retryCount?: number;
	}
}

// ─── Payload / request types ──────────────────────────────────────────────────

export interface LoginCredentials {
	email: string;
	password: string;
}

export interface ScanPayload {
	keyword: string;
	location: string;
	radius: number;
	limit: number;
	country?: string;
	min_rating?: number | null;
	max_rating?: number | null;
	min_reviews?: number | null;
	max_reviews?: number | null;
}

export interface EmailPayload {
	subject?: string;
	body?: string;
	[key: string]: unknown;
}

export interface AuditTemplatePayload {
	name: string;
	prompt: string;
	is_default?: boolean;
}

export interface SettingsPayload {
	sender_name?: string;
	company_name?: string;
	offer_description?: string;
	tone_of_voice?: string;
	default_email_language?: string;
	email_provider?: string;
	resend_api_key?: string;
	smtp_host?: string;
	smtp_port?: number | null;
	smtp_user?: string;
	smtp_password?: string;
	smtp_from_email?: string;
}

// ─── Axios instance ───────────────────────────────────────────────────────────

const api: AxiosInstance = axios.create({
	baseURL:
		import.meta.env.NUXT_PUBLIC_API_BASE ?? "http://localhost:8000/api",
	headers: {
		"Content-Type": "application/json",
	},
});

// Request interceptor — attach JWT from cookie on every request
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
	const token = getCookieValue("auth_token");
	if (token) {
		config.headers.Authorization = `Bearer ${token}`;
	}
	return config;
});

const _sleep = (ms: number): Promise<void> =>
	new Promise((r) => setTimeout(r, ms));

// Response interceptor — handle 401 (logout) and 429 (rate-limit backoff)
api.interceptors.response.use(
	(response: AxiosResponse) => response,
	async (error: unknown) => {
		const axiosError = error as {
			response?: { status?: number; headers?: Record<string, string> };
			config?: InternalAxiosRequestConfig;
		};

		// ── 401: clear session and redirect ──────────────────────────────────
		if (axiosError.response?.status === 401) {
			document.cookie = "auth_token=; Max-Age=0; path=/";
			window.location.href = "/login";
			return Promise.reject(error);
		}

		// ── 429: rate-limit hit — retry with exponential backoff ─────────────
		// Distinguish infrastructure rate-limit (has Retry-After header) from
		// application quota-exceeded 429 (no Retry-After) so quota errors still
		// reach the page-level handler unchanged.
		if (
			axiosError.response?.status === 429 &&
			axiosError.response.headers?.["retry-after"] &&
			axiosError.config
		) {
			const config = axiosError.config;
			config._retryCount = (config._retryCount ?? 0) + 1;

			if (config._retryCount <= 3) {
				const retryAfterSec = parseInt(
					axiosError.response.headers["retry-after"] ?? "5",
					10,
				);
				// Exponential backoff: 5 s → 10 s → 20 s (capped at 30 s)
				const delay = Math.min(
					retryAfterSec * 1000 * Math.pow(2, config._retryCount - 1),
					30_000,
				);

				if (config._retryCount === 1) {
					// Show toast only on the first hit to avoid spamming
					try {
						const toast = useToast();
						toast.warning(
							"Zbyt wiele zapytań — zwolnij na chwilę. Ponawiam automatycznie…",
							{ timeout: Math.min(delay + 2_000, 10_000) },
						);
					} catch {
						// useToast may not be available outside component context
					}
				}

				await _sleep(delay);
				return api(config);
			}

			// Exhausted all retries — inform the user
			try {
				const toast = useToast();
				toast.error(
					"Zbyt wiele zapytań do serwera. Odczekaj chwilę przed kolejną akcją.",
				);
			} catch {
				// useToast may not be available outside component context
			}
		}

		return Promise.reject(error);
	},
);

function getCookieValue(name: string): string | null {
	const match = document.cookie.match(
		new RegExp("(^| )" + name + "=([^;]+)"),
	);
	return match ? decodeURIComponent(match[2] ?? "") : null;
}

// ─── API methods ──────────────────────────────────────────────────────────────

export default {
	// Auth
	login(credentials: LoginCredentials): Promise<AxiosResponse> {
		return api.post("/auth/login", credentials);
	},
	register(credentials: LoginCredentials): Promise<AxiosResponse> {
		return api.post("/auth/register", credentials);
	},
	me(): Promise<AxiosResponse> {
		return api.get("/auth/me");
	},
	forgotPassword(email: string): Promise<AxiosResponse> {
		return api.post("/auth/forgot-password", { email });
	},
	resetPassword(token: string, new_password: string): Promise<AxiosResponse> {
		return api.post("/auth/reset-password", { token, new_password });
	},

	// Leads
	getLeads(): Promise<AxiosResponse> {
		return api.get("/leads");
	},
	updateLeadStatus(id: number, status: string): Promise<AxiosResponse> {
		return api.patch(`/leads/${id}`, { status });
	},
	updateLeadNotes(id: number, notes: string): Promise<AxiosResponse> {
		return api.patch(`/leads/${id}`, { notes });
	},
	deleteLead(id: number): Promise<AxiosResponse> {
		return api.delete(`/leads/${id}`);
	},
	bulkUpdateStatus(ids: number[], status: string): Promise<AxiosResponse> {
		return api.patch("/leads/bulk-update-status", { ids, status });
	},
	bulkDeleteLeads(ids: number[]): Promise<AxiosResponse> {
		return api.delete("/leads/bulk-delete", { data: { ids } });
	},
	exportLeadsCsv(): Promise<AxiosResponse<Blob>> {
		return api.get("/leads/export/csv", { responseType: "blob" });
	},

	// Scan
	triggerScan(payload: ScanPayload): Promise<AxiosResponse> {
		return api.post("/scan", payload);
	},

	// Audit
	auditLead(id: number): Promise<AxiosResponse> {
		return api.post(`/leads/${id}/audit`);
	},
	auditLeadWithTemplate(
		id: number,
		templateId: number | null,
		targetLanguage: string | null,
	): Promise<AxiosResponse> {
		return api.post(`/leads/${id}/audit`, {
			template_id: templateId ?? null,
			target_language: targetLanguage ?? null,
		});
	},

	// Email
	sendEmail(id: number, data: EmailPayload): Promise<AxiosResponse> {
		return api.post(`/leads/${id}/send-email`, data);
	},

	// Settings
	getSettings(): Promise<AxiosResponse> {
		return api.get("/settings");
	},
	updateSettings(data: SettingsPayload): Promise<AxiosResponse> {
		return api.put("/settings", data);
	},

	// Audit templates
	getAuditTemplates(): Promise<AxiosResponse> {
		return api.get("/settings/templates");
	},
	createAuditTemplate(data: AuditTemplatePayload): Promise<AxiosResponse> {
		return api.post("/settings/templates", data);
	},
	updateAuditTemplate(
		id: number,
		data: AuditTemplatePayload,
	): Promise<AxiosResponse> {
		return api.put(`/settings/templates/${id}`, data);
	},
	deleteAuditTemplate(id: number): Promise<AxiosResponse> {
		return api.delete(`/settings/templates/${id}`);
	},

	// Usage / quota
	getUsage(): Promise<AxiosResponse> {
		return api.get("/usage");
	},

	// Admin
	adminGetUsers(): Promise<AxiosResponse> {
		return api.get("/admin/users");
	},
	adminSetPlan(userId: number, plan: string): Promise<AxiosResponse> {
		return api.post("/admin/set-plan", { user_id: userId, plan });
	},

	// AI
	getKeywordSuggestions(description: string): Promise<AxiosResponse> {
		return api.post("/ai/keyword-suggestions", { description });
	},
	generateAuditPrompt(description: string): Promise<AxiosResponse> {
		return api.post("/ai/generate-audit-prompt", { description });
	},
};
