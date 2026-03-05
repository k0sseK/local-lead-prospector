<script setup>
import { ref, onMounted } from "vue";
import api from "./services/api.js";
import "leaflet/dist/leaflet.css";
import { LMap, LTileLayer, LMarker, LCircle } from "@vue-leaflet/vue-leaflet";
import KanbanBoard from "./components/KanbanBoard.vue";
import { useToast } from "vue-toastification";
import { useLeadStatus } from "./composables/useLeadStatus.js";

const toast = useToast();
const leads = ref([]);
const loading = ref(true);
const error = ref(null);
const viewMode = ref("kanban"); // 'list' or 'kanban'

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
const searchRadius = ref(5.0);
const searchLimit = ref(10);
const mapCenter = ref([52.069, 19.48]);
const mapZoom = ref(6);
const markerPosition = ref(null);
const isScanning = ref(false);
const scanMessage = ref(null);

const onMapClick = (e) => {
	markerPosition.value = [e.latlng.lat, e.latlng.lng];
};

const locateUser = () => {
	if ("geolocation" in navigator) {
		navigator.geolocation.getCurrentPosition(
			(position) => {
				const lat = position.coords.latitude;
				const lng = position.coords.longitude;
				mapCenter.value = [lat, lng];
				markerPosition.value = [lat, lng];
				mapZoom.value = 13;
			},
			(error) => {
				console.error("Error getting location: ", error);
				alert("Nie udało się pobrać Twojej lokalizacji.");
			},
		);
	} else {
		alert("Geolokalizacja nie jest obsługiwana przez Twoją przeglądarkę.");
	}
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
			mapCenter.value = [lat, lng];
			markerPosition.value = [lat, lng];
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
		error.value =
			"Please provide both keyword and select a location on the map to scan.";
		return;
	}

	try {
		isScanning.value = true;
		error.value = null;
		scanMessage.value = null;

		const payload = {
			keyword: searchKeyword.value,
			lat: markerPosition.value[0],
			lng: markerPosition.value[1],
			radius_km: parseFloat(searchRadius.value),
			limit: parseInt(searchLimit.value, 10),
		};

		const response = await api.triggerScan(payload);
		scanMessage.value = response.data.message;

		// Refresh the list after scanning
		await fetchLeads();
	} catch (err) {
		error.value =
			err.response?.data?.detail ||
			"Failed to trigger scan. Check if API key is set in .env";
		console.error(err);
	} finally {
		isScanning.value = false;
	}
};

// Delegujemy do composable — obsługuje optimistic update, revert i toast
const changeStatus = (lead, newStatus) => updateLeadStatus(lead.id, newStatus);

const handleKanbanStatusUpdate = ({ leadId, newStatus }) =>
	updateLeadStatus(leadId, newStatus);

onMounted(() => {
	fetchLeads();
});
</script>

<template>
	<div class="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
		<div class="max-w-4xl mx-auto">
			<h1 class="text-3xl font-bold text-gray-900 mb-8 text-center">
				B2B Lead Generator MVP (Google Places)
			</h1>

			<!-- Formularz skanowania -->
			<div
				class="bg-white shadow px-4 py-5 sm:rounded-lg sm:p-6 mb-8 border border-gray-200"
			>
				<div class="md:grid md:grid-cols-3 md:gap-6">
					<div class="md:col-span-1">
						<h3 class="text-lg font-medium leading-6 text-gray-900">
							Pozyskaj Nowe Leady
						</h3>
						<p class="mt-1 text-sm text-gray-500">
							Wyszukaj lokalne firmy używając interaktywnej mapy.
							Zaznacz punkt i dostosuj promień.
						</p>
					</div>
					<div class="mt-5 md:mt-0 md:col-span-2">
						<form @submit.prevent="runScan">
							<div class="grid grid-cols-6 gap-6">
								<div class="col-span-6 sm:col-span-3">
									<label
										for="keyword"
										class="block text-sm font-medium text-gray-700"
										>Słowo klucz / Branża</label
									>
									<input
										v-model="searchKeyword"
										type="text"
										name="keyword"
										id="keyword"
										placeholder="np. restaurant"
										class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md border p-2"
									/>
								</div>

								<div class="col-span-6 sm:col-span-3">
									<label
										for="limit"
										class="block text-sm font-medium text-gray-700"
										>Limit wyników</label
									>
									<input
										v-model="searchLimit"
										type="number"
										min="1"
										max="20"
										name="limit"
										id="limit"
										class="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md border p-2"
									/>
								</div>

								<div class="col-span-6">
									<label
										for="radius"
										class="block text-sm font-medium text-gray-700 font-semibold"
										>Promień wyszukiwania:
										{{ searchRadius }} km</label
									>
									<input
										v-model="searchRadius"
										type="range"
										min="1"
										max="50"
										step="1"
										name="radius"
										id="radius"
										class="mt-2 w-full accent-indigo-600"
									/>
								</div>

								<div class="col-span-6">
									<div
										class="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-3"
									>
										<div class="flex-1 w-full">
											<label
												for="address"
												class="block text-sm font-medium text-gray-700 mb-1"
											>
												Wybierz obszar na mapie lub
												wpisz adres
											</label>
											<div class="flex gap-2">
												<input
													v-model="manualAddress"
													@keyup.enter.prevent="
														searchAddress
													"
													type="text"
													id="address"
													placeholder="np. Warszawa, Marszałkowska"
													class="focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md border p-2"
												/>
												<button
													type="button"
													@click="searchAddress"
													:disabled="
														isSearchingAddress
													"
													class="text-sm bg-white text-gray-700 hover:bg-gray-50 px-3 py-2 rounded-md border border-gray-300 transition-colors whitespace-nowrap shadow-sm disabled:opacity-50"
												>
													<span
														v-if="
															isSearchingAddress
														"
														>Szukam...</span
													>
													<span v-else>Szukaj</span>
												</button>
											</div>
										</div>
										<button
											type="button"
											@click="locateUser"
											class="text-sm bg-indigo-50 text-indigo-700 hover:bg-indigo-100 px-3 py-2 rounded-md border border-indigo-200 transition-colors flex items-center justify-center gap-1 shadow-sm whitespace-nowrap h-[38px]"
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
													d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
												/>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
												/>
											</svg>
											Moja lokalizacja
										</button>
									</div>
									<div
										style="
											height: 350px;
											width: 100%;
											border-radius: 0.375rem;
											overflow: hidden;
											border: 1px solid #d1d5db;
											position: relative;
											z-index: 10;
										"
									>
										<l-map
											ref="map"
											v-model:zoom="mapZoom"
											:center="mapCenter"
											@click="onMapClick"
											:useGlobalLeaflet="false"
										>
											<l-tile-layer
												url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
												layer-type="base"
												name="OpenStreetMap"
											></l-tile-layer>

											<l-marker
												v-if="markerPosition"
												:lat-lng="markerPosition"
											></l-marker>
											<l-circle
												v-if="markerPosition"
												:lat-lng="markerPosition"
												:radius="searchRadius * 1000"
												color="blue"
												fillColor="#3b82f6"
												:fillOpacity="0.2"
											></l-circle>
										</l-map>
									</div>
									<p
										v-if="!markerPosition"
										class="text-sm text-red-500 mt-1"
									>
										Kliknij na mapie, aby ustawić środek
										wyszukiwania.
									</p>
								</div>
							</div>

							<div
								class="pt-5 text-right flex justify-end items-center space-x-3"
							>
								<div
									v-if="isScanning"
									class="flex items-center text-indigo-600 text-sm"
								>
									<svg
										class="animate-spin -ml-1 mr-3 h-5 w-5 text-indigo-600"
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
									Skanowanie Google Places...
								</div>
								<button
									type="submit"
									:disabled="isScanning"
									class="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
								>
									Szukaj Leadów
								</button>
							</div>
						</form>
					</div>
				</div>

				<div
					v-if="scanMessage"
					class="mt-4 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded text-sm"
				>
					{{ scanMessage }}
				</div>
			</div>

			<div v-if="loading" class="text-center text-gray-500">
				Loading leads...
			</div>

			<div
				v-else-if="error"
				class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4"
			>
				{{ error }}
			</div>

			<div v-else>
				<!-- Toggle view -->
				<div
					class="flex justify-end mb-4 bg-white p-2 rounded shadow-sm border border-gray-100"
				>
					<div class="flex items-center space-x-2">
						<span class="text-sm text-gray-500 font-medium mr-2"
							>Widok:</span
						>
						<button
							@click="viewMode = 'kanban'"
							:class="
								viewMode === 'kanban'
									? 'bg-indigo-100 text-indigo-700'
									: 'bg-gray-50 text-gray-600 hover:bg-gray-100'
							"
							class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors focus:outline-none"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 inline-block mr-1 mb-0.5"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
								/>
							</svg>
							Kanban
						</button>
						<button
							@click="viewMode = 'list'"
							:class="
								viewMode === 'list'
									? 'bg-indigo-100 text-indigo-700'
									: 'bg-gray-50 text-gray-600 hover:bg-gray-100'
							"
							class="px-3 py-1.5 rounded-md text-sm font-medium transition-colors focus:outline-none"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-4 w-4 inline-block mr-1 mb-0.5"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M4 6h16M4 10h16M4 14h16M4 18h16"
								/>
							</svg>
							Lista
						</button>
					</div>
				</div>

				<!-- Kanban View -->
				<div v-if="viewMode === 'kanban'">
					<KanbanBoard
						:leads="leads"
						@update-status="handleKanbanStatusUpdate"
					/>
				</div>

				<!-- List View -->
				<div
					v-else
					class="bg-white shadow overflow-hidden sm:rounded-md"
				>
					<ul role="list" class="divide-y divide-gray-200">
						<li
							v-for="lead in leads"
							:key="lead.id"
							class="px-4 py-4 sm:px-6 flex items-center justify-between"
						>
							<div
								class="flex-1 min-w-0 flex flex-col justify-center"
							>
								<p
									class="text-sm font-medium text-indigo-600 truncate"
								>
									{{ lead.company_name }}
								</p>
								<p class="mt-1 text-sm text-gray-500 truncate">
									Address: {{ lead.address || "N/A" }} <br />
									Phone: {{ lead.phone || "N/A" }}
								</p>
								<p class="mt-1 text-xs text-gray-400">
									Created:
									{{
										new Date(
											lead.created_at,
										).toLocaleString()
									}}
								</p>
							</div>

							<div
								class="flex flex-col sm:flex-row items-center gap-2 ml-4"
							>
								<span
									class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize"
									:class="{
										'bg-yellow-100 text-yellow-800':
											lead.status === 'new',
										'bg-green-100 text-green-800':
											lead.status === 'contacted',
										'bg-red-100 text-red-800':
											lead.status === 'rejected',
									}"
								>
									{{ lead.status }}
								</span>
								<div
									class="flex gap-2 mt-2 sm:mt-0 flex-wrap justify-end"
								>
									<button
										v-if="lead.status !== 'contacted'"
										@click="changeStatus(lead, 'contacted')"
										class="text-xs bg-green-50 text-green-700 hover:bg-green-100 px-2 py-1 rounded border border-green-200 transition-colors"
									>
										Contacted
									</button>
									<button
										v-if="lead.status !== 'rejected'"
										@click="changeStatus(lead, 'rejected')"
										class="text-xs bg-red-50 text-red-700 hover:bg-red-100 px-2 py-1 rounded border border-red-200 transition-colors"
									>
										Reject
									</button>
									<button
										v-if="lead.status !== 'new'"
										@click="changeStatus(lead, 'new')"
										class="text-xs bg-gray-50 text-gray-700 hover:bg-gray-100 px-2 py-1 rounded border border-gray-200 transition-colors"
									>
										Reset
									</button>
								</div>
							</div>
						</li>

						<li
							v-if="leads.length === 0"
							class="px-4 py-4 sm:px-6 text-center text-gray-500"
						>
							No leads found. Run the scraper script to generate
							mock data!
						</li>
					</ul>
				</div>
			</div>
		</div>
	</div>
</template>
