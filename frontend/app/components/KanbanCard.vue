<script setup>
import { computed, ref } from "vue";
import { toast } from "vue-sonner";
import api from "@/services/api";
import { CheckCircle, FileText } from "lucide-vue-next";


const props = defineProps({
	lead: {
		type: Object,
		required: true,
	},
	isAuditing: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["audit-lead", "lead-deleted"]);

const isModalOpen = ref(false);
const isSendingEmail = ref(false);
const isDeleting = ref(false);
const isRegeneratingEmail = ref(false);
const emailSubject = ref("");
const editableEmailDraft = ref("");
const notesValue = ref("");
const isSavingNotes = ref(false);
const notesTimeout = ref(null);
const selectedEmailLanguage = ref("auto");

const EMAIL_LANGUAGES = [
	{ value: "auto", label: "🌐 Auto-wykrywanie" },
	{ value: "polskim", label: "🇵🇱 Polski" },
	{ value: "angielskim", label: "🇬🇧 Angielski" },
	{ value: "hiszpańskim", label: "🇪🇸 Hiszpański" },
	{ value: "niemieckim", label: "🇩🇪 Niemiecki" },
	{ value: "francuskim", label: "🇫🇷 Francuski" },
];

const formattedDate = computed(() => {
	if (!props.lead.created_at) return "";
	return new Date(props.lead.created_at).toLocaleDateString();
});

const openModal = () => {
	editableEmailDraft.value = props.lead.audit_report?.email_draft || "";
	notesValue.value = props.lead.notes || "";
	selectedEmailLanguage.value = "auto";
	isModalOpen.value = true;
};

const copyEmailDraft = async () => {
	const emailText = editableEmailDraft.value;
	if (!emailText) return;

	try {
		await navigator.clipboard.writeText(emailText);
		toast.success("Mail skopiowany do schowka!");
	} catch (err) {
		const textarea = document.createElement("textarea");
		textarea.value = emailText;
		document.body.appendChild(textarea);
		textarea.select();
		document.execCommand("copy");
		document.body.removeChild(textarea);
		toast.success("Mail skopiowany do schowka!");
	}
};

const onNotesInput = () => {
	clearTimeout(notesTimeout.value);
	notesTimeout.value = setTimeout(async () => {
		isSavingNotes.value = true;
		try {
			await api.updateLeadNotes(props.lead.id, notesValue.value);
			props.lead.notes = notesValue.value;
		} catch {
			toast.error("Nie udało się zapisać notatki.");
		} finally {
			isSavingNotes.value = false;
		}
	}, 800);
};

const deleteLead = async () => {
	if (!confirm(`Usunąć lead "${props.lead.company_name}"?`)) return;
	try {
		isDeleting.value = true;
		await api.deleteLead(props.lead.id);
		emit("lead-deleted", props.lead.id);
	} catch {
		toast.error("Nie udało się usunąć leada.");
	} finally {
		isDeleting.value = false;
	}
};

const regenerateEmail = async () => {
	try {
		isRegeneratingEmail.value = true;
		const lang = selectedEmailLanguage.value === "auto" ? null : selectedEmailLanguage.value;
		const response = await api.auditLeadWithTemplate(props.lead.id, null, lang);
		const { task_id, lead_id } = response.data;

		// Polling co 2s aż do zakończenia taska
		let attempts = 0;
		const interval = setInterval(async () => {
			attempts++;
			if (attempts > 90) {
				clearInterval(interval);
				isRegeneratingEmail.value = false;
				toast.error("Timeout — regeneracja trwa zbyt długo.");
				return;
			}
			try {
				const statusRes = await api.getTaskStatus(task_id);
				const { status } = statusRes.data;
				if (status === "SUCCESS") {
					clearInterval(interval);
					const leadRes = await api.getLead(lead_id);
					const updated = leadRes.data;
					Object.assign(props.lead, updated);
					editableEmailDraft.value = updated.audit_report?.email_draft || "";
					isRegeneratingEmail.value = false;
					toast.success("Mail zregenerowany!");
				} else if (status === "FAILURE") {
					clearInterval(interval);
					isRegeneratingEmail.value = false;
					toast.error("Nie udało się zregenerować maila.");
				}
			} catch { /* błąd sieci — próbujemy dalej */ }
		}, 2000);
	} catch (err) {
		isRegeneratingEmail.value = false;
		toast.error(err.response?.data?.detail || "Nie udało się zregenerować maila.");
	}
};

const sendEmail = async () => {
	if (!emailSubject.value) {
		toast.error("Wprowadź temat maila.");
		return;
	}
	try {
		isSendingEmail.value = true;
		const response = await api.sendEmail(props.lead.id, {
			subject: emailSubject.value,
			body: editableEmailDraft.value,
		});
		toast.success("E-mail został pomyślnie wysłany!");
		Object.assign(props.lead, response.data.lead); // Reactively update the lead to trigger board column update
		isModalOpen.value = false;
	} catch (error) {
		console.error(error);
		toast.error(
			error.response?.data?.detail || "Nie udało się wysłać e-maila.",
		);
	} finally {
		isSendingEmail.value = false;
	}
};
</script>

<template>
	<div
		class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 cursor-grab active:cursor-grabbing hover:shadow-md transition-shadow group relative"
	>
		<button
			@click.stop="deleteLead"
			:disabled="isDeleting"
			class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity text-gray-300 hover:text-red-500 p-0.5 rounded"
			title="Usuń lead"
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
					d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
				/>
			</svg>
		</button>
		<div class="flex justify-between items-start mb-2">
			<h4
				class="text-sm font-semibold text-gray-900 leading-tight transition-colors flex flex-col gap-1.5"
			>
				<a
					v-if="lead.place_id"
					:href="`https://www.google.com/maps/search/?api=1&query=Google&query_place_id=${lead.place_id}`"
					target="_blank"
					@click.stop
					class="hover:text-indigo-600 hover:underline flex items-start gap-1 group/title"
					title="Otwórz w Mapach Google"
				>
					<span class="line-clamp-2 leading-tight">{{
						lead.company_name
					}}</span>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						class="h-3.5 w-3.5 flex-shrink-0 text-indigo-400 opacity-0 group-hover/title:opacity-100 transition-opacity mt-0.5"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
						/>
					</svg>
				</a>
				<span
					v-else
					class="group-hover:text-indigo-600 transition-colors"
					>{{ lead.company_name }}</span
				>
				<span
					v-if="lead.website_uri && lead.has_ssl === false"
					class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-700 border border-red-200 whitespace-nowrap w-max"
				>
					Brak SSL!
				</span>
			</h4>
			<div
				v-if="lead.audit_report?.raw_data"
				class="flex flex-wrap gap-1 mt-1"
			>
				<span
					v-if="lead.audit_report.raw_data.cms"
					class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-700 border border-blue-200"
				>
					💻 {{ lead.audit_report.raw_data.cms }}
				</span>
				<span
					v-if="
						lead.audit_report.raw_data.social_media &&
						lead.audit_report.raw_data.social_media.length === 0
					"
					class="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-orange-100 text-orange-700 border border-orange-200"
				>
					⚠️ Brak Social Media
				</span>
			</div>

			<div
				v-if="lead.rating"
				class="flex items-center bg-yellow-50 px-1.5 py-0.5 rounded text-xs text-yellow-700 font-medium border border-yellow-100 flex-shrink-0 ml-2"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3 w-3 text-yellow-400 mr-0.5"
					viewBox="0 0 20 20"
					fill="currentColor"
				>
					<path
						d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
					/>
				</svg>
				{{ lead.rating }}
				<span
					v-if="lead.reviews_count"
					class="text-yellow-600/70 ml-0.5"
					>({{ lead.reviews_count }})</span
				>
			</div>
		</div>

		<div class="text-xs text-gray-500 space-y-1">
			<p class="flex items-start gap-1">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3.5 w-3.5 text-gray-400 mt-0.5 flex-shrink-0"
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
				<span
					class="line-clamp-2"
					:title="lead.address || 'Brak adresu'"
				>
					{{ lead.address || "Brak adresu" }}
				</span>
			</p>

			<p v-if="lead.phone" class="flex items-center gap-1">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3.5 w-3.5 text-gray-400"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
					/>
				</svg>
				<a
					:href="`tel:${lead.phone}`"
					class="hover:text-indigo-600 truncate"
					@click.stop
				>
					{{ lead.phone }}
				</a>
			</p>

			<p v-if="lead.email" class="flex items-center gap-1 text-gray-600">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3.5 w-3.5 text-gray-400 flex-shrink-0"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
					/>
				</svg>
				<a
					:href="`mailto:${lead.email}`"
					class="hover:text-indigo-600 truncate"
					@click.stop
				>
					{{ lead.email }}
				</a>
			</p>
		</div>

		<div v-if="lead.audited === false" class="mt-3">
			<button
				@click.stop="emit('audit-lead', lead.id)"
				class="w-full text-xs font-semibold py-1.5 bg-brand-green/10 text-brand-teal rounded hover:bg-brand-green/20 border border-brand-green/20 flex items-center justify-center gap-1 transition-colors"
				:disabled="isAuditing"
			>
				<span v-if="isAuditing" class="flex items-center gap-2">
					<svg
						class="animate-spin h-3.5 w-3.5 text-brand-teal"
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
					Analizowanie AI...
				</span>
				<span v-else class="flex items-center gap-1">
					<CheckCircle class="w-3.5 h-3.5" />
					Audyt AI
				</span>
			</button>
		</div>
		<div
			v-else-if="lead.audited === true && lead.audit_report"
			class="mt-3"
		>
			<button
				@click.stop="openModal"
				class="w-full text-xs font-semibold py-1.5 bg-brand-green/10 text-brand-teal rounded hover:bg-brand-green/20 border border-brand-green/20 flex items-center justify-center gap-1 transition-colors"
			>
				<FileText class="w-3.5 h-3.5" />
				Raport AI
			</button>
		</div>
		<div
			class="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center"
		>
			<span
				class="text-[10px] text-gray-400 uppercase tracking-wider font-semibold"
			>
				ID: {{ lead.id }}
			</span>
			<span class="text-[10px] text-gray-400">
				{{ formattedDate }}
			</span>
		</div>

		<!-- Audit Report Modal -->
		<Teleport to="body">
			<div
				v-if="isModalOpen"
				class="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/50"
				@click.stop="isModalOpen = false"
			>
				<div
					class="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] flex flex-col overflow-hidden"
					@click.stop
				>
					<!-- Header -->
					<div
						class="px-6 py-4 border-b border-gray-100 flex justify-between items-center bg-gradient-to-r from-purple-50 to-indigo-50"
					>
						<h3
							class="font-bold text-gray-900 flex items-center gap-2 text-base"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5 text-purple-600"
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
							Raport AI: {{ lead.company_name }}
						</h3>
						<button
							@click="isModalOpen = false"
							class="text-gray-400 hover:text-gray-600 transition-colors"
						>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M6 18L18 6M6 6l12 12"
								/>
							</svg>
						</button>
					</div>

					<!-- Body -->
					<div class="p-6 overflow-y-auto bg-white flex-1 space-y-6">
						<!-- AI Selling Points -->
						<div
							v-if="lead.audit_report?.selling_points?.length > 0"
						>
							<p
								class="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-4 w-4 text-amber-500"
									viewBox="0 0 20 20"
									fill="currentColor"
								>
									<path
										fill-rule="evenodd"
										d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z"
										clip-rule="evenodd"
									/>
								</svg>
								Punkty Sprzedażowe (AI)
							</p>
							<ul class="space-y-2">
								<li
									v-for="(point, idx) in lead.audit_report
										.selling_points"
									:key="idx"
									class="flex gap-3 bg-indigo-50/60 p-3 rounded-lg border border-indigo-100"
								>
									<span
										class="text-indigo-500 font-bold text-sm flex-shrink-0 mt-0.5"
										>{{ idx + 1 }}.</span
									>
									<p
										class="text-sm text-gray-800 leading-relaxed"
									>
										{{ point }}
									</p>
								</li>
							</ul>
						</div>
						<div
							v-else-if="
								!lead.audit_report?.selling_points?.length
							"
						>
							<div class="text-center py-4">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									class="h-10 w-10 text-green-400 mx-auto mb-2"
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
								<p class="text-gray-700 font-medium text-sm">
									AI nie znalazło krytycznych problemów.
								</p>
							</div>
						</div>

						<!-- Email Draft -->
						<div
							v-if="lead.audit_report?.email_draft"
							class="border-t border-gray-100 pt-5"
						>
							<div class="flex items-center justify-between mb-3">
								<p
									class="text-sm font-semibold text-gray-700 flex items-center gap-2"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-4 w-4 text-purple-500"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
										/>
									</svg>
									Propozycja Maila
								</p>
								<button
									@click="copyEmailDraft"
									class="text-xs font-semibold px-3 py-1.5 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors border border-purple-200 flex items-center gap-1.5 shadow-sm"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-3.5 w-3.5"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
										/>
									</svg>
									Skopiuj Maila
								</button>
							</div>

							<!-- Language selector + regenerate -->
							<div class="flex items-center gap-2 mb-3">
								<select
									v-model="selectedEmailLanguage"
									id="email-language-select"
									class="flex-1 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition-colors"
									title="Wybierz język maila"
								>
									<option
										v-for="lang in EMAIL_LANGUAGES"
										:key="lang.value"
										:value="lang.value"
									>
										{{ lang.label }}
									</option>
								</select>
								<button
									@click="regenerateEmail"
									:disabled="isRegeneratingEmail"
									class="flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-60 shadow-sm whitespace-nowrap"
									title="Wygeneruj nową wersję maila w wybranym języku"
								>
									<svg
										v-if="isRegeneratingEmail"
										class="animate-spin h-3.5 w-3.5"
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
										class="h-3.5 w-3.5"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
										/>
									</svg>
									{{
										isRegeneratingEmail
											? "Generuję..."
											: "Regeneruj maila"
									}}
								</button>
							</div>

							<textarea
								v-model="editableEmailDraft"
								class="w-full bg-gray-50 rounded-lg border border-gray-200 p-4 text-sm text-gray-700 leading-relaxed font-mono max-h-64 overflow-y-auto mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
								rows="10"
							></textarea>

							<!-- Notatki -->
							<div class="mb-4">
								<label
									class="block text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2"
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										class="h-4 w-4 text-gray-400"
										fill="none"
										viewBox="0 0 24 24"
										stroke="currentColor"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
										/>
									</svg>
									Notatki
									<span
										v-if="isSavingNotes"
										class="text-xs text-gray-400 font-normal"
										>zapisywanie...</span
									>
								</label>
								<textarea
									v-model="notesValue"
									@input="onNotesInput"
									placeholder="Dodaj notatki o tym leadzie..."
									class="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none bg-gray-50"
									rows="3"
								></textarea>
							</div>

							<!-- Sekcja wysyłki e-mail -->
							<div
								class="bg-indigo-50/50 p-4 rounded-lg border border-indigo-100"
							>
								<label
									class="block text-sm font-semibold text-gray-700 mb-2"
									>Temat maila</label
								>
								<input
									v-model="emailSubject"
									type="text"
									placeholder="Wpisz temat wiadomości..."
									class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 mb-3"
								/>
								<button
									@click="sendEmail"
									:disabled="isSendingEmail"
									class="w-full flex justify-center items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 shadow-sm"
								>
									<span
										v-if="isSendingEmail"
										class="flex items-center gap-2"
									>
										<svg
											class="animate-spin h-4 w-4 text-white"
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
										Wysyłanie...
									</span>
									<span
										v-else
										class="flex items-center gap-2"
									>
										Wyślij e-mail teraz
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
												d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
											/>
										</svg>
									</span>
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
