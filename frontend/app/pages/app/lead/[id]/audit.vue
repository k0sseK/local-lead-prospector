<script setup>
import { ref, onMounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { toast } from "vue-sonner";
import api from "@/services/api";
import { formatDate, initials } from "@/utils/format.js";
import {
	ArrowLeft,
	Share2,
	Star,
	MapPin,
	Globe,
	Clock,
	ShieldAlert,
	Search,
	Zap,
	FileText,
	Check,
	X,
	AlertTriangle,
	AlertCircle,
	CheckCircle,
	XCircle,
	Lightbulb,
	MessageCircle,
	Calendar,
	CheckCircle2,
} from "lucide-vue-next";

definePageMeta({ layout: "dashboard", middleware: ["auth"] });

const route = useRoute();
const router = useRouter();

const leadId = Number(route.params.id);
const lead = ref(null);
const loading = ref(true);
const error = ref(null);

const fetchLead = async () => {
	try {
		loading.value = true;
		const res = await api.getLeads();
		lead.value = res.data.find((l) => l.id === parseInt(route.params.id));
		if (!lead.value) {
			error.value = "Lead nie został znaleziony.";
		} else if (!lead.value.audited) {
			error.value = "Ten lead nie posiada jeszcze audytu AI.";
		}
	} catch {
		error.value = "Nie udało się załadować danych audytu.";
	} finally {
		loading.value = false;
	}
};

onMounted(fetchLead);

// Parse AI analysis from the lead object
const aiAnalysis = computed(() => {
	if (!lead.value?.ai_analysis) return null;
	try {
		if (typeof lead.value.ai_analysis === "object")
			return lead.value.ai_analysis;
		return JSON.parse(lead.value.ai_analysis);
	} catch {
		return null;
	}
});

const overallScore = computed(() => {
	if (!lead.value) return 0;
	let score = 100;
	if (!lead.value.has_ssl) score -= 25;
	if (lead.value.slow_website) score -= 15;
	if (!lead.value.is_mobile_friendly) score -= 20;
	return Math.max(0, score);
});

const scoreColor = computed(() => {
	const s = overallScore.value;
	if (s >= 80) return "text-green-500";
	if (s >= 60) return "text-yellow-500";
	return "text-red-500";
});

const scoreLabel = computed(() => {
	const s = overallScore.value;
	if (s >= 80) return "Dobry";
	if (s >= 60) return "Średni";
	return "Słaby";
});

const criticalCount = computed(() => {
	let c = 0;
	if (!lead.value?.has_ssl) c++;
	return c;
});

const warningCount = computed(() => {
	let c = 0;
	if (lead.value?.slow_website) c++;
	if (!lead.value?.is_mobile_friendly) c++;
	return c;
});

// Score ring calculation
function scoreRingDasharray(score) {
	return `${score}, 100`;
}
</script>

<template>
	<div class="px-4 py-6 md:px-8 space-y-6 bg-slate-50 min-h-screen">
		<!-- Loading -->
		<div v-if="loading" class="flex items-center justify-center h-64">
			<div class="text-slate-500">Ładowanie raportu...</div>
		</div>

		<!-- Error -->
		<div v-else-if="error" class="text-center py-16">
			<p class="text-slate-600">{{ error }}</p>
			<button
				@click="router.push(`/app/lead/${route.params.id}`)"
				class="mt-4 px-4 py-2 bg-brand-teal text-white rounded-lg text-sm hover:bg-brand-teal/90"
			>
				Wróć do szczegółów leadu
			</button>
		</div>

		<template v-else-if="lead">
			<!-- Back Navigation & Actions -->
			<div class="flex items-center justify-between">
				<button
					@click="router.push(`/app/lead/${lead.id}`)"
					class="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-brand-teal transition-colors"
				>
					<ArrowLeft class="w-4 h-4" />
					Powrót do szczegółów
				</button>
				<div class="flex items-center gap-3">
					<button
						class="inline-flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-all shadow-sm"
					>
						<Share2 class="w-4 h-4" />
						Udostępnij
					</button>
				</div>
			</div>

			<!-- Business Header Card -->
			<div
				class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm"
			>
				<div class="flex flex-col md:flex-row md:items-center gap-6">
					<div class="flex items-center gap-4">
						<div
							class="w-16 h-16 bg-gradient-to-br from-brand-green to-brand-teal rounded-xl flex items-center justify-center text-black text-2xl font-bold shadow-lg"
						>
							{{ initials(lead.company_name) }}
						</div>
						<div>
							<div class="flex items-center gap-3">
								<h1 class="text-2xl font-bold text-slate-900">
									{{ lead.company_name }}
								</h1>
								<span
									v-if="lead.rating"
									class="inline-flex items-center gap-1 px-2 py-1 bg-yellow-50 border border-yellow-200 rounded-md text-xs font-semibold text-yellow-700"
								>
									<Star
										class="w-3 h-3 text-yellow-500 fill-yellow-500"
									/>
									{{ lead.rating }}
								</span>
							</div>
							<p
								class="text-sm text-slate-500 mt-1 flex items-center gap-2"
							>
								<MapPin class="w-4 h-4 text-slate-400" />
								{{ lead.address || "Brak adresu" }}
							</p>
							<div
								class="flex items-center gap-4 mt-2 text-xs text-slate-400"
							>
								<span
									v-if="lead.website"
									class="flex items-center gap-1"
								>
									<Globe class="w-3 h-3" />
									{{ lead.website }}
								</span>
								<span class="flex items-center gap-1">
									<Clock class="w-3 h-3" />
									Audyt:
									{{
										formatDate(
											lead.audited_at || lead.updated_at,
										)
									}}
								</span>
							</div>
						</div>
					</div>
					<div class="md:ml-auto flex items-center gap-6">
						<!-- Overall Score Ring -->
						<div class="flex items-center gap-4">
							<div class="relative w-20 h-20">
								<svg
									class="w-20 h-20"
									style="transform: rotate(-90deg)"
									viewBox="0 0 36 36"
								>
									<path
										class="text-slate-200"
										d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
										fill="none"
										stroke="currentColor"
										stroke-width="3"
									/>
									<path
										:class="scoreColor"
										:stroke-dasharray="
											scoreRingDasharray(overallScore)
										"
										d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
										fill="none"
										stroke="currentColor"
										stroke-width="3"
										stroke-linecap="round"
									/>
								</svg>
								<div
									class="absolute inset-0 flex items-center justify-center"
								>
									<span
										class="text-xl font-bold text-slate-900"
										>{{ overallScore }}</span
									>
								</div>
							</div>
							<div>
								<p class="text-sm font-semibold text-slate-900">
									Ogólny wynik
								</p>
								<p
									class="text-xs font-medium"
									:class="scoreColor"
								>
									{{ scoreLabel }}
								</p>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Report Grid -->
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
				<!-- Security Analysis -->
				<div
					class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
				>
					<div
						class="p-5 border-b border-slate-100 flex items-center justify-between"
					>
						<div class="flex items-center gap-3">
							<div
								class="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center"
							>
								<ShieldAlert class="w-5 h-5 text-red-600" />
							</div>
							<div>
								<h3 class="font-bold text-slate-900">
									Analiza Bezpieczeństwa
								</h3>
								<p class="text-xs text-slate-500">
									SSL, HTTPS, Szyfrowanie
								</p>
							</div>
						</div>
						<div class="flex items-center gap-1">
							<span
								class="text-2xl font-bold"
								:class="
									lead.has_ssl
										? 'text-green-500'
										: 'text-red-500'
								"
							>
								{{ lead.has_ssl ? 90 : 45 }}
							</span>
							<span class="text-xs text-slate-400">/100</span>
						</div>
					</div>
					<div class="p-5 space-y-4">
						<div class="flex items-start gap-3">
							<div
								class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
								:class="
									lead.has_ssl ? 'bg-green-100' : 'bg-red-100'
								"
							>
								<Check
									v-if="lead.has_ssl"
									class="w-3.5 h-3.5 text-green-600"
								/>
								<X v-else class="w-3.5 h-3.5 text-red-600" />
							</div>
							<div class="flex-1">
								<div class="flex items-center justify-between">
									<p
										class="text-sm font-medium text-slate-900"
									>
										Certyfikat SSL
									</p>
									<span
										class="text-xs font-semibold"
										:class="
											lead.has_ssl
												? 'text-green-600'
												: 'text-red-600'
										"
									>
										{{ lead.has_ssl ? "Aktywny" : "Brak" }}
									</span>
								</div>
								<p class="text-xs text-slate-500 mt-1">
									{{
										lead.has_ssl
											? "Strona posiada ważny certyfikat SSL."
											: "Strona nie posiada ważnego certyfikatu SSL."
									}}
								</p>
							</div>
						</div>

						<div class="flex items-start gap-3">
							<div
								class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
								:class="
									lead.has_ssl ? 'bg-green-100' : 'bg-red-100'
								"
							>
								<Check
									v-if="lead.has_ssl"
									class="w-3.5 h-3.5 text-green-600"
								/>
								<X v-else class="w-3.5 h-3.5 text-red-600" />
							</div>
							<div class="flex-1">
								<div class="flex items-center justify-between">
									<p
										class="text-sm font-medium text-slate-900"
									>
										Protokół HTTPS
									</p>
									<span
										class="text-xs font-semibold"
										:class="
											lead.has_ssl
												? 'text-green-600'
												: 'text-red-600'
										"
									>
										{{
											lead.has_ssl
												? "Aktywny"
												: "Nieaktywny"
										}}
									</span>
								</div>
								<p class="text-xs text-slate-500 mt-1">
									{{
										lead.has_ssl
											? "Połączenie jest szyfrowane."
											: "Połączenie nie jest szyfrowane."
									}}
								</p>
							</div>
						</div>

						<div
							v-if="!lead.has_ssl"
							class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg"
						>
							<div class="flex items-start gap-2">
								<AlertCircle
									class="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5"
								/>
								<div>
									<p
										class="text-xs font-semibold text-red-700"
									>
										Ryzyko wysokie
									</p>
									<p class="text-xs text-red-600 mt-1">
										Brak szyfrowania SSL naraża dane
										użytkowników. Zalecana natychmiastowa
										instalacja certyfikatu.
									</p>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- Performance -->
				<div
					class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
				>
					<div
						class="p-5 border-b border-slate-100 flex items-center justify-between"
					>
						<div class="flex items-center gap-3">
							<div
								class="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center"
							>
								<Zap class="w-5 h-5 text-green-600" />
							</div>
							<div>
								<h3 class="font-bold text-slate-900">
									Wydajność
								</h3>
								<p class="text-xs text-slate-500">
									Prędkość strony, dostępność
								</p>
							</div>
						</div>
						<div class="flex items-center gap-1">
							<span
								class="text-2xl font-bold"
								:class="
									lead.slow_website
										? 'text-yellow-500'
										: 'text-green-500'
								"
							>
								{{ lead.slow_website ? 55 : 85 }}
							</span>
							<span class="text-xs text-slate-400">/100</span>
						</div>
					</div>
					<div class="p-5 space-y-4">
						<div class="flex items-start gap-3">
							<div
								class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
								:class="
									!lead.slow_website
										? 'bg-green-100'
										: 'bg-yellow-100'
								"
							>
								<Check
									v-if="!lead.slow_website"
									class="w-3.5 h-3.5 text-green-600"
								/>
								<AlertTriangle
									v-else
									class="w-3.5 h-3.5 text-yellow-600"
								/>
							</div>
							<div class="flex-1">
								<div class="flex items-center justify-between">
									<p
										class="text-sm font-medium text-slate-900"
									>
										Prędkość ładowania
									</p>
									<span
										class="text-xs font-semibold"
										:class="
											!lead.slow_website
												? 'text-green-600'
												: 'text-yellow-600'
										"
									>
										{{
											!lead.slow_website
												? "Dobra"
												: "Wolna"
										}}
									</span>
								</div>
								<div
									v-if="!lead.slow_website"
									class="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden"
								>
									<div
										class="h-full bg-green-500 rounded-full"
										style="width: 85%"
									></div>
								</div>
								<div
									v-else
									class="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden"
								>
									<div
										class="h-full bg-yellow-500 rounded-full"
										style="width: 45%"
									></div>
								</div>
							</div>
						</div>

						<div class="flex items-start gap-3">
							<div
								class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
								:class="
									lead.is_mobile_friendly !== false
										? 'bg-green-100'
										: 'bg-red-100'
								"
							>
								<Check
									v-if="lead.is_mobile_friendly !== false"
									class="w-3.5 h-3.5 text-green-600"
								/>
								<X v-else class="w-3.5 h-3.5 text-red-600" />
							</div>
							<div class="flex-1">
								<div class="flex items-center justify-between">
									<p
										class="text-sm font-medium text-slate-900"
									>
										Responsywność mobilna
									</p>
									<span
										class="text-xs font-semibold"
										:class="
											lead.is_mobile_friendly !== false
												? 'text-green-600'
												: 'text-red-600'
										"
									>
										{{
											lead.is_mobile_friendly !== false
												? "Optymalna"
												: "Problem"
										}}
									</span>
								</div>
								<p class="text-xs text-slate-500 mt-1">
									{{
										lead.is_mobile_friendly !== false
											? "Strona poprawnie wyświetla się na urządzeniach mobilnych."
											: "Strona ma problemy z wyświetlaniem mobilnym."
									}}
								</p>
							</div>
						</div>

						<div
							v-if="lead.slow_website"
							class="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg"
						>
							<div class="flex items-start gap-2">
								<Lightbulb
									class="w-4 h-4 text-yellow-600 flex-shrink-0 mt-0.5"
								/>
								<div>
									<p
										class="text-xs font-semibold text-yellow-700"
									>
										Rekomendacja
									</p>
									<p class="text-xs text-yellow-600 mt-1">
										Zoptymalizuj obrazy, włącz cache
										przeglądarki i rozważ CDN, aby poprawić
										prędkość strony.
									</p>
								</div>
							</div>
						</div>
					</div>
				</div>

				<!-- SEO Analysis -->
				<div
					class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
				>
					<div
						class="p-5 border-b border-slate-100 flex items-center justify-between"
					>
						<div class="flex items-center gap-3">
							<div
								class="w-10 h-10 bg-yellow-50 rounded-lg flex items-center justify-center"
							>
								<Search class="w-5 h-5 text-yellow-600" />
							</div>
							<div>
								<h3 class="font-bold text-slate-900">
									Analiza SEO
								</h3>
								<p class="text-xs text-slate-500">
									Obecność online, widoczność
								</p>
							</div>
						</div>
						<div class="flex items-center gap-1">
							<span class="text-2xl font-bold text-yellow-500"
								>72</span
							>
							<span class="text-xs text-slate-400">/100</span>
						</div>
					</div>
					<div class="p-5 space-y-4">
						<div class="flex items-start gap-3">
							<div
								class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
								:class="
									lead.website ? 'bg-green-100' : 'bg-red-100'
								"
							>
								<Check
									v-if="lead.website"
									class="w-3.5 h-3.5 text-green-600"
								/>
								<X v-else class="w-3.5 h-3.5 text-red-600" />
							</div>
							<div class="flex-1">
								<div class="flex items-center justify-between">
									<p
										class="text-sm font-medium text-slate-900"
									>
										Strona internetowa
									</p>
									<span
										class="text-xs font-semibold"
										:class="
											lead.website
												? 'text-green-600'
												: 'text-red-600'
										"
									>
										{{ lead.website ? "Obecna" : "Brak" }}
									</span>
								</div>
								<p class="text-xs text-slate-500 mt-1">
									{{
										lead.website ||
										"Firma nie posiada strony WWW."
									}}
								</p>
							</div>
						</div>

						<div class="flex items-start gap-3">
							<div
								class="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5"
								:class="
									lead.rating
										? 'bg-green-100'
										: 'bg-yellow-100'
								"
							>
								<Check
									v-if="lead.rating"
									class="w-3.5 h-3.5 text-green-600"
								/>
								<AlertTriangle
									v-else
									class="w-3.5 h-3.5 text-yellow-600"
								/>
							</div>
							<div class="flex-1">
								<div class="flex items-center justify-between">
									<p
										class="text-sm font-medium text-slate-900"
									>
										Opinie Google
									</p>
									<span
										class="text-xs font-semibold"
										:class="
											lead.rating
												? 'text-green-600'
												: 'text-yellow-600'
										"
									>
										{{
											lead.rating
												? `${lead.rating}/5`
												: "Brak"
										}}
									</span>
								</div>
								<p class="text-xs text-slate-500 mt-1">
									{{
										lead.review_count
											? `${lead.review_count} opinii na Google Maps.`
											: "Brak opinii Google."
									}}
								</p>
							</div>
						</div>
					</div>
				</div>

				<!-- AI Analysis -->
				<div
					class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
				>
					<div
						class="p-5 border-b border-slate-100 flex items-center justify-between"
					>
						<div class="flex items-center gap-3">
							<div
								class="w-10 h-10 bg-brand-green/10 rounded-lg flex items-center justify-center"
							>
								<FileText class="w-5 h-5 text-brand-teal" />
							</div>
							<div>
								<h3 class="font-bold text-slate-900">
									Analiza AI
								</h3>
								<p class="text-xs text-slate-500">
									Wygenerowana przez Gemini
								</p>
							</div>
						</div>
					</div>
					<div class="p-5">
						<div v-if="aiAnalysis">
							<div v-if="aiAnalysis.email_subject" class="mb-3">
								<p
									class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1"
								>
									Sugerowany temat emaila
								</p>
								<p
									class="text-sm text-slate-900 font-medium bg-slate-50 rounded-lg px-3 py-2"
								>
									{{ aiAnalysis.email_subject }}
								</p>
							</div>
							<div v-if="aiAnalysis.email_body">
								<p
									class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1"
								>
									Sugerowana treść emaila
								</p>
								<div
									class="text-sm text-slate-700 bg-slate-50 rounded-lg px-3 py-2 whitespace-pre-wrap max-h-48 overflow-y-auto"
								>
									{{ aiAnalysis.email_body }}
								</div>
							</div>
							<div v-if="aiAnalysis.summary" class="mt-3">
								<p
									class="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1"
								>
									Podsumowanie
								</p>
								<p class="text-sm text-slate-700">
									{{ aiAnalysis.summary }}
								</p>
							</div>
						</div>
						<div v-else class="text-center py-6 text-slate-400">
							<FileText class="w-8 h-8 mx-auto mb-2" />
							<p class="text-sm">Brak danych analizy AI</p>
						</div>
					</div>
				</div>
			</div>

			<!-- Summary -->
			<div
				class="bg-gradient-to-r from-slate-800 to-slate-700 rounded-xl p-6 text-white"
			>
				<div class="flex flex-col md:flex-row md:items-center gap-6">
					<div class="flex-1">
						<h3 class="text-lg font-bold mb-2">
							Podsumowanie audytu
						</h3>
						<p class="text-sm text-slate-300 leading-relaxed">
							{{ lead.company_name }} uzyskał
							{{ overallScore }}/100 punktów w audycie
							technicznym.
							{{
								criticalCount > 0
									? `Wykryto ${criticalCount} krytyczny problem. `
									: ""
							}}
							{{
								warningCount > 0
									? `Znaleziono ${warningCount} obszary do poprawy.`
									: "Brak ostrzeżeń."
							}}
						</p>
					</div>
					<div class="flex flex-wrap gap-3 shrink-0">
						<div
							class="px-4 py-2 bg-white/10 rounded-lg backdrop-blur-sm"
						>
							<p class="text-xs text-slate-400">Krytyczne</p>
							<p class="text-lg font-bold text-red-400">
								{{ criticalCount }}
							</p>
						</div>
						<div
							class="px-4 py-2 bg-white/10 rounded-lg backdrop-blur-sm"
						>
							<p class="text-xs text-slate-400">Do poprawy</p>
							<p class="text-lg font-bold text-yellow-400">
								{{ warningCount }}
							</p>
						</div>
					</div>
				</div>
			</div>

			<!-- Action Buttons -->
			<div class="flex flex-col sm:flex-row gap-4 pt-4">
				<button
					@click="router.push(`/app/lead/${lead.id}`)"
					class="flex-1 h-12 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
				>
					<MessageCircle class="w-5 h-5" />
					Wróć do szczegółów
				</button>
				<button
					@click="router.push('/app')"
					class="flex-1 h-12 bg-white border border-slate-200 hover:border-slate-300 text-slate-700 rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
				>
					<CheckCircle2 class="w-5 h-5" />
					Dashboard
				</button>
			</div>
		</template>
	</div>
</template>
