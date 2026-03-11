<script setup>
import { ref, onMounted, computed } from "vue";
import api from "@/services/api.js";
import {
	GoogleMap,
	CustomMarker,
	Circle as GoogleCircle,
} from "vue3-google-map";
import { useRuntimeConfig } from "#app";
import KanbanBoard from "@/components/KanbanBoard.vue";
import { useToast } from "vue-toastification";
import { useLeadStatus } from "@/composables/useLeadStatus.js";
import { useRouter } from "#imports";
import { formatDate } from "@/utils/format.js";
import {
	CheckCircle,
	Star,
	Mail,
	Phone,
	Globe,
	MapPin,
	FileText,
	Search
} from "lucide-vue-next";

definePageMeta({
	layout: "dashboard",
	middleware: ["auth"],
});

const router = useRouter();
const toast = useToast();
const leads = ref([]);
const loading = ref(true);
const error = ref(null);
const viewMode = ref("kanban");

const { updateLeadStatus } = useLeadStatus(leads);

const fetchLeads = async () => {
	try {
		loading.value = true;
		const response = await api.getLeads();
		leads.value = response.data;
	} catch (err) {
		error.value =
			"Failed to load leads from the API. Make sure the backend is running.";
		console.error(err);
	} finally {
		loading.value = false;
	}
};

const searchKeyword = ref("");
const searchRadius = ref([5]);
const searchLimit = ref(10);
const searchCountry = ref("pl"); // kod kraju ISO 3166-1 alpha-2

const COUNTRIES = [
	{ code: "pl", name: "Polska 🇵🇱" },
	{ code: "de", name: "Niemcy 🇩🇪" },
	{ code: "fr", name: "Francja 🇫🇷" },
	{ code: "es", name: "Hiszpania 🇪🇸" },
	{ code: "it", name: "Włochy 🇮🇹" },
	{ code: "pt", name: "Portugalia 🇵🇹" },
	{ code: "nl", name: "Holandia 🇳🇱" },
	{ code: "be", name: "Belgia 🇧🇪" },
	{ code: "at", name: "Austria 🇦🇹" },
	{ code: "ch", name: "Szwajcaria 🇨🇭" },
	{ code: "cz", name: "Czechy 🇨🇿" },
	{ code: "sk", name: "Słowacja 🇸🇰" },
	{ code: "hu", name: "Węgry 🇭🇺" },
	{ code: "ro", name: "Rumunia 🇷🇴" },
	{ code: "ua", name: "Ukraina 🇺🇦" },
	{ code: "gb", name: "Wielka Brytania 🇬🇧" },
	{ code: "us", name: "USA 🇺🇸" },
];

// ─── Filtry kwalifikacji ──────────────────────────────────────────
const showFiltersPanel = ref(false);
const filterWebsite = ref("all"); // "all" | "with" | "without"
const filterMinRating = ref("");
const filterMaxRating = ref("");
const filterMinReviews = ref("");
const filterMaxReviews = ref("");

const activeFilterCount = computed(() => {
	let count = 0;
	if (filterWebsite.value !== "all") count++;
	if (filterMinRating.value !== "") count++;
	if (filterMaxRating.value !== "") count++;
	if (filterMinReviews.value !== "") count++;
	if (filterMaxReviews.value !== "") count++;
	return count;
});
// ─────────────────────────────────────────────────────────────────

const config = useRuntimeConfig();
const googleMapsApiKey = config.public.googleMapsApiKey;

const mapCenter = ref({ lat: 52.069, lng: 19.48 });
const mapZoom = ref(6);
const markerPosition = ref(null);
const isScanning = ref(false);
const isLocating = ref(false);
const scanMessage = ref(null);

// ─── Keyword Suggestions ─────────────────────────────────────────
const showKeywordPanel = ref(false);
const keywordDescription = ref("");
const isGeneratingKeywords = ref(false);
const keywordSuggestions = ref([]);
const keywordDetectedLocation = ref(null);

const generateKeywords = async () => {
	if (!keywordDescription.value.trim()) {
		toast.error("Opisz czego szukasz, aby wygenerować sugestie.");
		return;
	}
	isGeneratingKeywords.value = true;
	keywordSuggestions.value = [];
	keywordDetectedLocation.value = null;
	try {
		const res = await api.getKeywordSuggestions(keywordDescription.value);
		keywordSuggestions.value = res.data.suggestions;
		keywordDetectedLocation.value = res.data.detected_location ?? null;
	} catch (err) {
		toast.error(
			err.response?.data?.detail || "Nie udało się wygenerować sugestii.",
		);
	} finally {
		isGeneratingKeywords.value = false;
	}
};

const applyKeyword = async (kw) => {
	searchKeyword.value = kw;
	showKeywordPanel.value = false;
	keywordSuggestions.value = [];
	keywordDescription.value = "";

	const loc = keywordDetectedLocation.value;
	keywordDetectedLocation.value = null;

	if (loc) {
		try {
			const response = await fetch(
				`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(loc)}`,
			);
			const data = await response.json();
			if (data && data.length > 0) {
				const lat = parseFloat(data[0].lat);
				const lng = parseFloat(data[0].lon);
				mapCenter.value = { lat, lng };
				markerPosition.value = { lat, lng };
				mapZoom.value = 13;
				toast.success(`Lokalizacja ustawiona na: ${loc}`);
			}
		} catch {
			// lokalizacja nieznaleziona — cicho ignorujemy
		}
	}
};
// ─────────────────────────────────────────────────────────────────

const onMapClick = (e) => {
	if (e.latLng) {
		markerPosition.value = {
			lat: e.latLng.lat(),
			lng: e.latLng.lng(),
		};
	}
};

const locateUser = () => {
	if (!("geolocation" in navigator) || !navigator.geolocation) {
		toast.error(
			"Geolokalizacja nie jest obsługiwana przez Twoją przeglądarkę.",
		);
		return;
	}

	isLocating.value = true;

	navigator.geolocation.getCurrentPosition(
		(position) => {
			const lat = position.coords.latitude;
			const lng = position.coords.longitude;
			mapCenter.value = { lat, lng };
			markerPosition.value = { lat, lng };
			mapZoom.value = 13;
			isLocating.value = false;
		},
		(err) => {
			console.error("Geolocation error:", err.code, err.message);
			isLocating.value = false;
			if (err.code === 1) {
				// PERMISSION_DENIED
				toast.error(
					"Brak dostępu do lokalizacji. Zezwól na lokalizację w ustawieniach przeglądarki.",
				);
			} else if (err.code === 2) {
				// POSITION_UNAVAILABLE
				toast.error(
					"Nie można ustalić lokalizacji. Sprawdź czy GPS jest włączony.",
				);
			} else if (err.code === 3) {
				// TIMEOUT
				toast.error(
					"Pobieranie lokalizacji przekroczyło czas. Spróbuj ponownie.",
				);
			} else {
				toast.error("Nie udało się pobrać Twojej lokalizacji.");
			}
		},
		{
			enableHighAccuracy: true,
			timeout: 10000,
			maximumAge: 0,
		},
	);
};

const manualAddress = ref("");
const isSearchingAddress = ref(false);

const searchAddress = async () => {
	if (!manualAddress.value) return;

	try {
		isSearchingAddress.value = true;
		const response = await fetch(
			`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(manualAddress.value)}`,
		);
		const data = await response.json();

		if (data && data.length > 0) {
			const lat = parseFloat(data[0].lat);
			const lng = parseFloat(data[0].lon);
			mapCenter.value = { lat, lng };
			markerPosition.value = { lat, lng };
			mapZoom.value = 13;
			toast.success("Znaleziono lokalizację na podstawie adresu!");
		} else {
			toast.error("Nie udało się odnaleźć podanego adresu.");
		}
	} catch (err) {
		console.error("Geocoding error:", err);
		toast.error("Wystąpił błąd podczas wyszukiwania adresu.");
	} finally {
		isSearchingAddress.value = false;
	}
};

const runScan = async () => {
	if (!searchKeyword.value || !markerPosition.value) {
		toast.error("Wprowadź branżę i zaznacz punkt na mapie.");
		return;
	}

	if (scanLimitReached.value) {
		toast.error(
			"Wyczerpałeś miesięczny limit skanów. Przejdź na plan Pro, aby kontynuować.",
			{ timeout: 5000 },
		);
		return;
	}

	try {
		isScanning.value = true;
		error.value = null;
		scanMessage.value = null;

		const payload = {
			keyword: searchKeyword.value,
			lat: markerPosition.value.lat,
			lng: markerPosition.value.lng,
			radius_km: parseFloat(searchRadius.value[0]),
			limit: parseInt(searchLimit.value, 10),
			country_code: searchCountry.value,
			website_filter: filterWebsite.value,
			min_rating:
				filterMinRating.value !== ""
					? parseFloat(filterMinRating.value)
					: null,
			max_rating:
				filterMaxRating.value !== ""
					? parseFloat(filterMaxRating.value)
					: null,
			min_reviews:
				filterMinReviews.value !== ""
					? parseInt(filterMinReviews.value)
					: null,
			max_reviews:
				filterMaxReviews.value !== ""
					? parseInt(filterMaxReviews.value)
					: null,
		};

		const response = await api.triggerScan(payload);
		scanMessage.value = response.data.message;

		await fetchLeads();
		await fetchUsage();
	} catch (err) {
		const detail = err.response?.data?.detail;
		if (err.response?.status === 429) {
			toast.error(
				detail || "Limit skanów wyczerpany. Przejdź na plan Pro.",
			);
		} else {
			toast.error(detail || "Failed to trigger scan.");
		}
		console.error(err);
	} finally {
		isScanning.value = false;
	}
};

const handleKanbanStatusUpdate = ({ leadId, newStatus }) =>
	updateLeadStatus(leadId, newStatus);

const listSelectionMode = ref(false);
const listSelectedIds = ref(new Set());
const isListBulkProcessing = ref(false);

const handleLeadDeleted = (leadId) => {
	leads.value = leads.value.filter((l) => l.id !== leadId);
	// also deselect from list bulk selection
	const s = new Set(listSelectedIds.value);
	s.delete(leadId);
	listSelectedIds.value = s;
};

const listAllSelected = computed(
	() =>
		leads.value.length > 0 &&
		listSelectedIds.value.size === leads.value.length,
);

const toggleListSelectionMode = () => {
	listSelectionMode.value = !listSelectionMode.value;
	if (!listSelectionMode.value) listSelectedIds.value = new Set();
};

const toggleListSelectLead = (id) => {
	const s = new Set(listSelectedIds.value);
	if (s.has(id)) s.delete(id);
	else s.add(id);
	listSelectedIds.value = s;
};

const toggleListSelectAll = () => {
	if (listAllSelected.value) {
		listSelectedIds.value = new Set();
	} else {
		listSelectedIds.value = new Set(leads.value.map((l) => l.id));
	}
};

const LIST_STATUSES = [
	{ id: "new", label: "Nowe", color: "bg-gray-100 text-gray-700" },
	{
		id: "to_contact",
		label: "Do kontaktu",
		color: "bg-blue-100 text-blue-700",
	},
	{
		id: "contacted",
		label: "Wysłano ofertę",
		color: "bg-yellow-100 text-yellow-700",
	},
	{ id: "rejected", label: "Odrzucone", color: "bg-red-100 text-red-700" },
	{ id: "closed", label: "Sukces", color: "bg-green-100 text-green-700" },
];

const listBulkMoveToStatus = async (targetStatus) => {
	if (listSelectedIds.value.size === 0) return;
	isListBulkProcessing.value = true;
	try {
		const ids = [...listSelectedIds.value];
		await api.bulkUpdateStatus(ids, targetStatus);
		ids.forEach((id) => updateLeadStatus(id, targetStatus));
		const label = LIST_STATUSES.find((s) => s.id === targetStatus)?.label;
		toast.success(
			`Przeniesiono ${ids.length} lead${ids.length === 1 ? "a" : "ów"} do "${label}"`,
		);
		listSelectedIds.value = new Set();
		listSelectionMode.value = false;
	} catch (err) {
		console.error(err);
		toast.error("Błąd podczas masowej zmiany statusu.");
	} finally {
		isListBulkProcessing.value = false;
	}
};

const listBulkDelete = async () => {
	if (listSelectedIds.value.size === 0) return;
	const count = listSelectedIds.value.size;
	if (
		!confirm(
			`Czy na pewno chcesz usunąć ${count} lead${count === 1 ? "a" : "ów"}? Tej akcji nie można cofnąć.`,
		)
	)
		return;
	isListBulkProcessing.value = true;
	try {
		const ids = [...listSelectedIds.value];
		await api.bulkDeleteLeads(ids);
		ids.forEach((id) => handleLeadDeleted(id));
		toast.success(`Usunięto ${count} lead${count === 1 ? "a" : "ów"}.`);
		listSelectedIds.value = new Set();
		listSelectionMode.value = false;
	} catch (err) {
		console.error(err);
		toast.error("Błąd podczas masowego usuwania.");
	} finally {
		isListBulkProcessing.value = false;
	}
};
// ─────────────────────────────────────────────────────────────────

const exportCsv = async () => {
	try {
		const response = await api.exportLeadsCsv();
		const url = URL.createObjectURL(
			new Blob([response.data], { type: "text/csv" }),
		);
		const a = document.createElement("a");
		a.href = url;
		a.download = "leads.csv";
		a.click();
		URL.revokeObjectURL(url);
	} catch {
		toast.error("Nie udało się wyeksportować leadów.");
	}
};

// ─── Quota / Usage ───────────────────────────────────────────────
const usage = ref(null);

const fetchUsage = async () => {
	try {
		const res = await api.getUsage();
		usage.value = res.data;
	} catch {
		// nie blokuj UI jeśli endpoint zawiedzie
	}
};

const scanLimitReached = computed(
	() => usage.value && usage.value.usage.scans >= usage.value.limits.scans,
);

const auditLimitReached = computed(
	() =>
		usage.value &&
		usage.value.usage.ai_audits >= usage.value.limits.ai_audits,
);
// ─────────────────────────────────────────────────────────────────

const isAuditingAll = ref(false);
const auditAllProgress = ref({ done: 0, total: 0 });

// ─── Audit Templates ─────────────────────────────────────────────
const auditTemplates = ref([]);
const selectedTemplateId = ref(null);

const fetchAuditTemplates = async () => {
	try {
		const res = await api.getAuditTemplates();
		auditTemplates.value = res.data;
		const def = res.data.find((t) => t.is_default);
		if (def) selectedTemplateId.value = def.id;
	} catch {
		// Brak szablonów — używamy domyślnego SEO
	}
};
// ─────────────────────────────────────────────────────────────────

const auditAll = async () => {
	const unaudited = leads.value.filter((l) => !l.audited);
	if (unaudited.length === 0) {
		toast.info("Wszystkie leady są już zbadane.");
		return;
	}

	isAuditingAll.value = true;
	auditAllProgress.value = { done: 0, total: unaudited.length };

	for (const lead of unaudited) {
		try {
			const response = await api.auditLeadWithTemplate(
				lead.id,
				selectedTemplateId.value,
			);
			const updated = response.data;
			const idx = leads.value.findIndex((l) => l.id === lead.id);
			if (idx !== -1) {
				leads.value[idx] = { ...leads.value[idx], ...updated };
			}
		} catch (err) {
			if (err.response?.status === 429) {
				toast.error(
					err.response.data?.detail ||
						"Limit audytów wyczerpany. Przejdź na plan Pro.",
				);
				break;
			}
			toast.error(`Audyt nieudany: ${lead.company_name}`);
		}
		auditAllProgress.value.done++;
	}

	await fetchUsage();
	isAuditingAll.value = false;
	toast.success("Audyt wszystkich leadów zakończony!");
};

onMounted(() => {
	fetchLeads();
	fetchUsage();
	fetchAuditTemplates();
});
</script>

<template>
	<div class="px-4 py-6 md:px-8 space-y-8 bg-slate-50 min-h-screen">
		<div
			class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4"
		>
			<div>
				<h1 class="text-3xl font-bold tracking-tight text-slate-900">
					Wyszukiwarka
				</h1>
				<p class="text-slate-500 mt-2">
					Wyszukuj nowe firmy na mapie i zarządzaj lejkiem
					sprzedażowym.
				</p>
			</div>

			<!-- Licznik zużycia -->
			<div v-if="usage" class="flex flex-wrap gap-2 shrink-0">
				<span
					class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium"
					:class="
						usage.usage.ai_audits >= usage.limits.ai_audits
							? 'border-red-300 bg-red-50 text-red-700'
							: 'border-slate-200 bg-white text-slate-600'
					"
				>
					<svg
						class="w-4 h-4"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
						/>
					</svg>
					Audyty AI: {{ usage.usage.ai_audits }}/{{
						usage.limits.ai_audits
					}}
				</span>
				<span
					class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium"
					:class="
						usage.usage.scans >= usage.limits.scans
							? 'border-red-300 bg-red-50 text-red-700'
							: 'border-slate-200 bg-white text-slate-600'
					"
				>
					<svg
						class="w-4 h-4"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						/>
					</svg>
					Skany: {{ usage.usage.scans }}/{{ usage.limits.scans }}
				</span>
				<span
					class="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-medium capitalize"
					:class="
						usage.plan === 'pro'
							? 'border-brand-green/30 bg-brand-green/10 text-brand-teal'
							: 'border-slate-200 bg-white text-slate-500'
					"
				>
					{{ usage.plan === "pro" ? "Pro" : "Darmowy" }}
				</span>
			</div>
		</div>

		<div
			class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
		>
			<div class="p-6 border-b border-slate-100">
				<h3 class="text-lg font-bold text-slate-900">
					Pozyskaj Nowe Leady
				</h3>
				<p class="text-sm text-slate-500">
					Skorzystaj z wyszukiwarki opartej o Google Places
				</p>
			</div>
			<div class="p-6">
				<div class="grid grid-cols-1 md:grid-cols-12 gap-6">
					<!-- Settings form -->
					<div class="md:col-span-4 space-y-6">
						<div class="space-y-4">
							<div class="space-y-2">
								<div class="flex items-center justify-between">
									<label
										class="text-sm font-medium text-slate-700"
										>Branża / Słowo kluczowe</label
									>
									<button
										type="button"
										@click="
											showKeywordPanel = !showKeywordPanel
										"
										class="inline-flex items-center gap-1 text-xs font-medium text-brand-teal hover:text-brand-teal/90 transition-colors"
									>
										✨ Magiczne słowa kluczowe
									</button>
								</div>
								<Input
									v-model="searchKeyword"
									placeholder="np. biuro rachunkowe, dentysta"
								/>
								<!-- Inline keyword suggestion panel -->
								<div
									v-show="showKeywordPanel"
									class="mt-2 rounded-lg border border-brand-green/20 bg-brand-green/5 p-4 space-y-3"
								>
									<p
										class="text-xs font-semibold text-brand-teal uppercase tracking-wide"
									>
										Generator słów kluczowych AI
									</p>
									<textarea
										v-model="keywordDescription"
										rows="2"
										placeholder="Opisz kogo szukasz, np. chcę znaleźć hydraulików w Warszawie"
										class="w-full rounded-md border border-brand-green/20 bg-white px-3 py-2 text-sm text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-green/40 resize-none"
									/>
									<Button
										@click="generateKeywords"
										:disabled="isGeneratingKeywords"
										class="w-full bg-brand-teal hover:bg-brand-teal/90 text-white text-sm"
										size="sm"
									>
										<svg
											v-if="isGeneratingKeywords"
											class="animate-spin h-4 w-4 mr-2"
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
											/>
											<path
												class="opacity-75"
												fill="currentColor"
												d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
											/>
										</svg>
										{{
											isGeneratingKeywords
												? "Generuję..."
												: "Generuj"
										}}
									</Button>
									<div
										v-if="keywordSuggestions.length > 0"
										class="space-y-2 pt-1"
									>
										<p
											v-if="keywordDetectedLocation"
											class="text-xs text-brand-teal"
										>
											📍 Wykryto lokalizację:
											<strong>{{
												keywordDetectedLocation
											}}</strong>
											— zostanie ustawiona na mapie po
											kliknięciu.
										</p>
										<div class="flex flex-wrap gap-2">
											<Badge
												v-for="kw in keywordSuggestions"
												:key="kw"
												@click="applyKeyword(kw)"
												class="cursor-pointer bg-white border border-brand-green/30 text-brand-teal hover:bg-brand-green/10 transition-colors text-xs px-2 py-1"
											>
												{{ kw }}
											</Badge>
										</div>
									</div>
								</div>
							</div>
							<div class="space-y-2">
								<label
									class="text-sm font-medium text-slate-700"
									>Limit wyników</label
								>
								<Input
									v-model="searchLimit"
									type="number"
									min="1"
									max="60"
								/>
							</div>
							<div class="space-y-4 pt-2">
								<div class="flex justify-between">
									<label
										class="text-sm font-medium text-slate-700"
										>Promień wyszukiwania</label
									>
									<span class="text-sm text-slate-500"
										>{{ searchRadius[0] }} km</span
									>
								</div>
								<Slider
									v-model="searchRadius"
									:min="1"
									:max="50"
									:step="1"
								/>
							</div>
						</div>

						<!-- ─── Kraj wyszukiwania ──────────────────────────────────────────── -->
						<div class="pt-4 border-t border-slate-100 space-y-2">
							<label
								class="text-sm font-medium text-slate-700 flex items-center gap-1.5"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="14"
									height="14"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
								>
									<circle cx="12" cy="12" r="10" />
									<path
										d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"
									/>
								</svg>
								Kraj wyszukiwania
							</label>
							<select
								v-model="searchCountry"
								id="search-country-select"
								class="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-green/30 transition-colors"
							>
								<option
									v-for="c in COUNTRIES"
									:key="c.code"
									:value="c.code"
								>
									{{ c.name }}
								</option>
							</select>
							<p class="text-xs text-slate-400">
								Wyniki zostaną ograniczone do wybranego kraju.
							</p>
						</div>
						<!-- ──────────────────────────────────────────────────────────────── -->

						<!-- ─── Filtry kwalifikacji ─────────────────────────────────── -->
						<div class="pt-4 border-t border-slate-100">
							<button
								type="button"
								@click="showFiltersPanel = !showFiltersPanel"
								class="flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors w-full"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="14"
									height="14"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
								>
									<polygon
										points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"
									/>
								</svg>
								<span>Filtry kwalifikacji</span>
								<span
									v-if="activeFilterCount > 0"
									class="ml-1 inline-flex items-center justify-center rounded-full bg-brand-green/10 text-brand-teal text-xs font-semibold px-1.5 py-0.5 leading-none"
									>{{ activeFilterCount }} aktywne</span
								>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="14"
									height="14"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									class="ml-auto transition-transform duration-200"
									:class="
										showFiltersPanel ? 'rotate-180' : ''
									"
								>
									<polyline points="6 9 12 15 18 9" />
								</svg>
							</button>

							<div
								v-show="showFiltersPanel"
								class="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-4"
							>
								<!-- Strona WWW -->
								<div class="space-y-1.5">
									<p
										class="text-xs font-semibold text-slate-500 uppercase tracking-wide"
									>
										Strona WWW
									</p>
									<div class="flex gap-1.5">
										<button
											type="button"
											@click="filterWebsite = 'all'"
											:class="
												filterWebsite === 'all'
													? 'bg-brand-green text-white border-brand-green'
													: 'bg-white text-slate-600 border-slate-200 hover:border-brand-green'
											"
											class="flex-1 rounded-md border px-2 py-1.5 text-xs font-medium transition-all"
										>
											Wszyscy
										</button>
										<button
											type="button"
											@click="filterWebsite = 'without'"
											:class="
												filterWebsite === 'without'
													? 'bg-brand-teal text-white border-brand-teal'
													: 'bg-white text-slate-600 border-slate-200 hover:border-brand-teal/50'
											"
											class="flex-1 rounded-md border px-2 py-1.5 text-xs font-medium transition-all"
										>
											Bez strony
										</button>
										<button
											type="button"
											@click="filterWebsite = 'with'"
											:class="
												filterWebsite === 'with'
													? 'bg-brand-teal text-white border-brand-teal'
													: 'bg-white text-slate-600 border-slate-200 hover:border-brand-teal/50'
											"
											class="flex-1 rounded-md border px-2 py-1.5 text-xs font-medium transition-all"
										>
											Ze stroną
										</button>
									</div>
								</div>

								<!-- Ocena -->
								<div class="space-y-1.5">
									<p
										class="text-xs font-semibold text-slate-500 uppercase tracking-wide"
									>
										Ocena (0 – 5)
									</p>
									<div class="flex items-center gap-2">
										<div
											class="flex-1 flex items-center gap-1"
										>
											<span
												class="text-xs text-slate-400 shrink-0"
												>od</span
											>
											<input
												v-model="filterMinRating"
												type="number"
												min="0"
												max="5"
												step="0.1"
												placeholder="0.0"
												class="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-green/30"
											/>
										</div>
										<div
											class="flex-1 flex items-center gap-1"
										>
											<span
												class="text-xs text-slate-400 shrink-0"
												>do</span
											>
											<input
												v-model="filterMaxRating"
												type="number"
												min="0"
												max="5"
												step="0.1"
												placeholder="5.0"
												class="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-green/30"
											/>
										</div>
									</div>
								</div>

								<!-- Recenzje -->
								<div class="space-y-1.5">
									<p
										class="text-xs font-semibold text-slate-500 uppercase tracking-wide"
									>
										Liczba recenzji
									</p>
									<div class="flex items-center gap-2">
										<div
											class="flex-1 flex items-center gap-1"
										>
											<span
												class="text-xs text-slate-400 shrink-0"
												>min</span
											>
											<input
												v-model="filterMinReviews"
												type="number"
												min="0"
												step="1"
												placeholder="0"
												class="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-green/30"
											/>
										</div>
										<div
											class="flex-1 flex items-center gap-1"
										>
											<span
												class="text-xs text-slate-400 shrink-0"
												>max</span
											>
											<input
												v-model="filterMaxReviews"
												type="number"
												min="0"
												step="1"
												placeholder="∞"
												class="w-full rounded-md border border-slate-200 bg-white px-2 py-1.5 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-green/30"
											/>
										</div>
									</div>
								</div>
							</div>
						</div>
						<!-- ─────────────────────────────────────────────────────────── -->

						<div class="pt-4 border-t border-slate-100">
							<label
								class="text-sm font-medium text-slate-700 block mb-2"
								>Szybka lokalizacja</label
							>
							<div class="flex gap-2 mb-2">
								<Input
									v-model="manualAddress"
									@keyup.enter.prevent="searchAddress"
									placeholder="Wpisz miasto..."
									class="flex-1"
								/>
								<Button
									@click="searchAddress"
									:disabled="isSearchingAddress"
									variant="secondary"
									>Szukaj</Button
								>
							</div>
							<Button
								@click="locateUser"
								:disabled="isLocating"
								variant="outline"
								class="w-full"
							>
								<svg
									v-if="isLocating"
									class="animate-spin h-4 w-4 mr-2"
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
									width="16"
									height="16"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									class="lucide lucide-navigation mr-2"
								>
									<polygon
										points="3 11 22 2 13 21 11 13 3 11"
									/>
								</svg>
								{{
									isLocating
										? "Szukam lokalizacji..."
										: "Moja lokalizacja"
								}}
							</Button>
						</div>

						<div class="pt-4 space-y-3">
							<!-- Limit wyczerpany — upgrade CTA -->
							<div
								v-if="scanLimitReached"
								class="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-3"
							>
								<div class="flex items-start gap-3">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-5 w-5 text-amber-500 shrink-0 mt-0.5"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
										/>
									</svg>
									<div>
										<p
											class="text-sm font-semibold text-amber-800"
										>
											Miesięczny limit skanów wyczerpany
										</p>
										<p
											class="text-xs text-amber-700 mt-0.5"
										>
											Uaktualnij do planu Pro, aby uzyskać
											nieograniczone skanowania i więcej
											funkcji.
										</p>
									</div>
								</div>
								<NuxtLink
									to="/pricing"
									class="flex items-center justify-center gap-2 w-full rounded-md bg-gradient-to-r from-brand-green to-brand-teal hover:opacity-90 px-4 py-2.5 text-sm font-bold text-black transition-all shadow-sm"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-4 w-4"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M13 10V3L4 14h7v7l9-11h-7z"
										/>
									</svg>
									Przejdź na plan Pro
								</NuxtLink>
							</div>

							<Button
								@click="runScan"
								:disabled="isScanning || scanLimitReached"
								class="w-full h-12"
								:class="
									scanLimitReached
										? 'bg-slate-300 cursor-not-allowed text-slate-500 hover:bg-slate-300'
										: 'bg-brand-teal hover:bg-brand-teal/90'
								"
							>
								<span
									v-if="isScanning"
									class="flex items-center gap-2"
								>
									<svg
										class="animate-spin h-4 w-4"
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
									Skanowanie...
								</span>
								<span
									v-else-if="scanLimitReached"
									class="flex items-center gap-2"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-4 w-4"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
										/>
									</svg>
									Limit wyczerpany
								</span>
								<span v-else class="flex items-center gap-2">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										width="18"
										height="18"
										viewBox="0 0 24 24"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										stroke-linecap="round"
										stroke-linejoin="round"
										class="lucide lucide-radar"
									>
										<path
											d="M19.07 4.93A10 10 0 0 0 6.99 3.34"
										/>
										<path d="M4 6h.01" />
										<path
											d="M2.29 9.62A10 10 0 1 0 21.31 8.35"
										/>
										<path
											d="M16.24 7.76A6 6 0 1 0 8.23 16.67"
										/>
										<path d="M12 18h.01" />
										<path
											d="M17.99 11.66A6 6 0 0 1 15.77 16.67"
										/>
										<circle cx="12" cy="12" r="2" />
										<path d="m13.41 10.59 5.66-5.66" />
									</svg>
									Rozpocznij skanowanie
								</span>
							</Button>
						</div>

						<div
							v-if="scanMessage"
							class="mt-4 p-3 rounded-md bg-green-50 text-green-700 text-sm border border-green-200 flex items-center justify-between gap-3"
						>
							<span>{{ scanMessage }}</span>
							<NuxtLink
								to="/app/scan-results"
								class="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-green-600 hover:bg-green-700 text-white text-xs font-semibold transition-colors"
							>
								Zobacz wyniki
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="12"
									height="12"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2.5"
									stroke-linecap="round"
									stroke-linejoin="round"
								>
									<path d="M5 12h14" />
									<path d="m12 5 7 7-7 7" />
								</svg>
							</NuxtLink>
						</div>
					</div>

					<!-- Map -->
					<div
						class="md:col-span-8 rounded-lg overflow-hidden border border-slate-200 min-h-[400px] bg-slate-100 z-10 relative"
					>
						<GoogleMap
							:api-key="googleMapsApiKey"
							style="width: 100%; height: 100%; min-height: 400px"
							:center="mapCenter"
							:zoom="mapZoom"
							@click="onMapClick"
							:disableDefaultUI="false"
						>
							<CustomMarker
								v-if="markerPosition"
								:options="{ position: markerPosition }"
							>
								<div style="text-align: center">
									<svg
										xmlns="http://www.w3.org/2000/svg"
										width="36"
										height="36"
										viewBox="0 0 24 24"
										fill="#11998e"
										stroke="white"
										stroke-width="2"
										stroke-linecap="round"
										stroke-linejoin="round"
									>
										<path
											d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z"
										></path>
										<circle cx="12" cy="10" r="3"></circle>
									</svg>
								</div>
							</CustomMarker>
							<GoogleCircle
								v-if="markerPosition"
								:options="{
									center: markerPosition,
									radius: searchRadius[0] * 1000,
									strokeColor: '#11998e',
									strokeOpacity: 0.8,
									strokeWeight: 2,
									fillColor: '#11998e',
									fillOpacity: 0.1,
								}"
							/>
						</GoogleMap>
					</div>
				</div>
			</div>
		</div>

		<!-- Leads Section -->
		<div v-if="loading" class="text-center py-10 text-slate-500">
			Ładowanie leadów...
		</div>
		<div
			v-else-if="error"
			class="bg-red-50 text-red-700 p-4 rounded-md border border-red-200"
		>
			{{ error }}
		</div>
		<div v-else>
			<div class="flex justify-between items-center mb-4">
				<h2 class="text-xl font-bold text-slate-900">Tablica leadów</h2>
				<div class="flex items-center gap-3">
					<Button
						v-if="leads.length > 0"
						@click="exportCsv"
						variant="outline"
						size="sm"
						class="border-slate-200 text-slate-600 hover:bg-slate-50"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-3.5 w-3.5 mr-1.5"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
							/>
						</svg>
						Eksport CSV
					</Button>
					<select
						v-if="
							auditTemplates.length > 0 &&
							leads.some((l) => !l.audited)
						"
						v-model="selectedTemplateId"
						class="text-xs rounded-md border border-brand-green/30 bg-white px-2 py-1.5 text-brand-teal focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-brand-green/40"
						title="Wybierz szablon audytu"
					>
						<option :value="null">Domyślny (SEO)</option>
						<option
							v-for="t in auditTemplates"
							:key="t.id"
							:value="t.id"
						>
							{{ t.name }}
						</option>
					</select>
					<Button
						v-if="leads.some((l) => !l.audited)"
						@click="auditAll"
						:disabled="isAuditingAll"
						variant="outline"
						size="sm"
						class="border-brand-green/30 text-brand-teal hover:bg-brand-green/10"
					>
						<svg
							v-if="isAuditingAll"
							class="animate-spin h-3.5 w-3.5 mr-1.5"
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
							class="h-3.5 w-3.5 mr-1.5"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
						<span v-if="isAuditingAll">
							Audyt... {{ auditAllProgress.done }}/{{
								auditAllProgress.total
							}}
						</span>
						<span v-else>
							Audytuj wszystkie ({{
								leads.filter((l) => !l.audited).length
							}})
						</span>
					</Button>
					<div
						class="flex items-center gap-1 bg-white p-1 rounded-lg border border-slate-200 shadow-sm"
					>
						<Button
							variant="ghost"
							size="sm"
							@click="viewMode = 'kanban'"
							:class="{
								'bg-slate-100 text-slate-900':
									viewMode === 'kanban',
								'text-slate-500': viewMode !== 'kanban',
							}"
						>
							Kanban
						</Button>
						<Button
							variant="ghost"
							size="sm"
							@click="viewMode = 'list'"
							:class="{
								'bg-slate-100 text-slate-900':
									viewMode === 'list',
								'text-slate-500': viewMode !== 'list',
							}"
						>
							Lista
						</Button>
					</div>
				</div>
			</div>

			<div v-if="viewMode === 'kanban'">
				<KanbanBoard
					:leads="leads"
					@update-status="handleKanbanStatusUpdate"
					@lead-deleted="handleLeadDeleted"
				/>
			</div>

			<div v-else class="space-y-2">
				<!-- List bulk action toolbar -->
				<div
					class="flex flex-wrap items-center gap-2 px-1 py-2"
					:class="
						listSelectionMode ? 'justify-between' : 'justify-end'
					"
				>
					<template v-if="listSelectionMode">
						<div class="flex flex-wrap items-center gap-3">
							<label
								class="flex items-center gap-2 cursor-pointer select-none"
							>
								<input
									type="checkbox"
									:checked="listAllSelected"
									:indeterminate="
										listSelectedIds.size > 0 &&
										!listAllSelected
									"
									@change="toggleListSelectAll"
									class="w-4 h-4 rounded accent-brand-teal cursor-pointer"
								/>
								<span
									class="text-sm text-slate-600 font-medium"
								>
									{{
										listSelectedIds.size > 0
											? `Zaznaczono ${listSelectedIds.size}`
											: "Zaznacz wszystkie"
									}}
								</span>
							</label>

							<template v-if="listSelectedIds.size > 0">
								<div class="h-4 w-px bg-slate-200"></div>
								<span
									class="text-xs text-slate-500 font-medium uppercase tracking-wide"
									>Przenieś do:</span
								>
								<div class="flex flex-wrap gap-1">
									<button
										v-for="status in LIST_STATUSES"
										:key="status.id"
										@click="listBulkMoveToStatus(status.id)"
										:disabled="isListBulkProcessing"
										class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold transition-all hover:opacity-80 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
										:class="status.color"
									>
										{{ status.label }}
									</button>
								</div>
								<div class="h-4 w-px bg-slate-200"></div>
								<button
									@click="listBulkDelete"
									:disabled="isListBulkProcessing"
									class="inline-flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-semibold bg-red-100 text-red-700 hover:bg-red-200 transition-colors active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
								>
									<svg
										v-if="isListBulkProcessing"
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
										<polyline
											points="3 6 5 6 21 6"
										></polyline>
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

					<button
						@click="toggleListSelectionMode"
						class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
						:class="
							listSelectionMode
								? 'bg-brand-green/10 text-brand-teal hover:bg-brand-green/20'
								: 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 shadow-sm'
						"
					>
						<svg
							v-if="listSelectionMode"
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
						{{
							listSelectionMode
								? "Anuluj zaznaczanie"
								: "Zaznacz leady"
						}}
					</button>
				</div>

				<!-- List view as Cards Grid -->
				<div
					class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mt-4"
				>
					<div
						v-for="lead in leads"
						:key="lead.id"
						class="bg-white p-4 rounded-xl shadow-sm border transition-shadow cursor-pointer group flex flex-col justify-between"
						:class="[
							listSelectedIds.has(lead.id)
								? 'border-brand-green/40 ring-2 ring-brand-green/10'
								: 'border-slate-200 hover:shadow-md'
						]"
						@click="listSelectionMode ? toggleListSelectLead(lead.id) : router.push(`/app/lead/${lead.id}`)"
					>
						<div>
							<div class="flex justify-between items-start mb-2">
								<div class="flex items-start gap-2 flex-1 min-w-0">
									<input
										v-if="listSelectionMode"
										type="checkbox"
										:checked="listSelectedIds.has(lead.id)"
										@click.stop="toggleListSelectLead(lead.id)"
										class="w-4 h-4 rounded border-slate-300 text-brand-teal focus:ring-brand-green/40 cursor-pointer mt-0.5 flex-shrink-0"
									/>
									<div class="min-w-0">
										<h4
											class="text-sm font-semibold text-slate-900 leading-tight group-hover:text-brand-teal transition-colors line-clamp-2"
										>
											{{ lead.company_name }}
										</h4>
										<div class="flex flex-wrap gap-1 mt-1.5">
											<span
												class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold"
												:class="LIST_STATUSES.find((s) => s.id === lead.status)?.color || 'bg-slate-100 text-slate-700'"
											>
												{{ LIST_STATUSES.find((s) => s.id === lead.status)?.label || lead.status }}
											</span>
											<span
												v-if="!lead.has_ssl && lead.website"
												class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700 border border-red-200"
											>
												Brak SSL!
											</span>
											<span
												v-else-if="lead.slow_website"
												class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-yellow-100 text-yellow-700 border border-yellow-200"
											>
												Wolna strona
											</span>
										</div>
									</div>
								</div>
								<div
									v-if="lead.rating"
									class="flex items-center bg-yellow-50 px-1.5 py-0.5 rounded text-[11px] text-yellow-700 font-medium border border-yellow-100 flex-shrink-0 ml-2"
								>
									<Star class="w-3 h-3 text-yellow-400 fill-yellow-400 mr-0.5" />
									{{ lead.rating }}
								</div>
							</div>

							<div class="text-xs text-slate-500 space-y-1 mt-3">
								<p v-if="lead.address" class="flex items-start gap-1">
									<MapPin class="w-3 h-3 mt-0.5 flex-shrink-0 text-slate-400" />
									<span class="line-clamp-2">{{ lead.address }}</span>
								</p>
								<p v-if="lead.phone" class="flex items-center gap-1">
									<Phone class="w-3 h-3 flex-shrink-0 text-slate-400" />
									{{ lead.phone }}
								</p>
								<p v-if="lead.email" class="flex items-center gap-1 truncate">
									<Mail class="w-3 h-3 flex-shrink-0 text-slate-400" />
									{{ lead.email }}
								</p>
								<p v-if="lead.website" class="flex items-center gap-1 truncate">
									<Globe class="w-3 h-3 flex-shrink-0 text-slate-400" />
									{{ lead.website }}
								</p>
							</div>
						</div>

						<div class="mt-auto">
							<div class="mt-4">
								<button
									v-if="lead.audited"
									@click.stop="router.push(`/app/lead/${lead.id}/audit`)"
									class="w-full text-xs font-semibold py-1.5 bg-brand-green/10 text-brand-teal rounded hover:bg-brand-green/20 border border-brand-green/20 flex items-center justify-center gap-1 transition-colors"
								>
									<FileText class="w-3.5 h-3.5" />
									Raport AI
								</button>
								<button
									v-else
									@click.stop="router.push(`/app/lead/${lead.id}`)"
									class="w-full text-xs font-semibold py-1.5 bg-brand-green/10 text-brand-teal rounded hover:bg-brand-green/20 border border-brand-green/20 flex items-center justify-center gap-1 transition-colors"
								>
									<CheckCircle class="w-3.5 h-3.5" />
									Audyt AI
								</button>
							</div>

							<div class="mt-3 pt-3 border-t border-slate-100 flex justify-between items-center text-[10px] text-slate-400">
								<span class="uppercase font-semibold">ID: {{ lead.id }}</span>
								<span>{{ formatDate(lead.created_at) }}</span>
							</div>
						</div>
					</div>

					<!-- Empty State -->
					<div
						v-if="leads.length === 0"
						class="col-span-full py-12 text-center text-slate-500 bg-white rounded-xl border border-slate-200 flex flex-col items-center justify-center"
					>
						<div class="w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3">
							<Search class="w-6 h-6 text-slate-400" />
						</div>
						<p class="text-sm font-medium text-slate-900">Brak leadów</p>
						<p class="text-xs mt-1 max-w-sm">
							Użyj wyszukiwarki powyżej, aby znaleźć potencjalnych klientów w Twojej okolicy.
						</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
