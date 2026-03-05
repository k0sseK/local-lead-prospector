<script setup>
import { ref, watch } from "vue";
import draggable from "vuedraggable";
import KanbanCard from "./KanbanCard.vue";
import { useToast } from "vue-toastification";

const props = defineProps({
	leads: {
		type: Array,
		required: true,
	},
});

const emit = defineEmits(["update-status"]);
const toast = useToast();

const auditingIds = ref(new Set());

const handleAuditLead = async (leadId) => {
	if (auditingIds.value.has(leadId)) return;

	auditingIds.value.add(leadId);
	try {
		const response = await fetch(
			`http://localhost:8000/api/leads/${leadId}/audit`,
			{
				method: "POST",
			},
		);

		if (!response.ok) {
			throw new Error("Błąd podczas audytu");
		}

		const updatedLead = await response.json();

		// Update the lead in our localColumns
		for (const columnId in localColumns.value) {
			const index = localColumns.value[columnId].findIndex(
				(l) => l.id === leadId,
			);
			if (index !== -1) {
				const localLead = localColumns.value[columnId][index];
				localLead.email = updatedLead.email;
				localLead.has_ssl = updatedLead.has_ssl;
				localLead.audited = updatedLead.audited;
				localLead.audit_report = updatedLead.audit_report;
				break;
			}
		}
		toast.success("Audyt zakończony pomyślnie");
	} catch (error) {
		console.error(error);
		toast.error("Nie udało się przeprowadzić audytu");
	} finally {
		auditingIds.value.delete(leadId);
	}
};

const COLUMNS = [
	{
		id: "new",
		title: "Nowe",
		bgColor: "bg-gray-100",
		headerColor: "text-gray-700",
	},
	{
		id: "to_contact",
		title: "Do kontaktu",
		bgColor: "bg-blue-50",
		headerColor: "text-blue-700",
	},
	{
		id: "contacted",
		title: "Wysłano ofertę",
		bgColor: "bg-yellow-50",
		headerColor: "text-yellow-700",
	},
	{
		id: "rejected",
		title: "Odrzucone",
		bgColor: "bg-red-50",
		headerColor: "text-red-700",
	},
	{
		id: "closed",
		title: "Sukces",
		bgColor: "bg-green-50",
		headerColor: "text-green-700",
	},
];

const localColumns = ref({
	new: [],
	to_contact: [],
	contacted: [],
	rejected: [],
	closed: [],
});

watch(
	() => props.leads,
	(newLeads) => {
		const newLocal = {
			new: [],
			to_contact: [],
			contacted: [],
			rejected: [],
			closed: [],
		};
		newLeads.forEach((lead) => {
			if (newLocal[lead.status]) {
				newLocal[lead.status].push(lead);
			}
		});
		localColumns.value = newLocal;
	},
	{ immediate: true, deep: true },
);

const onChange = (event, newStatus) => {
	if (event.added) {
		const lead = event.added.element;
		const oldStatus = lead.status;

		// Optimistic UI - we emit immediately. Wait, we shouldn't mutate prop directly here,
		// but vuedraggable might have already mutated the local array if we bound it via modelValue.
		// Let's emit to parent to handle the API call
		emit("update-status", {
			leadId: lead.id,
			newStatus: newStatus,
			oldStatus: oldStatus,
			lead: lead,
		});
	}
};
</script>

<template>
	<div class="flex gap-4 overflow-x-auto pb-4 items-start min-h-[600px]">
		<div
			v-for="column in COLUMNS"
			:key="column.id"
			class="flex-shrink-0 w-80 rounded-xl flex flex-col max-h-full"
			:class="column.bgColor"
		>
			<!-- Column Header -->
			<div class="p-4 flex items-center justify-between">
				<h3
					class="font-bold text-sm tracking-wide uppercase"
					:class="column.headerColor"
				>
					{{ column.title }}
				</h3>
				<span
					class="bg-white px-2 py-0.5 rounded-full text-xs font-semibold text-gray-500 shadow-sm"
				>
					{{ localColumns[column.id].length }}
				</span>
			</div>

			<!-- Draggable Area -->
			<div class="p-2 flex-1 overflow-y-auto">
				<draggable
					class="h-full min-h-[150px] space-y-3"
					v-model="localColumns[column.id]"
					group="leads"
					item-key="id"
					ghost-class="opacity-50"
					drag-class="drag-active"
					@change="(e) => onChange(e, column.id)"
					:animation="200"
				>
					<template #item="{ element }">
						<KanbanCard
							:lead="element"
							:is-auditing="auditingIds.has(element.id)"
							@audit-lead="handleAuditLead"
						/>
					</template>
				</draggable>
			</div>
		</div>
	</div>
</template>

<style scoped>
/* Hidden scrollbar but keep functionality */
.overflow-y-auto::-webkit-scrollbar {
	width: 6px;
}
.overflow-y-auto::-webkit-scrollbar-track {
	background: transparent;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
	background: rgba(156, 163, 175, 0.5);
	border-radius: 10px;
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover {
	background: rgba(107, 114, 128, 0.8);
}
.drag-active {
	transform: rotate(2deg) scale(1.05) !important;
}
</style>
