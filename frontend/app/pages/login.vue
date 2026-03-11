<script setup lang="ts">
import { useAuth } from "@/composables/useAuth";
import { ArrowRight } from "lucide-vue-next";

definePageMeta({ layout: "default" });

const { login, isAuthenticated } = useAuth();

if (isAuthenticated.value) {
	navigateTo("/app");
}

const email = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function handleSubmit() {
	error.value = "";
	loading.value = true;
	try {
		await login(email.value, password.value);
	} catch (err: any) {
		error.value =
			err.response?.data?.detail || "Nieprawidłowy email lub hasło.";
	} finally {
		loading.value = false;
	}
}
</script>

<template>
	<div class="flex-1 flex items-center justify-center py-16 px-4">
		<div class="w-full max-w-md">
			<div class="text-center mb-8">
				<h1 class="text-3xl font-extrabold text-white mb-2">
					Zaloguj się
				</h1>
				<p class="text-slate-400 text-sm">Wróć do swojego panelu CRM</p>
			</div>

			<div
				class="bg-brand-card border border-brand-teal/20 rounded-2xl p-8 space-y-5 shadow-[0_20px_60px_rgba(0,0,0,0.4)]"
			>
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
				<div class="space-y-2">
					<div class="flex items-center justify-between">
						<label
							for="password"
							class="text-sm font-medium text-slate-300"
							>Hasło</label
						>
						<NuxtLink
							to="/auth/forgot-password"
							class="text-xs text-brand-green hover:underline transition-colors brightness-110"
						>
							Zapomniałeś hasła?
						</NuxtLink>
					</div>
					<input
						id="password"
						type="password"
						v-model="password"
						placeholder="••••••••"
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
					:disabled="loading"
					class="w-full h-11 flex items-center justify-center gap-2 rounded-full font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{{ loading ? "Logowanie..." : "Zaloguj się" }}
					<ArrowRight v-if="!loading" class="w-4 h-4" />
				</button>
			</div>

			<p class="text-center text-sm text-slate-500 mt-6">
				Nie masz konta?
				<NuxtLink
					to="/register"
					class="text-brand-green hover:brightness-110 font-medium transition-colors"
				>
					Zarejestruj się
				</NuxtLink>
			</p>
		</div>
	</div>
</template>
