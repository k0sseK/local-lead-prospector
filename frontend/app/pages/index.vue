<script setup>
definePageMeta({
	layout: "default",
});
</script>

<template>
	<div class="flex-1 flex flex-col relative overflow-hidden bg-slate-50">
		<!-- Hero Section -->
		<section
			class="relative pt-24 pb-32 flex flex-col items-center justify-center min-h-[80vh] px-4 sm:px-6 lg:px-8 text-center bg-white border-b border-slate-200"
		>
			<!-- Decorative background glow -->
			<div
				class="absolute inset-0 z-0 overflow-hidden pointer-events-none"
			>
				<div
					class="absolute -top-[20%] -left-[10%] w-[50%] h-[50%] rounded-full bg-indigo-500/10 blur-[120px]"
				></div>
				<div
					class="absolute top-[40%] -right-[10%] w-[40%] h-[40%] rounded-full bg-blue-500/10 blur-[100px]"
				></div>
			</div>

			<div class="relative z-10 max-w-4xl mx-auto space-y-8">
				<div
					class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-100/50 text-indigo-600 text-sm font-medium mb-4 shadow-sm"
				>
					<span class="relative flex h-2 w-2">
						<span
							class="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"
						></span>
						<span
							class="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"
						></span>
					</span>
					Nuxt 4 + shadcn-vue MVP
				</div>

				<h1
					class="text-5xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-slate-900 leading-[1.1]"
				>
					Zdobądź klientów B2B <br class="hidden sm:block" />
					<span
						class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-blue-500"
						>w 3 minuty</span
					>
				</h1>

				<p
					class="text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed"
				>
					Zautomatyzuj pozyskiwanie leadów. Skanuj Google Maps,
					audytuj strony za pomocą AI i wysyłaj spersonalizowane maile
					bezpośrednio z wbudowanego CRM.
				</p>

				<div
					class="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
				>
					<NuxtLink to="/app">
						<Button
							size="lg"
							class="w-full sm:w-auto text-base h-12 px-8 bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-600/20 transition-all hover:-translate-y-0.5"
						>
							Rozpocznij za darmo
							<svg
								xmlns="http://www.w3.org/2000/svg"
								width="20"
								height="20"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
								class="lucide lucide-arrow-right ml-2"
							>
								<path d="M5 12h14" />
								<path d="m12 5 7 7-7 7" />
							</svg>
						</Button>
					</NuxtLink>
				</div>
			</div>
		</section>

		<!-- Features Section -->
		<section class="py-24 bg-slate-50 relative z-10">
			<div class="container mx-auto px-4 max-w-7xl">
				<h2 class="text-3xl font-bold text-center text-slate-900 mb-16">
					Jak to działa?
				</h2>
				<div class="grid grid-cols-1 md:grid-cols-3 gap-8">
					<Card
						class="border-slate-200 shadow-sm hover:shadow-md transition-shadow"
					>
						<CardHeader>
							<div
								class="w-12 h-12 rounded-xl bg-indigo-100 flex items-center justify-center text-indigo-600 mb-4"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="24"
									height="24"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									class="lucide lucide-map-pin"
								>
									<path
										d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"
									/>
									<circle cx="12" cy="10" r="3" />
								</svg>
							</div>
							<CardTitle>1. Znajdź firmy</CardTitle>
							<CardDescription
								>Wpisz słowo kluczowe i wybierz obszar na mapie,
								by błyskawicznie pobrać setki leadów z Google
								Places.</CardDescription
							>
						</CardHeader>
					</Card>

					<Card
						class="border-slate-200 shadow-sm hover:shadow-md transition-shadow"
					>
						<CardHeader>
							<div
								class="w-12 h-12 rounded-xl bg-blue-100 flex items-center justify-center text-blue-600 mb-4"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="24"
									height="24"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									class="lucide lucide-sparkles"
								>
									<path
										d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"
									/>
									<path d="M5 3v4" />
									<path d="M19 17v4" />
									<path d="M3 5h4" />
									<path d="M17 19h4" />
								</svg>
							</div>
							<CardTitle>2. Audyt AI</CardTitle>
							<CardDescription
								>Aplikacja sprawdzi stronę klienta (SSL, CMS,
								Social Media) i wygeneruje
								hiper-spersonalizowanego maila.</CardDescription
							>
						</CardHeader>
					</Card>

					<Card
						class="border-slate-200 shadow-sm hover:shadow-md transition-shadow"
					>
						<CardHeader>
							<div
								class="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center text-green-600 mb-4"
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									width="24"
									height="24"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									class="lucide lucide-send"
								>
									<path d="m22 2-7 20-4-9-9-4Z" />
									<path d="M22 2 11 13" />
								</svg>
							</div>
							<CardTitle>3. Zamykaj sprzedaż</CardTitle>
							<CardDescription
								>Wyślij propozycję bezpośrednio z wbudowanego
								CRM i zarządzaj statusem leada na tablicy
								Kanban.</CardDescription
							>
						</CardHeader>
					</Card>
				</div>
			</div>
		</section>
	</div>
</template>
