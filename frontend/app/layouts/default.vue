<script setup lang="ts">
import { useAuth } from "@/composables/useAuth";

const { isAuthenticated } = useAuth();
</script>

<template>
	<div class="min-h-screen flex flex-col bg-brand-dark text-slate-300">
		<!-- Navbar -->
		<header
			class="sticky top-0 z-50 w-full backdrop-blur-sm bg-brand-dark/95 border-b border-b-white/5"
		>
			<div
				class="container mx-auto px-6 lg:px-12 max-w-7xl flex h-20 items-center justify-between"
			>
				<NuxtLink to="/" class="flex items-center gap-2.5 group">
					<img src="/logo.png" alt="" class="h-8 w-auto" />
					<span class="font-bold text-xl tracking-tight leading-none">
						<span class="text-brand-green">znajdz</span
						><span class="text-white">firmy&#8203;.&#8203;pl</span>
					</span>
				</NuxtLink>
				<nav class="flex items-center gap-6">
					<NuxtLink
						to="/pricing"
						class="hidden sm:inline-block text-sm font-semibold text-slate-400 hover:text-brand-green transition-colors"
					>
						Cennik
					</NuxtLink>
					<NuxtLink
						to="/kontakt"
						class="hidden sm:inline-block text-sm font-semibold text-slate-400 hover:text-brand-green transition-colors"
					>
						Kontakt
					</NuxtLink>
					<template v-if="isAuthenticated">
						<NuxtLink
							to="/app"
							class="px-6 py-2.5 rounded-full text-sm font-bold text-black bg-gradient-to-r from-brand-green to-brand-teal hover:brightness-110 transition-all shadow-[0_0_20px_rgba(56,239,125,0.2)]"
						>
							Przejdź do panelu
						</NuxtLink>
					</template>
					<template v-else>
						<NuxtLink
							to="/login"
							class="hidden sm:inline-block text-sm font-semibold text-slate-400 hover:text-brand-green transition-colors"
						>
							Zaloguj się
						</NuxtLink>
						<NuxtLink
							to="/register"
							class="px-6 py-2.5 rounded-full text-sm font-bold text-black bg-gradient-to-r from-brand-green to-brand-teal hover:brightness-110 transition-all shadow-[0_0_20px_rgba(56,239,125,0.2)]"
						>
							Zacznij
						</NuxtLink>
					</template>
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
				<NuxtLink to="/" class="flex items-center gap-2.5 group">
					<img
						src="/logo.png"
						alt=""
						class="h-7 w-auto opacity-60 group-hover:opacity-100 transition-opacity"
					/>
					<span
						class="font-bold text-base tracking-tight leading-none opacity-60 group-hover:opacity-100 transition-opacity"
					>
						<span class="text-brand-green">znajdz</span
						><span class="text-white">firmy&#8203;.&#8203;pl</span>
					</span>
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
					&copy;
					{{ new Date().getFullYear() }} znajdzfirmy&#8203;.&#8203;pl.
					Built for velocity.
				</p>
			</div>
		</footer>
	</div>
</template>
