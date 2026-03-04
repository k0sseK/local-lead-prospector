<script setup>
import { computed } from "vue";

const props = defineProps({
	lead: {
		type: Object,
		required: true,
	},
});

const formattedDate = computed(() => {
	if (!props.lead.created_at) return "";
	return new Date(props.lead.created_at).toLocaleDateString();
});
</script>

<template>
	<div
		class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow group relative"
	>
		<div class="flex justify-between items-start mb-2">
			<h4
				class="text-sm font-semibold text-gray-900 leading-tight group-hover:text-indigo-600 transition-colors"
			>
				{{ lead.company_name }}
			</h4>
			<div
				v-if="lead.rating"
				class="flex items-center bg-yellow-50 px-1.5 py-0.5 rounded text-xs text-yellow-700 font-medium border border-yellow-100 flex-shrink-0 ml-2"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3 w-3 text-yellow-400 mr-0.5"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
					/>
				</svg>
				{{ lead.rating }}
				<span
					v-if="lead.reviews_count"
					class="text-yellow-600/70 ml-0.5"
					>({{ lead.reviews_count }})</span
				>
			</div>
		</div>

		<div class="text-xs text-gray-500 space-y-1">
			<p class="flex items-start gap-1">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3.5 w-3.5 text-gray-400 mt-0.5 flex-shrink-0"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
					/>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
					/>
				</svg>
				<span
					class="line-clamp-2"
					:title="lead.address || 'Brak adresu'"
				>
					{{ lead.address || "Brak adresu" }}
				</span>
			</p>

			<p v-if="lead.phone" class="flex items-center gap-1">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3.5 w-3.5 text-gray-400"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
					/>
				</svg>
				<a
					:href="`tel:${lead.phone}`"
					class="hover:text-indigo-600 truncate"
					@click.stop
				>
					{{ lead.phone }}
				</a>
			</p>
		</div>
		<div
			class="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center"
		>
			<span
				class="text-[10px] text-gray-400 uppercase tracking-wider font-semibold"
			>
				ID: {{ lead.id }}
			</span>
			<span class="text-[10px] text-gray-400">
				{{ formattedDate }}
			</span>
		</div>
	</div>
</template>
