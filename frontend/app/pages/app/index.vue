<script setup>
import { ref, onMounted } from "vue";
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

definePageMeta({
	layout: "dashboard",
	middleware: ["auth"],
});

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

const config = useRuntimeConfig();
const googleMapsApiKey = config.public.googleMapsApiKey;

const mapCenter = ref({ lat: 52.069, lng: 19.48 });
const mapZoom = ref(6);
const markerPosition = ref(null);
const isScanning = ref(false);
const isLocating = ref(false);
const scanMessage = ref(null);

const onMapClick = (e) => {
	if (e.latLng) {
		markerPosition.value = {
			lat: e.latLng.lat(),
			lng: e.latLng.lng(),
		};
	}
};

const locateUser = () => {
	if (!"geolocation" in navigator || !navigator.geolocation) {
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
		};

		const response = await api.triggerScan(payload);
		scanMessage.value = response.data.message;

		await fetchLeads();
	} catch (err) {
		toast.error(err.response?.data?.detail || "Failed to trigger scan.");
		console.error(err);
	} finally {
		isScanning.value = false;
	}
};

const handleKanbanStatusUpdate = ({ leadId, newStatus }) =>
	updateLeadStatus(leadId, newStatus);
const changeStatus = (lead, newStatus) => updateLeadStatus(lead.id, newStatus);

const handleLeadDeleted = (leadId) => {
	leads.value = leads.value.filter((l) => l.id !== leadId);
};

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

const isAuditingAll = ref(false);
const auditAllProgress = ref({ done: 0, total: 0 });

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
			const response = await api.auditLead(lead.id);
			const updated = response.data;
			const idx = leads.value.findIndex((l) => l.id === lead.id);
			if (idx !== -1) {
				leads.value[idx] = { ...leads.value[idx], ...updated };
			}
		} catch {
			toast.error(`Audyt nieudany: ${lead.company_name}`);
		}
		auditAllProgress.value.done++;
	}

	isAuditingAll.value = false;
	toast.success("Audyt wszystkich leadów zakończony!");
};

onMounted(() => {
	fetchLeads();
});
</script>

<template>
	<div class="px-4 py-6 md:px-8 space-y-8 bg-slate-50 min-h-screen">
		<div>
			<h1 class="text-3xl font-bold tracking-tight text-slate-900">
				Leady
			</h1>
			<p class="text-slate-500 mt-2">
				Wyszukuj nowe firmy na mapie i zarządzaj lejkiem sprzedażowym.
			</p>
		</div>

		<Card class="border-slate-200">
			<CardHeader>
				<CardTitle>Pozyskaj Nowe Leady</CardTitle>
				<CardDescription
					>Skorzystaj z wyszukiwarki opartej o Google
					Places</CardDescription
				>
			</CardHeader>
			<CardContent>
				<div class="grid grid-cols-1 md:grid-cols-12 gap-6">
					<!-- Settings form -->
					<div class="md:col-span-4 space-y-6">
						<div class="space-y-4">
							<div class="space-y-2">
								<label
									class="text-sm font-medium text-slate-700"
									>Branża / Słowo kluczowe</label
								>
								<Input
									v-model="searchKeyword"
									placeholder="np. biuro rachunkowe, dentysta"
								/>
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
								{{ isLocating ? 'Szukam lokalizacji...' : 'Moja lokalizacja' }}
							</Button>
						</div>

						<div class="pt-4">
							<Button
								@click="runScan"
								:disabled="isScanning"
								class="w-full bg-indigo-600 hover:bg-indigo-700 h-12"
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
							class="mt-4 p-3 rounded-md bg-green-50 text-green-700 text-sm border border-green-200"
						>
							{{ scanMessage }}
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
										fill="#4f46e5"
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
									strokeColor: '#4f46e5',
									strokeOpacity: 0.8,
									strokeWeight: 2,
									fillColor: '#4f46e5',
									fillOpacity: 0.1,
								}"
							/>
						</GoogleMap>
					</div>
				</div>
			</CardContent>
		</Card>

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
				<h2 class="text-xl font-semibold text-slate-900">
					Tablica leadów
				</h2>
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
					<Button
						v-if="leads.some((l) => !l.audited)"
						@click="auditAll"
						:disabled="isAuditingAll"
						variant="outline"
						size="sm"
						class="border-indigo-200 text-indigo-700 hover:bg-indigo-50"
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

			<div
				v-else
				class="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden"
			>
				<ul role="list" class="divide-y divide-slate-100">
					<li
						v-for="lead in leads"
						:key="lead.id"
						class="p-4 hover:bg-slate-50 flex items-center justify-between transition-colors"
					>
						<div class="flex-1 min-w-0">
							<p
								class="text-sm font-semibold text-indigo-600 truncate"
							>
								{{ lead.company_name }}
							</p>
							<p class="mt-1 text-sm text-slate-500 truncate">
								{{ lead.address || "Brak adresu" }} •
								{{ lead.phone || "Brak telefonu" }}
							</p>
						</div>
						<div class="flex items-center gap-3">
							<span
								class="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold capitalize bg-slate-100 text-slate-700"
							>
								{{ lead.status }}
							</span>
						</div>
					</li>
					<li
						v-if="leads.length === 0"
						class="p-8 text-center text-slate-500"
					>
						Brak leadów. Uruchom skanowanie wyszukiwarką powyżej!
					</li>
				</ul>
			</div>
		</div>
	</div>
</template>
