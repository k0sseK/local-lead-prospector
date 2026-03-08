<script setup>
import { useAuth } from "@/composables/useAuth";

const { init } = useAuth();
await init();
</script>

<template>
	<NuxtLayout>
		<NuxtPage />
	</NuxtLayout>
</template>
