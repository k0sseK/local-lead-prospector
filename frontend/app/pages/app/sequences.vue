<script setup>
import { ref, computed, onMounted } from "vue";
import { toast } from "vue-sonner";
import {
	Mail,
	Play,
	Pause,
	X,
	ChevronDown,
	ChevronUp,
	Plus,
	Loader2,
	CheckCircle,
	Clock,
	AlertCircle,
	SkipForward,
} from "lucide-vue-next";
import api from "@/services/api";

definePageMeta({ layout: "dashboard", middleware: ["auth"] });

// ─── State ────────────────────────────────────────────────────────────────────
const sequences = ref([]);
const loading = ref(false);
const expandedSeq = ref(null);

// New sequence modal
const showModal = ref(false);
const modalLeadId = ref(null);
const modalLeadName = ref("");
const isGenerating = ref(false);
const isCreating = ref(false);
const activeStepTab = ref(0);
const drafts = ref([
	{ subject: "", body: "" },
	{ subject: "", body: "" },
	{ subject: "", body: "" },
]);

const { leads, fetchLeads } = useLeads();

onMounted(async () => {
	await Promise.all([loadSequences(), fetchLeads()]);
});

// ─── Helpers ──────────────────────────────────────────────────────────────────
const leadsWithEmail = computed(() =>
	(leads.value || []).filter((l) => l.email),
);

const STEP_LABELS = ["Dzień 1", "Dzień 3", "Dzień 7"];

function stepStatusIcon(status) {
	return {
		sent: CheckCircle,
		pending: Clock,
		failed: AlertCircle,
		skipped: SkipForward,
	}[status] || Clock;
}

function stepStatusClass(status) {
	return {
		sent: "text-green-500",
		pending: "text-slate-400",
		failed: "text-red-500",
		skipped: "text-slate-300",
	}[status] || "text-slate-400";
}

function seqStatusBadge(status) {
	return {
		active: "bg-emerald-100 text-emerald-700",
		paused: "bg-yellow-100 text-yellow-700",
		completed: "bg-slate-100 text-slate-600",
		cancelled: "bg-red-100 text-red-500",
	}[status] || "bg-slate-100 text-slate-600";
}

function seqStatusLabel(status) {
	return {
		active: "Aktywna",
		paused: "Wstrzymana",
		completed: "Ukończona",
		cancelled: "Anulowana",
	}[status] || status;
}

function formatDate(dt) {
	if (!dt) return "—";
	return new Date(dt).toLocaleDateString("pl-PL", {
		day: "2-digit",
		month: "2-digit",
		year: "numeric",
		hour: "2-digit",
		minute: "2-digit",
	});
}

function sentCount(seq) {
	return (seq.steps || []).filter((s) => s.status === "sent").length;
}

// ─── Load sequences ───────────────────────────────────────────────────────────
async function loadSequences() {
	loading.value = true;
	try {
		const res = await api.listSequences();
		sequences.value = res.data;
	} catch (e) {
		toast.error("Nie udało się załadować sekwencji.");
	} finally {
		loading.value = false;
	}
}

// ─── New sequence modal ───────────────────────────────────────────────────────
function openModal(lead = null) {
	modalLeadId.value = lead?.id ?? null;
	modalLeadName.value = lead?.company_name ?? "";
	activeStepTab.value = 0;
	drafts.value = [
		{ subject: "", body: "" },
		{ subject: "", body: "" },
		{ subject: "", body: "" },
	];
	showModal.value = true;
}

function closeModal() {
	showModal.value = false;
}

async function generateDrafts() {
	if (!modalLeadId.value) {
		toast.error("Wybierz leada przed generowaniem.");
		return;
	}
	isGenerating.value = true;
	try {
		const res = await api.generateSequenceDrafts(modalLeadId.value);
		res.data.drafts.forEach((d, i) => {
			drafts.value[i] = { subject: d.subject, body: d.body };
		});
		toast.success("Szkice wygenerowane przez AI.");
	} catch (e) {
		toast.error(e.response?.data?.detail || "Błąd generowania szkiców.");
	} finally {
		isGenerating.value = false;
	}
}

async function createSequence() {
	if (!modalLeadId.value) {
		toast.error("Wybierz leada.");
		return;
	}
	for (let i = 0; i < 3; i++) {
		if (!drafts.value[i].subject.trim() || !drafts.value[i].body.trim()) {
			toast.error(`Wypełnij temat i treść dla Emaila ${i + 1}.`);
			activeStepTab.value = i;
			return;
		}
	}
	isCreating.value = true;
	try {
		await api.createSequence(modalLeadId.value, drafts.value);
		toast.success("Sekwencja uruchomiona!");
		closeModal();
		await loadSequences();
	} catch (e) {
		toast.error(e.response?.data?.detail || "Błąd tworzenia sekwencji.");
	} finally {
		isCreating.value = false;
	}
}

// ─── Sequence actions ─────────────────────────────────────────────────────────
async function patchSeq(seqId, status) {
	try {
		await api.patchSequence(seqId, status);
		await loadSequences();
		const labels = { paused: "Wstrzymano", active: "Wznowiono", cancelled: "Anulowano" };
		toast.success(`${labels[status] ?? "Zaktualizowano"} sekwencję.`);
	} catch (e) {
		toast.error(e.response?.data?.detail || "Błąd aktualizacji sekwencji.");
	}
}

// ─── Inline step edit ─────────────────────────────────────────────────────────
const editingStep = ref(null); // { seqId, stepId, subject, body }

function startEditStep(seqId, step) {
	editingStep.value = {
		seqId,
		stepId: step.id,
		subject: step.subject,
		body: step.body,
	};
}

async function saveStep() {
	if (!editingStep.value) return;
	try {
		await api.updateSequenceStep(editingStep.value.seqId, editingStep.value.stepId, {
			subject: editingStep.value.subject,
			body: editingStep.value.body,
		});
		editingStep.value = null;
		await loadSequences();
		toast.success("Krok zapisany.");
	} catch (e) {
		toast.error(e.response?.data?.detail || "Błąd zapisu kroku.");
	}
}
</script>

<template>
	<div class="max-w-4xl mx-auto px-4 py-8 space-y-6">
		<!-- Header -->
		<div class="flex items-center justify-between">
			<div>
				<h1 class="text-2xl font-bold text-slate-900">Sekwencje e-mail</h1>
				<p class="text-sm text-slate-500 mt-1">
					Automatyczne follow-upy: Dzień 1 → Dzień 3 → Dzień 7
				</p>
			</div>
			<button
				@click="openModal()"
				class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors"
			>
				<Plus class="w-4 h-4" />
				Nowa sekwencja
			</button>
		</div>

		<!-- Loading -->
		<div v-if="loading" class="flex items-center justify-center py-16 text-slate-400">
			<Loader2 class="w-6 h-6 animate-spin mr-2" />
			Ładowanie…
		</div>

		<!-- Empty state -->
		<div
			v-else-if="sequences.length === 0"
			class="text-center py-20 text-slate-400"
		>
			<Mail class="w-10 h-10 mx-auto mb-3 opacity-40" />
			<p class="text-base font-medium">Brak sekwencji</p>
			<p class="text-sm mt-1">Kliknij „Nowa sekwencja", aby uruchomić follow-upy dla leada.</p>
		</div>

		<!-- Sequences list -->
		<div v-else class="space-y-3">
			<div
				v-for="seq in sequences"
				:key="seq.id"
				class="bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm"
			>
				<!-- Row header -->
				<div class="flex items-center justify-between px-5 py-4 gap-3">
					<!-- Left: lead name + badges -->
					<div class="flex items-center gap-3 min-w-0">
						<button
							@click="expandedSeq = expandedSeq === seq.id ? null : seq.id"
							class="text-slate-400 hover:text-slate-600 flex-shrink-0"
						>
							<ChevronDown v-if="expandedSeq !== seq.id" class="w-4 h-4" />
							<ChevronUp v-else class="w-4 h-4" />
						</button>
						<div class="min-w-0">
							<p class="font-semibold text-slate-800 truncate">{{ seq.company_name }}</p>
							<p class="text-xs text-slate-400 mt-0.5">
								Utworzono {{ formatDate(seq.created_at) }}
							</p>
						</div>
					</div>

					<!-- Center: step progress dots -->
					<div class="flex items-center gap-2 flex-shrink-0">
						<div
							v-for="step in seq.steps"
							:key="step.id"
							class="flex items-center gap-1"
							:title="`Email ${step.step_number}: ${step.status}`"
						>
							<component
								:is="stepStatusIcon(step.status)"
								class="w-4 h-4"
								:class="stepStatusClass(step.status)"
							/>
						</div>
						<span class="text-xs text-slate-400 ml-1">
							{{ sentCount(seq) }}/{{ seq.steps.length }}
						</span>
					</div>

					<!-- Right: status + actions -->
					<div class="flex items-center gap-2 flex-shrink-0">
						<span
							class="px-2 py-0.5 rounded-full text-xs font-medium"
							:class="seqStatusBadge(seq.status)"
						>
							{{ seqStatusLabel(seq.status) }}
						</span>

						<template v-if="seq.status === 'active'">
							<button
								@click="patchSeq(seq.id, 'paused')"
								title="Wstrzymaj"
								class="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
							>
								<Pause class="w-4 h-4" />
							</button>
						</template>
						<template v-else-if="seq.status === 'paused'">
							<button
								@click="patchSeq(seq.id, 'active')"
								title="Wznów"
								class="p-1.5 rounded-lg text-slate-500 hover:bg-slate-100 transition-colors"
							>
								<Play class="w-4 h-4" />
							</button>
						</template>

						<button
							v-if="seq.status !== 'completed' && seq.status !== 'cancelled'"
							@click="patchSeq(seq.id, 'cancelled')"
							title="Anuluj"
							class="p-1.5 rounded-lg text-slate-500 hover:bg-red-50 hover:text-red-500 transition-colors"
						>
							<X class="w-4 h-4" />
						</button>
					</div>
				</div>

				<!-- Expanded steps -->
				<div
					v-if="expandedSeq === seq.id"
					class="border-t border-slate-100 bg-slate-50 divide-y divide-slate-100"
				>
					<div
						v-for="step in seq.steps"
						:key="step.id"
						class="px-5 py-4"
					>
						<!-- Step header -->
						<div class="flex items-center justify-between mb-2">
							<div class="flex items-center gap-2">
								<component
									:is="stepStatusIcon(step.status)"
									class="w-4 h-4"
									:class="stepStatusClass(step.status)"
								/>
								<span class="text-sm font-medium text-slate-700">
									{{ STEP_LABELS[step.step_number - 1] }} — Email {{ step.step_number }}
								</span>
								<span
									v-if="step.status === 'sent'"
									class="text-xs text-slate-400"
								>
									wysłano {{ formatDate(step.sent_at) }}
								</span>
								<span
									v-else-if="step.status === 'pending'"
									class="text-xs text-slate-400"
								>
									zaplanowano {{ formatDate(step.scheduled_at) }}
								</span>
							</div>
							<button
								v-if="step.status === 'pending' && editingStep?.stepId !== step.id"
								@click="startEditStep(seq.id, step)"
								class="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
							>
								Edytuj
							</button>
						</div>

						<!-- Inline edit mode -->
						<template v-if="editingStep && editingStep.stepId === step.id">
							<input
								v-model="editingStep.subject"
								class="w-full mb-2 px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
								placeholder="Temat"
							/>
							<textarea
								v-model="editingStep.body"
								rows="5"
								class="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-y"
								placeholder="Treść wiadomości"
							/>
							<div class="flex gap-2 mt-2">
								<button
									@click="saveStep"
									class="px-3 py-1 bg-indigo-600 text-white text-xs rounded-lg hover:bg-indigo-700"
								>
									Zapisz
								</button>
								<button
									@click="editingStep = null"
									class="px-3 py-1 bg-slate-100 text-slate-600 text-xs rounded-lg hover:bg-slate-200"
								>
									Anuluj
								</button>
							</div>
						</template>

						<!-- Read-only view -->
						<template v-else>
							<p class="text-xs font-medium text-slate-600 mb-1">
								Temat: {{ step.subject }}
							</p>
							<p class="text-xs text-slate-500 whitespace-pre-line line-clamp-3">
								{{ step.body }}
							</p>
						</template>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- ─── New Sequence Modal ──────────────────────────────────────────────── -->
	<Teleport to="body">
		<div
			v-if="showModal"
			class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
			@click.self="closeModal"
		>
			<div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
				<!-- Modal header -->
				<div class="flex items-center justify-between px-6 py-4 border-b border-slate-100">
					<h2 class="text-lg font-semibold text-slate-900">Nowa sekwencja e-mail</h2>
					<button @click="closeModal" class="text-slate-400 hover:text-slate-600">
						<X class="w-5 h-5" />
					</button>
				</div>

				<!-- Modal body -->
				<div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
					<!-- Lead picker -->
					<div>
						<label class="block text-sm font-medium text-slate-700 mb-1">Lead</label>
						<select
							v-model="modalLeadId"
							@change="modalLeadName = leadsWithEmail.find(l => l.id === modalLeadId)?.company_name ?? ''"
							class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
						>
							<option :value="null" disabled>— wybierz leada z emailem —</option>
							<option v-for="l in leadsWithEmail" :key="l.id" :value="l.id">
								{{ l.company_name }} ({{ l.email }})
							</option>
						</select>
					</div>

					<!-- Generate AI drafts button -->
					<button
						@click="generateDrafts"
						:disabled="!modalLeadId || isGenerating"
						class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-indigo-300 text-indigo-700 bg-indigo-50 text-sm font-medium hover:bg-indigo-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					>
						<Loader2 v-if="isGenerating" class="w-4 h-4 animate-spin" />
						<Mail v-else class="w-4 h-4" />
						{{ isGenerating ? "Generuję szkice AI…" : "Wygeneruj szkice AI (opcjonalne)" }}
					</button>

					<!-- Step tabs -->
					<div>
						<div class="flex gap-1 mb-4 bg-slate-100 p-1 rounded-lg">
							<button
								v-for="(label, i) in STEP_LABELS"
								:key="i"
								@click="activeStepTab = i"
								class="flex-1 py-1.5 text-sm font-medium rounded-md transition-colors"
								:class="
									activeStepTab === i
										? 'bg-white text-slate-900 shadow-sm'
										: 'text-slate-500 hover:text-slate-700'
								"
							>
								{{ label }}
							</button>
						</div>

						<div class="space-y-3">
							<div>
								<label class="block text-xs font-medium text-slate-600 mb-1">Temat</label>
								<input
									v-model="drafts[activeStepTab].subject"
									class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
									:placeholder="`Temat emaila ${activeStepTab + 1}`"
								/>
							</div>
							<div>
								<label class="block text-xs font-medium text-slate-600 mb-1">Treść</label>
								<textarea
									v-model="drafts[activeStepTab].body"
									rows="8"
									class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-y"
									:placeholder="`Treść wiadomości (email ${activeStepTab + 1})`"
								/>
							</div>
						</div>
					</div>

					<!-- Day offset info -->
					<p class="text-xs text-slate-400 text-center">
						Email 1 wysyłany natychmiast · Email 2 po 2 dniach (Dzień 3) · Email 3 po 6 dniach (Dzień 7)
					</p>
				</div>

				<!-- Modal footer -->
				<div class="px-6 py-4 border-t border-slate-100 flex justify-end gap-3">
					<button
						@click="closeModal"
						class="px-4 py-2 text-sm text-slate-600 hover:text-slate-900"
					>
						Anuluj
					</button>
					<button
						@click="createSequence"
						:disabled="isCreating || !modalLeadId"
						class="inline-flex items-center gap-2 px-5 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					>
						<Loader2 v-if="isCreating" class="w-4 h-4 animate-spin" />
						Uruchom sekwencję
					</button>
				</div>
			</div>
		</div>
	</Teleport>
</template>
