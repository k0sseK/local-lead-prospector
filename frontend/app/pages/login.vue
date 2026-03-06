<script setup lang="ts">
import { useAuth } from "@/composables/useAuth"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"

definePageMeta({ layout: "default" })

const { login } = useAuth()

const email = ref("")
const password = ref("")
const error = ref("")
const loading = ref(false)

async function handleSubmit() {
  error.value = ""
  loading.value = true
  try {
    await login(email.value, password.value)
  } catch (err: any) {
    error.value = err.response?.data?.detail || "Login failed. Check your credentials."
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex-1 flex items-center justify-center py-16 px-4">
    <Card class="w-full max-w-md">
      <CardHeader>
        <CardTitle class="text-2xl">Sign in</CardTitle>
        <CardDescription>Enter your email and password to access your account</CardDescription>
      </CardHeader>
      <CardContent class="space-y-4">
        <div class="space-y-2">
          <Label for="email">Email</Label>
          <Input
            id="email"
            type="email"
            v-model="email"
            placeholder="you@example.com"
            @keyup.enter="handleSubmit"
          />
        </div>
        <div class="space-y-2">
          <Label for="password">Password</Label>
          <Input
            id="password"
            type="password"
            v-model="password"
            placeholder="••••••••"
            @keyup.enter="handleSubmit"
          />
        </div>
        <p v-if="error" class="text-sm text-red-600">{{ error }}</p>
      </CardContent>
      <CardFooter class="flex flex-col gap-3">
        <Button class="w-full" :disabled="loading" @click="handleSubmit">
          {{ loading ? "Signing in..." : "Sign in" }}
        </Button>
        <p class="text-sm text-slate-500 text-center">
          No account?
          <NuxtLink to="/register" class="text-indigo-600 hover:underline font-medium">
            Register
          </NuxtLink>
        </p>
      </CardFooter>
    </Card>
  </div>
</template>
