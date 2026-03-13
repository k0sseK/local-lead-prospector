<script setup lang="ts">
import { ref } from "vue";
import {
	ArrowLeft,
	ArrowRight,
	Loader2,
	CheckCircle2,
	KeyRound,
} from "lucide-vue-next";
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
	<div
		class="flex-1 flex items-center justify-center py-16 px-4 relative overflow-hidden"
	>
		<!-- Background Glow -->
		<div
			class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-brand-green/10 rounded-full blur-[120px] -z-10 animate-pulse"
		></div>

		<div class="w-full max-w-md relative">
			<div class="text-center mb-10">
				<h1 class="text-4xl font-black text-white mb-3 tracking-tight">
					Odzyskaj
					<span
						class="text-transparent bg-clip-text bg-gradient-to-r from-brand-green to-brand-teal"
						>hasło</span
					>
				</h1>
				<p
					class="text-slate-400 text-sm max-w-[280px] mx-auto leading-relaxed"
				>
					Podaj swój e-mail, aby otrzymać bezpieczny link do
					zresetowania konta.
				</p>
			</div>

			<div
				class="bg-brand-card/80 backdrop-blur-xl border border-brand-teal/20 rounded-3xl p-8 space-y-6 shadow-[0_20px_60px_rgba(0,0,0,0.6)] relative overflow-hidden"
			>
				<!-- Subtle internal glow -->
				<div
					class="absolute -top-10 -right-10 w-32 h-32 bg-brand-teal/10 rounded-full blur-3xl"
				></div>

				<template v-if="success">
					<div
						class="text-center space-y-5 py-4 animate-in fade-in zoom-in duration-500"
					>
						<div class="relative inline-block">
							<CheckCircle2
								class="w-20 h-20 text-brand-green mx-auto relative z-10"
							/>
							<div
								class="absolute inset-0 bg-brand-green/20 blur-2xl rounded-full"
							></div>
						</div>
						<div class="space-y-2">
							<h2 class="text-2xl font-bold text-white">
								Sprawdź e-mail
							</h2>
							<p
								class="text-slate-400 text-sm leading-relaxed px-4"
							>
								Wysłaliśmy instrukcje na Twój adres. Link będzie
								ważny przez
								<span class="text-brand-green font-medium"
									>15 minut</span
								>.
							</p>
						</div>
						<div class="pt-6">
							<NuxtLink
								to="/login"
								class="w-full h-12 flex items-center justify-center rounded-full font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(56,239,125,0.3)]"
							>
								Wróć do logowania
							</NuxtLink>
						</div>
					</div>
				</template>

				<template v-else>
					<div class="space-y-5 relative">
						<div class="space-y-2">
							<label
								for="email"
								class="text-xs font-bold tracking-wider text-slate-500 ml-1"
								>Adres e-mail</label
							>
							<div class="relative group">
								<input
									id="email"
									type="email"
									v-model="email"
									placeholder="nazwa@firma.pl"
									@keyup.enter="handleSubmit"
									class="w-full h-12 px-4 rounded-xl text-sm bg-brand-dark/50 border border-brand-teal/20 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-4 focus:ring-brand-green/5 transition-all group-hover:border-brand-teal/40"
								/>
							</div>
						</div>

						<p
							v-if="error"
							class="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 animate-in slide-in-from-top-2 duration-300"
						>
							{{ error }}
						</p>

						<button
							@click="handleSubmit"
							:disabled="loading || !email"
							class="w-full h-12 flex items-center justify-center gap-2 rounded-xl font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-[0_10px_30px_rgba(0,0,0,0.3)]"
						>
							<Loader2
								v-if="loading"
								class="w-5 h-5 animate-spin"
							/>
							<template v-else> Wyślij link do resetu </template>
						</button>

						<div
							class="text-center mt-6 pt-6 border-t border-brand-teal/10"
						>
							<NuxtLink
								to="/login"
								class="inline-flex items-center gap-2 text-sm text-slate-400 transition-colors hover:text-brand-green font-medium group"
							>
								<ArrowLeft
									class="w-4 h-4 transition-transform group-hover:-translate-x-1"
								/>
								Wróć do logowania
							</NuxtLink>
						</div>
					</div>
				</template>
			</div>
		</div>
	</div>
</template>
