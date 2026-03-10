<script setup>
import { ref, onMounted } from "vue";
import api from "@/services/api.js";
import { useToast } from "vue-toastification";
import { useAuth } from "@/composables/useAuth";

definePageMeta({
	layout: "dashboard",
	middleware: ["auth"],
});

const toast = useToast();
const { user } = useAuth();
const users = ref([]);
const loading = ref(true);
const changingPlan = ref(null); // userId currently being changed

const PLANS = ["free", "pro", "admin"];

const PLAN_LIMITS = {
	free:  { ai_audits: 10,  scans: 5,  emails_sent: 20 },
	pro:   { ai_audits: 300, scans: 50, emails_sent: 500 },
	admin: { ai_audits: 999999, scans: 999999, emails_sent: 999999 },
};

const fetchUsers = async () => {
	try {
		loading.value = true;
		const res = await api.adminGetUsers();
		users.value = res.data;
	} catch (err) {
		if (err.response?.status === 403) {
			toast.error("Brak uprawnień do panelu admina.");
		} else {
			toast.error("Błąd pobierania użytkowników.");
		}
	} finally {
		loading.value = false;
	}
};

const setPlan = async (userId, plan) => {
	changingPlan.value = userId;
	try {
		await api.adminSetPlan(userId, plan);
		const u = users.value.find((u) => u.id === userId);
		if (u) u.plan = plan;
		toast.success(`Plan zmieniony na "${plan}".`);
	} catch (err) {
		toast.error(err.response?.data?.detail || "Błąd zmiany planu.");
	} finally {
		changingPlan.value = null;
	}
};

const planBadgeClass = (plan) => {
	if (plan === "pro") return "bg-violet-900/40 text-violet-300 border-violet-700/40";
	if (plan === "admin") return "bg-amber-900/40 text-amber-300 border-amber-700/40";
	return "bg-slate-800 text-slate-400 border-slate-700/40";
};

const usagePercent = (used, action, plan) => {
	const limit = PLAN_LIMITS[plan]?.[action] || 10;
	if (limit >= 999999) return 0;
	return Math.min(100, Math.round((used / limit) * 100));
};

const usageBarClass = (pct) => {
	if (pct >= 90) return "bg-red-500";
	if (pct >= 60) return "bg-yellow-500";
	return "bg-brand-green";
};

const totalCost = computed(() =>
	users.value.reduce((sum, u) => sum + (u.usage?.cost_usd || 0), 0),
);

onMounted(fetchUsers);
</script>

<template>
	<div class="px-4 py-6 md:px-8 space-y-6 bg-slate-50 min-h-screen">
		<!-- Header -->
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-3xl font-bold tracking-tight text-slate-900">Panel Admina</h1>
				<p class="text-slate-500 mt-1">Zarządzanie użytkownikami i monitorowanie zużycia.</p>
			</div>
			<div class="flex gap-3 items-center">
				<div class="text-right">
					<p class="text-xs text-slate-500">Koszt AI (bieżący miesiąc)</p>
					<p class="text-lg font-bold text-slate-800">${{ totalCost.toFixed(4) }}</p>
				</div>
				<button
					@click="fetchUsers"
					class="px-4 py-2 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
				>
					Odśwież
				</button>
			</div>
		</div>

		<!-- Table -->
		<div class="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm">
			<div v-if="loading" class="py-16 text-center text-slate-400">Ładowanie...</div>

			<table v-else class="w-full text-sm">
				<thead class="bg-slate-50 border-b border-slate-200">
					<tr>
						<th class="text-left px-4 py-3 font-semibold text-slate-600">Użytkownik</th>
						<th class="text-left px-4 py-3 font-semibold text-slate-600">Plan</th>
						<th class="text-left px-4 py-3 font-semibold text-slate-600">Audyty AI</th>
						<th class="text-left px-4 py-3 font-semibold text-slate-600">Skany</th>
						<th class="text-right px-4 py-3 font-semibold text-slate-600">Leady</th>
						<th class="text-right px-4 py-3 font-semibold text-slate-600">Koszt AI</th>
						<th class="text-left px-4 py-3 font-semibold text-slate-600">Zmień plan</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-slate-100">
					<tr
						v-for="u in users"
						:key="u.id"
						:class="u.id === user?.id ? 'bg-brand-green/5' : 'hover:bg-slate-50'"
						class="transition-colors"
					>
						<!-- Email -->
						<td class="px-4 py-3">
							<div class="font-medium text-slate-800 truncate max-w-[180px]">{{ u.email }}</div>
							<div class="text-xs text-slate-400 mt-0.5">
								{{ u.created_at ? new Date(u.created_at).toLocaleDateString('pl-PL') : '—' }}
							</div>
						</td>

						<!-- Plan badge -->
						<td class="px-4 py-3">
							<span
								class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border"
								:class="planBadgeClass(u.plan)"
							>
								{{ u.plan }}
							</span>
						</td>

						<!-- AI Audits usage bar -->
						<td class="px-4 py-3">
							<div class="flex items-center gap-2 min-w-[100px]">
								<div class="flex-1 h-1.5 rounded-full bg-slate-200 overflow-hidden">
									<div
										class="h-full rounded-full transition-all"
										:class="usageBarClass(usagePercent(u.usage.ai_audits, 'ai_audits', u.plan))"
										:style="{ width: usagePercent(u.usage.ai_audits, 'ai_audits', u.plan) + '%' }"
									></div>
								</div>
								<span class="text-xs text-slate-500 shrink-0">
									{{ u.usage.ai_audits }}/{{ u.plan === 'admin' ? '∞' : PLAN_LIMITS[u.plan]?.ai_audits }}
								</span>
							</div>
						</td>

						<!-- Scans usage bar -->
						<td class="px-4 py-3">
							<div class="flex items-center gap-2 min-w-[80px]">
								<div class="flex-1 h-1.5 rounded-full bg-slate-200 overflow-hidden">
									<div
										class="h-full rounded-full transition-all"
										:class="usageBarClass(usagePercent(u.usage.scans, 'scans', u.plan))"
										:style="{ width: usagePercent(u.usage.scans, 'scans', u.plan) + '%' }"
									></div>
								</div>
								<span class="text-xs text-slate-500 shrink-0">
									{{ u.usage.scans }}/{{ u.plan === 'admin' ? '∞' : PLAN_LIMITS[u.plan]?.scans }}
								</span>
							</div>
						</td>

						<!-- Leads count -->
						<td class="px-4 py-3 text-right text-slate-700 font-medium">
							{{ u.leads_count }}
						</td>

						<!-- Cost -->
						<td class="px-4 py-3 text-right">
							<span :class="u.usage.cost_usd > 0.5 ? 'text-orange-600 font-semibold' : 'text-slate-500'">
								${{ u.usage.cost_usd.toFixed(4) }}
							</span>
						</td>

						<!-- Plan change -->
						<td class="px-4 py-3">
							<div class="flex gap-1">
								<button
									v-for="plan in PLANS"
									:key="plan"
									:disabled="u.plan === plan || changingPlan === u.id"
									@click="setPlan(u.id, plan)"
									class="px-2 py-1 rounded text-xs font-medium border transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
									:class="
										u.plan === plan
											? 'bg-slate-100 border-slate-200 text-slate-400'
											: 'bg-white border-slate-200 text-slate-600 hover:border-slate-400 hover:text-slate-800'
									"
								>
									{{ plan }}
								</button>
							</div>
						</td>
					</tr>
				</tbody>
			</table>

			<div v-if="!loading && users.length === 0" class="py-12 text-center text-slate-400">
				Brak użytkowników.
			</div>
		</div>

		<!-- Summary stats -->
		<div class="grid grid-cols-2 md:grid-cols-4 gap-4">
			<div class="rounded-xl border border-slate-200 bg-white p-4">
				<p class="text-xs text-slate-500 font-medium uppercase tracking-wide">Wszyscy users</p>
				<p class="text-2xl font-bold text-slate-800 mt-1">{{ users.length }}</p>
			</div>
			<div class="rounded-xl border border-slate-200 bg-white p-4">
				<p class="text-xs text-slate-500 font-medium uppercase tracking-wide">Plan Pro</p>
				<p class="text-2xl font-bold text-violet-600 mt-1">{{ users.filter(u => u.plan === 'pro').length }}</p>
			</div>
			<div class="rounded-xl border border-slate-200 bg-white p-4">
				<p class="text-xs text-slate-500 font-medium uppercase tracking-wide">Audyty AI (miesiąc)</p>
				<p class="text-2xl font-bold text-slate-800 mt-1">{{ users.reduce((s, u) => s + u.usage.ai_audits, 0) }}</p>
			</div>
			<div class="rounded-xl border border-slate-200 bg-white p-4">
				<p class="text-xs text-slate-500 font-medium uppercase tracking-wide">Koszt AI (miesiąc)</p>
				<p class="text-2xl font-bold text-slate-800 mt-1">${{ totalCost.toFixed(3) }}</p>
			</div>
		</div>
	</div>
</template>
