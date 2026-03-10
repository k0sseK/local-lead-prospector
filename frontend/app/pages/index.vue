<script setup>
import { ArrowRight, PlayCircle } from "lucide-vue-next";

definePageMeta({
	layout: "default",
});
</script>

<template>
	<div class="bg-brand-dark">
		<!-- Hero Section -->
		<section class="relative pt-24 pb-32 overflow-hidden">
			<div
				class="absolute top-0 right-0 w-[500px] h-[500px] rounded-full blur-[120px] pointer-events-none bg-brand-green/5"
			></div>

			<div class="container mx-auto px-6 lg:px-12 max-w-7xl">
				<div class="flex flex-col lg:flex-row items-center gap-16">
					<!-- Left: Headline & CTA -->
					<div class="flex-1 text-left space-y-8 z-10">
						<div
							v-motion
							:initial="{ opacity: 0, y: -16 }"
							:enter="{
								opacity: 1,
								y: 0,
								transition: { duration: 500 },
							}"
							class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase bg-brand-teal/10 border border-brand-teal/30 text-brand-green"
						>
							Przyszłość prospectingu B2B
						</div>

						<h1
							v-motion
							:initial="{ opacity: 0, y: 32 }"
							:enter="{
								opacity: 1,
								y: 0,
								transition: { duration: 650, delay: 120 },
							}"
							class="text-6xl md:text-7xl lg:text-8xl font-extrabold text-white leading-[1.05]"
						>
							Zdobądź klientów B2B<br />
							<span class="text-brand-green">w 3 minuty.</span>
						</h1>

						<p
							v-motion
							:initial="{ opacity: 0, y: 24 }"
							:enter="{
								opacity: 1,
								y: 0,
								transition: { duration: 600, delay: 260 },
							}"
							class="text-xl max-w-xl leading-relaxed text-slate-400"
						>
							Zautomatyzuj cały proces sprzedaży. Od skanowania
							Google Maps po inteligentny audyt stron i wysyłkę
							spersonalizowanych maili z CRM.
						</p>

						<div
							v-motion
							:initial="{ opacity: 0, y: 20 }"
							:enter="{
								opacity: 1,
								y: 0,
								transition: { duration: 600, delay: 400 },
							}"
							class="flex flex-col sm:flex-row items-center gap-4 pt-4"
						>
							<NuxtLink
								to="/register"
								class="w-full sm:w-auto h-14 px-10 flex items-center justify-center rounded-full text-lg font-bold text-black bg-gradient-to-r from-brand-green to-brand-teal transition-all hover:-translate-y-1 shadow-[0_10px_40px_rgba(56,239,125,0.25)]"
							>
								Rozpocznij za darmo
								<ArrowRight class="ml-3 w-6 h-6" />
							</NuxtLink>
							<NuxtLink
								to="/app"
								class="flex items-center gap-2 font-medium text-emerald-100/60 hover:text-white transition-colors"
							>
								<PlayCircle class="w-6 h-6" />
								Zobacz demo (2 min)
							</NuxtLink>
						</div>
					</div>

					<!-- Right: CRM mockup -->
					<div
						v-motion
						:initial="{ opacity: 0, x: 60 }"
						:enter="{
							opacity: 1,
							x: 0,
							transition: { duration: 700, delay: 200 },
						}"
						class="flex-1 w-full lg:w-auto relative"
					>
						<div
							class="rounded-2xl overflow-hidden lg:rotate-2 hover:rotate-0 transition-transform duration-500 border border-brand-green/10 shadow-[0_0_0_1px_rgba(56,239,125,0.1),0_20px_50px_rgba(0,0,0,0.6)]"
						>
							<!-- Fake browser chrome -->
							<div
								class="p-3 flex gap-1.5 border-b bg-brand-card border-brand-green/10"
							>
								<div
									class="w-2.5 h-2.5 rounded-full bg-brand-green/30"
								></div>
								<div
									class="w-2.5 h-2.5 rounded-full bg-brand-green/20"
								></div>
								<div
									class="w-2.5 h-2.5 rounded-full bg-brand-green/10"
								></div>
							</div>
							<!-- Kanban preview -->
							<div class="p-6 space-y-4 bg-[#0f1a18]">
								<div
									class="flex justify-between items-center mb-2"
								>
									<div
										class="h-3 w-20 rounded bg-brand-green/20"
									></div>
									<div
										class="h-6 w-6 rounded bg-brand-green/15"
									></div>
								</div>
								<div class="grid grid-cols-3 gap-3">
									<div class="space-y-2">
										<div
											class="h-2 w-12 rounded bg-brand-green/30"
										></div>
										<div
											class="rounded-lg p-3 space-y-2 bg-brand-card border border-brand-green/10"
										>
											<div
												class="h-2 w-full rounded bg-white/10"
											></div>
											<div
												class="h-2 w-3/4 rounded bg-white/[0.07]"
											></div>
											<div
												class="h-4 w-12 rounded-full mt-2 bg-brand-green/20"
											></div>
										</div>
										<div
											class="rounded-lg p-3 space-y-2 bg-brand-card border border-brand-green/10"
										>
											<div
												class="h-2 w-full rounded bg-white/10"
											></div>
											<div
												class="h-2 w-2/3 rounded bg-white/[0.07]"
											></div>
										</div>
									</div>
									<div class="space-y-2">
										<div
											class="h-2 w-16 rounded bg-brand-teal/40"
										></div>
										<div
											class="rounded-lg p-3 space-y-2 bg-brand-card border border-brand-teal/20"
										>
											<div
												class="h-2 w-full rounded bg-white/10"
											></div>
											<div
												class="h-2 w-4/5 rounded bg-white/[0.07]"
											></div>
											<div
												class="h-4 w-16 rounded-full mt-2 bg-brand-teal/25"
											></div>
										</div>
									</div>
									<div class="space-y-2">
										<div
											class="h-2 w-14 rounded bg-brand-green/20"
										></div>
										<div
											class="rounded-lg p-3 space-y-2 bg-brand-card border border-brand-green/10"
										>
											<div
												class="h-2 w-full rounded bg-white/10"
											></div>
											<div
												class="h-2 w-1/2 rounded bg-white/[0.07]"
											></div>
										</div>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!-- How It Works -->
		<section class="py-32 bg-[#0f1a18] border-b border-brand-teal/15">
			<div class="container mx-auto px-6 lg:px-12 max-w-7xl">
				<div
					v-motion
					:initial="{ opacity: 0, y: 40 }"
					:visible-once="{
						opacity: 1,
						y: 0,
						transition: { duration: 600 },
					}"
					class="text-center mb-20 space-y-4"
				>
					<h2 class="text-4xl md:text-5xl font-extrabold text-white">
						Jak to działa?
					</h2>
					<p
						class="text-lg text-slate-400 max-w-xl mx-auto leading-relaxed"
					>
						Trzy proste kroki dzielą Cię od pełnego lejka sprzedaży.
						Od surowych danych po gotowe deale.
					</p>
				</div>

				<div class="grid grid-cols-1 md:grid-cols-3 gap-16 lg:gap-24">
					<div
						v-motion
						:initial="{ opacity: 0, y: 50 }"
						:visible-once="{
							opacity: 1,
							y: 0,
							transition: { duration: 600, delay: 0 },
						}"
						class="relative pt-10"
					>
						<span
							class="absolute -top-4 -left-4 text-8xl font-extrabold select-none z-0 leading-none text-brand-green opacity-[0.08]"
							>1</span
						>
						<div class="relative z-10 space-y-4">
							<h3 class="text-2xl font-bold text-white">
								Znajdź firmy
							</h3>
							<p class="leading-relaxed text-slate-400">
								Wpisz słowo kluczowe i wybierz obszar na mapie,
								by błyskawicznie pobrać setki leadów z Google
								Places wraz z ich danymi kontaktowymi.
							</p>
						</div>
					</div>

					<div
						v-motion
						:initial="{ opacity: 0, y: 50 }"
						:visible-once="{
							opacity: 1,
							y: 0,
							transition: { duration: 600, delay: 160 },
						}"
						class="relative pt-10"
					>
						<span
							class="absolute -top-4 -left-4 text-8xl font-extrabold select-none z-0 leading-none text-brand-green opacity-[0.08]"
							>2</span
						>
						<div class="relative z-10 space-y-4">
							<h3 class="text-2xl font-bold text-white">
								Audyt AI
							</h3>
							<p class="leading-relaxed text-slate-400">
								Aplikacja sprawdzi stronę klienta (SSL, CMS,
								Social Media) i wygeneruje
								hiper-spersonalizowany scenariusz rozmowy lub
								maila.
							</p>
						</div>
					</div>

					<div
						v-motion
						:initial="{ opacity: 0, y: 50 }"
						:visible-once="{
							opacity: 1,
							y: 0,
							transition: { duration: 600, delay: 320 },
						}"
						class="relative pt-10"
					>
						<span
							class="absolute -top-4 -left-4 text-8xl font-extrabold select-none z-0 leading-none text-brand-green opacity-[0.08]"
							>3</span
						>
						<div class="relative z-10 space-y-4">
							<h3 class="text-2xl font-bold text-white">
								Zamykaj sprzedaż
							</h3>
							<p class="leading-relaxed text-slate-400">
								Wyślij propozycję bezpośrednio z wbudowanego CRM
								i zarządzaj statusem leada na przejrzystej
								tablicy Kanban.
							</p>
						</div>
					</div>
				</div>
			</div>
		</section>

		<!--CTA Section -->
		<section class="py-24 bg-brand-dark">
			<div class="container mx-auto px-6 lg:px-12 max-w-7xl">
				<div
					v-motion
					:initial="{ opacity: 0, scale: 0.96, y: 30 }"
					:visible-once="{
						opacity: 1,
						scale: 1,
						y: 0,
						transition: { duration: 650 },
					}"
					class="relative rounded-3xl overflow-hidden bg-gradient-to-br from-brand-green via-emerald-400 to-brand-teal px-12 py-20 text-center"
				>
					<h2
						class="text-4xl md:text-5xl lg:text-6xl font-extrabold text-[#0a1a0f] mb-10 leading-tight"
					>
						Gotowy na przyspieszenie<br />sprzedaży o 300%?
					</h2>
					<NuxtLink
						to="/register"
						class="inline-flex items-center justify-center px-10 py-4 rounded-full font-bold text-base text-brand-green bg-[#0a1a0f] hover:bg-[#0f2414] transition-all hover:-translate-y-0.5 shadow-xl"
					>
						Zacznij bezpłatny okres próbny
					</NuxtLink>
				</div>
			</div>
		</section>
	</div>
</template>
