<script setup>
import { ref, computed, onMounted } from "vue";
import { toast } from "vue-sonner";
import api from "@/services/api";
import {
	User,
	CreditCard,
	Shield,
	Bell,
	Puzzle,
	Save,
	Bot,
	Mail,
	Plus,
	Pencil,
	Trash2,
	Star,
	Sparkles,
	Check,
	ChevronRight,
	BarChart2,
	Zap,
} from "lucide-vue-next";

definePageMeta({ middleware: "auth", layout: "dashboard" });

const activeTab = ref("ai");

const form = ref({
	sender_name: "",
	company_name: "",
	offer_description: "",
	tone_of_voice: "formalny",
	default_email_language: "polskim",
	email_provider: "resend",
	resend_api_key: "",
	smtp_host: "",
	smtp_port: null,
	smtp_user: "",
	smtp_password: "",
	smtp_from_email: "",
});

const saving = ref(false);

const toneOptions = [
	{ value: "formalny", label: "Formalny i profesjonalny" },
	{ value: "luzny-startupowy", label: "Luźny i startupowy" },
	{
		value: "krotki-sprzedazowy",
		label: "Krótki, bezpośrednio i sprzedażowy",
	},
];

const languageOptions = [
	{ value: "polskim", label: "🇵🇱 Polski" },
	{ value: "angielskim", label: "🇬🇧 Angielski" },
	{ value: "hiszpańskim", label: "🇪🇸 Hiszpański" },
	{ value: "niemieckim", label: "🇩🇪 Niemiecki" },
	{ value: "francuskim", label: "🇫🇷 Francuski" },
	{ value: "włoskim", label: "🇮🇹 Włoski" },
	{ value: "portugalskim", label: "🇵🇹 Portugalski" },
];

const usage = ref(null);

const usagePlanLabel = computed(() => {
	if (usage.value?.plan === "admin") return "Admin";
	if (usage.value?.plan === "pro") return "Pro";
	return "Darmowy";
});

const usagePlanPrice = computed(() => {
	if (usage.value?.plan === "admin") return "--";
	return usage.value?.plan === "pro" ? "49" : "0";
});

onMounted(async () => {
	await Promise.all([
		api
			.getSettings()
			.then((r) => Object.assign(form.value, r.data))
			.catch((e) => {
				if (e.response?.status !== 404)
					toast.error("Nie udało się załadować ustawień.");
			}),
		loadTemplates(),
		api
			.getUsage()
			.then((r) => {
				usage.value = r.data;
			})
			.catch(() => {}),
	]);
});

async function saveSettings() {
	saving.value = true;
	try {
		await api.updateSettings(form.value);
		toast.success("Ustawienia zostały zapisane.");
	} catch {
		toast.error("Nie udało się zapisać ustawień.");
	} finally {
		saving.value = false;
	}
}

// ─── Audit Templates ──────────────────────────────────────────────────────────

const templates = ref([]);
const templateForm = ref({ name: "", prompt: "", is_default: false });
const editingTemplate = ref(null);
const savingTemplate = ref(false);
const showTemplateForm = ref(false);

const promptDescription = ref("");
const isGeneratingPrompt = ref(false);

async function loadTemplates() {
	try {
		const res = await api.getAuditTemplates();
		templates.value = res.data;
	} catch {
		toast.error("Nie udało się załadować szablonów.");
	}
}

function openNewTemplate() {
	editingTemplate.value = null;
	templateForm.value = { name: "", prompt: "", is_default: false };
	promptDescription.value = "";
	showTemplateForm.value = true;
}

function openEditTemplate(t) {
	editingTemplate.value = t;
	templateForm.value = {
		name: t.name,
		prompt: t.prompt,
		is_default: t.is_default,
	};
	promptDescription.value = "";
	showTemplateForm.value = true;
}

function cancelTemplateForm() {
	showTemplateForm.value = false;
	editingTemplate.value = null;
}

async function generatePrompt() {
	if (!promptDescription.value.trim()) {
		toast.error("Opisz cel audytu, aby wygenerować prompt.");
		return;
	}
	isGeneratingPrompt.value = true;
	try {
		const res = await api.generateAuditPrompt(promptDescription.value);
		templateForm.value.prompt = res.data.prompt;
		toast.success("Prompt wygenerowany!");
	} catch (err) {
		toast.error(
			err.response?.data?.detail || "Nie udało się wygenerować promptu.",
		);
	} finally {
		isGeneratingPrompt.value = false;
	}
}

async function saveTemplate() {
	if (!templateForm.value.name.trim() || !templateForm.value.prompt.trim()) {
		toast.error("Nazwa i treść prompta są wymagane.");
		return;
	}
	savingTemplate.value = true;
	try {
		if (editingTemplate.value) {
			await api.updateAuditTemplate(
				editingTemplate.value.id,
				templateForm.value,
			);
			toast.success("Szablon zaktualizowany.");
		} else {
			await api.createAuditTemplate(templateForm.value);
			toast.success("Szablon zapisany.");
		}
		await loadTemplates();
		cancelTemplateForm();
	} catch {
		toast.error("Nie udało się zapisać szablonu.");
	} finally {
		savingTemplate.value = false;
	}
}

async function deleteTemplate(id) {
	if (!confirm("Usunąć ten szablon?")) return;
	try {
		await api.deleteAuditTemplate(id);
		templates.value = templates.value.filter((t) => t.id !== id);
		toast.success("Szablon usunięty.");
	} catch {
		toast.error("Nie udało się usunąć szablonu.");
	}
}

async function setDefault(t) {
	try {
		await api.updateAuditTemplate(t.id, { is_default: true });
		await loadTemplates();
		toast.success(`"${t.name}" ustawiony jako domyślny.`);
	} catch {
		toast.error("Nie udało się ustawić domyślnego szablonu.");
	}
}

// ─── Resend dialog ────────────────────────────────────────────────
const showResendDialog = ref(false);
const resendSteps = [
	'Przejdź na stronę <a href="https://resend.com" target="_blank" class="text-brand-teal underline">resend.com</a> i załóż darmowe konto.',
	"W panelu Resend przejdź do zakładki <strong>API Keys</strong> i kliknij <strong>Create API Key</strong>.",
	'Nadaj kluczowi dowolną nazwę i zezwól na domyślne uprawnienia ("Sending access"). Skopiuj wygenerowany klucz zaczynający się od <code>re_...</code> i wklej go tutaj.',
	"Następnie przejdź do <strong>Domains</strong>, dodaj swoją domenę i postępuj zgodnie z poleceniami (dopisanie rekordów TXT w DNS). To wymagane, by maile nie lądowały w spamie!",
];

const TABS = [
	{ id: "ai", label: "Audytor i AI", icon: Bot },
	{ id: "templates", label: "Szablony Audytów", icon: Sparkles },
	{ id: "email", label: "Bramka E-mail", icon: Mail },
	{ id: "account", label: "Konto", icon: CreditCard },
];
</script>

<template>
	<div class="px-4 py-6 md:px-8 min-h-screen bg-slate-50">
		<!-- Page Header -->
		<div class="mb-6">
			<h1 class="text-3xl font-bold tracking-tight text-slate-900">
				Ustawienia
			</h1>
			<p class="text-slate-500 mt-2">
				Dostosuj zachowanie audytora AI, bazę wiedzy firmy oraz
				konfigurację bramki e-mailowej.
			</p>
		</div>

		<!-- Tab Navigation -->
		<div class="border-b border-slate-200 mb-6">
			<nav class="flex gap-1 overflow-x-auto">
				<button
					v-for="tab in TABS"
					:key="tab.id"
					@click="activeTab = tab.id"
					class="flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap"
					:class="
						activeTab === tab.id
							? 'border-brand-teal text-brand-teal'
							: 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
					"
				>
					<component :is="tab.icon" class="w-4 h-4" />
					{{ tab.label }}
				</button>
			</nav>
		</div>

		<!-- ── AI Auditor Tab ─────────────────────────────────────────── -->
		<div v-if="activeTab === 'ai'" class="max-w-2xl space-y-6">
			<div
				class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden"
			>
				<div class="p-6 border-b border-slate-100">
					<h2 class="text-lg font-bold text-slate-900">
						Baza Wiedzy
					</h2>
					<p class="text-sm text-slate-500 mt-1">
						Uzupełnij poniższe informacje, aby AI prawidłowo
						układała wiadomości handlowe.
					</p>
				</div>
				<div class="p-6 space-y-5">
					<div class="space-y-2">
						<label class="text-sm font-medium text-slate-700"
							>Imię i nazwisko / Podpis</label
						>
						<input
							v-model="form.sender_name"
							type="text"
							placeholder="np. Jan Kowalski"
							class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
						/>
					</div>

					<div class="space-y-2">
						<label class="text-sm font-medium text-slate-700"
							>Nazwa firmy</label
						>
						<input
							v-model="form.company_name"
							type="text"
							placeholder="np. WebAgency Sp. z o.o."
							class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
						/>
					</div>

					<div class="space-y-2">
						<label class="text-sm font-medium text-slate-700"
							>Krótki opis oferty</label
						>
						<textarea
							v-model="form.offer_description"
							rows="3"
							placeholder="np. Tworzymy strony internetowe..."
							class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-green/30"
						></textarea>
					</div>

					<div class="space-y-2">
						<label class="text-sm font-medium text-slate-700"
							>Ton wypowiedzi AI</label
						>
						<select
							v-model="form.tone_of_voice"
							class="w-full h-10 px-3 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
						>
							<option
								v-for="option in toneOptions"
								:key="option.value"
								:value="option.value"
							>
								{{ option.label }}
							</option>
						</select>
					</div>

					<div class="space-y-2">
						<label class="text-sm font-medium text-slate-700"
							>Domyślny język maila</label
						>
						<select
							v-model="form.default_email_language"
							class="w-full h-10 px-3 rounded-lg border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
						>
							<option
								v-for="option in languageOptions"
								:key="option.value"
								:value="option.value"
							>
								{{ option.label }}
							</option>
						</select>
						<p class="text-xs text-slate-400">
							Używany gdy wykrywanie automatyczne zawiedzie.
						</p>
					</div>
				</div>
				<div class="p-6 border-t border-slate-100">
					<button
						@click="saveSettings"
						:disabled="saving"
						class="px-6 py-2.5 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-60 flex items-center gap-2"
					>
						<Save class="w-4 h-4" />
						{{ saving ? "Zapisywanie..." : "Zapisz ustawienia" }}
					</button>
				</div>
			</div>
		</div>

		<!-- ── Templates Tab ──────────────────────────────────────────── -->
		<div v-if="activeTab === 'templates'" class="max-w-2xl space-y-4">
			<!-- Templates List -->
			<div
				v-if="templates.length > 0"
				class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden"
			>
				<div class="p-6 border-b border-slate-100">
					<h2 class="text-lg font-bold text-slate-900">
						Twoje szablony
					</h2>
					<p class="text-sm text-slate-500 mt-1">
						Wybierz szablon domyślny lub edytuj istniejący.
					</p>
				</div>
				<div class="p-4 space-y-3">
					<div
						v-for="t in templates"
						:key="t.id"
						class="flex items-start justify-between gap-4 p-4 rounded-lg border transition-colors"
						:class="
							t.is_default
								? 'border-brand-green/30 bg-brand-green/5'
								: 'border-slate-200'
						"
					>
						<div class="flex-1 min-w-0">
							<div class="flex items-center gap-2 mb-1">
								<span
									class="font-semibold text-slate-900 text-sm"
									>{{ t.name }}</span
								>
								<span
									v-if="t.is_default"
									class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-brand-green/10 text-brand-teal border border-brand-green/20"
								>
									<Star class="w-3 h-3" />
									Domyślny
								</span>
							</div>
							<p class="text-xs text-slate-500 line-clamp-2">
								{{ t.prompt }}
							</p>
						</div>
						<div class="flex gap-2 shrink-0">
							<button
								v-if="!t.is_default"
								@click="setDefault(t)"
								class="text-xs text-slate-500 hover:text-brand-teal underline"
							>
								Domyślny
							</button>
							<button
								@click="openEditTemplate(t)"
								class="text-xs text-slate-500 hover:text-slate-900 underline"
							>
								Edytuj
							</button>
							<button
								@click="deleteTemplate(t.id)"
								class="text-xs text-red-400 hover:text-red-600 underline"
							>
								Usuń
							</button>
						</div>
					</div>
				</div>
			</div>

			<p
				v-else-if="!showTemplateForm"
				class="text-sm text-slate-500 text-center py-6"
			>
				Nie masz jeszcze żadnych szablonów. Kliknij "Dodaj szablon", aby
				zacząć.
			</p>

			<!-- Template Form -->
			<div
				v-if="showTemplateForm"
				class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden"
			>
				<div class="p-6 border-b border-slate-100">
					<h2 class="text-lg font-bold text-slate-900">
						{{
							editingTemplate ? "Edytuj szablon" : "Nowy szablon"
						}}
					</h2>
					<p class="text-sm text-slate-500 mt-1">
						Wpisz opis celu audytu i skorzystaj z AI, lub wpisz
						prompt ręcznie.
					</p>
				</div>
				<div class="p-6 space-y-4">
					<div class="space-y-2">
						<label class="text-sm font-medium text-slate-700"
							>Nazwa szablonu</label
						>
						<input
							v-model="templateForm.name"
							type="text"
							placeholder="np. Audyt Social Media, Audyt Reklam Google"
							class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
						/>
					</div>

					<!-- AI Generator -->
					<div
						class="rounded-lg border border-dashed border-brand-green/30 bg-brand-green/5 p-4 space-y-3"
					>
						<p
							class="text-sm font-medium text-brand-teal flex items-center gap-2"
						>
							<Sparkles class="w-4 h-4" />
							Wygeneruj prompt przez AI
						</p>
						<p class="text-xs text-slate-500">
							Opisz, co chcesz audytować, a Gemini stworzy
							profesjonalny prompt.
						</p>
						<textarea
							v-model="promptDescription"
							rows="2"
							placeholder="np. Chcę audytować obecność firmy na Instagramie i Facebooku"
							class="w-full rounded-lg border border-input bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-green/30 resize-none"
						></textarea>
						<button
							@click="generatePrompt"
							:disabled="isGeneratingPrompt"
							class="px-4 py-2 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-medium disabled:opacity-60 transition-colors flex items-center gap-2"
						>
							<Sparkles class="w-4 h-4" />
							{{
								isGeneratingPrompt
									? "Generowanie..."
									: "Generuj prompt AI"
							}}
						</button>
					</div>

					<div class="space-y-2">
						<label class="text-sm font-medium text-slate-700"
							>Treść prompta (instrukcje audytu)</label
						>
						<textarea
							v-model="templateForm.prompt"
							rows="8"
							placeholder="Oceń obecność firmy na platformach społecznościowych..."
							class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-green/30 resize-none font-mono"
						></textarea>
					</div>

					<label class="flex items-center gap-2 cursor-pointer">
						<input
							type="checkbox"
							v-model="templateForm.is_default"
							class="w-4 h-4 rounded border-slate-300 text-brand-teal focus:ring-brand-green/40"
						/>
						<span class="text-sm text-slate-700"
							>Ustaw jako domyślny szablon audytu</span
						>
					</label>
				</div>
				<div class="p-6 border-t border-slate-100 flex gap-3">
					<button
						@click="saveTemplate"
						:disabled="savingTemplate"
						class="px-6 py-2.5 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-60"
					>
						{{
							savingTemplate ? "Zapisywanie..." : "Zapisz szablon"
						}}
					</button>
					<button
						@click="cancelTemplateForm"
						class="px-6 py-2.5 bg-white border border-slate-200 rounded-lg text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
					>
						Anuluj
					</button>
				</div>
			</div>

			<button
				v-if="!showTemplateForm"
				@click="openNewTemplate"
				class="flex items-center gap-2 px-4 py-2.5 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-semibold transition-colors"
			>
				<Plus class="w-4 h-4" />
				Dodaj szablon
			</button>
		</div>

		<!-- ── Email Gateway Tab ──────────────────────────────────────── -->
		<div v-if="activeTab === 'email'" class="max-w-2xl space-y-6">
			<div
				class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden"
			>
				<div class="p-6 border-b border-slate-100">
					<h2 class="text-lg font-bold text-slate-900">
						Dostawca Poczty E-mail
					</h2>
					<p class="text-sm text-slate-500 mt-1">
						Wybierz, przez jakiego dostawcę system ma wysyłać Twoje
						wiadomości do leadów.
					</p>
				</div>
				<div class="p-6 space-y-6">
					<!-- Provider toggle -->
					<div class="space-y-3">
						<label class="text-sm font-semibold text-slate-700"
							>Typ dostawcy</label
						>
						<div class="grid grid-cols-2 gap-4">
							<label
								class="flex items-center justify-center p-4 border rounded-xl cursor-pointer hover:bg-slate-50 transition-colors"
								:class="
									form.email_provider === 'resend'
										? 'border-brand-green/40 bg-brand-green/10'
										: 'border-slate-200'
								"
							>
								<input
									type="radio"
									value="resend"
									v-model="form.email_provider"
									class="sr-only"
								/>
								<span class="font-medium text-slate-900 text-sm"
									>Platforma Resend API</span
								>
							</label>
							<label
								class="flex items-center justify-center p-4 border rounded-xl cursor-pointer hover:bg-slate-50 transition-colors"
								:class="
									form.email_provider === 'smtp'
										? 'border-brand-green/40 bg-brand-green/10'
										: 'border-slate-200'
								"
							>
								<input
									type="radio"
									value="smtp"
									v-model="form.email_provider"
									class="sr-only"
								/>
								<span class="font-medium text-slate-900 text-sm"
									>Prywatny Serwer SMTP</span
								>
							</label>
						</div>
					</div>

					<!-- Resend Settings -->
					<div
						v-if="form.email_provider === 'resend'"
						class="space-y-4 pt-4 border-t border-slate-100"
					>
						<div class="space-y-2">
							<div class="flex items-center justify-between">
								<label
									class="text-sm font-medium text-slate-700"
									>Klucz Resend API (*)</label
								>
								<button
									@click="showResendDialog = true"
									class="text-xs text-brand-teal hover:text-brand-teal/90 underline font-medium"
								>
									Jak zdobyć klucz?
								</button>
							</div>
							<input
								v-model="form.resend_api_key"
								type="password"
								placeholder="re_..."
								class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
							/>
						</div>
						<div class="space-y-2">
							<label class="text-sm font-medium text-slate-700"
								>Domena / Adres wysyłający (*)</label
							>
							<input
								v-model="form.smtp_from_email"
								type="text"
								placeholder="np. kontakt@mojafirma.pl"
								class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
							/>
						</div>
					</div>

					<!-- SMTP Settings -->
					<div
						v-if="form.email_provider === 'smtp'"
						class="space-y-4 pt-4 border-t border-slate-100"
					>
						<div class="grid grid-cols-2 gap-4">
							<div class="space-y-2">
								<label
									class="text-sm font-medium text-slate-700"
									>Adres serwera (Host) (*)</label
								>
								<input
									v-model="form.smtp_host"
									type="text"
									placeholder="np. smtp.gmail.com"
									class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
								/>
							</div>
							<div class="space-y-2">
								<label
									class="text-sm font-medium text-slate-700"
									>Port (*)</label
								>
								<input
									v-model="form.smtp_port"
									type="number"
									placeholder="np. 465"
									class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
								/>
							</div>
						</div>
						<div class="grid grid-cols-2 gap-4">
							<div class="space-y-2">
								<label
									class="text-sm font-medium text-slate-700"
									>Użytkownik (Login) (*)</label
								>
								<input
									v-model="form.smtp_user"
									type="text"
									placeholder="np. biuro@mojafirma.pl"
									class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
								/>
							</div>
							<div class="space-y-2">
								<label
									class="text-sm font-medium text-slate-700"
									>Hasło Aplikacji (*)</label
								>
								<input
									v-model="form.smtp_password"
									type="password"
									placeholder="••••••••"
									class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
								/>
							</div>
						</div>
						<div class="space-y-2">
							<label class="text-sm font-medium text-slate-700"
								>E-mail nadawcy (*)</label
							>
							<input
								v-model="form.smtp_from_email"
								type="text"
								placeholder="np. biuro@mojafirma.pl"
								class="w-full h-10 px-3 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-green/30"
							/>
							<p class="text-xs text-slate-400">
								Upewnij się, że masz prawo wysyłać z tego adresu
								e-mail przez wybrany serwer.
							</p>
						</div>
					</div>
				</div>
				<div class="p-6 border-t border-slate-100">
					<button
						@click="saveSettings"
						:disabled="saving"
						class="px-6 py-2.5 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-60 flex items-center gap-2"
					>
						<Save class="w-4 h-4" />
						{{ saving ? "Zapisywanie..." : "Zapisz ustawienia" }}
					</button>
				</div>
			</div>
		</div>

		<!-- ── Account Tab ────────────────────────────────────────────── -->
		<div v-if="activeTab === 'account'" class="max-w-2xl space-y-6">
			<div
				class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden"
			>
				<div class="p-6 border-b border-slate-100">
					<h2 class="text-lg font-bold text-slate-900">
						Aktualny plan
					</h2>
				</div>
				<div class="p-6 space-y-6">
					<div v-if="usage" class="space-y-4">
						<div
							class="bg-gradient-to-r from-slate-800 to-slate-700 rounded-xl p-6 text-white"
						>
							<div class="flex items-center justify-between">
								<div>
									<p
										class="text-xs text-slate-400 uppercase tracking-wide font-medium"
									>
										Twój plan
									</p>
									<h3 class="text-2xl font-bold mt-1">
										{{ usagePlanLabel }}
									</h3>
								</div>
								<div class="text-right">
									<p class="text-3xl font-bold">
										{{ usagePlanPrice }}
										<span
											class="text-sm font-normal text-slate-400"
											>PLN</span
										>
									</p>
									<p class="text-xs text-slate-400">
										{{
											usage.plan === "admin"
												? "konto administracyjne"
												: "miesięcznie"
										}}
									</p>
								</div>
							</div>
						</div>

						<h3 class="text-sm font-semibold text-slate-900">
							Wykorzystanie limitów
						</h3>
						<div class="space-y-4">
							<div>
								<div
									class="flex items-center justify-between text-sm mb-1"
								>
									<span class="text-slate-600"
										>Audyty AI</span
									>
									<span class="font-medium text-slate-900"
										>{{ usage.usage.ai_audits }}/{{
											usage.limits.ai_audits
										}}</span
									>
								</div>
								<div
									class="h-2 bg-slate-100 rounded-full overflow-hidden"
								>
									<div
										class="h-full bg-brand-green rounded-full transition-all"
										:style="`width: ${Math.min(100, (usage.usage.ai_audits / usage.limits.ai_audits) * 100)}%`"
									></div>
								</div>
							</div>
							<div>
								<div
									class="flex items-center justify-between text-sm mb-1"
								>
									<span class="text-slate-600">Skany</span>
									<span class="font-medium text-slate-900"
										>{{ usage.usage.scans }}/{{
											usage.limits.scans
										}}</span
									>
								</div>
								<div
									class="h-2 bg-slate-100 rounded-full overflow-hidden"
								>
									<div
										class="h-full bg-brand-green rounded-full transition-all"
										:style="`width: ${Math.min(100, (usage.usage.scans / usage.limits.scans) * 100)}%`"
									></div>
								</div>
							</div>
						</div>

						<a
							v-if="usage.plan === 'free'"
							href="/pricing"
							class="flex items-center justify-center gap-2 w-full py-3 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg font-semibold text-sm transition-all"
						>
							<Zap class="w-4 h-4" />
							Ulepsz do Pro
						</a>
					</div>

					<div v-else class="text-center py-8 text-slate-400">
						<BarChart2 class="w-8 h-8 mx-auto mb-2" />
						<p class="text-sm">Ładowanie danych konta...</p>
					</div>
				</div>
			</div>
		</div>

		<!-- Resend Instructions Dialog -->
		<Teleport to="body">
			<div
				v-if="showResendDialog"
				class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
				@click.self="showResendDialog = false"
			>
				<div class="bg-white rounded-2xl shadow-2xl w-full max-w-md">
					<div class="p-6 border-b border-slate-100">
						<h2 class="text-lg font-bold text-slate-900">
							Konfiguracja platformy Resend
						</h2>
						<p class="text-sm text-slate-500 mt-1">
							Postępuj zgodnie z poniższymi instrukcjami, aby
							podłączyć darmowe wysyłanie e-maili przez Resend.
						</p>
					</div>
					<div class="p-6 space-y-4 text-sm text-slate-700">
						<div
							v-for="(step, i) in resendSteps"
							:key="i"
							class="flex gap-3"
						>
							<div
								class="flex-shrink-0 w-6 h-6 rounded-full bg-brand-green/10 text-brand-teal flex items-center justify-center font-bold text-xs"
							>
								{{ i + 1 }}
							</div>
							<div v-html="step"></div>
						</div>
					</div>
					<div class="p-6 border-t border-slate-100">
						<button
							@click="showResendDialog = false"
							class="w-full py-2.5 bg-brand-teal hover:bg-brand-teal/90 text-white rounded-lg text-sm font-semibold transition-colors"
						>
							Rozumiem
						</button>
					</div>
				</div>
			</div>
		</Teleport>
	</div>
</template>
