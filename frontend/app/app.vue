<script setup>
import { Toaster } from "vue-toastification";
import { useAuth } from "@/composables/useAuth"

const { init } = useAuth()
await init()
</script>

<template>
	<NuxtLayout>
		<NuxtPage />
	</NuxtLayout>
</template>
