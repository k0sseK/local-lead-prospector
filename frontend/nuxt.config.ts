import { fileURLToPath } from "node:url";

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
	compatibilityDate: "2025-01-01",
	ssr: false,
	future: {
		compatibilityVersion: 4,
	},
	devtools: { enabled: true },

	modules: ["@nuxtjs/tailwindcss", "shadcn-nuxt", "@vueuse/motion/nuxt"],
	css: ["~/assets/css/tailwind.css"],

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
			googleMapsApiKey: process.env.NUXT_PUBLIC_GOOGLE_MAPS_API_KEY || "",
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
				{ rel: "preconnect", href: "https://api.fontshare.com" },
				{
					rel: "stylesheet",
					href: "https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@800&f[]=satoshi@400,500,700&display=swap",
				},
			],
		},
	},
});
