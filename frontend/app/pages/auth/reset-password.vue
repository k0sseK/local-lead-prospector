<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ArrowLeft, Loader2, CheckCircle2 } from "lucide-vue-next";
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
		const response = await api.resetPassword(token.value, password.value);
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
					Nowe hasło
				</h1>
				<p class="text-slate-400 text-sm">
					Wprowadź i potwierdź swoje nowe hasło do systemu.
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
							Hasło zostało zmienione
						</h2>
						<p class="text-slate-300 text-sm leading-relaxed">
							Twoje hasło zostało pomyślnie zmienione. Możesz
							teraz wrócić do strony logowania.
						</p>
						<div class="pt-4">
							<NuxtLink
								to="/login"
								class="w-full h-11 flex items-center justify-center rounded-full font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:brightness-110 transition-all"
							>
								Zaloguj się na nowo
							</NuxtLink>
						</div>
					</div>
				</template>

				<template v-else>
					<div class="space-y-4">
						<div class="space-y-2">
							<label
								for="password"
								class="text-sm font-medium text-slate-300"
								>Nowe hasło</label
							>
							<input
								id="password"
								type="password"
								v-model="password"
								placeholder="••••••••"
								class="w-full h-10 px-3 rounded-lg text-sm bg-brand-dark border border-brand-teal/20 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-1 focus:ring-brand-green/30 transition-colors"
							/>
						</div>

						<div class="space-y-2">
							<label
								for="confirmPassword"
								class="text-sm font-medium text-slate-300"
								>Powtórz powe hasło</label
							>
							<input
								id="confirmPassword"
								type="password"
								v-model="confirmPassword"
								placeholder="••••••••"
								@keyup.enter="handleSubmit"
								class="w-full h-10 px-3 rounded-lg text-sm bg-brand-dark border border-brand-teal/20 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-1 focus:ring-brand-green/30 transition-colors"
							/>
						</div>

						<p
							v-if="error"
							class="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 leading-tight"
						>
							{{ error }}
						</p>

						<button
							@click="handleSubmit"
							:disabled="loading || !token"
							class="w-full h-11 flex items-center justify-center gap-2 rounded-full font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:brightness-110 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
						>
							<Loader2
								v-if="loading"
								class="w-4 h-4 animate-spin"
							/>
							<template v-else> Zmień hasło i zapisz </template>
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
