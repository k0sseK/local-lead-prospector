<script setup>
import { useAuth } from "@/composables/useAuth";
import { Toaster } from "@/components/ui/sonner";

const { init } = useAuth();
await init();
</script>

<template>
	<NuxtLayout>
		<NuxtPage />
	</NuxtLayout>
	<Toaster />
</template>
