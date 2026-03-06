<script setup></script>

<template>
	<div class="min-h-screen bg-white flex flex-col font-sans text-slate-900">
		<!-- Navbar -->
		<header
			class="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/80 backdrop-blur-md"
		>
			<div
				class="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl flex h-16 items-center justify-between"
			>
				<NuxtLink to="/" class="flex items-center gap-2 group">
					<div
						class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm group-hover:bg-indigo-700 transition-colors"
					>
						L
					</div>
					<span class="font-bold text-lg tracking-tight"
						>Local Lead Prospector</span
					>
				</NuxtLink>
				<nav class="flex items-center gap-4">
					<NuxtLink to="/app">
						<Button
							variant="ghost"
							class="hidden sm:flex hover:bg-slate-100"
							>Log in</Button
						>
					</NuxtLink>
					<NuxtLink to="/app">
						<Button
							class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium shadow-sm transition-all hover:shadow-md"
						>
							Przejdź do aplikacji
						</Button>
					</NuxtLink>
				</nav>
			</div>
		</header>

		<!-- Pagemain content -->
		<main class="flex-1 flex flex-col">
			<slot />
		</main>

		<!-- Footer -->
		<footer class="border-t border-slate-200 bg-slate-50 py-8">
			<div
				class="container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-slate-500"
			>
				<p>
					&copy; 2026 Local Lead Prospector. Wszelkie prawa
					zastrzeżone.
				</p>
				<div class="flex gap-6">
					<a href="#" class="hover:text-slate-900 transition-colors"
						>Polityka prywatności</a
					>
					<a href="#" class="hover:text-slate-900 transition-colors"
						>Regulamin</a
					>
				</div>
			</div>
		</footer>
	</div>
</template>
