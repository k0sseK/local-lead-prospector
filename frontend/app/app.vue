<script setup>
import { useAuth } from "@/composables/useAuth";
import { Toaster } from "@/components/ui/sonner";
import "vue-sonner/style.css";

const { init } = useAuth();
await init();
</script>

<template>
	<NuxtLayout>
		<NuxtPage />
	</NuxtLayout>
	<Toaster />
</template>
