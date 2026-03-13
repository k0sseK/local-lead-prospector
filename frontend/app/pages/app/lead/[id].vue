<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "#imports";
import { toast } from "vue-sonner";
import api from "@/services/api";
import {
	ArrowLeft,
	ChevronRight,
	Building2,
	Star,
	MapPin,
	Contact2,
	Phone,
	Mail,
	Globe,
	Clock,
	ShieldAlert,
	StickyNote,
	Trash2,
	Send,
	FileText,
	CheckCircle,
	AlertCircle,
	XCircle,
	Lock,
	ExternalLink,
} from "lucide-vue-next";
import { formatDate } from "@/utils/format.js";

definePageMeta({ layout: "dashboard", middleware: ["auth"] });

const route = useRoute();
const router = useRouter();

const lead = ref(null);
const loading = ref(true);
const error = ref(null);
const notes = ref("");
const savingNotes = ref(false);
const isAuditing = ref(false);
const showEmailModal = ref(false);

const STATUS_MAP = {
	new: { label: "Nowe", cls: "bg-gray-100 text-gray-700 border-gray-200" },
	to_contact: {
		label: "Do kontaktu",
		cls: "bg-blue-100 text-blue-700 border-blue-200",
	},
	contacted: {
		label: "Wysłano ofertę",
		cls: "bg-yellow-100 text-yellow-700 border-yellow-200",
	},
	rejected: {
		label: "Odrzucone",
		cls: "bg-red-100 text-red-700 border-red-200",
	},
	closed: {
		label: "Sukces",
		cls: "bg-green-100 text-green-700 border-green-200",
	},
	audited: {
		label: "Audytowany",
		cls: "bg-brand-green/10 text-brand-teal border-brand-green/20",
	},
};

const STATUSES = [
	{ id: "new", label: "Nowe" },
	{ id: "to_contact", label: "Do kontaktu" },
	{ id: "contacted", label: "Wysłano ofertę" },
	{ id: "rejected", label: "Odrzucone" },
	{ id: "closed", label: "Sukces" },
];

const statusInfo = computed(
	() => STATUS_MAP[lead.value?.status] || STATUS_MAP.new,
);

const fetchLead = async () => {
	try {
		loading.value = true;
		const leadId = parseInt(route.params.id);
		const res = await api.getLead(leadId);
		lead.value = res.data;
		if (!lead.value) {
			error.value = "Lead nie został znaleziony.";
		} else {
			notes.value = lead.value.notes || "";
		}
	} catch {
		error.value = "Nie udało się załadować danych leadu.";
	} finally {
		loading.value = false;
	}
};

const saveNotes = async () => {
	savingNotes.value = true;
	try {
		await api.updateLeadNotes(lead.value.id, notes.value);
		lead.value.notes = notes.value;
		toast.success("Notatki zapisane.");
	} catch {
		toast.error("Nie udało się zapisać notatek.");
	} finally {
		savingNotes.value = false;
	}
};

const changeStatus = async (status) => {
	try {
		await api.updateLeadStatus(lead.value.id, status);
		lead.value.status = status;
		toast.success(`Status zmieniony na "${STATUS_MAP[status]?.label}".`);
	} catch {
		toast.error("Nie udało się zmienić statusu.");
	}
};

const runAudit = async () => {
	if (isAuditing.value) return;
	isAuditing.value = true;
	try {
		const res = await api.auditLead(lead.value.id);
		lead.value = { ...lead.value, ...res.data };
		toast.success("Audyt zakończony!");
		router.push(`/app/lead/${lead.value.id}/audit`);
	} catch (err) {
		const detail = err.response?.data?.detail;
		if (err.response?.status === 429) {
			toast.error(
				detail || "Limit audytów wyczerpany. Przejdź na plan Pro.",
			);
		} else {
			toast.error(detail || "Audyt nie powiódł się.");
		}
	} finally {
		isAuditing.value = false;
	}
};

const deleteLead = async () => {
	if (!confirm("Usunąć ten lead? Tej akcji nie można cofnąć.")) return;
	try {
		await api.deleteLead(lead.value.id);
		toast.success("Lead usunięty.");
		router.push("/app");
	} catch {
		toast.error("Nie udało się usunąć leadu.");
	}
};

onMounted(fetchLead);

// ─── Email Modal ──────────────────────────────────────────────────
const emailSubject = ref("");
const emailBody = ref("");
const isSendingEmail = ref(false);
const emailLanguage = ref("polskim");

const LANGUAGE_OPTIONS = [
	{ value: "polskim", label: "Polski" },
	{ value: "angielskim", label: "Angielski" },
	{ value: "niemieckim", label: "Niemiecki" },
	{ value: "hiszpańskim", label: "Hiszpański" },
	{ value: "francuskim", label: "Francuski" },
];

const openEmailModal = () => {
	emailSubject.value = "";
	emailBody.value = "";
	showEmailModal.value = true;
};

const sendEmail = async () => {
	if (!emailSubject.value.trim() || !emailBody.value.trim()) {
		toast.error("Temat i treść wiadomości są wymagane.");
		return;
	}
	isSendingEmail.value = true;
	try {
		await api.sendEmail(lead.value.id, {
			subject: emailSubject.value,
			body: emailBody.value,
			target_language: emailLanguage.value,
		});
		toast.success("Email wysłany!");
		showEmailModal.value = false;
	} catch (err) {
		toast.error(
			err.response?.data?.detail || "Nie udało się wysłać emaila.",
		);
	} finally {
		isSendingEmail.value = false;
	}
};
</script>

<template>
	<div class="px-4 py-6 md:px-8 space-y-6 bg-slate-50 min-h-screen">
		<!-- Loading -->
		<div v-if="loading" class="flex items-center justify-center h-64">
			<div class="text-slate-500">Ładowanie...</div>
		</div>

		<!-- Error -->
		<div v-else-if="error" class="text-center py-16">
			<p class="text-slate-600">{{ error }}</p>
			<button
				@click="router.push('/app')"
				class="mt-4 px-4 py-2 bg-brand-teal text-white rounded-lg text-sm hover:bg-brand-teal/90"
			>
				Wróć do dashboardu
			</button>
		</div>

		<template v-else-if="lead">
			<!-- Breadcrumb -->
			<div class="flex items-center gap-2 text-sm">
				<button
					@click="router.push('/app')"
					class="inline-flex items-center gap-1.5 text-slate-500 hover:text-slate-700 transition-colors"
				>
					<ArrowLeft class="w-4 h-4" />
					Leady
				</button>
				<ChevronRight class="w-4 h-4 text-slate-300" />
				<span class="text-slate-900 font-medium">{{
					lead.company_name
				}}</span>
			</div>

			<!-- Lead Header -->
			<div
				class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4"
			>
				<div class="flex items-start gap-4">
					<div
						class="w-16 h-16 rounded-2xl bg-brand-green/10 border border-brand-green/20 flex items-center justify-center flex-shrink-0"
					>
						<Building2 class="w-8 h-8 text-brand-teal" />
					</div>
					<div>
						<div class="flex items-center gap-3 flex-wrap">
							<h1
								class="text-2xl md:text-3xl font-bold text-slate-900"
							>
								{{ lead.company_name }}
							</h1>
							<span
								v-if="lead.website && !lead.has_ssl"
								class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700 border border-red-200"
								>Brak SSL!</span
							>
						</div>
						<div class="flex items-center gap-4 mt-2 flex-wrap">
							<div
								v-if="lead.rating"
								class="flex items-center gap-1.5 text-sm text-slate-600"
							>
								<Star
									class="w-4 h-4 text-yellow-400 fill-yellow-400"
								/>
								<span class="font-semibold text-slate-900">{{
									lead.rating
								}}</span>
								<span
									v-if="lead.review_count"
									class="text-slate-400"
									>({{ lead.review_count }} opinii)</span
								>
							</div>
							<div
								v-if="lead.address"
								class="flex items-center gap-1.5 text-sm text-slate-600"
							>
								<MapPin class="w-4 h-4 text-slate-400" />
								<span>{{ lead.address }}</span>
							</div>
						</div>
					</div>
				</div>

				<div class="flex items-center gap-3 flex-wrap">
					<button
						@click="openEmailModal"
						class="inline-flex items-center gap-1.5 px-4 py-2 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-medium transition-all shadow-sm"
					>
						<Mail class="w-4 h-4" />
						Skontaktuj się
					</button>
					<button
						v-if="lead.audited"
						@click="router.push(`/app/lead/${lead.id}/audit`)"
						class="inline-flex items-center gap-1.5 px-4 py-2 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-medium transition-all shadow-sm"
					>
						<FileText class="w-4 h-4" />
						Raport AI
					</button>
					<button
						v-else
						@click="runAudit"
						:disabled="isAuditing"
						class="inline-flex items-center gap-1.5 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-all disabled:opacity-60"
					>
						<CheckCircle class="w-4 h-4" />
						{{ isAuditing ? "Audytuję..." : "Uruchom audyt AI" }}
					</button>
				</div>
			</div>

			<!-- Content Grid -->
			<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
				<!-- Main Column (2/3) -->
				<div class="lg:col-span-2 space-y-6">
					<!-- Contact Info -->
					<div
						class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
					>
						<div class="p-6 border-b border-slate-100">
							<h3
								class="text-lg font-bold text-slate-900 flex items-center gap-2"
							>
								<Contact2 class="w-5 h-5 text-green-600" />
								Informacje kontaktowe
							</h3>
						</div>
						<div class="p-6 space-y-4">
							<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
								<div v-if="lead.phone" class="space-y-1">
									<label
										class="text-xs font-medium text-slate-500 uppercase tracking-wide"
										>Telefon</label
									>
									<a
										:href="`tel:${lead.phone}`"
										class="flex items-center gap-2 text-sm font-medium text-slate-900 hover:text-brand-teal transition-colors"
									>
										<Phone class="w-4 h-4 text-slate-400" />
										{{ lead.phone }}
									</a>
								</div>
								<div v-if="lead.email" class="space-y-1">
									<label
										class="text-xs font-medium text-slate-500 uppercase tracking-wide"
										>Email</label
									>
									<a
										:href="`mailto:${lead.email}`"
										class="flex items-center gap-2 text-sm font-medium text-slate-900 hover:text-brand-teal transition-colors"
									>
										<Mail class="w-4 h-4 text-slate-400" />
										{{ lead.email }}
									</a>
								</div>
								<div v-if="lead.website" class="space-y-1">
									<label
										class="text-xs font-medium text-slate-500 uppercase tracking-wide"
										>Strona www</label
									>
									<a
										:href="
											lead.website.startsWith('http')
												? lead.website
												: 'https://' + lead.website
										"
										target="_blank"
										class="flex items-center gap-2 text-sm font-medium text-slate-900 hover:text-brand-teal transition-colors"
									>
										<Globe class="w-4 h-4 text-slate-400" />
										{{ lead.website }}
										<ExternalLink
											class="w-3 h-3 text-slate-400"
										/>
									</a>
								</div>
							</div>
							<div
								v-if="lead.address"
								class="pt-4 border-t border-slate-100 space-y-1"
							>
								<label
									class="text-xs font-medium text-slate-500 uppercase tracking-wide"
									>Pełny adres</label
								>
								<p
									class="flex items-start gap-2 text-sm text-slate-700"
								>
									<MapPin
										class="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0"
									/>
									{{ lead.address }}
								</p>
							</div>
						</div>
					</div>

					<!-- AI Audit Status -->
					<div
						class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
					>
						<div class="p-6 border-b border-slate-100">
							<h3
								class="text-lg font-bold text-slate-900 flex items-center gap-2"
							>
								<ShieldAlert
									class="w-5 h-5"
									:class="
										lead.audited
											? 'text-brand-teal'
											: 'text-slate-400'
									"
								/>
								Status audytu AI
							</h3>
						</div>
						<div class="p-6">
							<div
								v-if="!lead.audited"
								class="flex flex-col items-center py-8 text-center"
							>
								<div
									class="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4"
								>
									<ShieldAlert
										class="w-8 h-8 text-slate-400"
									/>
								</div>
								<p class="text-slate-600 font-medium">
									Brak audytu AI
								</p>
								<p class="text-sm text-slate-400 mt-1">
									Uruchom audyt, aby zobaczyć analizę strony
									WWW tej firmy.
								</p>
								<button
									@click="runAudit"
									:disabled="isAuditing"
									class="mt-4 px-4 py-2 bg-brand-teal text-white rounded-lg text-sm font-medium hover:bg-brand-teal/90 disabled:opacity-60 transition-colors"
								>
									{{
										isAuditing
											? "Audytuję..."
											: "Uruchom audyt AI"
									}}
								</button>
							</div>

							<div v-else>
								<div class="grid grid-cols-3 gap-4">
									<div
										class="text-center p-4 bg-slate-50 rounded-lg"
									>
										<div
											class="w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-2"
											:class="
												lead.is_mobile_friendly
													? 'bg-green-100'
													: 'bg-red-100'
											"
										>
											<CheckCircle
												v-if="lead.is_mobile_friendly"
												class="w-6 h-6 text-green-600"
											/>
											<XCircle
												v-else
												class="w-6 h-6 text-red-600"
											/>
										</div>
										<p
											class="text-xs font-medium text-slate-600"
										>
											Responsywność
										</p>
										<p
											class="text-sm font-bold"
											:class="
												lead.is_mobile_friendly
													? 'text-green-600'
													: 'text-red-600'
											"
										>
											{{
												lead.is_mobile_friendly
													? "OK"
													: "Problem"
											}}
										</p>
									</div>
									<div
										class="text-center p-4 bg-slate-50 rounded-lg"
									>
										<div
											class="w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-2"
											:class="
												lead.slow_website
													? 'bg-yellow-100'
													: 'bg-green-100'
											"
										>
											<AlertCircle
												v-if="lead.slow_website"
												class="w-6 h-6 text-yellow-600"
											/>
											<CheckCircle
												v-else
												class="w-6 h-6 text-green-600"
											/>
										</div>
										<p
											class="text-xs font-medium text-slate-600"
										>
											Prędkość
										</p>
										<p
											class="text-sm font-bold"
											:class="
												lead.slow_website
													? 'text-yellow-600'
													: 'text-green-600'
											"
										>
											{{
												lead.slow_website
													? "Wolna"
													: "OK"
											}}
										</p>
									</div>
									<div
										class="text-center p-4 bg-slate-50 rounded-lg"
									>
										<div
											class="w-12 h-12 mx-auto rounded-full flex items-center justify-center mb-2"
											:class="
												lead.has_ssl
													? 'bg-green-100'
													: 'bg-red-100'
											"
										>
											<CheckCircle
												v-if="lead.has_ssl"
												class="w-6 h-6 text-green-600"
											/>
											<Lock
												v-else
												class="w-6 h-6 text-red-600"
											/>
										</div>
										<p
											class="text-xs font-medium text-slate-600"
										>
											Bezpieczeństwo
										</p>
										<p
											class="text-sm font-bold"
											:class="
												lead.has_ssl
													? 'text-green-600'
													: 'text-red-600'
											"
										>
											{{
												lead.has_ssl ? "OK" : "Problem"
											}}
										</p>
									</div>
								</div>
								<div
									class="mt-4 flex items-center justify-center"
								>
									<button
										@click="
											router.push(
												`/app/lead/${lead.id}/audit`,
											)
										"
										class="inline-flex items-center gap-1.5 px-4 py-2 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-semibold transition-colors"
									>
										<FileText class="w-4 h-4" />
										Zobacz pełny raport
									</button>
								</div>
							</div>
						</div>
					</div>

					<!-- Notes -->
					<div
						class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
					>
						<div class="p-6 border-b border-slate-100">
							<h3
								class="text-lg font-bold text-slate-900 flex items-center gap-2"
							>
								<StickyNote class="w-5 h-5 text-green-600" />
								Notatki
							</h3>
						</div>
						<div class="p-6 space-y-3">
							<textarea
								v-model="notes"
								rows="4"
								placeholder="Dodaj notatki dotyczące tego leadu..."
								class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-green/30"
							></textarea>
							<button
								@click="saveNotes"
								:disabled="savingNotes"
								class="px-4 py-2 bg-brand-teal text-white rounded-lg text-sm font-medium hover:bg-brand-teal/90 disabled:opacity-60 transition-colors"
							>
								{{
									savingNotes
										? "Zapisywanie..."
										: "Zapisz notatki"
								}}
							</button>
						</div>
					</div>
				</div>

				<!-- Sidebar -->
				<div class="space-y-6">
					<!-- Lead Metadata -->
					<div
						class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
					>
						<div class="p-5 border-b border-slate-100">
							<h3
								class="text-sm font-bold text-slate-900 uppercase tracking-wide"
							>
								Szczegóły leadu
							</h3>
						</div>
						<div class="p-5 space-y-3">
							<div class="flex items-center justify-between">
								<span class="text-sm text-slate-500"
									>ID leadu</span
								>
								<span
									class="text-sm font-mono font-medium text-slate-900"
									>#{{ lead.id }}</span
								>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-sm text-slate-500"
									>Data dodania</span
								>
								<span
									class="text-sm font-medium text-slate-900"
									>{{ formatDate(lead.created_at) }}</span
								>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-sm text-slate-500"
									>Źródło</span
								>
								<span
									class="inline-flex items-center gap-1.5 text-sm font-medium text-slate-900"
								>
									<MapPin
										class="w-3.5 h-3.5 text-green-500"
									/>
									Google Places
								</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-sm text-slate-500"
									>Status</span
								>
								<span
									class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border"
									:class="statusInfo.cls"
								>
									<span
										class="w-1.5 h-1.5 rounded-full bg-current"
									></span>
									{{ statusInfo.label }}
								</span>
							</div>
						</div>
					</div>

					<!-- Change Status -->
					<div
						class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
					>
						<div class="p-5 border-b border-slate-100">
							<h3
								class="text-sm font-bold text-slate-900 uppercase tracking-wide"
							>
								Zmień status
							</h3>
						</div>
						<div class="p-3 space-y-1">
							<button
								v-for="s in STATUSES"
								:key="s.id"
								@click="changeStatus(s.id)"
								class="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors text-left"
								:class="
									lead.status === s.id
										? 'bg-brand-green/10 text-brand-teal font-semibold'
										: 'text-slate-700 hover:bg-slate-50'
								"
							>
								<span
									class="w-1.5 h-1.5 rounded-full flex-shrink-0"
									:class="
										STATUS_MAP[s.id]?.cls.includes('blue')
											? 'bg-blue-500'
											: STATUS_MAP[s.id]?.cls.includes(
														'yellow',
												  )
												? 'bg-yellow-500'
												: STATUS_MAP[
															s.id
													  ]?.cls.includes('red')
													? 'bg-red-500'
													: STATUS_MAP[
																s.id
														  ]?.cls.includes(
																'green',
														  )
														? 'bg-green-500'
														: 'bg-gray-400'
									"
								></span>
								{{ s.label }}
							</button>
						</div>
					</div>

					<!-- Quick Actions -->
					<div
						class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
					>
						<div class="p-5 border-b border-slate-100">
							<h3
								class="text-sm font-bold text-slate-900 uppercase tracking-wide"
							>
								Szybkie akcje
							</h3>
						</div>
						<div class="p-2">
							<button
								@click="openEmailModal"
								class="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-50 transition-colors text-left"
							>
								<div
									class="w-8 h-8 rounded-lg bg-brand-green/10 flex items-center justify-center"
								>
									<Send class="w-4 h-4 text-brand-teal" />
								</div>
								<div>
									<p
										class="text-sm font-medium text-slate-900"
									>
										Wyślij email
									</p>
									<p class="text-xs text-slate-500">
										Skontaktuj się z leadem
									</p>
								</div>
							</button>
							<div class="h-px bg-slate-100 my-1"></div>
							<button
								@click="deleteLead"
								class="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-red-50 transition-colors text-left"
							>
								<div
									class="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center"
								>
									<Trash2 class="w-4 h-4 text-red-600" />
								</div>
								<div>
									<p class="text-sm font-medium text-red-600">
										Usuń lead
									</p>
									<p class="text-xs text-slate-500">
										Nieodwracalne
									</p>
								</div>
							</button>
						</div>
					</div>
				</div>
			</div>
		</template>

		<!-- Email Modal -->
		<Teleport to="body">
			<div
				v-if="showEmailModal"
				class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
				@click.self="showEmailModal = false"
			>
				<div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg">
					<div class="p-6 border-b border-slate-100">
						<h2 class="text-lg font-bold text-slate-900">
							Wyślij email do leadu
						</h2>
						<p class="text-sm text-slate-500 mt-1">
							{{ lead?.email || "Brak adresu email" }}
						</p>
					</div>
					<div class="p-6 space-y-4">
						<div class="space-y-2">
							<label class="text-sm font-medium text-slate-700"
								>Temat</label
							>
							<input
								v-model="emailSubject"
								type="text"
								class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
								placeholder="Temat wiadomości"
							/>
						</div>
						<div class="space-y-2">
							<label class="text-sm font-medium text-slate-700"
								>Język emaila</label
							>
							<select
								v-model="emailLanguage"
								class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
							>
								<option
									v-for="opt in LANGUAGE_OPTIONS"
									:key="opt.value"
									:value="opt.value"
								>
									{{ opt.label }}
								</option>
							</select>
						</div>
						<div class="space-y-2">
							<label class="text-sm font-medium text-slate-700"
								>Treść</label
							>
							<textarea
								v-model="emailBody"
								rows="6"
								class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-green/30"
								placeholder="Treść wiadomości..."
							></textarea>
						</div>
					</div>
					<div class="p-6 border-t border-slate-100 flex gap-3">
						<button
							@click="sendEmail"
							:disabled="isSendingEmail"
							class="flex-1 px-4 py-2 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-medium disabled:opacity-60 transition-colors"
						>
							{{
								isSendingEmail ? "Wysyłanie..." : "Wyślij email"
							}}
						</button>
						<button
							@click="showEmailModal = false"
							class="px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
						>
							Anuluj
						</button>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
