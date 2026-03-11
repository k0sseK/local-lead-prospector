<script setup>
import { ref, computed, onMounted } from "vue";
import { useToast } from "vue-toastification";
import api from "@/services/api.js";
import { formatDate } from "@/utils/format.js";
import {
	Users,
	Activity,
	Zap,
	CheckCircle,
	Gauge,
	Database,
	Server,
	TrendingUp,
	Search,
	Shield,
} from "lucide-vue-next";

definePageMeta({
	layout: "dashboard",
	middleware: ["auth"],
});

const toast = useToast();

const users = ref([]);
const loading = ref(true);
const searchQuery = ref("");
const updatingUserId = ref(null);

const fetchUsers = async () => {
	try {
		loading.value = true;
		const res = await api.adminGetUsers();
		users.value = res.data;
	} catch (err) {
		if (err.response?.status === 403) {
			toast.error("Brak uprawnień administratora.");
		} else {
			toast.error("Nie udało się załadować użytkowników.");
		}
	} finally {
		loading.value = false;
	}
};

onMounted(fetchUsers);

const filteredUsers = computed(() => {
	if (!searchQuery.value) return users.value;
	const q = searchQuery.value.toLowerCase();
	return users.value.filter((u) => u.email?.toLowerCase().includes(q));
});

const setPlan = async (userId, plan) => {
	updatingUserId.value = userId;
	try {
		await api.adminSetPlan(userId, plan);
		const user = users.value.find((u) => u.id === userId);
		if (user) user.plan = plan;
		toast.success(
			`Plan zmieniony na "${plan === "pro" ? "Pro" : "Darmowy"}".`,
		);
	} catch (err) {
		toast.error(
			err.response?.data?.detail || "Nie udało się zmienić planu.",
		);
	} finally {
		updatingUserId.value = null;
	}
};

function initials(email) {
	if (!email) return "?";
	return email.substring(0, 2).toUpperCase();
}

function avatarColor(email) {
	const colors = [
		"bg-brand-green/10 text-brand-teal",
		"bg-pink-100 text-pink-600",
		"bg-green-100 text-green-600",
		"bg-purple-100 text-purple-600",
		"bg-blue-100 text-blue-600",
		"bg-orange-100 text-orange-600",
		"bg-teal-100 text-teal-600",
	];
	if (!email) return colors[0];
	const idx = email.charCodeAt(0) % colors.length;
	return colors[idx];
}

const totalUsers = computed(() => users.value.length);
const proUsers = computed(
	() => users.value.filter((u) => u.plan === "pro").length,
);
const freeUsers = computed(
	() => users.value.filter((u) => u.plan !== "pro").length,
);
</script>

<template>
	<div class="px-4 py-6 md:px-8 space-y-6 bg-slate-50 min-h-screen">
		<!-- Page Header -->
		<div
			class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4"
		>
			<div>
				<h1 class="text-3xl font-bold tracking-tight text-slate-900">
					Panel Admina
				</h1>
				<p class="text-slate-500 mt-2">
					Zarządzaj systemem, użytkownikami i monitoruj wydajność
				</p>
			</div>

			<div class="flex flex-wrap items-center gap-3 shrink-0">
				<span
					class="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700"
				>
					<Users class="w-4 h-4 text-green-500" />
					{{ totalUsers }} użytkowników
				</span>
				<span
					class="inline-flex items-center gap-1.5 rounded-full border border-green-200 bg-green-50 px-3 py-1.5 text-sm font-medium text-green-700"
				>
					<CheckCircle class="w-4 h-4 text-green-500" />
					System OK
				</span>
			</div>
		</div>

		<!-- System Health Cards -->
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
			<div
				class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm"
			>
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-3">
						<div
							class="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center"
						>
							<Gauge class="w-5 h-5 text-green-600" />
						</div>
						<div>
							<p
								class="text-xs font-medium text-slate-500 uppercase"
							>
								Wydajność
							</p>
							<p class="text-lg font-bold text-slate-900">94%</p>
						</div>
					</div>
					<div class="relative w-12 h-12">
						<svg
							class="w-12 h-12 transform -rotate-90"
							viewBox="0 0 36 36"
						>
							<path
								class="text-slate-100"
								d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
								fill="none"
								stroke="currentColor"
								stroke-width="3"
							/>
							<path
								class="text-green-500"
								stroke-dasharray="94, 100"
								d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
								fill="none"
								stroke="currentColor"
								stroke-width="3"
								stroke-linecap="round"
							/>
						</svg>
					</div>
				</div>
				<div class="flex items-center gap-1.5 text-xs text-green-600">
					<TrendingUp class="w-3.5 h-3.5" />
					<span>Doskonała</span>
				</div>
			</div>

			<div
				class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm"
			>
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-3">
						<div
							class="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center"
						>
							<Database class="w-5 h-5 text-green-600" />
						</div>
						<div>
							<p
								class="text-xs font-medium text-slate-500 uppercase"
							>
								Baza danych
							</p>
							<p class="text-lg font-bold text-slate-900">87%</p>
						</div>
					</div>
					<div class="relative w-12 h-12">
						<svg
							class="w-12 h-12 transform -rotate-90"
							viewBox="0 0 36 36"
						>
							<path
								class="text-slate-100"
								d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
								fill="none"
								stroke="currentColor"
								stroke-width="3"
							/>
							<path
								class="text-green-500"
								stroke-dasharray="87, 100"
								d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
								fill="none"
								stroke="currentColor"
								stroke-width="3"
								stroke-linecap="round"
							/>
						</svg>
					</div>
				</div>
				<div class="flex items-center gap-1.5 text-xs text-green-600">
					<CheckCircle class="w-3.5 h-3.5" />
					<span>Stabilna</span>
				</div>
			</div>

			<div
				class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm"
			>
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-3">
						<div
							class="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center"
						>
							<Server class="w-5 h-5 text-green-600" />
						</div>
						<div>
							<p
								class="text-xs font-medium text-slate-500 uppercase"
							>
								API Health
							</p>
							<p class="text-lg font-bold text-slate-900">100%</p>
						</div>
					</div>
					<div class="relative w-12 h-12">
						<svg
							class="w-12 h-12 transform -rotate-90"
							viewBox="0 0 36 36"
						>
							<path
								class="text-slate-100"
								d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
								fill="none"
								stroke="currentColor"
								stroke-width="3"
							/>
							<path
								class="text-green-500"
								stroke-dasharray="100, 100"
								d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
								fill="none"
								stroke="currentColor"
								stroke-width="3"
								stroke-linecap="round"
							/>
						</svg>
					</div>
				</div>
				<div class="flex items-center gap-1.5 text-xs text-green-600">
					<CheckCircle class="w-3.5 h-3.5" />
					<span>Wszystkie systemy GO</span>
				</div>
			</div>

			<div
				class="bg-white border border-slate-200 rounded-xl p-5 shadow-sm"
			>
				<div class="flex items-center justify-between mb-4">
					<div class="flex items-center gap-3">
						<div
							class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center"
						>
							<Users class="w-5 h-5 text-blue-600" />
						</div>
						<div>
							<p
								class="text-xs font-medium text-slate-500 uppercase"
							>
								Użytkownicy
							</p>
							<p class="text-lg font-bold text-slate-900">
								{{ totalUsers }}
							</p>
						</div>
					</div>
				</div>
				<div class="flex items-center gap-3 text-xs">
					<span class="text-brand-teal font-medium"
						>{{ proUsers }} Pro</span
					>
					<span class="text-slate-300">•</span>
					<span class="text-slate-500">{{ freeUsers }} Darmowy</span>
				</div>
			</div>
		</div>

		<!-- Users Table -->
		<div
			class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
		>
			<div
				class="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
			>
				<h3 class="text-lg font-bold text-slate-900">
					Zarządzanie użytkownikami
				</h3>
				<div class="flex items-center gap-3">
					<div class="relative">
						<Search
							class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4"
						/>
						<input
							v-model="searchQuery"
							type="text"
							placeholder="Wyszukaj użytkownika..."
							class="h-10 pl-10 pr-4 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-green/30 text-sm"
						/>
					</div>
				</div>
			</div>

			<div v-if="loading" class="p-8">
				<div class="animate-pulse space-y-3">
					<div
						v-for="i in 5"
						:key="i"
						class="h-12 bg-slate-100 rounded"
					></div>
				</div>
			</div>

			<div
				v-else-if="filteredUsers.length === 0"
				class="p-8 text-center text-slate-400"
			>
				<Users class="w-8 h-8 mx-auto mb-2" />
				<p class="text-sm">
					{{
						searchQuery
							? "Brak wyników wyszukiwania."
							: "Brak użytkowników."
					}}
				</p>
			</div>

			<div v-else class="overflow-x-auto">
				<table class="w-full">
					<thead class="bg-slate-50 border-b border-slate-100">
						<tr>
							<th
								class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase"
							>
								Użytkownik
							</th>
							<th
								class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase"
							>
								Plan
							</th>
							<th
								class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase"
							>
								Rola
							</th>
							<th
								class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase"
							>
								Data rejestracji
							</th>
							<th
								class="px-5 py-3 text-left text-xs font-semibold text-slate-500 uppercase"
							>
								Akcje
							</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-slate-100">
						<tr
							v-for="user in filteredUsers"
							:key="user.id"
							class="hover:bg-slate-50 transition-colors"
						>
							<td class="px-5 py-4">
								<div class="flex items-center gap-3">
									<div
										class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
										:class="avatarColor(user.email)"
									>
										{{ initials(user.email) }}
									</div>
									<span
										class="text-sm font-medium text-slate-900"
										>{{ user.email }}</span
									>
								</div>
							</td>
							<td class="px-5 py-4">
								<span
									class="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold border"
									:class="
										user.plan === 'pro'
											? 'bg-brand-green/10 text-brand-teal border-brand-green/20'
											: 'bg-slate-100 text-slate-600 border-slate-200'
									"
									>{{
										user.plan === "pro" ? "Pro" : "Darmowy"
									}}</span
								>
							</td>
							<td class="px-5 py-4">
								<span
									class="inline-flex items-center gap-1 text-xs font-medium"
									:class="
										user.role === 'admin'
											? 'text-brand-teal'
											: 'text-slate-500'
									"
								>
									<Shield
										v-if="user.role === 'admin'"
										class="w-3.5 h-3.5"
									/>
									{{
										user.role === "admin" ? "Admin" : "User"
									}}
								</span>
							</td>
							<td class="px-5 py-4 text-sm text-slate-500">
								{{ formatDate(user.created_at) }}
							</td>
							<td class="px-5 py-4">
								<div class="flex items-center gap-2">
									<button
										v-if="user.plan !== 'pro'"
										@click="setPlan(user.id, 'pro')"
										:disabled="updatingUserId === user.id"
										class="px-3 py-1 text-xs font-semibold rounded-lg bg-brand-green/10 text-brand-teal hover:bg-brand-green/20 transition-colors disabled:opacity-50 flex items-center gap-1 border border-brand-green/10"
									>
										<Zap class="w-3 h-3" />
										Ulepsz do Pro
									</button>
									<button
										v-else
										@click="setPlan(user.id, 'free')"
										:disabled="updatingUserId === user.id"
										class="px-3 py-1 text-xs font-semibold rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors disabled:opacity-50"
									>
										Obniż do Darmowego
									</button>
								</div>
							</td>
						</tr>
					</tbody>
				</table>
			</div>

			<div
				v-if="!loading && filteredUsers.length > 0"
				class="px-5 py-3 border-t border-slate-100 text-xs text-slate-400"
			>
				Pokazano {{ filteredUsers.length }} z
				{{ users.length }} użytkowników
			</div>
		</div>

		<!-- Stats Row -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
			<div
				class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm"
			>
				<h3 class="text-base font-bold text-slate-900 mb-4">
					Rozkład planów
				</h3>
				<div class="space-y-3">
					<div>
						<div
							class="flex items-center justify-between text-sm mb-1"
						>
							<span class="text-slate-600">Pro</span>
							<span class="font-medium text-slate-900"
								>{{ proUsers }} użytkowników</span
							>
						</div>
						<div
							class="h-2 bg-slate-100 rounded-full overflow-hidden"
						>
							<div
								class="h-full bg-brand-green rounded-full transition-all"
								:style="`width: ${totalUsers > 0 ? (proUsers / totalUsers) * 100 : 0}%`"
							></div>
						</div>
					</div>
					<div>
						<div
							class="flex items-center justify-between text-sm mb-1"
						>
							<span class="text-slate-600">Free</span>
							<span class="font-medium text-slate-900"
								>{{ freeUsers }} użytkowników</span
							>
						</div>
						<div
							class="h-2 bg-slate-100 rounded-full overflow-hidden"
						>
							<div
								class="h-full bg-slate-400 rounded-full transition-all"
								:style="`width: ${totalUsers > 0 ? (freeUsers / totalUsers) * 100 : 0}%`"
							></div>
						</div>
					</div>
				</div>
			</div>

			<div
				class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm"
			>
				<h3 class="text-base font-bold text-slate-900 mb-4">
					Informacje systemowe
				</h3>
				<div class="space-y-2 text-sm divide-y divide-slate-50">
					<div class="flex items-center justify-between py-2">
						<span class="text-slate-600">Wszyscy użytkownicy</span>
						<span class="font-semibold text-slate-900">{{
							totalUsers
						}}</span>
					</div>
					<div class="flex items-center justify-between py-2">
						<span class="text-slate-600">Konta Pro</span>
						<span class="font-semibold text-brand-teal">{{
							proUsers
						}}</span>
					</div>
					<div class="flex items-center justify-between py-2">
						<span class="text-slate-600">Konta Darmowe</span>
						<span class="font-semibold text-slate-600">{{
							freeUsers
						}}</span>
					</div>
					<div class="flex items-center justify-between py-2">
						<span class="text-slate-600"
							>Konwersja Darmowy → Pro</span
						>
						<span class="font-semibold text-slate-900">
							{{
								totalUsers > 0
									? Math.round((proUsers / totalUsers) * 100)
									: 0
							}}%
						</span>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
