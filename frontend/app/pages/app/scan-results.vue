<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRouter } from "#imports";
import { toast } from "vue-sonner";
import api from "@/services/api";
import {
	ArrowLeft,
	CheckCircle,
	ChevronDown,
	Search,
	Star,
	Mail,
	Phone,
	Globe,
	X,
	RotateCcw,
	ChevronLeft,
	ChevronRight,
	CheckSquare,
	FileOutput,
	Trash2,
	MapPin,
	FileText,
} from "lucide-vue-next";
import { formatDate } from "@/utils/format.js";

definePageMeta({ layout: "dashboard", middleware: ["auth"] });

const router = useRouter();

// Server-side paginated local state (niezależny od useLeads)
const leads = ref([]);
const total = ref(0);
const loading = ref(false);

// Invaliduje cache kanban/export po mutacjach
const { invalidateLeads } = useLeads();

const searchQuery = ref("");
const sortBy = ref("newest");
const filterHasEmail = ref(false);
const filterHasPhone = ref(false);
const filterHasWebsite = ref(false);
const filterMinRating = ref(0);
const selectedIds = ref(new Set());
const page = ref(1);
const pageSize = 20;

const fetchResults = async () => {
	loading.value = true;
	try {
		const res = await api.getLeads({
			page: page.value,
			page_size: pageSize,
			search: searchQuery.value || undefined,
			sort_by: sortBy.value,
			has_email: filterHasEmail.value || undefined,
			has_phone: filterHasPhone.value || undefined,
			has_website: filterHasWebsite.value || undefined,
			min_rating:
				filterMinRating.value > 0 ? filterMinRating.value : undefined,
		});
		leads.value = res.data.items;
		total.value = res.data.total;
	} catch {
		toast.error("Nie udało się załadować leadów.");
	} finally {
		loading.value = false;
	}
};

// Zmiana filtrów/sortowania → reset do strony 1 i refetch
const resetAndFetch = () => {
	if (page.value === 1) {
		fetchResults();
	} else {
		page.value = 1; // watch(page) wyzwoli fetchResults
	}
};

watch(
	[sortBy, filterHasEmail, filterHasPhone, filterHasWebsite, filterMinRating],
	resetAndFetch,
);

// Debounce dla wyszukiwania tekstowego
let _searchTimer = null;
watch(searchQuery, () => {
	clearTimeout(_searchTimer);
	_searchTimer = setTimeout(resetAndFetch, 300);
});

// Zmiana strony → fetch
watch(page, fetchResults);

onMounted(fetchResults);

const totalPages = computed(() =>
	Math.max(1, Math.ceil(total.value / pageSize)),
);

const allSelected = computed(
	() =>
		leads.value.length > 0 &&
		leads.value.every((l) => selectedIds.value.has(l.id)),
);

const selectedCount = computed(() => selectedIds.value.size);

const statusBadgeMap = computed(() =>
	Object.fromEntries(leads.value.map((l) => [l.id, statusBadge(l)])),
);

const visiblePages = computed(() => {
	const total = totalPages.value;
	const cur = page.value;
	if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
	return [
		...new Set(
			[1, total, cur - 2, cur - 1, cur, cur + 1, cur + 2].filter(
				(p) => p >= 1 && p <= total,
			),
		),
	].sort((a, b) => a - b);
});

function toggleSelect(id) {
	const s = new Set(selectedIds.value);
	if (s.has(id)) s.delete(id);
	else s.add(id);
	selectedIds.value = s;
}

function toggleSelectAll() {
	if (allSelected.value) {
		selectedIds.value = new Set();
	} else {
		selectedIds.value = new Set(leads.value.map((l) => l.id));
	}
}

function clearSelection() {
	selectedIds.value = new Set();
}

function clearFilters() {
	searchQuery.value = "";
	filterHasEmail.value = false;
	filterHasPhone.value = false;
	filterHasWebsite.value = false;
	filterMinRating.value = 0;
}

async function bulkDelete() {
	const ids = [...selectedIds.value];
	if (!confirm(`Usunąć ${ids.length} leadów?`)) return;
	try {
		await api.bulkDeleteLeads(ids);
		selectedIds.value = new Set();
		toast.success(`Usunięto ${ids.length} leadów.`);
		invalidateLeads(); // odśwież kanban/export
		fetchResults();
	} catch {
		toast.error("Błąd podczas usuwania.");
	}
}

function statusBadge(lead) {
	if (!lead.has_ssl && lead.website_uri)
		return {
			text: "Brak SSL!",
			cls: "bg-red-100 text-red-700 border-red-200",
		};
	if (lead.slow_website)
		return {
			text: "Slow website",
			cls: "bg-yellow-100 text-yellow-700 border-yellow-200",
		};
	return null;
}
</script>

<template>
	<div class="px-4 py-6 md:px-8 space-y-6 bg-slate-50 min-h-screen">
		<!-- Page Header -->
		<div
			class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4"
		>
			<div>
				<h1 class="text-3xl font-bold tracking-tight text-slate-900">
					Wyniki Skanowania
				</h1>
				<p class="text-slate-500 mt-2">
					Znaleziono <strong>{{ total }}</strong> firm w bazie danych.
				</p>
			</div>

			<div class="flex flex-wrap items-center gap-3 shrink-0">
				<span
					class="inline-flex items-center gap-1.5 rounded-full border border-green-300 bg-green-50 px-3 py-1.5 text-sm font-medium text-green-700"
				>
					<CheckCircle class="w-4 h-4" />
					{{ total }} wyników
				</span>

				<select
					v-model="sortBy"
					class="appearance-none h-9 pl-3 pr-8 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-green/30 cursor-pointer"
				>
					<option value="newest">Najnowsze</option>
					<option value="rating">Rating (wysoki)</option>
					<option value="name">Nazwa (A-Z)</option>
				</select>
			</div>
		</div>

		<!-- Filter Panel -->
		<div class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
			<div class="flex flex-col lg:flex-row gap-4">
				<div class="flex-1 relative">
					<Search
						class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4"
					/>
					<input
						v-model="searchQuery"
						type="text"
						placeholder="Wyszukaj firmę, branżę lub słowo kluczowe..."
						class="w-full h-10 pl-10 pr-4 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-green/30 text-sm"
					/>
				</div>

				<div class="flex flex-wrap items-center gap-2">
					<button
						@click="filterMinRating = filterMinRating > 0 ? 0 : 4"
						:class="
							filterMinRating > 0
								? 'bg-brand-green/10 border-brand-green/20 text-brand-teal'
								: 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
						"
						class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors"
					>
						<Star class="w-3 h-3" />
						Rating >4.0
						<X v-if="filterMinRating > 0" class="w-3 h-3" />
					</button>
					<button
						@click="filterHasEmail = !filterHasEmail"
						:class="
							filterHasEmail
								? 'bg-green-50 border-green-200 text-green-700'
								: 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
						"
						class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors"
					>
						<Mail class="w-3 h-3" />
						Ma email
						<X v-if="filterHasEmail" class="w-3 h-3" />
					</button>
					<button
						@click="filterHasPhone = !filterHasPhone"
						:class="
							filterHasPhone
								? 'bg-blue-50 border-blue-200 text-blue-700'
								: 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
						"
						class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors"
					>
						<Phone class="w-3 h-3" />
						Ma telefon
						<X v-if="filterHasPhone" class="w-3 h-3" />
					</button>
					<button
						@click="filterHasWebsite = !filterHasWebsite"
						:class="
							filterHasWebsite
								? 'bg-amber-50 border-amber-200 text-amber-700'
								: 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
						"
						class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-medium transition-colors"
					>
						<Globe class="w-3 h-3" />
						Ma stronę
						<X v-if="filterHasWebsite" class="w-3 h-3" />
					</button>
				</div>

				<button
					@click="clearFilters"
					class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
				>
					<RotateCcw class="w-3.5 h-3.5" />
					Wyczyść
				</button>
			</div>
		</div>

		<!-- Results -->
		<div class="space-y-4">
			<div class="flex items-center justify-between">
				<h2 class="text-lg font-bold text-slate-900">
					Znalezione firmy
				</h2>
				<div class="flex items-center gap-2">
					<span class="text-sm text-slate-500"
						>Zaznacz wszystkie</span
					>
					<input
						type="checkbox"
						:checked="allSelected"
						@change="toggleSelectAll"
						class="w-4 h-4 rounded border-slate-300 text-brand-teal focus:ring-brand-green/40 cursor-pointer"
					/>
				</div>
			</div>

			<!-- Loading -->
			<div
				v-if="loading"
				class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
			>
				<div
					v-for="i in 8"
					:key="i"
					class="bg-white rounded-xl border border-slate-200 p-4 animate-pulse"
				>
					<div class="h-4 bg-slate-200 rounded mb-3 w-3/4"></div>
					<div class="h-3 bg-slate-100 rounded mb-2 w-1/2"></div>
					<div class="h-3 bg-slate-100 rounded w-2/3"></div>
				</div>
			</div>

			<!-- Empty -->
			<div
				v-else-if="leads.length === 0"
				class="text-center py-16 text-slate-500"
			>
				<Search class="w-12 h-12 mx-auto mb-4 text-slate-300" />
				<p class="text-lg font-medium">Brak wyników</p>
				<p class="text-sm mt-1">
					Spróbuj zmienić filtry lub wróć na dashboard i wykonaj
					skanowanie.
				</p>
				<button
					@click="router.push('/app')"
					class="mt-4 px-4 py-2 bg-brand-teal text-white rounded-lg text-sm font-medium hover:bg-brand-teal/90 transition-colors"
				>
					Przejdź do wyszukiwarki
				</button>
			</div>

			<!-- Cards Grid -->
			<div
				v-else
				class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
			>
				<div
					v-for="lead in leads"
					:key="lead.id"
					class="bg-white p-4 rounded-xl shadow-sm border transition-shadow cursor-pointer group"
					:class="
						selectedIds.has(lead.id)
							? 'border-brand-green/40 ring-2 ring-brand-green/10'
							: 'border-slate-200 hover:shadow-md'
					"
					@click="router.push(`/app/lead/${lead.id}`)"
				>
					<div class="flex justify-between items-start mb-2">
						<div class="flex items-start gap-2 flex-1 min-w-0">
							<input
								type="checkbox"
								:checked="selectedIds.has(lead.id)"
								@click.stop="toggleSelect(lead.id)"
								class="w-4 h-4 rounded border-slate-300 text-brand-teal focus:ring-brand-green/40 cursor-pointer mt-0.5 flex-shrink-0"
							/>
							<div class="min-w-0">
								<h4
									class="text-sm font-semibold text-slate-900 leading-tight group-hover:text-brand-teal transition-colors line-clamp-2"
								>
									{{ lead.company_name }}
								</h4>
								<span
									v-if="statusBadgeMap[lead.id]"
									class="inline-flex items-center mt-1 px-1.5 py-0.5 rounded text-[10px] font-bold border"
									:class="statusBadgeMap[lead.id].cls"
									>{{ statusBadgeMap[lead.id].text }}</span
								>
							</div>
						</div>
						<div
							v-if="lead.rating"
							class="flex items-center bg-yellow-50 px-1.5 py-0.5 rounded text-[11px] text-yellow-700 font-medium border border-yellow-100 flex-shrink-0 ml-2"
						>
							<Star
								class="w-3 h-3 text-yellow-400 fill-yellow-400 mr-0.5"
							/>
							{{ lead.rating }}
						</div>
					</div>

					<div class="text-xs text-slate-500 space-y-1">
						<p v-if="lead.address" class="flex items-start gap-1">
							<MapPin class="w-3 h-3 mt-0.5 flex-shrink-0" />
							<span class="line-clamp-1">{{ lead.address }}</span>
						</p>
						<p v-if="lead.phone" class="flex items-center gap-1">
							<Phone class="w-3 h-3 flex-shrink-0" />
							{{ lead.phone }}
						</p>
						<p
							v-if="lead.email"
							class="flex items-center gap-1 truncate"
						>
							<Mail class="w-3 h-3 flex-shrink-0" />
							{{ lead.email }}
						</p>
						<p
							v-if="lead.website_uri"
							class="flex items-center gap-1 truncate"
						>
							<Globe class="w-3 h-3 flex-shrink-0" />
							{{ lead.website_uri }}
						</p>
					</div>

					<div class="mt-3">
						<button
							v-if="lead.audited"
							@click.stop="
								router.push(`/app/lead/${lead.id}/audit`)
							"
							class="w-full text-xs font-semibold py-1.5 bg-brand-green/10 text-brand-teal rounded hover:bg-brand-green/20 border border-brand-green/20 flex items-center justify-center gap-1"
						>
							<FileText class="w-3.5 h-3.5" />
							Raport AI
						</button>
						<button
							v-else
							@click.stop="router.push(`/app/lead/${lead.id}`)"
							class="w-full text-xs font-semibold py-1.5 bg-brand-green/10 text-brand-teal rounded hover:bg-brand-green/20 border border-brand-green/20 flex items-center justify-center gap-1"
						>
							<CheckCircle class="w-3.5 h-3.5" />
							Audyt AI
						</button>
					</div>

					<div
						class="mt-3 pt-3 border-t border-slate-100 flex justify-between items-center text-[10px] text-slate-400"
					>
						<span class="uppercase font-semibold"
							>ID: {{ lead.id }}</span
						>
						<span>{{ formatDate(lead.created_at) }}</span>
					</div>
				</div>
			</div>
		</div>

		<!-- Pagination -->
		<div
			v-if="totalPages > 1"
			class="flex items-center justify-between pt-4"
		>
			<p class="text-sm text-slate-500">
				Pokazano {{ (page - 1) * pageSize + 1 }}–{{
					Math.min(page * pageSize, total)
				}}
				z {{ total }} wyników
			</p>
			<div class="flex items-center gap-2">
				<button
					@click="page = Math.max(1, page - 1)"
					:disabled="page === 1"
					class="px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition-colors"
				>
					<ChevronLeft class="w-4 h-4" />
				</button>
				<button
					v-for="p in visiblePages"
					:key="p"
					@click="page = p"
					class="px-3 py-2 rounded-lg text-sm font-semibold transition-colors"
					:class="
						p === page
							? 'bg-brand-teal text-white'
							: 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
					"
				>
					{{ p }}
				</button>
				<button
					@click="page = Math.min(totalPages, page + 1)"
					:disabled="page === totalPages"
					class="px-3 py-2 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition-colors"
				>
					<ChevronRight class="w-4 h-4" />
				</button>
			</div>
		</div>

		<!-- Bulk Toolbar -->
		<Transition
			enter-active-class="transition-all duration-300"
			enter-from-class="opacity-0 translate-y-8"
			leave-active-class="transition-all duration-300"
			leave-to-class="opacity-0 translate-y-8"
		>
			<div
				v-if="selectedCount > 0"
				class="fixed bottom-8 left-1/2 -translate-x-1/2 bg-brand-dark text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-6 border border-brand-teal/10 z-50"
			>
				<div class="flex items-center gap-2">
					<CheckSquare class="w-4 h-4 text-brand-green" />
					<span class="text-sm font-medium"
						>Zaznaczono: {{ selectedCount }}</span
					>
					<button
						@click="clearSelection"
						class="text-xs text-slate-400 hover:text-white underline ml-2"
					>
						Odznacz
					</button>
				</div>
				<div class="h-6 w-px bg-white/10"></div>
				<div class="flex items-center gap-2">
					<button
						@click="
							router.push(
								`/app/export?ids=${[...selectedIds].join(',')}`,
							)
						"
						class="px-4 py-2 rounded-lg bg-brand-green text-xs font-semibold text-brand-dark hover:bg-brand-green/80 transition-colors flex items-center gap-1.5"
					>
						<FileOutput class="w-4 h-4" />
						Eksportuj zaznaczone
					</button>
					<button
						@click="bulkDelete"
						class="px-4 py-2 rounded-lg bg-red-600/20 text-red-400 border border-red-600/30 text-xs font-semibold hover:bg-red-600/30 transition-colors flex items-center gap-1.5"
					>
						<Trash2 class="w-4 h-4" />
						Usuń
					</button>
				</div>
			</div>
		</Transition>
	</div>
</template>
