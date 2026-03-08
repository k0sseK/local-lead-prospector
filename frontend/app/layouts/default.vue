<script setup></script>

<template>
	<div class="min-h-screen flex flex-col bg-brand-dark text-slate-300">
		<!-- Navbar -->
		<header
			class="sticky top-0 z-50 w-full backdrop-blur-sm bg-brand-dark/95 border-b border-b-white/5"
		>
			<div
				class="container mx-auto px-6 lg:px-12 max-w-7xl flex h-20 items-center justify-between"
			>
				<NuxtLink to="/" class="flex items-center gap-3">
					<div
						class="w-9 h-9 rounded-md flex items-center justify-center bg-brand-green text-black font-bold text-xl shadow-[0_0_15px_rgba(56,239,125,0.3)]"
					>
						L
					</div>
					<span class="font-bold text-xl tracking-tight text-white"
						>Local Lead Prospector</span
					>
				</NuxtLink>
				<nav class="flex items-center gap-8">
					<NuxtLink
						to="/login"
						class="hidden sm:inline-block text-sm font-semibold text-slate-400 hover:text-brand-green transition-colors"
					>
						Log in
					</NuxtLink>
					<NuxtLink
						to="/register"
						class="px-6 py-2.5 rounded-full text-sm font-bold text-black bg-gradient-to-r from-brand-green to-brand-teal hover:brightness-110 transition-all shadow-[0_0_20px_rgba(56,239,125,0.2)]"
					>
						Get started
					</NuxtLink>
				</nav>
			</div>
		</header>

		<!-- Page content -->
		<main class="flex-1 flex flex-col">
			<slot />
		</main>

		<!-- Footer -->
		<footer class="py-16 bg-[#050807] border-t border-emerald-950/50">
			<div
				class="container mx-auto px-6 lg:px-12 max-w-7xl flex flex-col md:flex-row items-center justify-between gap-10"
			>
				<NuxtLink to="/" class="flex items-center gap-3">
					<div
						class="w-8 h-8 rounded-lg flex items-center justify-center text-black font-extrabold bg-gradient-to-r from-brand-green to-brand-teal"
					>
						L
					</div>
					<span class="font-bold text-white tracking-tight"
						>Local Lead Prospector</span
					>
				</NuxtLink>
				<!-- <div class="flex gap-12 text-sm text-emerald-100/30">
					<a href="#" class="hover:text-brand-green transition-colors"
						>Polityka prywatności</a
					>
					<a href="#" class="hover:text-brand-green transition-colors"
						>Regulamin</a
					>
					<a href="#" class="hover:text-brand-green transition-colors"
						>Kontakt</a
					>
				</div> -->
				<p class="text-sm text-emerald-100/30">
					&copy; 2026 Local Lead Prospector. Built for velocity.
				</p>
			</div>
		</footer>
	</div>
</template>
