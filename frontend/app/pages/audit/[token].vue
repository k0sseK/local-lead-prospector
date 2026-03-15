<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute } from "#imports";
import api from "@/services/api";
import {
	ShieldCheck,
	ShieldX,
	Smartphone,
	SmartphoneNfc,
	Zap,
	ZapOff,
	Globe,
	Star,
	CheckCircle,
	XCircle,
	AlertTriangle,
	FileText,
	Lightbulb,
} from "lucide-vue-next";

definePageMeta({ layout: false });

const route = useRoute();
const token = route.params.token as string;

const report = ref<null | {
	company_name: string;
	website_uri: string | null;
	rating: number | null;
	reviews_count: number | null;
	industry: string | null;
	has_ssl: boolean | null;
	lead_score: number | null;
	audit_report: {
		raw_data: Record<string, unknown>;
		selling_points: string[];
		email_draft: string;
	} | null;
}>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
	try {
		const res = await api.getPublicAudit(token);
		report.value = res.data;
	} catch {
		error.value = "Raport nie został znaleziony lub wygasł.";
	} finally {
		loading.value = false;
	}
});

const raw = computed(() => report.value?.audit_report?.raw_data ?? {});
const sellingPoints = computed(() => report.value?.audit_report?.selling_points ?? []);

const score = computed(() => report.value?.lead_score ?? 0);

const scoreColor = computed(() => {
	if (score.value >= 80) return "#22c55e";
	if (score.value >= 50) return "#eab308";
	return "#ef4444";
});

const scoreLabel = computed(() => {
	if (score.value >= 80) return "Dobry";
	if (score.value >= 50) return "Średni";
	return "Słaby";
});

const scoreLabelColor = computed(() => {
	if (score.value >= 80) return "text-green-500";
	if (score.value >= 50) return "text-yellow-500";
	return "text-red-500";
});

// SVG ring: circumference = 2π × 15.9155 ≈ 100
const ringDasharray = computed(() => `${score.value} 100`);

const hasSsl = computed(() => raw.value.has_ssl === true);
const hasMobile = computed(() => raw.value.has_viewport === true);
const loadTime = computed(() => raw.value.load_time as number | null);
const isSlowLoad = computed(() => typeof loadTime.value === "number" && loadTime.value > 2);
const hasH1 = computed(() => raw.value.has_h1 === true);
const hasTitle = computed(() => raw.value.has_title === true);
const hasMetaDesc = computed(() => raw.value.has_meta_description === true);
const cms = computed(() => raw.value.cms as string | null);
const websiteReachable = computed(() => raw.value.website_reachable !== false);

const techRows = computed(() => [
	{
		label: "Certyfikat SSL",
		ok: hasSsl.value,
		okText: "Aktywny",
		failText: "Brak",
	},
	{
		label: "Responsywność mobilna",
		ok: hasMobile.value,
		okText: "Optymalna",
		failText: "Problem",
	},
	{
		label: "Prędkość ładowania",
		ok: !isSlowLoad.value,
		okText: loadTime.value ? `${loadTime.value.toFixed(2)}s` : "OK",
		failText: loadTime.value ? `${loadTime.value.toFixed(2)}s (wolna)` : "Wolna",
	},
	{
		label: "Nagłówek H1",
		ok: hasH1.value,
		okText: "Obecny",
		failText: "Brak",
	},
	{
		label: "Tytuł strony",
		ok: hasTitle.value,
		okText: "Obecny",
		failText: "Brak",
	},
	{
		label: "Meta description",
		ok: hasMetaDesc.value,
		okText: "Obecny",
		failText: "Brak",
	},
]);
</script>

<template>
	<div class="min-h-screen bg-slate-50 font-sans">
		<!-- Header branding -->
		<header class="bg-white border-b border-slate-200 shadow-sm">
			<div class="max-w-3xl mx-auto px-4 py-4 flex items-center gap-3">
				<div class="flex items-center gap-2">
					<div class="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center">
						<FileText class="w-4 h-4 text-white" />
					</div>
					<span class="font-bold text-slate-900 text-lg leading-none">
						<span class="text-emerald-500">znajdz</span><span>firmy.pl</span>
					</span>
				</div>
				<span class="text-slate-300 text-sm">|</span>
				<span class="text-sm text-slate-500">Raport audytu strony WWW</span>
			</div>
		</header>

		<!-- Loading -->
		<div v-if="loading" class="flex items-center justify-center h-64">
			<div class="text-slate-500 text-sm">Ładowanie raportu...</div>
		</div>

		<!-- Error -->
		<div v-else-if="error" class="max-w-3xl mx-auto px-4 py-24 text-center">
			<XCircle class="w-12 h-12 text-red-400 mx-auto mb-4" />
			<h1 class="text-xl font-bold text-slate-900 mb-2">Raport niedostępny</h1>
			<p class="text-slate-500">{{ error }}</p>
		</div>

		<div v-else-if="report" class="max-w-3xl mx-auto px-4 py-8 space-y-6">
			<!-- Company header + score -->
			<div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
				<div class="flex flex-col sm:flex-row sm:items-center gap-6">
					<div class="flex-1 min-w-0">
						<h1 class="text-2xl font-bold text-slate-900 truncate">
							{{ report.company_name }}
						</h1>
						<div class="flex flex-wrap items-center gap-4 mt-2">
							<a
								v-if="report.website_uri"
								:href="report.website_uri.startsWith('http') ? report.website_uri : 'https://' + report.website_uri"
								target="_blank"
								rel="noopener noreferrer"
								class="flex items-center gap-1.5 text-sm text-teal-600 hover:text-teal-700"
							>
								<Globe class="w-3.5 h-3.5" />
								{{ report.website_uri }}
							</a>
							<span
								v-if="report.rating"
								class="flex items-center gap-1 text-sm text-slate-600"
							>
								<Star class="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />
								{{ report.rating }}
								<span v-if="report.reviews_count" class="text-slate-400">({{ report.reviews_count }} opinii)</span>
							</span>
						</div>
						<div
							v-if="!websiteReachable"
							class="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 bg-red-50 border border-red-200 rounded-lg text-xs font-medium text-red-700"
						>
							<XCircle class="w-3.5 h-3.5" />
							Strona niedostępna podczas audytu
						</div>
					</div>

					<!-- Score gauge -->
					<div class="flex items-center gap-4 shrink-0">
						<div class="relative w-24 h-24">
							<svg class="w-24 h-24" style="transform: rotate(-90deg)" viewBox="0 0 36 36">
								<path
									class="text-slate-200"
									d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
									fill="none"
									stroke="currentColor"
									stroke-width="3"
								/>
								<path
									:stroke="scoreColor"
									:stroke-dasharray="ringDasharray"
									d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
									fill="none"
									stroke-width="3"
									stroke-linecap="round"
								/>
							</svg>
							<div class="absolute inset-0 flex items-center justify-center">
								<span class="text-2xl font-bold text-slate-900">{{ score }}</span>
							</div>
						</div>
						<div>
							<p class="text-sm font-semibold text-slate-700">Wynik strony</p>
							<p class="text-base font-bold" :class="scoreLabelColor">{{ scoreLabel }}</p>
							<p class="text-xs text-slate-400 mt-0.5">0 = dużo problemów</p>
						</div>
					</div>
				</div>
			</div>

			<!-- Technical audit table -->
			<div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
				<div class="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
					<Zap class="w-5 h-5 text-teal-500" />
					<h2 class="font-bold text-slate-900">Wyniki techniczne</h2>
				</div>
				<div v-if="cms" class="px-6 py-2 border-b border-slate-50 flex items-center justify-between text-sm">
					<span class="text-slate-500">System CMS</span>
					<span class="font-medium text-slate-700">{{ cms }}</span>
				</div>
				<div class="divide-y divide-slate-50">
					<div
						v-for="row in techRows"
						:key="row.label"
						class="px-6 py-3 flex items-center justify-between gap-4"
					>
						<span class="text-sm text-slate-700">{{ row.label }}</span>
						<span
							class="flex items-center gap-1.5 text-sm font-semibold"
							:class="row.ok ? 'text-green-600' : 'text-red-600'"
						>
							<CheckCircle v-if="row.ok" class="w-4 h-4" />
							<XCircle v-else class="w-4 h-4" />
							{{ row.ok ? row.okText : row.failText }}
						</span>
					</div>
				</div>
			</div>

			<!-- AI Selling points -->
			<div
				v-if="sellingPoints.length > 0"
				class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden"
			>
				<div class="px-6 py-4 border-b border-slate-100 flex items-center gap-2">
					<Lightbulb class="w-5 h-5 text-yellow-500" />
					<h2 class="font-bold text-slate-900">Co warto poprawić</h2>
				</div>
				<ul class="divide-y divide-slate-50">
					<li
						v-for="(point, i) in sellingPoints"
						:key="i"
						class="px-6 py-3 flex items-start gap-3"
					>
						<AlertTriangle class="w-4 h-4 text-yellow-500 flex-shrink-0 mt-0.5" />
						<span class="text-sm text-slate-700">{{ point }}</span>
					</li>
				</ul>
			</div>

			<!-- Summary badge row -->
			<div class="grid grid-cols-3 gap-4">
				<div
					class="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-center"
					:class="hasSsl ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'"
				>
					<ShieldCheck v-if="hasSsl" class="w-6 h-6 mx-auto text-green-500 mb-1" />
					<ShieldX v-else class="w-6 h-6 mx-auto text-red-500 mb-1" />
					<p class="text-xs font-semibold" :class="hasSsl ? 'text-green-700' : 'text-red-700'">SSL</p>
					<p class="text-xs" :class="hasSsl ? 'text-green-600' : 'text-red-600'">{{ hasSsl ? 'OK' : 'Brak' }}</p>
				</div>
				<div
					class="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-center"
					:class="hasMobile ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'"
				>
					<Smartphone v-if="hasMobile" class="w-6 h-6 mx-auto text-green-500 mb-1" />
					<SmartphoneNfc v-else class="w-6 h-6 mx-auto text-red-500 mb-1" />
					<p class="text-xs font-semibold" :class="hasMobile ? 'text-green-700' : 'text-red-700'">Mobile</p>
					<p class="text-xs" :class="hasMobile ? 'text-green-600' : 'text-red-600'">{{ hasMobile ? 'Responsywna' : 'Problem' }}</p>
				</div>
				<div
					class="bg-white rounded-xl border border-slate-200 shadow-sm p-4 text-center"
					:class="!isSlowLoad ? 'border-green-200 bg-green-50' : 'border-yellow-200 bg-yellow-50'"
				>
					<Zap v-if="!isSlowLoad" class="w-6 h-6 mx-auto text-green-500 mb-1" />
					<ZapOff v-else class="w-6 h-6 mx-auto text-yellow-500 mb-1" />
					<p class="text-xs font-semibold" :class="!isSlowLoad ? 'text-green-700' : 'text-yellow-700'">Prędkość</p>
					<p class="text-xs" :class="!isSlowLoad ? 'text-green-600' : 'text-yellow-600'">{{ !isSlowLoad ? 'Szybka' : 'Wolna' }}</p>
				</div>
			</div>

			<!-- Footer branding -->
			<div class="text-center py-4 border-t border-slate-200">
				<p class="text-xs text-slate-400">
					Raport wygenerowany przez
					<a href="/" class="font-semibold text-emerald-500 hover:text-emerald-600">znajdzfirmy.pl</a>
					— automatyczny audyt stron WWW dla agencji i freelancerów.
				</p>
			</div>
		</div>
	</div>
</template>
