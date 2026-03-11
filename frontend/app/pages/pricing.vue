<script setup>
import { Check, Zap, Star } from "lucide-vue-next";

definePageMeta({
	layout: "default",
});

const CONTACT_EMAIL = "hello@znajdzfirmy.pl";
const config = useRuntimeConfig();
const { user, init } = useAuth();

await init();

const checkoutUrl = computed(() => {
	const base = config.public.lemonCheckoutUrl;
	if (!base) return `mailto:${CONTACT_EMAIL}?subject=Zamówienie planu Pro`;
	if (!user.value) return base;
	const url = new URL(base);
	url.searchParams.set("checkout[email]", user.value.email);
	url.searchParams.set("checkout[custom][user_id]", String(user.value.id));
	return url.toString();
});

const freePlan = [
	"10 audytów AI miesięcznie",
	"5 skanów Google Maps miesięcznie",
	"20 wysyłek e-mail miesięcznie",
	"Do 50 leadów w CRM",
	"Widok Kanban i listowy",
	"Eksport CSV",
];

const proPlan = [
	"300 audytów AI miesięcznie",
	"50 skanów Google Maps miesięcznie",
	"500 wysyłek e-mail miesięcznie",
	"Nieograniczona liczba leadów",
	"Priorytetowe wsparcie",
	"Wszystko z planu Darmowego",
];
</script>

<template>
	<div class="bg-brand-dark min-h-screen">
		<!-- Header -->
		<div
			class="container mx-auto px-6 lg:px-12 max-w-5xl pt-24 pb-16 text-center"
		>
			<h1
				class="text-5xl md:text-6xl font-extrabold text-white leading-tight mb-4"
			>
				Prosty cennik.<br />
				<span class="text-brand-green">Bez niespodzianek.</span>
			</h1>
			<p class="text-slate-400 text-lg max-w-xl mx-auto">
				Zacznij bezpłatnie i przejdź na Pro gdy jesteś gotowy na pełną
				automatyzację.
			</p>
		</div>

		<!-- Plans -->
		<div class="container mx-auto px-6 lg:px-12 max-w-5xl pb-24">
			<div
				class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-3xl mx-auto"
			>
				<!-- Free -->
				<div
					class="relative rounded-2xl border border-white/10 bg-white/5 p-8 flex flex-col"
				>
					<div class="mb-6">
						<p
							class="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-2"
						>
							Darmowy
						</p>
						<div class="flex items-end gap-2">
							<span class="text-5xl font-extrabold text-white"
								>0 PLN</span
							>
							<span class="text-slate-500 mb-1">/miesiąc</span>
						</div>
						<p class="text-slate-500 text-sm mt-2">
							Na zawsze darmowy
						</p>
					</div>

					<ul class="space-y-3 flex-1 mb-8">
						<li
							v-for="feature in freePlan"
							:key="feature"
							class="flex items-start gap-3 text-sm text-slate-300"
						>
							<Check
								class="w-4 h-4 text-brand-green flex-shrink-0 mt-0.5"
							/>
							{{ feature }}
						</li>
					</ul>

					<NuxtLink
						to="/register"
						class="w-full h-11 flex items-center justify-center rounded-full text-sm font-semibold border border-white/20 text-white hover:bg-white/10 transition-colors"
					>
						Zacznij za darmo
					</NuxtLink>
				</div>

				<!-- Pro -->
				<div
					class="relative rounded-2xl border border-brand-green/40 bg-brand-green/5 p-8 flex flex-col shadow-[0_0_40px_rgba(56,239,125,0.08)]"
				>
					<!-- Badge -->
					<div class="absolute -top-3 left-1/2 -translate-x-1/2">
						<span
							class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-brand-green text-black"
						>
							<Star class="w-3 h-3" />
							Najpopularniejszy
						</span>
					</div>

					<div class="mb-6">
						<p
							class="text-sm font-semibold uppercase tracking-wider text-brand-green mb-2"
						>
							Pro
						</p>
						<div class="flex items-end gap-2">
							<span class="text-5xl font-extrabold text-white"
								>49 PLN</span
							>
							<span class="text-slate-500 mb-1">/miesiąc</span>
						</div>
						<p class="text-slate-500 text-sm mt-2">
							Płatność kartą lub BLIK
						</p>
					</div>

					<ul class="space-y-3 flex-1 mb-8">
						<li
							v-for="feature in proPlan"
							:key="feature"
							class="flex items-start gap-3 text-sm text-slate-300"
						>
							<Check
								class="w-4 h-4 text-brand-green flex-shrink-0 mt-0.5"
							/>
							{{ feature }}
						</li>
					</ul>

					<a
						:href="checkoutUrl"
						target="_blank"
						rel="noopener noreferrer"
						class="w-full h-11 flex items-center justify-center gap-2 rounded-full text-sm font-bold bg-gradient-to-r from-brand-green to-brand-teal text-black hover:-translate-y-0.5 transition-all shadow-[0_8px_30px_rgba(56,239,125,0.2)]"
					>
						<Zap class="w-4 h-4" />
						Zamów plan Pro
					</a>
					<p class="text-center text-xs text-slate-600 mt-3">
						Dostęp aktywowany automatycznie po płatności
					</p>
				</div>
			</div>

			<!-- FAQ -->
			<div class="mt-20 max-w-2xl mx-auto">
				<h2 class="text-2xl font-bold text-white text-center mb-10">
					Często zadawane pytania
				</h2>
				<div class="space-y-6">
					<div class="border-b border-white/10 pb-6">
						<h3 class="text-white font-semibold mb-2">
							Jak działają limity?
						</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							Limity resetują się automatycznie pierwszego dnia
							każdego miesiąca. Bieżące zużycie widzisz w
							dashboardzie.
						</p>
					</div>
					<div class="border-b border-white/10 pb-6">
						<h3 class="text-white font-semibold mb-2">
							Jak zamówić plan Pro bez firmy?
						</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							Kliknij "Zamów plan Pro" — płatność obsługuje
							LemonSqueezy (karta, BLIK). Dostęp aktywuje się
							automatycznie, bez żadnych formalności.
						</p>
					</div>
					<div class="border-b border-white/10 pb-6">
						<h3 class="text-white font-semibold mb-2">
							Czy mogę anulować w dowolnym momencie?
						</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							Tak. Plan Pro jest miesięczny — po upływie
							opłaconego okresu konto wraca automatycznie do planu
							Darmowego.
						</p>
					</div>
					<div>
						<h3 class="text-white font-semibold mb-2">
							Co z kluczem API do Google Maps?
						</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							Aplikacja używa naszego klucza API — nie musisz
							konfigurować nic po swojej stronie. Skany Google
							Maps są wliczone w Twój limit.
						</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
