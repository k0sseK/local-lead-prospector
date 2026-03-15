<script setup>
import { useAuth } from "@/composables/useAuth";
import { useQuota } from "@/composables/useQuota";
import {
	LayoutDashboard,
	Settings,
	Home,
	LogOut,
	Zap,
	ShieldCheck,
	ScanSearch,
	Download,
	MailCheck,
} from "lucide-vue-next";
import { useRoute } from "vue-router";

const { user, logout } = useAuth();
const route = useRoute();

const initials = computed(() => {
	if (!user.value?.email) return "?";
	return user.value.email.substring(0, 2).toUpperCase();
});

const navItems = [
	{ to: "/app", icon: LayoutDashboard, label: "Wyszukiwarka" },
	{ to: "/app/scan-results", icon: ScanSearch, label: "Wyniki Skanowania" },
	{ to: "/app/sequences", icon: MailCheck, label: "Sekwencje e-mail" },
	{ to: "/app/export", icon: Download, label: "Eksport CSV" },
	{ to: "/app/settings", icon: Settings, label: "Ustawienia" },
	{
		to: "/app/admin",
		icon: ShieldCheck,
		label: "Panel Admina",
		adminOnly: true,
	},
];

// Quota state — shared global cache; no duplicate API call if already fetched
const { quota, fetchQuota } = useQuota();
const userPlan = computed(() => quota.value?.plan ?? "free");
const planLabel = computed(() => {
	if (userPlan.value === "admin") return "Admin";
	if (userPlan.value === "pro") return "Pro";
	return "Darmowy";
});
const planBadgeClass = computed(() => {
	if (userPlan.value === "admin") return "text-amber-300 font-semibold";
	if (userPlan.value === "pro") return "text-brand-green font-semibold";
	return "text-slate-500";
});
const isMobileMenuOpen = ref(false);

onMounted(() => fetchQuota());
</script>

<template>
	<div class="min-h-screen flex" style="background-color: #0f1a18">
		<!-- Sidebar -->
		<aside
			class="w-64 hidden md:flex flex-col flex-shrink-0 sticky top-0 h-screen bg-brand-dark border-r border-brand-teal/10"
		>
			<!-- Logo -->
			<div
				class="h-16 flex items-center px-5 border-b border-brand-teal/10"
			>
				<NuxtLink
					to="/"
					class="flex items-center gap-2 group focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0 transition-colors"
					@mousedown.prevent
				>
					<img
						src="/logo.png"
						alt=""
						class="h-6 w-auto flex-shrink-0"
					/>
					<span
						class="font-bold text-sm tracking-tight leading-none truncate"
					>
						<span class="text-brand-green">znajdz</span
						><span class="text-white">firmy&#8203;.&#8203;pl</span>
					</span>
				</NuxtLink>
			</div>

			<!-- Nav -->
			<nav class="flex-1 px-3 py-5 space-y-1 overflow-y-auto">
				<NuxtLink
					v-for="item in navItems"
					v-show="!item.adminOnly || user?.role === 'admin'"
					:key="item.to"
					:to="item.to"
					class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-75 focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0 border"
					:class="
						route.path.startsWith(item.to) &&
						(item.to === '/app' ? route.path === '/app' : true)
							? 'bg-brand-green/10 text-brand-green border-brand-green/20'
							: 'text-slate-400 hover:text-white hover:bg-white/5 border-transparent'
					"
					@mousedown.prevent
				>
					<component :is="item.icon" class="w-4 h-4 flex-shrink-0" />
					{{ item.label }}
				</NuxtLink>
			</nav>

			<!-- Upgrade CTA (only for free plan) -->
			<div v-if="userPlan === 'free'" class="px-3 pb-3">
				<NuxtLink
					to="/pricing"
					class="flex items-center gap-2 w-full px-3 py-2.5 rounded-lg bg-brand-green/10 border border-brand-green/20 text-brand-green text-xs font-semibold hover:bg-brand-green/15 transition-colors focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
					@mousedown.prevent
				>
					<Zap class="w-3.5 h-3.5 flex-shrink-0" />
					<span>Ulepsz do Pro</span>
					<span class="ml-auto text-brand-green/60">49 PLN/mc</span>
				</NuxtLink>
			</div>

			<!-- User -->
			<div class="p-3 border-t border-brand-teal/10">
				<div class="flex items-center gap-3 px-3 py-2 rounded-lg">
					<div
						class="w-8 h-8 rounded-full bg-brand-teal/20 border border-brand-teal/30 flex items-center justify-center text-brand-green font-bold text-xs flex-shrink-0"
					>
						{{ initials }}
					</div>
					<div class="flex flex-col flex-1 min-w-0">
						<span class="text-sm font-medium text-white truncate">{{
							user?.email ?? "..."
						}}</span>
						<span class="text-xs" :class="planBadgeClass">
							{{ planLabel }}
						</span>
					</div>
					<button
						@click="logout"
						title="Wyloguj"
						class="text-slate-600 hover:text-brand-green transition-colors flex-shrink-0"
					>
						<LogOut class="w-4 h-4" />
					</button>
				</div>
			</div>
		</aside>

		<!-- Main -->
		<div class="flex-1 flex flex-col min-w-0">
			<!-- Mobile header -->
			<header
				class="md:hidden sticky top-0 z-30 flex h-16 items-center px-4 border-b bg-brand-dark border-brand-teal/10 justify-between"
			>
				<NuxtLink
					to="/"
					class="flex items-center gap-2 focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
				>
					<img
						src="/logo.png"
						alt=""
						class="h-6 w-auto flex-shrink-0"
					/>
					<span class="font-bold text-sm tracking-tight leading-none">
						<span class="text-brand-green">znajdz</span
						><span class="text-white">firmy&#8203;.&#8203;pl</span>
					</span>
				</NuxtLink>
				<span class="font-bold text-sm text-white">Prospector CRM</span>
				<button
					@click="isMobileMenuOpen = !isMobileMenuOpen"
					class="text-slate-400 hover:text-white focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="20"
						height="20"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
					>
						<line x1="4" x2="20" y1="12" y2="12" />
						<line x1="4" x2="20" y1="6" y2="6" />
						<line x1="4" x2="20" y1="18" y2="18" />
					</svg>
				</button>
			</header>

			<!-- Mobile Menu Dropdown -->
			<div
				v-show="isMobileMenuOpen"
				class="md:hidden fixed inset-0 z-50 bg-brand-dark/95 backdrop-blur-sm flex flex-col pt-16"
			>
				<div
					class="absolute top-0 left-0 right-0 h-16 px-4 flex items-center justify-between border-b border-brand-teal/10 bg-brand-dark"
				>
					<NuxtLink
						to="/"
						class="flex items-center gap-2 focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
						@click="isMobileMenuOpen = false"
					>
						<img
							src="/logo.png"
							alt=""
							class="h-6 w-auto flex-shrink-0"
						/>
						<span
							class="font-bold text-sm tracking-tight leading-none"
						>
							<span class="text-brand-green">znajdz</span
							><span class="text-white"
								>firmy&#8203;.&#8203;pl</span
							>
						</span>
					</NuxtLink>
					<button
						@click="isMobileMenuOpen = false"
						class="text-slate-400 hover:text-white focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="20"
							height="20"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
						>
							<line x1="18" y1="6" x2="6" y2="18"></line>
							<line x1="6" y1="6" x2="18" y2="18"></line>
						</svg>
					</button>
				</div>

				<nav class="flex-1 px-4 py-8 space-y-2 overflow-y-auto">
					<NuxtLink
						v-for="item in navItems"
						v-show="!item.adminOnly || user?.role === 'admin'"
						:key="item.to"
						:to="item.to"
						class="flex items-center gap-4 px-4 py-3 rounded-xl text-base font-medium transition-colors border"
						:class="
							route.path.startsWith(item.to) &&
							(item.to === '/app' ? route.path === '/app' : true)
								? 'bg-brand-green/10 text-brand-green border-brand-green/20'
								: 'text-slate-400 hover:text-white hover:bg-white/5 border-transparent'
						"
						@click="isMobileMenuOpen = false"
					>
						<component
							:is="item.icon"
							class="w-5 h-5 flex-shrink-0"
						/>
						{{ item.label }}
					</NuxtLink>
				</nav>

				<div class="px-4 pb-4" v-if="userPlan === 'free'">
					<NuxtLink
						to="/pricing"
						class="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl bg-brand-green/10 border border-brand-green/20 text-brand-green text-sm font-semibold hover:bg-brand-green/15 transition-colors focus:outline-none"
						@click="isMobileMenuOpen = false"
					>
						<Zap class="w-4 h-4 flex-shrink-0" />
						<span>Ulepsz do Pro</span>
					</NuxtLink>
				</div>

				<!-- User mobile footer -->
				<div class="p-4 border-t border-brand-teal/10 pb-8">
					<div class="flex items-center gap-3">
						<div
							class="w-10 h-10 rounded-full bg-brand-teal/20 border border-brand-teal/30 flex items-center justify-center text-brand-green font-bold text-sm flex-shrink-0"
						>
							{{ initials }}
						</div>
						<div class="flex flex-col flex-1 min-w-0">
							<span
								class="text-sm font-medium text-white truncate"
								>{{ user?.email ?? "..." }}</span
							>
							<span class="text-xs" :class="planBadgeClass">
								{{ planLabel }}
							</span>
						</div>
						<button
							@click="logout"
							title="Wyloguj"
							class="text-slate-400 hover:text-brand-green transition-colors flex-shrink-0 p-2"
						>
							<LogOut class="w-5 h-5" />
						</button>
					</div>
				</div>
			</div>

			<!-- Page content -->
			<main class="flex-1 overflow-x-hidden text-slate-800">
				<slot />
			</main>
		</div>
	</div>
</template>

<style scoped>
/* Aggressively remove all focus indicators that cause the "white outline" */
:deep(a:focus),
:deep(button:focus),
:deep(a:active),
:deep(button:active),
:deep(a:focus-visible),
:deep(button:focus-visible) {
	outline: none !important;
	outline: 0 !important;
	box-shadow: none !important;
	-webkit-appearance: none;
	appearance: none;
	--tw-ring-offset-width: 0px !important;
	--tw-ring-width: 0px !important;
	--tw-ring-color: transparent !important;
}

aside a,
aside button,
header a,
header button {
	-webkit-tap-highlight-color: transparent;
}
</style>
