<script setup>
import { Check, Zap, Star, Bolt, RefreshCw } from "lucide-vue-next";

definePageMeta({
	layout: "default",
});

const CONTACT_EMAIL = "hello@znajdzfirmy.pl";
const config = useRuntimeConfig();
const { user, init } = useAuth();

await init();

const billingPeriod = ref("monthly"); // 'monthly' | 'annual'

function buildCheckoutUrl(base) {
	if (!base) return `mailto:${CONTACT_EMAIL}?subject=Zamówienie`;
	if (!user.value) return base;
	try {
		const url = new URL(base);
		url.searchParams.set("checkout[email]", user.value.email);
		url.searchParams.set("checkout[custom][user_id]", String(user.value.id));
		return url.toString();
	} catch {
		return base;
	}
}

const proCheckoutUrl = computed(() =>
	buildCheckoutUrl(
		billingPeriod.value === "annual"
			? config.public.lsAnnualUrl
			: config.public.lsProUrl,
	),
);

const credits50Url = computed(() => buildCheckoutUrl(config.public.lsCredits50Url));
const credits200Url = computed(() => buildCheckoutUrl(config.public.lsCredits200Url));
const credits500Url = computed(() => buildCheckoutUrl(config.public.lsCredits500Url));

const freePlan = [
	"15 kredytów miesięcznie",
	"Reset 1. dnia miesiąca",
	"Do 50 leadów w CRM",
	"Widok Kanban i listowy",
	"Eksport CSV",
];

const proPlan = [
	"250 kredytów miesięcznie",
	"Rollover — niewykorzystane kredyty przechodzą (maks 500)",
	"Nieograniczona liczba leadów",
	"Priorytetowe wsparcie",
	"Wszystko z planu Darmowego",
];

const actionCosts = [
	{ label: "Skan wyników Google Maps", cost: 3, icon: "🔍" },
	{ label: "Audyt AI strony internetowej", cost: 2, icon: "🤖" },
	{ label: "Sekwencja emailowa (3 kroki)", cost: 1, icon: "✉️" },
];

const creditPacks = [
	{ credits: 50, price: 39, urlKey: "credits50Url" },
	{ credits: 200, price: 129, urlKey: "credits200Url", badge: "Najpopularniejszy" },
	{ credits: 500, price: 279, urlKey: "credits500Url", badge: "Najlepsza wartość" },
];
</script>

<template>
	<div class="bg-brand-dark min-h-screen">
		<!-- Header -->
		<div class="container mx-auto px-6 lg:px-12 max-w-5xl pt-24 pb-12 text-center">
			<h1 class="text-5xl md:text-6xl font-extrabold text-white leading-tight mb-4">
				Prosty cennik.<br />
				<span class="text-brand-green">Bez niespodzianek.</span>
			</h1>
			<p class="text-slate-400 text-lg max-w-xl mx-auto">
				Zacznij bezpłatnie i przejdź na Pro gdy jesteś gotowy. Możesz też doładować kredyty jednorazowo.
			</p>
		</div>

		<div class="container mx-auto px-6 lg:px-12 max-w-5xl pb-24">

			<!-- Billing toggle -->
			<div class="flex items-center justify-center gap-3 mb-10">
				<span :class="billingPeriod === 'monthly' ? 'text-white font-semibold' : 'text-slate-500'" class="text-sm cursor-pointer" @click="billingPeriod = 'monthly'">Miesięcznie</span>
				<button
					class="relative w-12 h-6 rounded-full transition-colors"
					:class="billingPeriod === 'annual' ? 'bg-brand-green' : 'bg-white/20'"
					@click="billingPeriod = billingPeriod === 'monthly' ? 'annual' : 'monthly'"
				>
					<span
						class="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform"
						:class="billingPeriod === 'annual' ? 'translate-x-6' : 'translate-x-0'"
					/>
				</button>
				<span :class="billingPeriod === 'annual' ? 'text-white font-semibold' : 'text-slate-500'" class="text-sm cursor-pointer" @click="billingPeriod = 'annual'">
					Rocznie
					<span class="ml-1.5 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-bold bg-brand-green/20 text-brand-green">-20%</span>
				</span>
			</div>

			<!-- Plan cards -->
			<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
				<!-- Free -->
				<div class="relative rounded-2xl border border-white/10 bg-white/5 p-7 flex flex-col">
					<div class="mb-5">
						<p class="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-2">Darmowy</p>
						<div class="flex items-end gap-2">
							<span class="text-4xl font-extrabold text-white">0 PLN</span>
							<span class="text-slate-500 mb-1">/mies</span>
						</div>
						<p class="text-slate-500 text-sm mt-1">Na zawsze darmowy</p>
					</div>
					<ul class="space-y-2.5 flex-1 mb-7">
						<li v-for="f in freePlan" :key="f" class="flex items-start gap-2.5 text-sm text-slate-300">
							<Check class="w-4 h-4 text-brand-green flex-shrink-0 mt-0.5" />
							{{ f }}
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
				<div class="relative rounded-2xl border border-brand-green/40 bg-brand-green/5 p-7 flex flex-col shadow-[0_0_40px_rgba(56,239,125,0.08)] md:col-span-1">
					<div class="absolute -top-3 left-1/2 -translate-x-1/2">
						<span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-brand-green text-black">
							<Star class="w-3 h-3" />
							Najpopularniejszy
						</span>
					</div>
					<div class="mb-5">
						<p class="text-sm font-semibold uppercase tracking-wider text-brand-green mb-2">Pro</p>
						<div class="flex items-end gap-2">
							<span class="text-4xl font-extrabold text-white">
								{{ billingPeriod === 'annual' ? '47' : '59' }} PLN
							</span>
							<span class="text-slate-500 mb-1">/mies</span>
						</div>
						<p class="text-slate-500 text-sm mt-1">
							<template v-if="billingPeriod === 'annual'">564 PLN/rok · oszczędzasz 144 PLN</template>
							<template v-else>Płatność kartą lub BLIK</template>
						</p>
					</div>
					<ul class="space-y-2.5 flex-1 mb-7">
						<li v-for="f in proPlan" :key="f" class="flex items-start gap-2.5 text-sm text-slate-300">
							<Check class="w-4 h-4 text-brand-green flex-shrink-0 mt-0.5" />
							{{ f }}
						</li>
					</ul>
					<a
						:href="proCheckoutUrl"
						target="_blank"
						rel="noopener noreferrer"
						class="w-full h-11 flex items-center justify-center gap-2 rounded-full text-sm font-bold bg-gradient-to-r from-brand-green to-brand-teal text-black hover:-translate-y-0.5 transition-all shadow-[0_8px_30px_rgba(56,239,125,0.2)]"
					>
						<Zap class="w-4 h-4" />
						{{ billingPeriod === 'annual' ? 'Zamów plan Pro Roczny' : 'Zamów plan Pro' }}
					</a>
					<p class="text-center text-xs text-slate-600 mt-2">Dostęp aktywowany automatycznie po płatności</p>
				</div>

				<!-- Blank / action costs card -->
				<div class="rounded-2xl border border-white/10 bg-white/5 p-7 flex flex-col">
					<p class="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">Koszt akcji</p>
					<p class="text-slate-500 text-xs mb-5">Kredyty odliczane z puli miesięcznej (potem z doładowań)</p>
					<div class="space-y-4 flex-1">
						<div v-for="a in actionCosts" :key="a.label" class="flex items-center justify-between">
							<div class="flex items-center gap-2 text-sm text-slate-300">
								<span>{{ a.icon }}</span>
								<span>{{ a.label }}</span>
							</div>
							<span class="text-brand-green font-bold text-sm whitespace-nowrap">{{ a.cost }} kr</span>
						</div>
					</div>
					<div class="mt-6 pt-4 border-t border-white/10">
						<p class="text-xs text-slate-500">Przykład: 15 kr darmowych = 5 skanów lub 7 audytów AI lub 15 sekwencji emailowych.</p>
					</div>
				</div>
			</div>

			<!-- Credit packs section -->
			<div id="doladowania" class="mb-16">
				<div class="text-center mb-8">
					<h2 class="text-2xl font-bold text-white mb-2">Doładowania kredytów</h2>
					<p class="text-slate-400 text-sm">Jednorazowy zakup — kredyty z doładowań <strong class="text-white">nigdy nie wygasają</strong> i są zużywane po wyczerpaniu puli miesięcznej.</p>
				</div>
				<div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
					<!-- 50 credits -->
					<div class="relative rounded-2xl border border-white/10 bg-white/5 p-6 flex flex-col items-center text-center">
						<p class="text-3xl font-extrabold text-white mb-1">50 kr</p>
						<p class="text-slate-400 text-sm mb-4">= 16 skanów lub 25 audytów AI</p>
						<p class="text-2xl font-bold text-white mb-5">39 PLN</p>
						<a
							:href="credits50Url"
							target="_blank"
							rel="noopener noreferrer"
							class="w-full h-10 flex items-center justify-center rounded-full text-sm font-semibold border border-white/20 text-white hover:bg-white/10 transition-colors"
						>
							Kup 50 kredytów
						</a>
					</div>
					<!-- 200 credits -->
					<div class="relative rounded-2xl border border-brand-green/30 bg-brand-green/5 p-6 flex flex-col items-center text-center">
						<div class="absolute -top-3 left-1/2 -translate-x-1/2">
							<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-brand-green text-black">Najpopularniejszy</span>
						</div>
						<p class="text-3xl font-extrabold text-white mb-1">200 kr</p>
						<p class="text-slate-400 text-sm mb-4">= 66 skanów lub 100 audytów AI</p>
						<p class="text-2xl font-bold text-white mb-5">129 PLN <span class="text-sm text-brand-green font-normal">0,65 PLN/kr</span></p>
						<a
							:href="credits200Url"
							target="_blank"
							rel="noopener noreferrer"
							class="w-full h-10 flex items-center justify-center gap-2 rounded-full text-sm font-bold bg-gradient-to-r from-brand-green to-brand-teal text-black hover:-translate-y-0.5 transition-all"
						>
							<Zap class="w-3.5 h-3.5" />
							Kup 200 kredytów
						</a>
					</div>
					<!-- 500 credits -->
					<div class="relative rounded-2xl border border-white/10 bg-white/5 p-6 flex flex-col items-center text-center">
						<div class="absolute -top-3 left-1/2 -translate-x-1/2">
							<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-white/10 text-slate-300">Najlepsza wartość</span>
						</div>
						<p class="text-3xl font-extrabold text-white mb-1">500 kr</p>
						<p class="text-slate-400 text-sm mb-4">= 166 skanów lub 250 audytów AI</p>
						<p class="text-2xl font-bold text-white mb-5">279 PLN <span class="text-sm text-brand-green font-normal">0,56 PLN/kr</span></p>
						<a
							:href="credits500Url"
							target="_blank"
							rel="noopener noreferrer"
							class="w-full h-10 flex items-center justify-center rounded-full text-sm font-semibold border border-white/20 text-white hover:bg-white/10 transition-colors"
						>
							Kup 500 kredytów
						</a>
					</div>
				</div>
			</div>

			<!-- FAQ -->
			<div class="mt-4 max-w-2xl mx-auto">
				<h2 class="text-2xl font-bold text-white text-center mb-10">Często zadawane pytania</h2>
				<div class="space-y-6">
					<div class="border-b border-white/10 pb-6">
						<h3 class="text-white font-semibold mb-2">Jak działają kredyty?</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							Każda akcja kosztuje kredyty: skan Google Maps — 3 kr, audyt AI — 2 kr, sekwencja emailowa — 1 kr.
							Kredyty miesięczne resetują się 1. dnia miesiąca (plan Pro — z rolloverem do maks. 500 kr).
							Kredyty z doładowań są zużywane po wyczerpaniu puli miesięcznej i nigdy nie wygasają.
						</p>
					</div>
					<div class="border-b border-white/10 pb-6">
						<h3 class="text-white font-semibold mb-2">Czym rollover różni się od zwykłego resetu?</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							W planie Pro niewykorzystane kredyty miesięczne przechodzą na kolejny miesiąc.
							Jeśli zużyjesz tylko 50 z 250 kr, następny miesiąc zaczynasz od 200 + 250 = 450 kr (maks. 500).
							Plan Darmowy resetuje się do 15 kr bez rollover.
						</p>
					</div>
					<div class="border-b border-white/10 pb-6">
						<h3 class="text-white font-semibold mb-2">Czy kredyty z doładowań wygasają?</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							Nie. Kredyty zakupione w paczkach nie mają daty ważności — możesz ich użyć kiedy chcesz.
						</p>
					</div>
					<div class="border-b border-white/10 pb-6">
						<h3 class="text-white font-semibold mb-2">Czy mogę anulować subskrypcję w dowolnym momencie?</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							Tak. Anulowanie jest możliwe w każdej chwili w ustawieniach konta.
							Po upływie opłaconego okresu konto wraca automatycznie do planu Darmowego.
						</p>
					</div>
					<div>
						<h3 class="text-white font-semibold mb-2">Co z kluczem API do Google Maps?</h3>
						<p class="text-slate-400 text-sm leading-relaxed">
							Aplikacja używa naszego klucza API — nie musisz konfigurować nic po swojej stronie.
						</p>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>
