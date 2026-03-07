import axios from "axios";

const api = axios.create({
	baseURL: "http://localhost:8000/api", // FastAPI default port
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
	}
);

function getCookieValue(name) {
	const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
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
	updateLeadNotes(id, notes) {
		return api.patch(`/leads/${id}`, { notes });
	},
};
