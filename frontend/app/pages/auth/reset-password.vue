<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ArrowLeft, Loader2, CheckCircle2, ShieldCheck, Lock } from "lucide-vue-next";
import api from "@/services/api";

definePageMeta({ layout: "default" });

const route = useRoute();
const password = ref("");
const confirmPassword = ref("");
const error = ref("");
const loading = ref(false);
const success = ref(false);
const token = ref<string>("");

onMounted(() => {
	token.value = route.query.token as string;
	if (!token.value) {
		error.value =
			"Brak lub nieprawidłowy token. Spróbuj zresetować hasło ponownie.";
	}
});

async function handleSubmit() {
	if (!token.value) {
		error.value = "Brak lub nieprawidłowy token.";
		return;
	}

	if (password.value !== confirmPassword.value) {
		error.value = "Podane hasła nie są takie same.";
		return;
	}

	if (password.value.length < 8) {
		error.value = "Hasło musi mieć co najmniej 8 znaków.";
		return;
	}

	error.value = "";
	loading.value = true;

	try {
		await api.resetPassword(token.value, password.value);
		success.value = true;
	} catch (err: any) {
		error.value =
			err.response?.data?.detail ||
			"Wygasły lub niepoprawny token. Spróbuj wygenerować nowy link.";
	} finally {
		loading.value = false;
	}
}
</script>

<template>
	<div class="flex-1 flex items-center justify-center py-16 px-4 relative overflow-hidden">
		<!-- Background Glow -->
		<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-teal/10 rounded-full blur-[140px] -z-10 animate-pulse"></div>

		<div class="w-full max-w-md relative">
			<div class="text-center mb-10">
				<div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-brand-teal/10 border border-brand-teal/20 text-brand-teal mb-6 shadow-[0_0_20px_rgba(17,153,142,0.15)]">
					<ShieldCheck class="w-8 h-8" />
				</div>
				<h1 class="text-4xl font-black text-white mb-3 tracking-tight">
					Nowe <span class="text-transparent bg-clip-text bg-gradient-to-r from-brand-green to-brand-teal">hasło</span>
				</h1>
				<p class="text-slate-400 text-sm max-w-[280px] mx-auto leading-relaxed">
					Twoje bezpieczeństwo jest priorytetem. Wprowadź nowe, silne hasło.
				</p>
			</div>

			<div
				class="bg-brand-card/80 backdrop-blur-xl border border-brand-teal/20 rounded-3xl p-8 space-y-6 shadow-[0_20px_60px_rgba(0,0,0,0.6)] relative overflow-hidden"
			>
				<!-- Subtle internal glow -->
				<div class="absolute -bottom-10 -left-10 w-32 h-32 bg-brand-green/10 rounded-full blur-3xl"></div>

				<template v-if="success">
					<div class="text-center space-y-5 py-4 animate-in fade-in zoom-in duration-500">
						<div class="relative inline-block">
							<CheckCircle2
								class="w-20 h-20 text-brand-green mx-auto relative z-10"
							/>
							<div class="absolute inset-0 bg-brand-green/20 blur-2xl rounded-full"></div>
						</div>
						<div class="space-y-2">
							<h2 class="text-2xl font-bold text-white">
								Hasło zmienione!
							</h2>
							<p class="text-slate-400 text-sm leading-relaxed px-4">
								Twoje konto jest już zabezpieczone nowym hasłem. Możesz się teraz zalogować.
							</p>
						</div>
						<div class="pt-6">
							<NuxtLink
								to="/login"
								class="w-full h-12 flex items-center justify-center rounded-full font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_0_20px_rgba(56,239,125,0.3)]"
							>
								Zaloguj się teraz
							</NuxtLink>
						</div>
					</div>
				</template>

				<template v-else>
					<div class="space-y-5 relative">
						<div class="space-y-4">
							<div class="space-y-2">
								<label
									for="password"
									class="text-xs font-bold uppercase tracking-wider text-slate-500 ml-1"
									>Nowe hasło</label
								>
								<div class="relative group">
									<input
										id="password"
										type="password"
										v-model="password"
										placeholder="••••••••"
										class="w-full h-12 px-4 rounded-xl text-sm bg-brand-dark/50 border border-brand-teal/20 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-4 focus:ring-brand-green/5 transition-all group-hover:border-brand-teal/40"
									/>
									<Lock class="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 pointer-events-none" />
								</div>
							</div>

							<div class="space-y-2">
								<label
									for="confirmPassword"
									class="text-xs font-bold uppercase tracking-wider text-slate-500 ml-1"
									>Powtórz hasło</label
								>
								<div class="relative group">
									<input
										id="confirmPassword"
										type="password"
										v-model="confirmPassword"
										placeholder="••••••••"
										@keyup.enter="handleSubmit"
										class="w-full h-12 px-4 rounded-xl text-sm bg-brand-dark/50 border border-brand-teal/20 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-4 focus:ring-brand-green/5 transition-all group-hover:border-brand-teal/40"
									/>
									<Lock class="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 pointer-events-none" />
								</div>
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
							:disabled="loading || !token"
							class="w-full h-12 flex items-center justify-center gap-2 rounded-xl font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 shadow-[0_10px_30px_rgba(0,0,0,0.3)]"
						>
							<Loader2
								v-if="loading"
								class="w-5 h-5 animate-spin"
							/>
							<template v-else>
								Zapisz nowe hasło
							</template>
						</button>

						<div
							class="text-center mt-6 pt-6 border-t border-brand-teal/10"
						>
							<NuxtLink
								to="/login"
								class="inline-flex items-center gap-2 text-sm text-slate-400 transition-colors hover:text-brand-green font-medium group"
							>
								<ArrowLeft class="w-4 h-4 transition-transform group-hover:-translate-x-1" />
								Wróć do logowania
							</NuxtLink>
						</div>
					</div>
				</template>
			</div>
		</div>
	</div>
</template>
