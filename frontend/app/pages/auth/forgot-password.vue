<script setup lang="ts">
import { ref } from "vue";
import { ArrowLeft, ArrowRight, Loader2, CheckCircle2 } from "lucide-vue-next";
import api from "@/services/api";

definePageMeta({ layout: "default" });

const email = ref("");
const error = ref("");
const loading = ref(false);
const success = ref(false);

async function handleSubmit() {
	if (!email.value) {
		error.value = "Podaj adres e-mail.";
		return;
	}

	error.value = "";
	loading.value = true;

	try {
		await api.forgotPassword(email.value);
		success.value = true;
	} catch (err: any) {
		error.value =
			err.response?.data?.detail ||
			"Wystąpił błąd serwera. Spróbuj powtórzyć operację lub napisz do wsparcia.";
	} finally {
		loading.value = false;
	}
}
</script>

<template>
	<div class="flex-1 flex items-center justify-center py-16 px-4">
		<div class="w-full max-w-md">
			<div class="flex justify-center mb-8">
				<div
					class="w-12 h-12 rounded-xl bg-brand-green flex items-center justify-center text-black font-extrabold text-2xl shadow-[0_0_20px_rgba(56,239,125,0.3)]"
				>
					L
				</div>
			</div>

			<div class="text-center mb-8">
				<h1 class="text-3xl font-extrabold text-white mb-2">
					Odzyskaj hasło
				</h1>
				<p class="text-slate-400 text-sm">
					Podaj swój e-mail, aby otrzymać link do zresetowania hasła.
				</p>
			</div>

			<div
				class="bg-brand-card border border-brand-teal/20 rounded-2xl p-8 space-y-5 shadow-[0_20px_60px_rgba(0,0,0,0.4)]"
			>
				<template v-if="success">
					<div class="text-center space-y-4">
						<CheckCircle2
							class="w-16 h-16 text-brand-green mx-auto mb-4"
						/>
						<h2 class="text-xl font-bold text-white">
							Sprawdź swoją skrzynkę
						</h2>
						<p class="text-slate-300 text-sm leading-relaxed">
							Jeśli konto istnieje, wysłaliśmy link na Twój adres
							e-mail. Link będzie ważny przez 15 minut. Zwróć
							uwagę na folder spam.
						</p>
						<div class="pt-4">
							<NuxtLink
								to="/login"
								class="w-full h-11 flex items-center justify-center rounded-full font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:brightness-110 transition-all"
							>
								Wróć do logowania
							</NuxtLink>
						</div>
					</div>
				</template>

				<template v-else>
					<div class="space-y-4">
						<div class="space-y-2">
							<label
								for="email"
								class="text-sm font-medium text-slate-300"
								>Email</label
							>
							<input
								id="email"
								type="email"
								v-model="email"
								placeholder="ty@firma.pl"
								@keyup.enter="handleSubmit"
								class="w-full h-10 px-3 rounded-lg text-sm bg-brand-dark border border-brand-teal/20 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-1 focus:ring-brand-green/30 transition-colors"
							/>
						</div>

						<p
							v-if="error"
							class="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2"
						>
							{{ error }}
						</p>

						<button
							@click="handleSubmit"
							:disabled="loading || !email"
							class="w-full h-11 flex items-center justify-center gap-2 rounded-full font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
						>
							<Loader2
								v-if="loading"
								class="w-4 h-4 animate-spin"
							/>
							<template v-else>
								Wyślij link do resetu
								<ArrowRight class="w-4 h-4" />
							</template>
						</button>

						<div
							class="text-center mt-6 pt-6 border-t border-brand-teal/10"
						>
							<NuxtLink
								to="/login"
								class="inline-flex items-center gap-2 text-sm text-brand-green transition-colors hover:brightness-110 font-medium"
							>
								<ArrowLeft class="w-4 h-4" />
								Wróć do logowania
							</NuxtLink>
						</div>
					</div>
				</template>
			</div>
		</div>
	</div>
</template>
