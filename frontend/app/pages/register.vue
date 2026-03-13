<script setup lang="ts">
import { useAuth } from "@/composables/useAuth";
import { ArrowRight, UserPlus, Mail, Lock, Loader2 } from "lucide-vue-next";

definePageMeta({ layout: "default" });

const { register, isAuthenticated } = useAuth();

if (isAuthenticated.value) {
	navigateTo("/app");
}

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const turnstileToken = ref("");
const turnstile = ref<{ reset: () => void } | null>(null);

function resetTurnstile() {
	turnstile.value?.reset();
	turnstileToken.value = "";
}

async function handleSubmit() {
	error.value = "";
	loading.value = true;
	try {
		await register(email.value, password.value, turnstileToken.value);
	} catch (err: any) {
		error.value =
			err.response?.data?.detail ||
			"Rejestracja nie powiodła się. Spróbuj ponownie.";
	} finally {
		resetTurnstile();
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
			class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-teal/5 rounded-full blur-[140px] -z-10 animate-pulse"
		></div>

		<div class="w-full max-w-md relative">
			<div class="text-center mb-10">
				<h1 class="text-4xl font-black text-white mb-3 tracking-tight">
					Utwórz
					<span
						class="text-transparent bg-clip-text bg-gradient-to-r from-brand-green to-brand-teal"
						>konto</span
					>
				</h1>
				<p
					class="text-slate-400 text-sm max-w-[280px] mx-auto leading-relaxed"
				>
					Zacznij za darmo — bez podawania karty kredytowej.
				</p>
			</div>

			<div
				class="bg-brand-card/80 backdrop-blur-xl border border-brand-teal/20 rounded-3xl p-8 space-y-6 shadow-[0_20px_60px_rgba(0,0,0,0.6)] relative overflow-hidden"
			>
				<!-- Subtle internal glow -->
				<div
					class="absolute -top-10 -right-10 w-32 h-32 bg-brand-green/10 rounded-full blur-3xl"
				></div>

				<div class="space-y-4">
					<div class="space-y-2">
						<label
							for="email"
							class="text-xs font-bold tracking-wider text-slate-500 ml-1"
							>Email</label
						>
						<div class="relative group">
							<input
								id="email"
								type="email"
								v-model="email"
								placeholder="ty@firma.pl"
								@keyup.enter="handleSubmit"
								class="w-full h-12 px-4 rounded-xl text-sm bg-brand-dark/50 border border-brand-teal/20 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-4 focus:ring-brand-green/5 transition-all group-hover:border-brand-teal/40"
							/>
							<Mail
								class="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 pointer-events-none"
							/>
						</div>
					</div>
					<div class="space-y-2">
						<label
							for="password"
							class="text-xs font-bold tracking-wider text-slate-500 ml-1"
							>Hasło</label
						>
						<div class="relative group">
							<input
								id="password"
								type="password"
								v-model="password"
								placeholder="••••••••"
								@keyup.enter="handleSubmit"
								class="w-full h-12 px-4 rounded-xl text-sm bg-brand-dark/50 border border-brand-teal/20 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-4 focus:ring-brand-green/5 transition-all group-hover:border-brand-teal/40"
							/>
							<Lock
								class="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-600 pointer-events-none"
							/>
						</div>
					</div>
				</div>

				<div class="flex justify-center py-2">
					<NuxtTurnstile ref="turnstile" v-model="turnstileToken" />
				</div>

				<p
					v-if="error"
					class="text-xs text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 animate-in slide-in-from-top-2 duration-300"
				>
					{{ error }}
				</p>

				<button
					@click="handleSubmit"
					:disabled="loading"
					class="w-full h-12 flex items-center justify-center gap-2 rounded-xl font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_10px_30px_rgba(0,0,0,0.3)]"
				>
					<template v-if="loading">
						<Loader2 class="w-5 h-5 animate-spin" />
						Tworzenie konta...
					</template>
					<template v-else> Utwórz konto </template>
				</button>
			</div>

			<p class="text-center text-sm text-slate-500 mt-8">
				Masz już konto?
				<NuxtLink
					to="/login"
					class="text-brand-green hover:brightness-110 font-bold transition-colors ml-1"
				>
					Zaloguj się
				</NuxtLink>
			</p>
		</div>
	</div>
</template>
