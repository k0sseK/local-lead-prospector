<script setup lang="ts">
const { data: articles, pending } = useAsyncData("wiedza-list", () =>
	queryCollection("wiedza").all(),
);
</script>

<template>
	<div class="min-h-screen bg-brand-dark text-white">
		<div class="max-w-4xl mx-auto px-6 py-16">
			<h1 class="text-4xl font-bold text-brand-green mb-2">Wiedza</h1>
			<p class="text-gray-400 mb-12 text-lg">
				Case studies i porady, które pomogą Ci zdobywać klientów B2B.
			</p>

			<div v-if="pending" class="text-gray-500">Ładowanie...</div>

			<div v-else-if="articles?.length" class="grid gap-6 sm:grid-cols-2">
				<NuxtLink
					v-for="article in articles"
					:key="article.path"
					:to="article.path"
					class="group block rounded-2xl border border-white/10 bg-brand-card p-6 transition hover:border-brand-green/50 hover:bg-white/5"
				>
					<p class="text-xs text-gray-500 mb-2">{{ article.date }}</p>
					<h2
						class="text-xl font-semibold text-white group-hover:text-brand-green transition mb-3 leading-snug"
					>
						{{ article.title }}
					</h2>
					<p class="text-gray-400 text-sm leading-relaxed line-clamp-3">
						{{ article.description }}
					</p>
					<span class="mt-4 inline-block text-sm text-brand-green font-medium">
						Czytaj dalej →
					</span>
				</NuxtLink>
			</div>

			<p v-else class="text-gray-500">Brak artykułów.</p>
		</div>
	</div>
</template>
