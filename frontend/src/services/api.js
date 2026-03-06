import axios from "axios";

const api = axios.create({
	baseURL: "http://localhost:8000/api", // FastAPI default port
	headers: {
		"Content-Type": "application/json",
	},
});

export default {
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
};
