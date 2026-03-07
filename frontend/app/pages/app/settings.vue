<script setup>
import { ref, onMounted } from "vue"
import { useToast } from "vue-toastification"
import api from "@/services/api"

definePageMeta({ middleware: "auth", layout: "dashboard" })

const toast = useToast()

const form = ref({
  sender_name: "",
  company_name: "",
  offer_description: "",
  tone_of_voice: "formalny",
})

const saving = ref(false)

const toneOptions = [
  { value: "formalny", label: "Formalny i profesjonalny" },
  { value: "luzny-startupowy", label: "Luźny i startupowy" },
  { value: "krotki-sprzedazowy", label: "Krótki, bezpośredni i sprzedażowy" },
]

onMounted(async () => {
  try {
    const response = await api.getSettings()
    Object.assign(form.value, response.data)
  } catch (error) {
    if (error.response?.status !== 404) {
      toast.error("Nie udało się załadować ustawień.")
    }
  }
})

async function saveSettings() {
  saving.value = true
  try {
    await api.updateSettings(form.value)
    toast.success("Ustawienia zostały zapisane.")
  } catch {
    toast.error("Nie udało się zapisać ustawień.")
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="p-6 max-w-2xl mx-auto">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-slate-900">Ustawienia Smart AI</h1>
      <p class="text-slate-500 mt-1 text-sm">
        Dane te zostaną użyte do personalizacji e-maili generowanych przez Gemini AI.
      </p>
    </div>

    <Card>
      <CardHeader>
        <CardTitle>Dane nadawcy</CardTitle>
        <CardDescription>
          Uzupełnij poniższe informacje, aby AI pisała maile w Twoim imieniu.
        </CardDescription>
      </CardHeader>
      <CardContent class="space-y-5">
        <div class="space-y-2">
          <Label for="sender_name">Imię i nazwisko</Label>
          <Input
            id="sender_name"
            v-model="form.sender_name"
            placeholder="np. Jan Kowalski"
          />
        </div>

        <div class="space-y-2">
          <Label for="company_name">Nazwa firmy</Label>
          <Input
            id="company_name"
            v-model="form.company_name"
            placeholder="np. WebAgency Sp. z o.o."
          />
        </div>

        <div class="space-y-2">
          <Label for="offer_description">Krótki opis oferty</Label>
          <textarea
            id="offer_description"
            v-model="form.offer_description"
            rows="3"
            placeholder="np. Tworzymy strony internetowe, sklepy online i zajmujemy się pozycjonowaniem SEO."
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
          />
        </div>

        <div class="space-y-2">
          <Label for="tone_of_voice">Ton wypowiedzi</Label>
          <select
            id="tone_of_voice"
            v-model="form.tone_of_voice"
            class="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          >
            <option
              v-for="option in toneOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
      </CardContent>
      <CardFooter>
        <Button :disabled="saving" @click="saveSettings">
          {{ saving ? "Zapisywanie..." : "Zapisz ustawienia" }}
        </Button>
      </CardFooter>
    </Card>
  </div>
</template>
