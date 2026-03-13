<script setup lang="ts">
import { useAuth } from "@/composables/useAuth";
import api from "@/services/api";
import { ArrowRight, LogIn, Mail, Lock, Loader2 } from "lucide-vue-next";

definePageMeta({ layout: "default" });

const { login, isAuthenticated } = useAuth();

if (isAuthenticated.value) {
	navigateTo("/app");
}

const email = ref("");
const password = ref("");
const error = ref("");
const infoMessage = ref("");
const loading = ref(false);
const turnstileToken = ref("");
const resendLoading = ref(false);
const turnstile = ref<{ reset: () => void } | null>(null);

const canResendVerification = computed(
	() =>
		!!email.value.trim() && error.value.toLowerCase().includes("zweryfik"),
);

function resetTurnstile() {
	turnstile.value?.reset();
	turnstileToken.value = "";
}

async function handleSubmit() {
	error.value = "";
	infoMessage.value = "";
	loading.value = true;
	try {
		await login(email.value, password.value, turnstileToken.value);
	} catch (err: any) {
		error.value =
			err.response?.data?.detail || "Nieprawidłowy email lub hasło.";
	} finally {
		resetTurnstile();
		loading.value = false;
	}
}

async function handleResendVerification() {
	if (!email.value.trim()) {
		error.value =
			"Wpisz adres e-mail, na który mamy wysłać nowy link weryfikacyjny.";
		return;
	}

	error.value = "";
	infoMessage.value = "";
	resendLoading.value = true;
	try {
		const response = await api.resendVerification({
			email: email.value.trim(),
		});
		infoMessage.value =
			response.data?.message ||
			"Jeśli konto istnieje i nie zostało jeszcze zweryfikowane, wysłaliśmy nowy link aktywacyjny.";
	} catch (err: any) {
		error.value =
			err.response?.data?.detail ||
			"Nie udało się wysłać nowego linku. Spróbuj ponownie za chwilę.";
	} finally {
		resendLoading.value = false;
	}
}
</script>

<template>
	<div
		class="flex-1 flex items-center justify-center py-16 px-4 relative overflow-hidden"
	>
		<!-- Background Glow -->
		<div
			class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-green/5 rounded-full blur-[140px] -z-10 animate-pulse"
		></div>

		<div class="w-full max-w-md relative">
			<div class="text-center mb-10">
				<h1 class="text-4xl font-black text-white mb-3 tracking-tight">
					Zaloguj
					<span
						class="text-transparent bg-clip-text bg-gradient-to-r from-brand-green to-brand-teal"
						>się</span
					>
				</h1>
				<p
					class="text-slate-400 text-sm max-w-[280px] mx-auto leading-relaxed"
				>
					Zaloguj się do swojego panelu, aby zarządzać leadami.
				</p>
			</div>

			<div
				class="bg-brand-card/80 backdrop-blur-xl border border-brand-teal/20 rounded-3xl p-8 space-y-6 shadow-[0_20px_60px_rgba(0,0,0,0.6)] relative overflow-hidden"
			>
				<!-- Subtle internal glow -->
				<div
					class="absolute -top-10 -right-10 w-32 h-32 bg-brand-teal/10 rounded-full blur-3xl"
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
						<div class="flex items-center justify-between ml-1">
							<label
								for="password"
								class="text-xs font-bold tracking-wider text-slate-500"
								>Hasło</label
							>
							<NuxtLink
								to="/auth/forgot-password"
								class="text-xs text-brand-green hover:underline transition-colors brightness-110"
							>
								Zapomniałeś hasła?
							</NuxtLink>
						</div>
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

				<p
					v-if="infoMessage"
					class="text-xs text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3"
				>
					{{ infoMessage }}
				</p>

				<button
					v-if="canResendVerification"
					@click="handleResendVerification"
					:disabled="resendLoading"
					class="w-full h-11 flex items-center justify-center gap-2 rounded-xl font-semibold text-sm text-white border border-brand-teal/30 bg-brand-dark/40 hover:border-brand-green/40 hover:bg-brand-dark/60 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
				>
					<template v-if="resendLoading">
						<Loader2 class="w-4 h-4 animate-spin" />
						Wysyłanie linku...
					</template>
					<template v-else>
						Wyślij ponownie link weryfikacyjny
					</template>
				</button>

				<button
					@click="handleSubmit"
					:disabled="loading"
					class="w-full h-12 flex items-center justify-center gap-2 rounded-xl font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-[0_10px_30px_rgba(0,0,0,0.3)]"
				>
					<template v-if="loading">
						<Loader2 class="w-5 h-5 animate-spin" />
						Logowanie...
					</template>
					<template v-else> Zaloguj się </template>
				</button>
			</div>

			<p class="text-center text-sm text-slate-500 mt-8">
				Nie masz konta?
				<NuxtLink
					to="/register"
					class="text-brand-green hover:brightness-110 font-bold transition-colors ml-1"
				>
					Zarejestruj się za darmo
				</NuxtLink>
			</p>
		</div>
	</div>
</template>
