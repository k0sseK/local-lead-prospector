import axios from "axios";

const api = axios.create({
	baseURL:
		import.meta.env.NUXT_PUBLIC_API_BASE ?? "http://localhost:8000/api",
	headers: {
		"Content-Type": "application/json",
	},
});

// Request interceptor — attach JWT from cookie on every request
api.interceptors.request.use((config) => {
	const token = getCookieValue("auth_token");
	if (token) {
		config.headers.Authorization = `Bearer ${token}`;
	}
	return config;
});

// Response interceptor — redirect to /login on 401
api.interceptors.response.use(
	(response) => response,
	(error) => {
		if (error.response?.status === 401) {
			document.cookie = "auth_token=; Max-Age=0; path=/";
			window.location.href = "/login";
		}
		return Promise.reject(error);
	},
);

function getCookieValue(name) {
	const match = document.cookie.match(
		new RegExp("(^| )" + name + "=([^;]+)"),
	);
	return match ? decodeURIComponent(match[2]) : null;
}

export default {
	login(credentials) {
		return api.post("/auth/login", credentials);
	},
	register(credentials) {
		return api.post("/auth/register", credentials);
	},
	me() {
		return api.get("/auth/me");
	},
	forgotPassword(email) {
		return api.post("/auth/forgot-password", { email });
	},
	resetPassword(token, new_password) {
		return api.post("/auth/reset-password", { token, new_password });
	},
	getLeads() {
		return api.get("/leads");
	},
	updateLeadStatus(id, status) {
		return api.patch(`/leads/${id}`, { status });
	},
	triggerScan(payload) {
		return api.post("/scan", payload);
	},
	auditLead(id) {
		return api.post(`/leads/${id}/audit`);
	},
	sendEmail(id, data) {
		return api.post(`/leads/${id}/send-email`, data);
	},
	deleteLead(id) {
		return api.delete(`/leads/${id}`);
	},
	bulkUpdateStatus(ids, status) {
		return api.patch("/leads/bulk-update-status", { ids, status });
	},
	bulkDeleteLeads(ids) {
		return api.delete("/leads/bulk-delete", { data: { ids } });
	},
	updateLeadNotes(id, notes) {
		return api.patch(`/leads/${id}`, { notes });
	},
	exportLeadsCsv() {
		return api.get("/leads/export/csv", { responseType: "blob" });
	},
	getSettings() {
		return api.get("/settings");
	},
	updateSettings(data) {
		return api.put("/settings", data);
	},
};
