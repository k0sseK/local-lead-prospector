/**
 * useLeadStatus.ts
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
import type { Ref } from "vue";
import { useToast } from "vue-toastification";
import api from "../services/api";
import type { Lead } from "./useLeads";

export function useLeadStatus(leads: Ref<Lead[]>) {
	const toast = useToast();

	/**
	 * Aktualizuje status leada z optimistic update i revert na błąd.
	 * @param leadId - ID leada do zaktualizowania
	 * @param newStatus - Nowy status
	 */
	const updateLeadStatus = async (
		leadId: number,
		newStatus: string,
	): Promise<void> => {
		const lead = leads.value.find((l) => l.id === leadId);
		if (!lead) {
			console.warn(`useLeadStatus: lead with id=${leadId} not found`);
			return;
		}

		const previousStatus = lead.status;
		lead.status = newStatus;

		try {
			const response = await api.updateLeadStatus(leadId, newStatus);
			lead.status = (response.data as Pick<Lead, "status">).status;
		} catch (err) {
			console.error("Status update failed:", err);
			lead.status = previousStatus;
			toast.error("Błąd aktualizacji. Przywrócono stary status.");
		}
	};

	return { updateLeadStatus };
}
