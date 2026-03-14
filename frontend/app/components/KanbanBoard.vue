<script setup>
import { ref, watch, computed, onUnmounted } from "vue";
import draggable from "vuedraggable";
import KanbanCard from "@/components/KanbanCard.vue";
import { toast } from "vue-sonner";
import api from "@/services/api";
import { useTaskPoller } from "@/composables/useTaskPoller";

const props = defineProps({
	leads: {
		type: Array,
		required: true,
	},
});

const emit = defineEmits(["update-status", "lead-deleted", "audit-all-done"]);

const auditingIds = ref(new Set());

const selectionMode = ref(false);
const selectedIds = ref(new Set());
const isBulkProcessing = ref(false);

const totalLeadsCount = computed(() => {
	let count = 0;
	for (const col in localColumns.value) {
		count += localColumns.value[col].length;
	}
	return count;
});

const allSelected = computed(() => {
	return (
		totalLeadsCount.value > 0 &&
		selectedIds.value.size === totalLeadsCount.value
	);
});

const toggleSelectionMode = () => {
	selectionMode.value = !selectionMode.value;
	if (!selectionMode.value) {
		selectedIds.value = new Set();
	}
};

const toggleSelectLead = (id) => {
	const s = new Set(selectedIds.value);
	if (s.has(id)) {
		s.delete(id);
	} else {
		s.add(id);
	}
	selectedIds.value = s;
};

const toggleSelectAll = () => {
	if (allSelected.value) {
		selectedIds.value = new Set();
	} else {
		const all = new Set();
		for (const col in localColumns.value) {
			localColumns.value[col].forEach((l) => all.add(l.id));
		}
		selectedIds.value = all;
	}
};

const selectColumnAll = (columnId) => {
	const s = new Set(selectedIds.value);
	const allInCol = localColumns.value[columnId].every((l) => s.has(l.id));
	if (allInCol) {
		localColumns.value[columnId].forEach((l) => s.delete(l.id));
	} else {
		localColumns.value[columnId].forEach((l) => s.add(l.id));
	}
	selectedIds.value = s;
};

const bulkMoveToStatus = async (targetStatus) => {
	if (selectedIds.value.size === 0) return;
	isBulkProcessing.value = true;
	try {
		const ids = [...selectedIds.value];
		await api.bulkUpdateStatus(ids, targetStatus);
		ids.forEach((id) => {
			emit("update-status", { leadId: id, newStatus: targetStatus });
		});
		toast.success(
			`Przeniesiono ${ids.length} lead${ids.length === 1 ? "a" : "ów"} do "${COLUMNS.find((c) => c.id === targetStatus)?.title}"`,
		);
		selectedIds.value = new Set();
		selectionMode.value = false;
	} catch (err) {
		console.error(err);
		toast.error("Błąd podczas masowej zmiany statusu.");
	} finally {
		isBulkProcessing.value = false;
	}
};

const bulkDelete = async () => {
	if (selectedIds.value.size === 0) return;
	const count = selectedIds.value.size;
	if (
		!confirm(
			`Czy na pewno chcesz usunąć ${count} lead${count === 1 ? "a" : "ów"}? Tej akcji nie można cofnąć.`,
		)
	)
		return;

	isBulkProcessing.value = true;
	try {
		const ids = [...selectedIds.value];
		await api.bulkDeleteLeads(ids);
		ids.forEach((id) => emit("lead-deleted", id));
		toast.success(`Usunięto ${count} lead${count === 1 ? "a" : "ów"}.`);
		selectedIds.value = new Set();
		selectionMode.value = false;
	} catch (err) {
		console.error(err);
		toast.error("Błąd podczas masowego usuwania.");
	} finally {
		isBulkProcessing.value = false;
	}
};

const { pollTask } = useTaskPoller();
const _pollerCleanups = new Map();

onUnmounted(() => {
	_pollerCleanups.forEach((cancel) => cancel());
	_pollerCleanups.clear();
});

const _applyUpdatedLead = async (leadId) => {
	try {
		const res = await api.getLead(leadId);
		const updatedLead = res.data;
		for (const columnId in localColumns.value) {
			const index = localColumns.value[columnId].findIndex((l) => l.id === leadId);
			if (index !== -1) {
				const lead = localColumns.value[columnId][index];
				lead.email = updatedLead.email;
				lead.has_ssl = updatedLead.has_ssl;
				lead.audited = updatedLead.audited;
				lead.audit_report = updatedLead.audit_report;
				lead.lead_score = updatedLead.lead_score;
				break;
			}
		}
	} catch { /* ignoruj */ }
};

const handleAuditLead = async (leadId) => {
	if (auditingIds.value.has(leadId)) return;
	auditingIds.value.add(leadId);

	try {
		const response = await api.auditLead(leadId);
		const { task_id } = response.data;

		const cancel = pollTask(task_id, {
			onSuccess: async () => {
				await _applyUpdatedLead(leadId);
				auditingIds.value.delete(leadId);
				_pollerCleanups.delete(leadId);
				toast.success("Audyt AI zakończony pomyślnie!");
			},
			onError: (msg) => {
				auditingIds.value.delete(leadId);
				_pollerCleanups.delete(leadId);
				toast.error(msg || "Nie udało się przeprowadzić audytu AI.");
			},
		});

		_pollerCleanups.set(leadId, cancel);
	} catch (error) {
		auditingIds.value.delete(leadId);
		toast.error(error.response?.data?.detail || "Nie udało się przeprowadzić audytu AI.");
	}
};

const COLUMNS = [
	{
		id: "new",
		title: "Nowe",
		bgColor: "bg-gray-100",
		headerColor: "text-gray-700",
		badgeColor: "bg-gray-200 text-gray-700",
	},
	{
		id: "to_contact",
		title: "Do kontaktu",
		bgColor: "bg-blue-50",
		headerColor: "text-blue-700",
		badgeColor: "bg-blue-100 text-blue-700",
	},
	{
		id: "contacted",
		title: "Wysłano ofertę",
		bgColor: "bg-yellow-50",
		headerColor: "text-yellow-700",
		badgeColor: "bg-yellow-100 text-yellow-700",
	},
	{
		id: "rejected",
		title: "Odrzucone",
		bgColor: "bg-red-50",
		headerColor: "text-red-700",
		badgeColor: "bg-red-100 text-red-700",
	},
	{
		id: "closed",
		title: "Sukces",
		bgColor: "bg-green-50",
		headerColor: "text-green-700",
		badgeColor: "bg-green-100 text-green-700",
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

const isAuditingAll = ref(false);
const auditAllProgress = ref({ done: 0, total: 0 });

const auditAll = async () => {
	const unaudited = [];
	for (const columnId in localColumns.value) {
		localColumns.value[columnId].forEach((l) => {
			if (!l.audited) unaudited.push(l);
		});
	}
	if (unaudited.length === 0) {
		toast.info("Wszystkie leady są już zbadane.");
		return;
	}

	isAuditingAll.value = true;
	auditAllProgress.value = { done: 0, total: unaudited.length };

	for (const lead of unaudited) {
		await handleAuditLead(lead.id);
		auditAllProgress.value.done++;
	}

	isAuditingAll.value = false;
	emit("audit-all-done");
};

const handleLeadDeleted = (leadId) => {
	for (const columnId in localColumns.value) {
		const idx = localColumns.value[columnId].findIndex(
			(l) => l.id === leadId,
		);
		if (idx !== -1) {
			localColumns.value[columnId].splice(idx, 1);
			break;
		}
	}
	// Also deselect
	const s = new Set(selectedIds.value);
	s.delete(leadId);
	selectedIds.value = s;
	emit("lead-deleted", leadId);
};

const onChange = (event, newStatus) => {
	if (event.added) {
		const lead = event.added.element;
		const oldStatus = lead.status;
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
	<div class="space-y-3">
		<!-- Bulk Action Toolbar -->
		<div
			class="flex flex-wrap items-center gap-2 px-1 py-2"
			:class="selectionMode ? 'justify-between' : 'justify-end'"
		>
			<!-- Selection mode controls -->
			<template v-if="selectionMode">
				<div class="flex items-center gap-3">
					<!-- Select All checkbox -->
					<label
						class="flex items-center gap-2 cursor-pointer select-none"
					>
						<input
							type="checkbox"
							:checked="allSelected"
							:indeterminate="
								selectedIds.size > 0 && !allSelected
							"
							@change="toggleSelectAll"
							class="w-4 h-4 rounded accent-indigo-600 cursor-pointer"
						/>
						<span class="text-sm text-slate-600 font-medium">
							{{
								selectedIds.size > 0
									? `Zaznaczono ${selectedIds.size}`
									: "Zaznacz wszystkie"
							}}
						</span>
					</label>

					<!-- Bulk action buttons — only shown when something is selected -->
					<template v-if="selectedIds.size > 0">
						<div class="h-4 w-px bg-slate-200"></div>
						<span
							class="text-xs text-slate-500 font-medium uppercase tracking-wide"
							>Przenieś do:</span
						>
						<div class="flex flex-wrap gap-1">
							<button
								v-for="col in COLUMNS"
								:key="col.id"
								@click="bulkMoveToStatus(col.id)"
								:disabled="isBulkProcessing"
								class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold transition-all hover:opacity-80 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
								:class="col.badgeColor"
							>
								{{ col.title }}
							</button>
						</div>
						<div class="h-4 w-px bg-slate-200"></div>
						<button
							@click="bulkDelete"
							:disabled="isBulkProcessing"
							class="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold bg-red-100 text-red-700 hover:bg-red-200 transition-colors active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
						>
							<svg
								v-if="isBulkProcessing"
								class="animate-spin h-3 w-3"
								xmlns="http://www.w3.org/2000/svg"
								fill="none"
								viewBox="0 0 24 24"
							>
								<circle
									class="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									stroke-width="4"
								></circle>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								></path>
							</svg>
							<svg
								v-else
								xmlns="http://www.w3.org/2000/svg"
								width="12"
								height="12"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<polyline points="3 6 5 6 21 6"></polyline>
								<path
									d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"
								></path>
								<path d="M10 11v6"></path>
								<path d="M14 11v6"></path>
								<path
									d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"
								></path>
							</svg>
							Usuń zaznaczone
						</button>
					</template>
				</div>
			</template>

			<!-- Toggle selection mode button -->
			<button
				@click="toggleSelectionMode"
				class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
				:class="
					selectionMode
						? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
						: 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 shadow-sm'
				"
			>
				<svg
					v-if="selectionMode"
					xmlns="http://www.w3.org/2000/svg"
					width="13"
					height="13"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2.5"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<line x1="18" y1="6" x2="6" y2="18"></line>
					<line x1="6" y1="6" x2="18" y2="18"></line>
				</svg>
				<svg
					v-else
					xmlns="http://www.w3.org/2000/svg"
					width="13"
					height="13"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<rect
						x="3"
						y="3"
						width="18"
						height="18"
						rx="2"
						ry="2"
					></rect>
					<polyline points="9 11 12 14 22 4"></polyline>
				</svg>
				{{ selectionMode ? "Anuluj zaznaczanie" : "Zaznacz leady" }}
			</button>
		</div>

		<!-- Kanban Board -->
		<div class="flex gap-4 overflow-x-auto pb-4 items-start min-h-[600px]">
			<div
				v-for="column in COLUMNS"
				:key="column.id"
				class="flex-shrink-0 w-80 rounded-xl flex flex-col max-h-full"
				:class="column.bgColor"
			>
				<!-- Column Header -->
				<div class="p-4 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<!-- Column select-all checkbox -->
						<label
							v-if="
								selectionMode &&
								localColumns[column.id].length > 0
							"
							class="cursor-pointer"
							:title="`Zaznacz wszystkie w kolumnie ${column.title}`"
						>
							<input
								type="checkbox"
								:checked="
									localColumns[column.id].every((l) =>
										selectedIds.has(l.id),
									)
								"
								:indeterminate="
									localColumns[column.id].some((l) =>
										selectedIds.has(l.id),
									) &&
									!localColumns[column.id].every((l) =>
										selectedIds.has(l.id),
									)
								"
								@change="selectColumnAll(column.id)"
								class="w-4 h-4 rounded accent-indigo-600 cursor-pointer"
							/>
						</label>
						<h3
							class="font-bold text-sm tracking-wide uppercase"
							:class="column.headerColor"
						>
							{{ column.title }}
						</h3>
					</div>
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
						:disabled="selectionMode"
					>
						<template #item="{ element }">
							<div
								class="relative"
								:class="selectionMode ? 'cursor-pointer' : ''"
								@click.capture="
									selectionMode
										? toggleSelectLead(element.id)
										: undefined
								"
							>
								<!-- Selection overlay -->
								<Transition name="fade">
									<div
										v-if="selectionMode"
										class="absolute inset-0 z-10 rounded-xl pointer-events-none transition-colors"
										:class="
											selectedIds.has(element.id)
												? 'ring-2 ring-indigo-500 bg-indigo-50/40 rounded-xl'
												: 'hover:bg-black/5 rounded-xl'
										"
									>
										<div class="absolute top-2 right-2">
											<div
												class="w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all"
												:class="
													selectedIds.has(element.id)
														? 'bg-indigo-600 border-indigo-600'
														: 'bg-white border-slate-300'
												"
											>
												<svg
													v-if="
														selectedIds.has(
															element.id,
														)
													"
													xmlns="http://www.w3.org/2000/svg"
													width="10"
													height="10"
													viewBox="0 0 24 24"
													fill="none"
													stroke="white"
													stroke-width="3.5"
													stroke-linecap="round"
													stroke-linejoin="round"
												>
													<polyline
														points="20 6 9 17 4 12"
													></polyline>
												</svg>
											</div>
										</div>
									</div>
								</Transition>
								<KanbanCard
									:lead="element"
									:is-auditing="auditingIds.has(element.id)"
									@audit-lead="handleAuditLead"
									@lead-deleted="handleLeadDeleted"
								/>
							</div>
						</template>
					</draggable>
				</div>
			</div>
		</div>
	</div>
</template>

<style scoped>
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

.fade-enter-active,
.fade-leave-active {
	transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
	opacity: 0;
}
</style>
