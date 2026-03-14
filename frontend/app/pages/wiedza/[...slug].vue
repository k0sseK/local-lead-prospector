<script setup lang="ts">
const route = useRoute();

const { data: article } = useAsyncData(`article-${route.path}`, () =>
	queryCollection("wiedza").path(route.path).first(),
);
</script>

<template>
	<div class="min-h-screen bg-brand-dark text-white">
		<div class="max-w-3xl mx-auto px-6 py-16">
			<NuxtLink
				to="/wiedza"
				class="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-brand-green transition mb-10"
			>
				← Wróć do Wiedzy
			</NuxtLink>

			<article
				v-if="article"
				class="prose prose-invert prose-headings:text-brand-green prose-a:text-brand-green prose-strong:text-white prose-blockquote:text-gray-300 prose-blockquote:border-brand-green max-w-none"
			>
				<ContentRenderer :value="article" />
			</article>

			<p v-else class="text-gray-500">Ładowanie...</p>
		</div>
	</div>
</template>
