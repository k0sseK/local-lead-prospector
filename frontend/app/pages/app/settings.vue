<script setup>
import { ref, onMounted } from "vue";
import { useToast } from "vue-toastification";
import api from "@/services/api";

definePageMeta({ middleware: "auth", layout: "dashboard" });

const toast = useToast();

const form = ref({
	sender_name: "",
	company_name: "",
	offer_description: "",
	tone_of_voice: "formalny",
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
	{ value: "krotki-sprzedazowy", label: "Krótki, bezpośredni i sprzedażowy" },
];

onMounted(async () => {
	try {
		const response = await api.getSettings();
		Object.assign(form.value, response.data);
	} catch (error) {
		if (error.response?.status !== 404) {
			toast.error("Nie udało się załadować ustawień.");
		}
	}
	await loadTemplates();
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
const editingTemplate = ref(null); // null = nowy, object = edytowany
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
	templateForm.value = { name: t.name, prompt: t.prompt, is_default: t.is_default };
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
		toast.error(err.response?.data?.detail || "Nie udało się wygenerować promptu.");
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
			await api.updateAuditTemplate(editingTemplate.value.id, templateForm.value);
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
</script>

<template>
	<div class="p-6 max-w-2xl mx-auto">
		<div class="mb-6">
			<h1 class="text-2xl font-bold text-slate-900">Ustawienia</h1>
			<p class="text-slate-500 mt-1 text-sm">
				Dostosuj zachowanie audytora AI, bazę wiedzy firmy oraz
				konfigurację bramki e-mailowej.
			</p>
		</div>

		<Tabs defaultValue="ai" class="w-full">
			<TabsList
				class="mb-6 w-full justify-start border-b rounded-none pb-0 h-auto bg-transparent"
			>
				<TabsTrigger
					value="ai"
					class="data-[state=active]:border-b-2 data-[state=active]:border-indigo-600 data-[state=active]:text-indigo-600 rounded-none bg-transparent shadow-none"
				>
					Audytor i AI
				</TabsTrigger>
				<TabsTrigger
					value="templates"
					class="data-[state=active]:border-b-2 data-[state=active]:border-indigo-600 data-[state=active]:text-indigo-600 rounded-none bg-transparent shadow-none"
				>
					Szablony Audytów
				</TabsTrigger>
				<TabsTrigger
					value="email"
					class="data-[state=active]:border-b-2 data-[state=active]:border-indigo-600 data-[state=active]:text-indigo-600 rounded-none bg-transparent shadow-none"
				>
					Bramka E-mail
				</TabsTrigger>
			</TabsList>

			<TabsContent value="ai">
				<Card>
					<CardHeader>
						<CardTitle>Baza Wiedzy</CardTitle>
						<CardDescription>
							Uzupełnij poniższe informacje, aby AI prawidłowo
							układała wiadomości handlowe.
						</CardDescription>
					</CardHeader>
					<CardContent class="space-y-5">
						<div class="space-y-2">
							<Label for="sender_name"
								>Imię i nazwisko / Podpis</Label
							>
							<Input
								id="sender_name"
								v-model="form.sender_name"
								placeholder="np. Jan Kowalski"
							/>
						</div>

						<div class="space-y-2">
							<Label for="company_name">Nazwa firmy</Label>
							<Input
								id="company_name"
								v-model="form.company_name"
								placeholder="np. WebAgency Sp. z o.o."
							/>
						</div>

						<div class="space-y-2">
							<Label for="offer_description"
								>Krótki opis oferty</Label
							>
							<textarea
								id="offer_description"
								v-model="form.offer_description"
								rows="3"
								placeholder="np. Tworzymy strony internetowe..."
								class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
							/>
						</div>

						<div class="space-y-2">
							<Label for="tone_of_voice">Ton wypowiedzi AI</Label>
							<select
								id="tone_of_voice"
								v-model="form.tone_of_voice"
								class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
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
					</CardContent>
					<CardFooter>
						<Button :disabled="saving" @click="saveSettings">
							{{
								saving ? "Zapisywanie..." : "Zapisz ustawienia"
							}}
						</Button>
					</CardFooter>
				</Card>
			</TabsContent>

			<!-- ── Szablony Audytów ─────────────────────────────────────────── -->
			<TabsContent value="templates">
				<div class="space-y-4">
					<!-- Lista szablonów -->
					<Card v-if="templates.length > 0">
						<CardHeader>
							<CardTitle>Twoje szablony</CardTitle>
							<CardDescription>
								Wybierz szablon domyślny lub edytuj istniejący.
							</CardDescription>
						</CardHeader>
						<CardContent class="space-y-3">
							<div
								v-for="t in templates"
								:key="t.id"
								class="flex items-start justify-between gap-4 p-3 rounded-lg border"
								:class="t.is_default ? 'border-indigo-400 bg-indigo-50/40' : 'border-slate-200'"
							>
								<div class="flex-1 min-w-0">
									<div class="flex items-center gap-2 mb-1">
										<span class="font-medium text-slate-900 text-sm">{{ t.name }}</span>
										<Badge v-if="t.is_default" class="text-xs bg-indigo-100 text-indigo-700 border-indigo-200">Domyślny</Badge>
									</div>
									<p class="text-xs text-slate-500 line-clamp-2">{{ t.prompt }}</p>
								</div>
								<div class="flex gap-3 shrink-0">
									<button
										v-if="!t.is_default"
										@click="setDefault(t)"
										class="text-xs text-slate-500 hover:text-indigo-600 underline"
									>Domyślny</button>
									<button
										@click="openEditTemplate(t)"
										class="text-xs text-slate-500 hover:text-slate-900 underline"
									>Edytuj</button>
									<button
										@click="deleteTemplate(t.id)"
										class="text-xs text-red-400 hover:text-red-600 underline"
									>Usuń</button>
								</div>
							</div>
						</CardContent>
					</Card>

					<p v-else-if="!showTemplateForm" class="text-sm text-slate-500 text-center py-4">
						Nie masz jeszcze żadnych szablonów. Kliknij "Dodaj szablon", aby zacząć.
					</p>

					<!-- Formularz nowego/edytowanego szablonu -->
					<Card v-if="showTemplateForm">
						<CardHeader>
							<CardTitle>{{ editingTemplate ? 'Edytuj szablon' : 'Nowy szablon' }}</CardTitle>
							<CardDescription>
								Wpisz opis celu audytu i skorzystaj z AI, lub wpisz prompt ręcznie.
							</CardDescription>
						</CardHeader>
						<CardContent class="space-y-4">
							<div class="space-y-2">
								<Label>Nazwa szablonu</Label>
								<Input
									v-model="templateForm.name"
									placeholder="np. Audyt Social Media, Audyt Reklam Google"
								/>
							</div>

							<!-- Generator AI -->
							<div class="rounded-lg border border-dashed border-indigo-300 bg-indigo-50/30 p-4 space-y-3">
								<p class="text-sm font-medium text-indigo-800">Wygeneruj prompt przez AI</p>
								<p class="text-xs text-slate-500">Opisz, co chcesz audytować, a Gemini stworzy profesjonalny prompt.</p>
								<textarea
									v-model="promptDescription"
									rows="2"
									placeholder="np. Chcę audytować obecność firmy na Instagramie i Facebooku"
									class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
								/>
								<Button
									variant="outline"
									size="sm"
									:disabled="isGeneratingPrompt"
									@click="generatePrompt"
								>
									{{ isGeneratingPrompt ? 'Generowanie...' : 'Generuj prompt AI' }}
								</Button>
							</div>

							<div class="space-y-2">
								<Label>Treść prompta (instrukcje audytu)</Label>
								<textarea
									v-model="templateForm.prompt"
									rows="8"
									placeholder="Oceń obecność firmy na platformach społecznościowych..."
									class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none font-mono"
								/>
							</div>

							<label class="flex items-center gap-2 cursor-pointer">
								<input type="checkbox" v-model="templateForm.is_default" class="rounded" />
								<span class="text-sm text-slate-700">Ustaw jako domyślny szablon audytu</span>
							</label>
						</CardContent>
						<CardFooter class="flex gap-2">
							<Button :disabled="savingTemplate" @click="saveTemplate">
								{{ savingTemplate ? 'Zapisywanie...' : 'Zapisz szablon' }}
							</Button>
							<Button variant="outline" @click="cancelTemplateForm">Anuluj</Button>
						</CardFooter>
					</Card>

					<Button v-if="!showTemplateForm" @click="openNewTemplate">
						+ Dodaj szablon
					</Button>
				</div>
			</TabsContent>

			<TabsContent value="email">
				<Card>
					<CardHeader>
						<CardTitle>Dostawca Poczty E-mail</CardTitle>
						<CardDescription>
							Wybierz, przez jakiego dostawcę system ma wysyłać
							Twoje wiadomości do leadów.
						</CardDescription>
					</CardHeader>
					<CardContent class="space-y-6">
						<div class="space-y-4">
							<Label class="text-base font-semibold"
								>Typ dostawcy</Label
							>
							<div class="grid grid-cols-2 gap-4">
								<label
									class="flex items-center justify-center p-4 border rounded-xl cursor-pointer hover:bg-slate-50 transition-colors"
									:class="{
										'border-indigo-600 bg-indigo-50/50 hover:bg-indigo-50':
											form.email_provider === 'resend',
									}"
								>
									<input
										type="radio"
										value="resend"
										v-model="form.email_provider"
										class="sr-only"
									/>
									<span class="font-medium text-slate-900"
										>Platforma Resend API</span
									>
								</label>
								<label
									class="flex items-center justify-center p-4 border rounded-xl cursor-pointer hover:bg-slate-50 transition-colors"
									:class="{
										'border-indigo-600 bg-indigo-50/50 hover:bg-indigo-50':
											form.email_provider === 'smtp',
									}"
								>
									<input
										type="radio"
										value="smtp"
										v-model="form.email_provider"
										class="sr-only"
									/>
									<span class="font-medium text-slate-900"
										>Prywatny Serwer SMTP</span
									>
								</label>
							</div>
						</div>

						<!-- Resend Setting Form -->
						<div
							v-if="form.email_provider === 'resend'"
							class="space-y-5 pt-4 border-t animate-in fade-in slide-in-from-top-2"
						>
							<div class="space-y-2">
								<div class="flex items-center justify-between">
									<Label for="resend_api_key"
										>Twój klucz publiczny Resend API
										(*)</Label
									>
									<Dialog>
										<DialogTrigger asChild>
											<button
												class="text-xs text-indigo-600 hover:text-indigo-700 underline font-medium"
											>
												Jak zdobyć klucz?
											</button>
										</DialogTrigger>
										<DialogContent>
											<DialogHeader>
												<DialogTitle
													>Konfiguracja platformy
													Resend</DialogTitle
												>
												<DialogDescription>
													Postępuj zgodnie z
													poniższymi instrukcjami, aby
													podłączyć darmowe wysyłanie
													e-maili przez Resend.
												</DialogDescription>
											</DialogHeader>
											<div
												class="space-y-4 py-4 text-sm text-slate-700"
											>
												<div class="flex gap-3">
													<div
														class="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs"
													>
														1
													</div>
													<div>
														Przejdź na stronę
														<a
															href="https://resend.com"
															target="_blank"
															class="text-indigo-600 underline"
															>resend.com</a
														>
														i załóż darmowe konto.
													</div>
												</div>
												<div class="flex gap-3">
													<div
														class="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs"
													>
														2
													</div>
													<div>
														W panelu Resend przejdź
														do zakładki
														<strong
															>API Keys</strong
														>
														i kliknij
														<strong
															>Create API
															Key</strong
														>.
													</div>
												</div>
												<div class="flex gap-3">
													<div
														class="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs"
													>
														3
													</div>
													<div>
														Nadaj kluczowi dowolną
														nazwę i zezwól na
														domyślne uprawnienia
														("Sending access").
														Skopiuj wygenerowany
														klucz zaczynający się od
														<code>re_...</code> i
														wklej go tutaj w polu
														obok.
													</div>
												</div>
												<div class="flex gap-3">
													<div
														class="flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-xs"
													>
														4
													</div>
													<div>
														Następnie przejdź do
														<strong>Domains</strong
														>, dodaj swoją domenę
														(np.
														<code>mojafirma.pl</code
														>) i postępuj zgodnie z
														poleceniami (dopisanie
														rekordów TXT w swoim
														hostingu DNS). To
														wymagane by maile nie
														lądowały w spamie!
													</div>
												</div>
											</div>
											<DialogFooter>
												<DialogClose asChild>
													<Button variant="outline"
														>Rozumiem</Button
													>
												</DialogClose>
											</DialogFooter>
										</DialogContent>
									</Dialog>
								</div>
								<Input
									id="resend_api_key"
									v-model="form.resend_api_key"
									type="password"
									placeholder="re_..."
								/>
							</div>
							<div class="space-y-2">
								<Label for="resend_from_email"
									>Domena / Adres wysyłający (*)</Label
								>
								<Input
									id="resend_from_email"
									v-model="form.smtp_from_email"
									placeholder="np. kontakt@mojafirma.pl"
								/>
							</div>
						</div>

						<!-- SMTP Settings Form -->
						<div
							v-if="form.email_provider === 'smtp'"
							class="space-y-5 pt-4 border-t animate-in fade-in slide-in-from-top-2"
						>
							<div class="grid grid-cols-2 gap-4">
								<div class="space-y-2">
									<Label for="smtp_host"
										>Adres serwera (Host) (*)</Label
									>
									<Input
										id="smtp_host"
										v-model="form.smtp_host"
										placeholder="np. smtp.gmail.com"
									/>
								</div>
								<div class="space-y-2">
									<Label for="smtp_port">Port (*)</Label>
									<Input
										id="smtp_port"
										v-model="form.smtp_port"
										placeholder="np. 465"
									/>
								</div>
							</div>

							<div class="grid grid-cols-2 gap-4">
								<div class="space-y-2">
									<Label for="smtp_user"
										>Użytkownik (Login) (*)</Label
									>
									<Input
										id="smtp_user"
										v-model="form.smtp_user"
										placeholder="np. biuro@mojafirma.pl"
									/>
								</div>
								<div class="space-y-2">
									<Label for="smtp_password"
										>Hasło Aplikacji (*)</Label
									>
									<Input
										id="smtp_password"
										v-model="form.smtp_password"
										type="password"
										placeholder="••••••••"
									/>
								</div>
							</div>

							<div class="space-y-2">
								<Label for="smtp_from"
									>E-mail nadawcy (widoczny u klienta)
									(*)</Label
								>
								<Input
									id="smtp_from"
									v-model="form.smtp_from_email"
									placeholder="np. biuro@mojafirma.pl"
								/>
								<p class="text-xs text-slate-500">
									Upewnij się, że masz prawo wysyłać z tego
									adresu e-mail przez wybrany serwer FTP.
								</p>
							</div>
						</div>
					</CardContent>
					<CardFooter>
						<Button :disabled="saving" @click="saveSettings">
							{{
								saving ? "Zapisywanie..." : "Zapisz u dostawcy"
							}}
						</Button>
					</CardFooter>
				</Card>
			</TabsContent>
		</Tabs>
	</div>
</template>
