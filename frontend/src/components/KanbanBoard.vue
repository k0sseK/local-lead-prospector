<script setup>
import { computed } from "vue";
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

// Reorganize leads into a reactive mutable structure for drag and drop
// VueDraggable v3 usually works best when it mutates arrays directly.
// To avoid mutating props directly (which throws warnings in Vue),
// we create a computed with setter, or we pass data up.
// Actually, the cleanest way in Vue 3 is to compute the list for each column
// and on 'change' event we emit the status change.

const getLeadsByStatus = (status) => {
	return props.leads.filter((lead) => lead.status === status);
};

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
					{{ getLeadsByStatus(column.id).length }}
				</span>
			</div>

			<!-- Draggable Area -->
			<div class="p-2 flex-1 overflow-y-auto">
				<!-- Note: vuedraggable requires an array to be passed to modelValue or list.
              Since we use computed filter, mutating it directly via v-model inside vuedraggable
              might be problematic if not two-way computed.
              We'll use `:list="getLeadsByStatus(column.id)"` to let it render,
              but rely on `@change` to synchronize data with parent.
              Wait, vuedraggable needs updatable lists to move items between lists.
         -->
				<draggable
					class="h-full min-h-[150px] space-y-3"
					:list="getLeadsByStatus(column.id)"
					group="leads"
					item-key="id"
					ghost-class="opacity-50"
					drag-class="rotate-2 scale-105"
					@change="(e) => onChange(e, column.id)"
					:animation="200"
				>
					<template #item="{ element }">
						<KanbanCard :lead="element" />
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
</style>
