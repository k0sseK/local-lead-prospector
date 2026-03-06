<script setup>
import { useAuth } from "@/composables/useAuth"

const { user, logout } = useAuth()

const initials = computed(() => {
  if (!user.value?.email) return "?"
  return user.value.email.substring(0, 2).toUpperCase()
})
</script>

<template>
	<div class="min-h-screen bg-slate-50 flex font-sans text-slate-900">
		<!-- Sidebar -->
		<aside
			class="w-64 border-r border-slate-200 bg-white hidden md:flex flex-col flex-shrink-0 sticky top-0 h-screen"
		>
			<div class="h-16 flex items-center px-6 border-b border-slate-200">
				<NuxtLink to="/" class="flex items-center gap-2 group">
					<div
						class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm group-hover:bg-indigo-700 transition-colors"
					>
						L
					</div>
					<span class="font-bold text-sm tracking-tight truncate"
						>Local Lead Prospector</span
					>
				</NuxtLink>
			</div>
			<nav class="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
				<NuxtLink
					to="/app"
					class="flex items-center gap-3 px-3 py-2 rounded-md bg-indigo-50 text-indigo-700 font-medium transition-colors"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="18"
						height="18"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="lucide lucide-layout-dashboard"
					>
						<rect width="7" height="9" x="3" y="3" rx="1" />
						<rect width="7" height="5" x="14" y="3" rx="1" />
						<rect width="7" height="9" x="14" y="12" rx="1" />
						<rect width="7" height="5" x="3" y="16" rx="1" />
					</svg>
					Prospector CRM
				</NuxtLink>
				<NuxtLink
					to="/"
					class="flex items-center gap-3 px-3 py-2 rounded-md text-slate-600 hover:bg-slate-50 hover:text-slate-900 font-medium transition-colors"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="18"
						height="18"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						class="lucide lucide-home"
					>
						<path
							d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"
						/>
						<polyline points="9 22 9 12 15 12 15 22" />
					</svg>
					Powrót na stronę
				</NuxtLink>
			</nav>
			<div class="p-4 border-t border-slate-200">
				<div class="flex items-center gap-3 px-3 py-2">
					<div
						class="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center text-slate-600 font-medium text-xs flex-shrink-0"
					>
						{{ initials }}
					</div>
					<div class="flex flex-col flex-1 min-w-0">
						<span class="text-sm font-medium truncate">{{ user?.email ?? "..." }}</span>
						<span class="text-xs text-slate-500">{{ user?.role ?? "" }}</span>
					</div>
					<button
						@click="logout"
						title="Log out"
						class="text-slate-400 hover:text-slate-700 transition-colors flex-shrink-0"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							width="16"
							height="16"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
							<polyline points="16 17 21 12 16 7" />
							<line x1="21" x2="9" y1="12" y2="12" />
						</svg>
					</button>
				</div>
			</div>
		</aside>

		<!-- Main Content -->
		<div class="flex-1 flex flex-col min-w-0">
			<!-- Mobile Header -->
			<header
				class="md:hidden sticky top-0 z-30 flex h-16 items-center px-4 border-b border-slate-200 bg-white shadow-sm justify-between"
			>
				<NuxtLink to="/" class="flex items-center gap-2">
					<div
						class="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-sm"
					>
						L
					</div>
				</NuxtLink>
				<span class="font-bold text-sm">Prospector CRM</span>
				<Button variant="ghost" size="icon">
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
						class="lucide lucide-menu"
					>
						<line x1="4" x2="20" y1="12" y2="12" />
						<line x1="4" x2="20" y1="6" y2="6" />
						<line x1="4" x2="20" y1="18" y2="18" />
					</svg>
				</Button>
			</header>

			<!-- Page Content -->
			<main class="flex-1 overflow-x-hidden">
				<slot />
			</main>
		</div>
	</div>
</template>
