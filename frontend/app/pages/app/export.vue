<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter, useRoute } from "#imports";
import { toast } from "vue-sonner";
import {
	ArrowLeft,
	Download,
	Star,
	MapPin,
	X,
	FileSpreadsheet,
	Lightbulb,
} from "lucide-vue-next";

definePageMeta({ layout: "dashboard", middleware: ["auth"] });

const router = useRouter();
const route = useRoute();

// ─── Global cached state (shared with index/scan-results) ────────────────────
const { leads, loading, fetchLeads } = useLeads();
const { quota: usage, fetchQuota } = useQuota();

const selectedIds = ref(new Set());
const isExporting = ref(false);

// Column configuration
const COLUMNS = [
	{ key: "name", label: "Nazwa firmy", default: true },
	{ key: "rating", label: "Ocena", default: true },
	{ key: "address", label: "Lokalizacja", default: true },
	{ key: "phone", label: "Telefon", default: true },
	{ key: "email", label: "Email", default: true },
	{ key: "website", label: "Strona www", default: false },
	{ key: "id", label: "ID Leadu", default: true },
	{ key: "created_at", label: "Data dodania", default: true },
	{ key: "audited", label: "Status audytu", default: false },
	{ key: "status", label: "Status lejka", default: false },
];

const selectedColumns = ref(
	new Set(COLUMNS.filter((c) => c.default).map((c) => c.key)),
);
const delimiter = ref(",");
const includeHeaders = ref(true);
const fileName = ref(
	`leads-export-${new Date().toISOString().slice(0, 10)}.csv`,
);

/** Apply ?ids= pre-selection after leads are loaded. */
function applyPreselect() {
	const idsParam = route.query.ids;
	if (idsParam) {
		const preselected = new Set(
			String(idsParam).split(",").map(Number).filter(Boolean),
		);
		selectedIds.value = new Set(
			leads.value.map((l) => l.id).filter((id) => preselected.has(id)),
		);
	} else {
		selectedIds.value = new Set(leads.value.map((l) => l.id));
	}
}

onMounted(async () => {
	// Both calls respect TTL cache — no extra API round-trips when navigating
	// from index or scan-results where leads/quota were already fetched.
	await Promise.all([fetchLeads(), fetchQuota()]);
	applyPreselect();
});

const usagePlanLabel = computed(() => {
	if (usage.value?.plan === "admin") return "Admin";
	if (usage.value?.plan === "pro") return "Pro";
	return "Darmowy";
});

const selectedLeads = computed(() =>
	leads.value.filter((l) => selectedIds.value.has(l.id)),
);
const selectedColumnList = computed(() =>
	COLUMNS.filter((c) => selectedColumns.value.has(c.key)),
);

function toggleColumn(key) {
	const s = new Set(selectedColumns.value);
	if (s.has(key)) s.delete(key);
	else s.add(key);
	selectedColumns.value = s;
}

function selectAllColumns() {
	selectedColumns.value = new Set(COLUMNS.map((c) => c.key));
}

function deselectAllColumns() {
	selectedColumns.value = new Set();
}

function removeFromSelection(id) {
	const s = new Set(selectedIds.value);
	s.delete(id);
	selectedIds.value = s;
}

function clearSelection() {
	selectedIds.value = new Set();
}

function formatDate(dt) {
	if (!dt) return "";
	return new Date(dt).toLocaleDateString("pl-PL");
}

function getLeadValue(lead, key) {
	switch (key) {
		case "name":
			return lead.company_name || "";
		case "rating":
			return lead.rating || "";
		case "address":
			return lead.address || "";
		case "phone":
			return lead.phone || "";
		case "email":
			return lead.email || "";
		case "website":
			return lead.website || "";
		case "id":
			return lead.id;
		case "created_at":
			return formatDate(lead.created_at);
		case "audited":
			return lead.audited ? "Audytowany" : "Nie audytowany";
		case "status":
			return lead.status || "new";
		default:
			return "";
	}
}

const exportCsv = async () => {
	if (selectedLeads.value.length === 0) {
		toast.error("Nie wybrano żadnych leadów.");
		return;
	}
	if (selectedColumns.value.size === 0) {
		toast.error("Nie wybrano żadnych kolumn.");
		return;
	}

	isExporting.value = true;

	try {
		const sep = delimiter.value === "tab" ? "\t" : delimiter.value;
		const cols = selectedColumnList.value;

		const rows = [];
		if (includeHeaders.value) {
			rows.push(cols.map((c) => c.label).join(sep));
		}

		for (const lead of selectedLeads.value) {
			rows.push(
				cols
					.map((c) => {
						const val = String(getLeadValue(lead, c.key));
						// Escape values with commas or quotes
						if (
							val.includes(sep) ||
							val.includes('"') ||
							val.includes("\n")
						) {
							return `"${val.replace(/"/g, '""')}"`;
						}
						return val;
					})
					.join(sep),
			);
		}

		const csvContent = rows.join("\n");
		const blob = new Blob(["\uFEFF" + csvContent], {
			type: "text/csv;charset=utf-8;",
		});
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = fileName.value.endsWith(".csv")
			? fileName.value
			: fileName.value + ".csv";
		a.click();
		URL.revokeObjectURL(url);

		toast.success("Eksport zakończony! Pobieranie rozpoczęte.");
	} catch (err) {
		toast.error("Wystąpił błąd podczas eksportu.");
		console.error(err);
	} finally {
		isExporting.value = false;
	}
};

const estimatedSize = computed(() => {
	if (selectedLeads.value.length === 0) return "0 B";
	const approxBytes =
		selectedLeads.value.length * selectedColumns.value.size * 30;
	if (approxBytes < 1024) return `${approxBytes} B`;
	return `~${Math.round(approxBytes / 1024)} KB`;
});
</script>

<template>
	<div class="px-4 py-6 md:px-8 space-y-6 bg-slate-50 min-h-screen">
		<!-- Page Header -->
		<div
			class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4"
		>
			<div>
				<h1 class="text-3xl font-bold tracking-tight text-slate-900">
					Eksport Leadów
				</h1>
				<p class="text-slate-500 mt-2">
					Skonfiguruj i pobierz wybrane leady w formacie CSV.
				</p>
			</div>

			<div v-if="usage" class="flex flex-wrap gap-2 shrink-0">
				<span
					class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-600"
				>
					<Lightbulb class="w-3.5 h-3.5 text-brand-green" />
					Kredyty: {{ usage.total_credits }}/{{
						usage.monthly_credits_limit
					}}
				</span>
				<span
					class="inline-flex items-center gap-1.5 rounded-full border bg-white px-3 py-1.5 text-sm font-medium"
					:class="
						usage.plan === 'admin'
							? 'border-amber-300 text-amber-700 bg-amber-50'
							: usage.plan === 'pro'
								? 'border-brand-green/30 text-brand-teal bg-brand-green/5'
								: 'border-slate-200 text-slate-500'
					"
				>
					{{ usagePlanLabel }}
				</span>
			</div>
		</div>

		<!-- Column Configuration -->
		<div
			class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
		>
			<div
				class="p-6 border-b border-slate-100 flex items-center justify-between"
			>
				<div>
					<h3 class="text-lg font-bold text-slate-900">
						Konfiguracja eksportu
					</h3>
					<p class="text-sm text-slate-500">
						Wybierz kolumny, które chcesz uwzględnić w pliku CSV.
					</p>
				</div>
				<div class="flex items-center gap-3">
					<button
						@click="selectAllColumns"
						class="text-sm font-medium text-brand-teal hover:text-brand-teal/90 transition-colors"
					>
						Zaznacz wszystkie
					</button>
					<span class="text-slate-300">|</span>
					<button
						@click="deselectAllColumns"
						class="text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
					>
						Odznacz wszystkie
					</button>
				</div>
			</div>

			<div class="p-6">
				<div
					class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4"
				>
					<label
						v-for="col in COLUMNS"
						:key="col.key"
						class="flex items-center gap-3 cursor-pointer group"
					>
						<input
							type="checkbox"
							:checked="selectedColumns.has(col.key)"
							@change="toggleColumn(col.key)"
							class="w-4 h-4 rounded border-slate-300 text-brand-teal focus:ring-brand-green/40 cursor-pointer"
						/>
						<span class="text-sm text-slate-700 font-medium">{{
							col.label
						}}</span>
					</label>
				</div>

				<!-- Selected columns preview -->
				<div class="mt-6 pt-6 border-t border-slate-100">
					<p class="text-sm font-medium text-slate-700 mb-3">
						Wybrane kolumny ({{ selectedColumns.size }}/{{
							COLUMNS.length
						}}):
					</p>
					<div class="flex flex-wrap gap-2">
						<span
							v-for="col in selectedColumnList"
							:key="col.key"
							class="inline-flex items-center gap-1 px-2.5 py-1 bg-brand-green/10 text-brand-teal rounded-full text-xs font-medium"
						>
							{{ col.label }}
						</span>
						<span
							v-if="selectedColumns.size === 0"
							class="text-sm text-slate-400"
							>Żadna kolumna nie jest wybrana</span
						>
					</div>
				</div>
			</div>
		</div>

		<!-- Two Column Layout -->
		<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
			<!-- Lead Selection -->
			<div
				class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
			>
				<div
					class="p-5 border-b border-slate-100 flex items-center justify-between"
				>
					<div class="flex items-center gap-3">
						<h3 class="text-base font-bold text-slate-900">
							Wybrane leady
						</h3>
						<span
							class="bg-brand-teal text-white px-2 py-0.5 rounded-full text-xs font-bold"
							>{{ selectedLeads.length }}</span
						>
					</div>
					<button
						@click="clearSelection"
						class="text-sm font-medium text-slate-500 hover:text-red-500 transition-colors flex items-center gap-1"
					>
						<X class="w-4 h-4" />
						Wyczyść
					</button>
				</div>

				<div v-if="loading" class="p-8 text-center text-slate-400">
					Ładowanie...
				</div>

				<div
					v-else-if="selectedLeads.length === 0"
					class="p-8 text-center text-slate-400"
				>
					<p class="text-sm">Żadne leady nie są wybrane.</p>
					<button
						@click="selectedIds = new Set(leads.map((l) => l.id))"
						class="mt-3 text-sm text-brand-teal hover:text-brand-teal/80 underline"
					>
						Zaznacz wszystkie
					</button>
				</div>

				<div
					v-else
					class="max-h-80 overflow-y-auto divide-y divide-slate-100"
				>
					<div
						v-for="lead in selectedLeads"
						:key="lead.id"
						class="p-4 hover:bg-slate-50 transition-colors group"
					>
						<div class="flex items-start justify-between gap-3">
							<div class="flex-1 min-w-0">
								<div class="flex items-center gap-2">
									<h4
										class="text-sm font-semibold text-slate-900 truncate"
									>
										{{ lead.company_name }}
									</h4>
									<div
										v-if="lead.rating"
										class="flex items-center bg-yellow-50 px-1.5 py-0.5 rounded text-[10px] text-yellow-700 font-medium border border-yellow-100 flex-shrink-0"
									>
										<Star
											class="w-3 h-3 text-yellow-400 fill-yellow-400 mr-0.5"
										/>
										{{ lead.rating }}
									</div>
								</div>
								<p
									v-if="lead.address"
									class="text-xs text-slate-500 mt-1 truncate flex items-center gap-1"
								>
									<MapPin class="w-3 h-3 flex-shrink-0" />
									{{ lead.address }}
								</p>
							</div>
							<button
								@click="removeFromSelection(lead.id)"
								class="text-slate-400 hover:text-red-500 transition-colors p-1 opacity-0 group-hover:opacity-100"
								title="Usuń z wyboru"
							>
								<X class="w-4 h-4" />
							</button>
						</div>
					</div>
				</div>

				<!-- Add all leads button if some are deselected -->
				<div
					v-if="!loading && selectedLeads.length < leads.length"
					class="p-3 border-t border-slate-100"
				>
					<button
						@click="selectedIds = new Set(leads.map((l) => l.id))"
						class="w-full text-sm text-brand-teal hover:text-brand-teal/80 font-medium transition-colors"
					>
						Zaznacz wszystkie {{ leads.length }} leadów
					</button>
				</div>
			</div>

			<!-- Export Options -->
			<div
				class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
			>
				<div class="p-5 border-b border-slate-100">
					<h3 class="text-base font-bold text-slate-900">
						Ustawienia pliku
					</h3>
					<p class="text-sm text-slate-500">
						Skonfiguruj format wyjściowy CSV.
					</p>
				</div>

				<div class="p-5 space-y-5">
					<!-- File Name -->
					<div class="space-y-2">
						<label
							class="text-sm font-medium text-slate-700 flex items-center gap-2"
						>
							<FileSpreadsheet class="w-4 h-4 text-slate-400" />
							Nazwa pliku
						</label>
						<input
							v-model="fileName"
							type="text"
							class="w-full h-10 px-3 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-green/30 text-sm"
						/>
						<p class="text-xs text-slate-400">
							Plik zostanie zapisany z rozszerzeniem .csv
						</p>
					</div>

					<!-- Delimiter -->
					<div class="space-y-2">
						<label class="text-sm font-medium text-slate-700"
							>Separator pól</label
						>
						<div class="grid grid-cols-3 gap-2">
							<label class="cursor-pointer">
								<input
									type="radio"
									v-model="delimiter"
									value=","
									class="sr-only peer"
								/>
								<div
									class="px-3 py-2 rounded-lg border border-slate-200 text-center text-sm transition-all peer-checked:bg-brand-green/10 peer-checked:border-brand-green/30 peer-checked:text-brand-teal hover:bg-slate-50 cursor-pointer"
								>
									Przecinek (,)
								</div>
							</label>
							<label class="cursor-pointer">
								<input
									type="radio"
									v-model="delimiter"
									value=";"
									class="sr-only peer"
								/>
								<div
									class="px-3 py-2 rounded-lg border border-slate-200 text-center text-sm transition-all peer-checked:bg-brand-green/10 peer-checked:border-brand-green/30 peer-checked:text-brand-teal hover:bg-slate-50 cursor-pointer"
								>
									Średnik (;)
								</div>
							</label>
							<label class="cursor-pointer">
								<input
									type="radio"
									v-model="delimiter"
									value="tab"
									class="sr-only peer"
								/>
								<div
									class="px-3 py-2 rounded-lg border border-slate-200 text-center text-sm transition-all peer-checked:bg-brand-green/10 peer-checked:border-brand-green/30 peer-checked:text-brand-teal hover:bg-slate-50 cursor-pointer"
								>
									Tabulator
								</div>
							</label>
						</div>
					</div>

					<!-- Include Headers -->
					<label class="flex items-center gap-3 cursor-pointer">
						<input
							type="checkbox"
							v-model="includeHeaders"
							class="w-4 h-4 rounded border-slate-300 text-brand-teal focus:ring-brand-green/40 cursor-pointer"
						/>
						<span class="text-sm text-slate-700"
							>Dołącz wiersz nagłówków</span
						>
					</label>
				</div>
			</div>
		</div>

		<!-- Action Buttons -->
		<div
			class="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-200"
		>
			<button
				@click="router.push('/app')"
				class="w-full sm:w-auto px-6 py-2.5 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all flex items-center justify-center gap-2"
			>
				<ArrowLeft class="w-4 h-4" />
				Anuluj
			</button>

			<div class="flex items-center gap-3 w-full sm:w-auto">
				<div
					class="hidden sm:flex items-center gap-2 text-sm text-slate-500 mr-4"
				>
					<FileSpreadsheet class="w-4 h-4" />
					<span
						>{{ estimatedSize }} •
						{{ selectedLeads.length }} rekordów</span
					>
				</div>
				<button
					@click="exportCsv"
					:disabled="
						isExporting ||
						selectedLeads.length === 0 ||
						selectedColumns.size === 0
					"
					class="w-full sm:w-auto px-6 py-2.5 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-semibold transition-all flex items-center justify-center gap-2 shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
				>
					<Download class="w-4 h-4" />
					{{ isExporting ? "Eksportowanie..." : "Pobierz CSV" }}
				</button>
			</div>
		</div>
	</div>
</template>
