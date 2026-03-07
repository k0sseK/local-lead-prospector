import { fileURLToPath } from "node:url";

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
	compatibilityDate: "2025-01-01",
	ssr: false,
	future: {
		compatibilityVersion: 4,
	},
	devtools: { enabled: true },

	modules: ["@nuxtjs/tailwindcss", "shadcn-nuxt"],

	shadcn: {
		prefix: "",
		componentDir: "./app/components/ui",
	},

	components: {
		dirs: [
			{
				path: "~/components/ui",
				ignore: ["**/*.ts"],
				pathPrefix: false,
			},
			"~/components",
		],
	},

	alias: {
		"@/lib/utils": fileURLToPath(
			new URL("./app/lib/utils.ts", import.meta.url),
		),
	},

	runtimeConfig: {
		public: {
			// Dev: http://localhost:8000/api
			// Prod: "" (nginx proxies /api/ to backend container)
			// Override with NUXT_PUBLIC_API_BASE env variable
			apiBase:
				process.env.NUXT_PUBLIC_API_BASE ?? "http://localhost:8000/api",
		},
	},

	vite: {
		define: {
			"import.meta.env.NUXT_PUBLIC_API_BASE": JSON.stringify(
				(process.env.NUXT_PUBLIC_API_BASE || "").startsWith("http")
					? process.env.NUXT_PUBLIC_API_BASE
					: process.env.NUXT_PUBLIC_API_BASE
						? `https://${process.env.NUXT_PUBLIC_API_BASE}`
						: "http://localhost:8000/api",
			),
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
