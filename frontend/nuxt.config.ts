// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
	compatibilityDate: "2025-01-01",
	future: {
		compatibilityVersion: 4,
	},
	devtools: { enabled: true },

	modules: ["@nuxtjs/tailwindcss", "shadcn-nuxt"],

	shadcn: {
		prefix: "",
		componentDir: "./app/components/ui",
	},

	runtimeConfig: {
		public: {
			apiBase: "http://localhost:8000/api",
		},
	},

	app: {
		head: {
			title: "Local Lead Prospector",
			meta: [
				{
					name: "description",
					content:
						"Zdobądź klientów B2B w 3 minuty — skanuj lokalne firmy, audytuj i kontaktuj się z leadami.",
				},
			],
			link: [
				{
					rel: "stylesheet",
					href: "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap",
				},
			],
		},
	},
});
