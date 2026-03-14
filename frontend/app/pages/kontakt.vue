<script setup lang="ts">
import { toast } from "vue-sonner";
import api from "@/services/api";

definePageMeta({ layout: "default" });

const name = ref("");
const email = ref("");
const message = ref("");
const turnstileToken = ref("");
const consentAccepted = ref(false);
const showPrivacyInfo = ref(false);
const loading = ref(false);
const turnstile = ref<{ reset: () => void } | null>(null);

function resetForm() {
	name.value = "";
	email.value = "";
	message.value = "";
	consentAccepted.value = false;
	showPrivacyInfo.value = false;
	turnstile.value?.reset();
	turnstileToken.value = "";
}

async function handleSubmit() {
	if (!consentAccepted.value) {
		toast.error(
			"Zaakceptuj informację o przetwarzaniu danych, aby wysłać formularz.",
		);
		return;
	}
	if (!turnstileToken.value) {
		toast.error("Proszę ukończyć weryfikację CAPTCHA.");
		return;
	}
	loading.value = true;
	try {
		await api.submitContactForm({
			name: name.value.trim(),
			email: email.value.trim(),
			message: message.value.trim(),
			cf_turnstile_response: turnstileToken.value,
		});
		toast.success("Wiadomość wysłana! Odezwiemy się wkrótce.");
		resetForm();
	} catch (err: any) {
		toast.error(
			err.response?.data?.detail ||
				"Nie udało się wysłać wiadomości. Spróbuj ponownie.",
		);
		turnstile.value?.reset();
		turnstileToken.value = "";
	} finally {
		loading.value = false;
	}
}
</script>

<template>
	<div class="bg-brand-dark min-h-screen relative overflow-hidden">
		<div
			class="absolute top-0 right-0 w-[520px] h-[520px] rounded-full blur-[120px] pointer-events-none bg-brand-green/5"
		></div>

		<div
			class="container mx-auto px-6 lg:px-12 max-w-5xl pt-24 pb-12 text-center"
		>
			<h1
				class="text-5xl md:text-6xl font-extrabold text-white leading-tight mb-4"
			>
				Skontaktuj się z nami.<br />
				<span class="text-brand-green">Odpowiadamy konkretnie.</span>
			</h1>
			<p class="text-slate-400 text-lg max-w-2xl mx-auto leading-relaxed">
				Masz pytania o produkt, wdrożenie albo plan Pro? Napisz przez
				formularz, a wrócimy z odpowiedzią tak szybko, jak to możliwe.
			</p>
		</div>

		<div class="container mx-auto px-6 lg:px-12 max-w-5xl pb-24">
			<div class="max-w-3xl mx-auto">
				<div
					class="rounded-2xl border border-brand-green/20 bg-brand-green/5 p-7 md:p-8 shadow-[0_0_40px_rgba(56,239,125,0.08)]"
				>
					<form @submit.prevent="handleSubmit" class="space-y-5">
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div class="space-y-2">
								<label
									for="name"
									class="text-xs font-semibold tracking-wider text-slate-400 uppercase"
									>Imię i nazwisko</label
								>
								<input
									id="name"
									type="text"
									v-model="name"
									required
									placeholder="Jan Kowalski"
									class="w-full h-12 px-4 rounded-xl text-sm bg-brand-dark/60 border border-white/10 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-4 focus:ring-brand-green/5 transition-all"
								/>
							</div>

							<div class="space-y-2">
								<label
									for="email"
									class="text-xs font-semibold tracking-wider text-slate-400 uppercase"
									>Adres e-mail</label
								>
								<input
									id="email"
									type="email"
									v-model="email"
									required
									placeholder="ty@firma.pl"
									class="w-full h-12 px-4 rounded-xl text-sm bg-brand-dark/60 border border-white/10 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-4 focus:ring-brand-green/5 transition-all"
								/>
							</div>
						</div>

						<div class="space-y-2">
							<label
								for="message"
								class="text-xs font-semibold tracking-wider text-slate-400 uppercase"
								>Wiadomość</label
							>
							<textarea
								id="message"
								v-model="message"
								required
								rows="6"
								placeholder="Napisz, czego potrzebujesz - wrócimy z konkretną propozycją."
								class="w-full px-4 py-3 rounded-xl text-sm bg-brand-dark/60 border border-white/10 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-4 focus:ring-brand-green/5 transition-all resize-none"
							></textarea>
						</div>

						<div
							class="space-y-3 rounded-xl border border-white/10 bg-brand-dark/45 p-4"
						>
							<label
								class="flex items-start gap-3 cursor-pointer"
							>
								<input
									v-model="consentAccepted"
									type="checkbox"
									required
									class="mt-1 h-4 w-4 rounded border-white/30 bg-brand-dark text-brand-green focus:ring-brand-green/40"
								/>
								<span
									class="text-sm leading-relaxed text-slate-300"
								>
									Zapoznałem się z
									<button
										type="button"
										@click="
											showPrivacyInfo = !showPrivacyInfo
										"
										class="font-semibold text-brand-green hover:text-brand-teal transition-colors underline underline-offset-2"
									>
										informacją o administratorze i
										przetwarzaniu danych.
									</button>
								</span>
							</label>

							<Transition
								enter-active-class="transition-all duration-300 ease-out"
								enter-from-class="opacity-0 -translate-y-1 max-h-0"
								enter-to-class="opacity-100 translate-y-0 max-h-80"
								leave-active-class="transition-all duration-200 ease-in"
								leave-from-class="opacity-100 translate-y-0 max-h-80"
								leave-to-class="opacity-0 -translate-y-1 max-h-0"
							>
								<div
									v-if="showPrivacyInfo"
									class="overflow-hidden space-y-3 rounded-lg border border-white/10 bg-brand-dark/55 p-3 text-xs leading-relaxed text-slate-400"
								>
									<p class="text-slate-300">
										Wyrażam zgodę na przetwarzanie moich
										danych osobowych przez znajdzfirmy.pl w
										celu realizacji powyższego zgłoszenia.
									</p>
									<p>
										Administratorem Twoich danych osobowych
										jest znajdzfirmy.pl. Podanie danych jest
										dobrowolne, ale niezbędne do odpowiedzi
										na powyższe zgłoszenie. Osobie, której
										dane dotyczą, przysługuje prawo dostępu
										do treści swoich danych oraz ich
										poprawiania. Informujemy również o
										prawie bycia zapomnianym poprzez
										wystąpienie z wnioskiem do
										administratora o usunięcie danych
										osobowych.
									</p>
								</div>
							</Transition>
						</div>

						<div class="flex justify-center pt-1">
							<NuxtTurnstile
								ref="turnstile"
								v-model="turnstileToken"
							/>
						</div>

						<button
							type="submit"
							:disabled="loading"
							class="w-full h-12 rounded-full text-sm font-bold text-black bg-gradient-to-r from-brand-green to-brand-teal hover:-translate-y-0.5 transition-all shadow-[0_8px_30px_rgba(56,239,125,0.2)] disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2"
						>
							<svg
								v-if="loading"
								class="w-4 h-4 animate-spin"
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
								/>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8v8H4z"
								/>
							</svg>
							{{ loading ? "Wysyłanie..." : "Wyślij wiadomość" }}
						</button>
					</form>
				</div>
			</div>
		</div>
	</div>
</template>
