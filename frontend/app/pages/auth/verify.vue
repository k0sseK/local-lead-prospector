<script setup lang="ts">
import {
	Loader2,
	CheckCircle2,
	XCircle,
	ArrowRight,
	Mail,
} from "lucide-vue-next";
import api from "@/services/api";

definePageMeta({ layout: "default" });

const route = useRoute();
const router = useRouter();

const status = ref<"loading" | "pending" | "success" | "error">("loading");
const errorMessage = ref("");
const resendEmail = ref("");
const resendLoading = ref(false);
const resendMessage = ref("");

onMounted(async () => {
	const token = route.query.token as string | undefined;
	const sent = route.query.sent as string | undefined;
	const email = route.query.email as string | undefined;
	if (email) {
		resendEmail.value = email;
	}

	if (!token && sent === "1") {
		status.value = "pending";
		return;
	}

	if (!token) {
		status.value = "error";
		errorMessage.value =
			"Brak tokenu weryfikacji. Upewnij się, że link pochodzi z poprawnie skopiowanego adresu e-mail.";
		return;
	}

	try {
		await api.verifyEmail(token);
		status.value = "success";
	} catch (err: any) {
		status.value = "error";
		errorMessage.value =
			err.response?.data?.detail ||
			"Wystąpił błąd podczas weryfikacji. Token mógł już wygasnąć lub zostać użyty.";
	}
});

function continueToApp() {
	router.push("/login");
}

async function handleResendVerification() {
	if (!resendEmail.value.trim()) {
		errorMessage.value =
			"Wpisz adres e-mail, na który mamy wysłać nowy link aktywacyjny.";
		status.value = "error";
		return;
	}

	resendLoading.value = true;
	resendMessage.value = "";
	try {
		const response = await api.resendVerification({
			email: resendEmail.value.trim(),
		});
		resendMessage.value =
			response.data?.message ||
			"Jeśli konto istnieje i nie zostało jeszcze zweryfikowane, wysłaliśmy nowy link aktywacyjny.";
		status.value = "pending";
	} catch (err: any) {
		status.value = "error";
		errorMessage.value =
			err.response?.data?.detail ||
			"Nie udało się wysłać nowego linku. Spróbuj ponownie za chwilę.";
	} finally {
		resendLoading.value = false;
	}
}
</script>

<template>
	<div
		class="flex-1 flex items-center justify-center py-16 px-4 relative overflow-hidden min-h-[calc(100vh-80px)]"
	>
		<!-- Background Glow -->
		<div
			class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-green/5 rounded-full blur-[140px] -z-10 animate-pulse"
		></div>

		<div class="w-full max-w-md relative">
			<div class="text-center mb-10">
				<h1 class="text-4xl font-black text-white mb-3 tracking-tight">
					Weryfikacja
					<span
						class="text-transparent bg-clip-text bg-gradient-to-r from-brand-green to-brand-teal"
						>E-mail</span
					>
				</h1>
				<p
					class="text-slate-400 text-sm max-w-[280px] mx-auto leading-relaxed"
				>
					Potwierdzanie Twojego adresu e-mail.
				</p>
			</div>

			<div
				class="bg-brand-card/80 backdrop-blur-xl border border-brand-teal/20 rounded-3xl p-8 space-y-6 shadow-[0_20px_60px_rgba(0,0,0,0.6)] relative overflow-hidden text-center"
			>
				<!-- Subtle internal glow -->
				<div
					class="absolute -top-10 -right-10 w-32 h-32 bg-brand-teal/10 rounded-full blur-3xl"
				></div>

				<div
					v-if="status === 'loading'"
					class="flex flex-col items-center justify-center py-8 space-y-4"
				>
					<Loader2 class="w-12 h-12 text-brand-green animate-spin" />
					<p class="text-slate-300 font-medium">
						Weryfikacja konta...
					</p>
				</div>

				<div
					v-else-if="status === 'pending'"
					class="flex flex-col items-center justify-center py-4 space-y-6"
				>
					<div
						class="w-16 h-16 bg-brand-teal/20 rounded-full flex items-center justify-center mb-2"
					>
						<Mail class="w-8 h-8 text-brand-teal" />
					</div>

					<div class="space-y-2">
						<h3 class="text-xl font-bold text-white">
							Sprawdź swoją skrzynkę
						</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							Wysłaliśmy link aktywacyjny na podany adres e-mail.
							Kliknij go, aby odblokować logowanie i limity konta.
						</p>
					</div>

					<div class="w-full space-y-3 text-left">
						<label
							for="resend-email"
							class="text-xs font-bold tracking-wider text-slate-500 ml-1 block"
						>
							E-mail do ponownej wysyłki
						</label>
						<input
							id="resend-email"
							v-model="resendEmail"
							type="email"
							placeholder="ty@firma.pl"
							class="w-full h-12 px-4 rounded-xl text-sm bg-brand-dark/50 border border-brand-teal/20 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-4 focus:ring-brand-green/5 transition-all"
						/>
						<button
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
						<p
							v-if="resendMessage"
							class="text-xs text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3"
						>
							{{ resendMessage }}
						</p>
					</div>

					<div class="pt-2">
						<NuxtLink
							to="/login"
							class="text-brand-green hover:underline font-medium flex items-center justify-center gap-2 text-sm"
						>
							Przejdź do logowania
						</NuxtLink>
					</div>
				</div>

				<div
					v-else-if="status === 'success'"
					class="flex flex-col items-center justify-center py-4 space-y-6"
				>
					<div
						class="w-16 h-16 bg-brand-green/20 rounded-full flex items-center justify-center mb-2"
					>
						<CheckCircle2 class="w-8 h-8 text-brand-green" />
					</div>

					<div class="space-y-2">
						<h3 class="text-xl font-bold text-white">Sukces!</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							Konto zweryfikowane pomyślnie! Twoje darmowe limity
							zostały odblokowane.
						</p>
					</div>

					<button
						@click="continueToApp"
						class="w-full h-12 flex items-center justify-center gap-2 rounded-xl font-bold text-sm text-black bg-gradient-to-r from-brand-green to-brand-teal hover:scale-[1.02] active:scale-[0.98] transition-all shadow-[0_10px_30px_rgba(0,0,0,0.3)] mt-4"
					>
						Przejdź do aplikacji
						<ArrowRight class="w-4 h-4" />
					</button>
				</div>

				<div
					v-else-if="status === 'error'"
					class="flex flex-col items-center justify-center py-4 space-y-6"
				>
					<div
						class="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mb-2"
					>
						<XCircle class="w-8 h-8 text-red-500" />
					</div>

					<div class="space-y-2">
						<h3 class="text-xl font-bold text-white">
							Weryfikacja nieudana
						</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							{{ errorMessage }}
						</p>
					</div>

					<div class="w-full space-y-3 text-left">
						<label
							for="resend-email-error"
							class="text-xs font-bold tracking-wider text-slate-500 ml-1 block"
						>
							Wyślij nowy link na adres e-mail
						</label>
						<input
							id="resend-email-error"
							v-model="resendEmail"
							type="email"
							placeholder="ty@firma.pl"
							class="w-full h-12 px-4 rounded-xl text-sm bg-brand-dark/50 border border-brand-teal/20 text-white placeholder:text-slate-600 focus:outline-none focus:border-brand-green/50 focus:ring-4 focus:ring-brand-green/5 transition-all"
						/>
						<button
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
						<p
							v-if="resendMessage"
							class="text-xs text-emerald-300 bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-3"
						>
							{{ resendMessage }}
						</p>
					</div>

					<div class="pt-4">
						<NuxtLink
							to="/login"
							class="text-brand-green hover:underline font-medium flex items-center justify-center gap-2 text-sm"
						>
							Wróć do logowania
						</NuxtLink>
					</div>
				</div>
			</div>

			<p class="text-center text-sm text-slate-500 mt-8">
				Skontaktuj się z
				<a
					href="mailto:kontakt@znajdzfirmy.pl"
					class="text-brand-green hover:brightness-110 font-bold transition-colors"
					>pomocą</a
				>
				techniczną.
			</p>
		</div>
	</div>
</template>
