<script setup>
import { computed } from "vue";

const props = defineProps({
	lead: {
		type: Object,
		required: true,
	},
	isAuditing: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["audit-lead"]);

const isModalOpen = ref(false);

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
				class="text-sm font-semibold text-gray-900 leading-tight transition-colors flex flex-col gap-1.5"
			>
				<a
					v-if="lead.place_id"
					:href="`https://www.google.com/maps/search/?api=1&query=Google&query_place_id=${lead.place_id}`"
					target="_blank"
					@click.stop
					class="hover:text-indigo-600 hover:underline flex items-start gap-1 group/title"
					title="Otwórz w Mapach Google"
				>
					<span class="line-clamp-2 leading-tight">{{
						lead.company_name
					}}</span>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-3.5 w-3.5 flex-shrink-0 text-indigo-400 opacity-0 group-hover/title:opacity-100 transition-opacity mt-0.5"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
						/>
					</svg>
				</a>
				<span
					v-else
					class="group-hover:text-indigo-600 transition-colors"
					>{{ lead.company_name }}</span
				>
				<span
					v-if="lead.website_uri && lead.has_ssl === false"
					class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700 border border-red-200 whitespace-nowrap w-max"
				>
					Brak SSL!
				</span>
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

			<p v-if="lead.email" class="flex items-center gap-1 text-gray-600">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3.5 w-3.5 text-gray-400 flex-shrink-0"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
					/>
				</svg>
				<a
					:href="`mailto:${lead.email}`"
					class="hover:text-indigo-600 truncate"
					@click.stop
				>
					{{ lead.email }}
				</a>
			</p>
		</div>

		<div v-if="lead.audited === false" class="mt-3">
			<button
				@click.stop="emit('audit-lead', lead.id)"
				class="w-full text-xs font-semibold px-2 py-1.5 bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100 transition-colors border border-indigo-100 flex justify-center items-center"
				:disabled="isAuditing"
			>
				<span v-if="isAuditing" class="flex items-center gap-2">
					<svg
						class="animate-spin h-3.5 w-3.5 text-indigo-700"
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
					>
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
						<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
					</svg>
					Audytowanie...
				</span>
				<span v-else class="flex items-center gap-1">
					<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
						<path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
					</svg>
					Zrób Audyt Biznesowy
				</span>
			</button>
		</div>
		<div v-else-if="lead.audited === true && lead.audit_report" class="mt-3">
			<button
				@click.stop="isModalOpen = true"
				class="w-full text-xs font-semibold px-2 py-1.5 bg-purple-50 text-purple-700 rounded hover:bg-purple-100 transition-colors border border-purple-100 flex justify-center items-center gap-1"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
				</svg>
				Wynik Audytu
			</button>
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

		<!-- Audit Report Modal -->
		<div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" @click.stop="isModalOpen = false">
			<div class="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] flex flex-col overflow-hidden" @click.stop>
				<div class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
					<h3 class="font-bold text-gray-900 flex items-center gap-2 text-base">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						Raport z Audytu: {{ lead.company_name }}
					</h3>
					<button @click="isModalOpen = false" class="text-gray-400 hover:text-gray-600 transition-colors">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
						</svg>
					</button>
				</div>
				<div class="p-6 overflow-y-auto bg-white flex-1">
					<div v-if="lead.audit_report?.selling_points?.length > 0">
						<p class="text-sm text-gray-600 mb-4 font-medium">Znalezione Punkty Sprzedażowe (Selling Points):</p>
						<ul class="space-y-3">
							<li v-for="(point, idx) in lead.audit_report.selling_points" :key="idx" class="flex gap-3 bg-red-50/50 p-3 rounded-lg border border-red-100">
								<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
								  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
								</svg>
								<div>
									<span class="text-xs font-bold uppercase tracking-wider mb-1 block" :class="point.type === 'google' ? 'text-blue-600' : 'text-orange-600'">
										{{ point.type === 'google' ? 'Google Places / Profil' : 'Strona WWW' }}
									</span>
									<p class="text-sm text-gray-800 leading-snug">{{ point.message }}</p>
								</div>
							</li>
						</ul>
					</div>
					<div v-else class="text-center py-8">
						<svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-green-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
						</svg>
						<p class="text-gray-800 font-medium">Brak krytycznych błędów z naszej strony!</p>
						<p class="text-sm text-gray-500 mt-1">Strona/wizytówka wydaje się być w dobrym stanie podstawowym.</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
