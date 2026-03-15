<script setup>
import { ref, onMounted } from "vue";
import api from "@/services/api";
import { toast } from "vue-sonner";
import { BookmarkCheck, Play, Trash2, ToggleLeft, ToggleRight, Clock } from "lucide-vue-next";

definePageMeta({
	layout: "dashboard",
	middleware: ["auth"],
});

const savedSearches = ref([]);
const loading = ref(true);
const runningIds = ref(new Set());
const deletingIds = ref(new Set());
const togglingIds = ref(new Set());

const SCHEDULE_LABELS = {
	manual: "Ręcznie",
	daily: "Codziennie",
	weekly: "Co tydzień",
	monthly: "Co miesiąc",
};

const fetchSavedSearches = async () => {
	loading.value = true;
	try {
		const res = await api.getSavedSearches();
		savedSearches.value = res.data;
	} catch {
		toast.error("Nie udało się pobrać zapisanych skanów.");
	} finally {
		loading.value = false;
	}
};

const runNow = async (search) => {
	if (runningIds.value.has(search.id)) return;
	runningIds.value = new Set([...runningIds.value, search.id]);
	try {
		const res = await api.runSavedSearch(search.id);
		const { task_id } = res.data;
		toast.success(`Skan "${search.name}" uruchomiony. Sprawdź wyniki za chwilę.`);

		// Poll and update last_run stats
		let attempts = 0;
		const interval = setInterval(async () => {
			attempts++;
			if (attempts > 90) {
				clearInterval(interval);
				runningIds.value = new Set([...runningIds.value].filter((id) => id !== search.id));
				return;
			}
			try {
				const statusRes = await api.getTaskStatus(task_id);
				const { status } = statusRes.data;
				if (status === "SUCCESS" || status === "FAILURE") {
					clearInterval(interval);
					runningIds.value = new Set([...runningIds.value].filter((id) => id !== search.id));
					await fetchSavedSearches(); // refresh to get last_run_at + last_run_leads
				}
			} catch { /* sieć — próbuj dalej */ }
		}, 2000);
	} catch (err) {
		toast.error(err.response?.data?.detail || "Nie udało się uruchomić skanu.");
		runningIds.value = new Set([...runningIds.value].filter((id) => id !== search.id));
	}
};

const toggleActive = async (search) => {
	if (togglingIds.value.has(search.id)) return;
	togglingIds.value = new Set([...togglingIds.value, search.id]);
	try {
		const res = await api.patchSavedSearch(search.id, { is_active: !search.is_active });
		const idx = savedSearches.value.findIndex((s) => s.id === search.id);
		if (idx !== -1) savedSearches.value[idx] = res.data;
	} catch {
		toast.error("Nie udało się zmienić statusu.");
	} finally {
		togglingIds.value = new Set([...togglingIds.value].filter((id) => id !== search.id));
	}
};

const changeSchedule = async (search, newSchedule) => {
	try {
		const res = await api.patchSavedSearch(search.id, { schedule: newSchedule });
		const idx = savedSearches.value.findIndex((s) => s.id === search.id);
		if (idx !== -1) savedSearches.value[idx] = res.data;
		toast.success("Harmonogram zaktualizowany.");
	} catch {
		toast.error("Nie udało się zaktualizować harmonogramu.");
	}
};

const deleteSaved = async (search) => {
	if (!confirm(`Usunąć skan "${search.name}"? Tej akcji nie można cofnąć.`)) return;
	deletingIds.value = new Set([...deletingIds.value, search.id]);
	try {
		await api.deleteSavedSearch(search.id);
		savedSearches.value = savedSearches.value.filter((s) => s.id !== search.id);
		toast.success("Skan usunięty.");
	} catch {
		toast.error("Nie udało się usunąć skanu.");
	} finally {
		deletingIds.value = new Set([...deletingIds.value].filter((id) => id !== search.id));
	}
};

const formatDate = (dt) => {
	if (!dt) return "—";
	return new Date(dt).toLocaleString("pl-PL", {
		day: "2-digit",
		month: "2-digit",
		year: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	});
};

onMounted(fetchSavedSearches);
</script>

<template>
	<div class="px-4 py-6 md:px-8 space-y-8 bg-slate-50 min-h-screen">
		<div class="flex items-start justify-between gap-4">
			<div>
				<h1 class="text-3xl font-bold tracking-tight text-slate-900">
					Zapisane skany
				</h1>
				<p class="text-slate-500 mt-2">
					Automatyczne skany uruchamiane wg harmonogramu.
				</p>
			</div>
			<NuxtLink
				to="/app"
				class="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-600 hover:text-brand-teal hover:border-brand-teal/40 transition-colors"
			>
				<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
				Nowy skan
			</NuxtLink>
		</div>

		<!-- Loading -->
		<div v-if="loading" class="flex justify-center py-16">
			<svg class="animate-spin h-8 w-8 text-brand-teal" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
			</svg>
		</div>

		<!-- Empty State -->
		<div
			v-else-if="savedSearches.length === 0"
			class="flex flex-col items-center justify-center py-20 text-center bg-white rounded-xl border border-slate-200"
		>
			<div class="w-14 h-14 bg-brand-green/10 rounded-full flex items-center justify-center mb-4">
				<BookmarkCheck class="w-7 h-7 text-brand-teal" />
			</div>
			<p class="text-base font-semibold text-slate-800">Brak zapisanych skanów</p>
			<p class="text-sm text-slate-500 mt-1 max-w-xs">
				Skonfiguruj skan w wyszukiwarce i kliknij „Zapisz ten skan", aby go tutaj dodać.
			</p>
			<NuxtLink
				to="/app"
				class="mt-5 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-brand-teal text-white text-sm font-semibold hover:bg-brand-teal/90 transition-colors"
			>
				Przejdź do wyszukiwarki
			</NuxtLink>
		</div>

		<!-- List -->
		<div v-else class="space-y-3">
			<div
				v-for="search in savedSearches"
				:key="search.id"
				class="bg-white rounded-xl border border-slate-200 p-5 shadow-sm"
				:class="!search.is_active ? 'opacity-60' : ''"
			>
				<div class="flex flex-col sm:flex-row sm:items-start gap-4">
					<!-- Main info -->
					<div class="flex-1 min-w-0">
						<div class="flex items-center gap-2 flex-wrap">
							<span class="text-base font-semibold text-slate-900 truncate">{{ search.name }}</span>
							<span
								class="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full border"
								:class="search.is_active ? 'bg-brand-green/10 text-brand-teal border-brand-green/20' : 'bg-slate-100 text-slate-500 border-slate-200'"
							>
								{{ search.is_active ? "Aktywny" : "Nieaktywny" }}
							</span>
						</div>

						<div class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-500">
							<span class="flex items-center gap-1">
								<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
								{{ search.keyword }}
							</span>
							<span class="flex items-center gap-1">
								<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
								{{ search.country_code.toUpperCase() }}
							</span>
							<span>{{ search.radius_km }} km · max {{ search.limit }} firm</span>
							<span v-if="search.auto_audit" class="text-brand-teal font-medium">Auto-audyt AI</span>
						</div>

						<div class="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-3">
							<!-- Schedule selector -->
							<div class="space-y-0.5">
								<p class="text-xs text-slate-400 uppercase tracking-wide font-medium">Harmonogram</p>
								<select
									:value="search.schedule"
									@change="changeSchedule(search, $event.target.value)"
									class="text-sm rounded-md border border-slate-200 bg-white px-2 py-1 text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-green/30 w-full"
								>
									<option value="manual">Ręcznie</option>
									<option value="daily">Codziennie</option>
									<option value="weekly">Co tydzień</option>
									<option value="monthly">Co miesiąc</option>
								</select>
							</div>

							<!-- Last run -->
							<div class="space-y-0.5">
								<p class="text-xs text-slate-400 uppercase tracking-wide font-medium">Ostatnie uruchomienie</p>
								<p class="text-sm text-slate-700">{{ formatDate(search.last_run_at) }}</p>
								<p v-if="search.last_run_leads != null" class="text-xs text-slate-500">
									{{ search.last_run_leads }} nowych leadów
								</p>
							</div>

							<!-- Next run -->
							<div class="space-y-0.5" v-if="search.schedule !== 'manual'">
								<p class="text-xs text-slate-400 uppercase tracking-wide font-medium">Następne uruchomienie</p>
								<p class="text-sm text-slate-700 flex items-center gap-1">
									<Clock class="w-3.5 h-3.5 text-slate-400" />
									{{ formatDate(search.next_run_at) }}
								</p>
							</div>
						</div>
					</div>

					<!-- Actions -->
					<div class="flex sm:flex-col gap-2 shrink-0">
						<!-- Run now -->
						<button
							@click="runNow(search)"
							:disabled="runningIds.has(search.id)"
							class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-brand-teal text-white text-sm font-medium hover:bg-brand-teal/90 transition-colors disabled:opacity-60"
						>
							<svg v-if="runningIds.has(search.id)" class="animate-spin w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/></svg>
							<Play v-else class="w-4 h-4" />
							{{ runningIds.has(search.id) ? "Skanowanie..." : "Uruchom" }}
						</button>

						<!-- Toggle active -->
						<button
							@click="toggleActive(search)"
							:disabled="togglingIds.has(search.id)"
							:title="search.is_active ? 'Dezaktywuj' : 'Aktywuj'"
							class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border text-sm font-medium transition-colors disabled:opacity-60"
							:class="search.is_active ? 'border-slate-200 text-slate-600 hover:border-amber-300 hover:text-amber-600' : 'border-brand-green/20 text-brand-teal hover:bg-brand-green/10'"
						>
							<ToggleRight v-if="search.is_active" class="w-4 h-4" />
							<ToggleLeft v-else class="w-4 h-4" />
							{{ search.is_active ? "Aktywny" : "Nieaktywny" }}
						</button>

						<!-- Delete -->
						<button
							@click="deleteSaved(search)"
							:disabled="deletingIds.has(search.id)"
							class="inline-flex items-center justify-center px-3 py-2 rounded-lg border border-red-100 text-red-500 hover:bg-red-50 text-sm transition-colors disabled:opacity-60"
							title="Usuń"
						>
							<Trash2 class="w-4 h-4" />
						</button>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
