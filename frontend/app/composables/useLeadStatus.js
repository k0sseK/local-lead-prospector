/**
 * useLeadStatus.js
 *
 * Composable enkapsulujący logikę aktualizacji statusu leada z:
 *  - Optimistic UI update
 *  - Poprawnym revert przy błędzie API
 *  - Toast notifications
 *
 * Zastępuje dwie zduplikowane funkcje z App.vue:
 *   - changeStatus()          → widok Lista
 *   - handleKanbanStatusUpdate() → widok Kanban
 */
import { useToast } from "vue-toastification";
import api from "../services/api.js";

export function useLeadStatus(leads) {
	const toast = useToast();

	/**
	 * Aktualizuje status leada z optimistic update i revert na błąd.
	 * @param {number} leadId - ID leada do zaktualizowania
	 * @param {string} newStatus - Nowy status
	 */
	const updateLeadStatus = async (leadId, newStatus) => {
		const lead = leads.value.find((l) => l.id === leadId);
		if (!lead) {
			console.warn(`useLeadStatus: lead with id=${leadId} not found`);
			return;
		}

		const previousStatus = lead.status;
		lead.status = newStatus;

		try {
			const response = await api.updateLeadStatus(leadId, newStatus);
			lead.status = response.data.status;
		} catch (err) {
			console.error("Status update failed:", err);
			lead.status = previousStatus;
			toast.error("Błąd aktualizacji. Przywrócono stary status.");
		}
	};

	return { updateLeadStatus };
}
