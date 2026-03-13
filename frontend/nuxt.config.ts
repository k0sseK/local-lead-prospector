import { fileURLToPath } from "node:url";

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
	compatibilityDate: "2025-01-01",
	ssr: false,
	future: {
		compatibilityVersion: 4,
	},
	devtools: { enabled: true },

	modules: [
		"@nuxtjs/tailwindcss",
		"@vueuse/motion/nuxt",
		"@nuxt/scripts",
		"@nuxtjs/turnstile",
	],

	turnstile: {
		siteKey: process.env.NUXT_PUBLIC_TURNSTILE_SITE_KEY || "",
	},

	scripts: {
		registry: {
			googleAnalytics: {
				id: process.env.NUXT_PUBLIC_GA_ID || "G-7KQK7CJRKM",
			},
		},
	},
	css: ["~/assets/css/tailwind.css"],

	components: {
		dirs: [
			{
				path: "~/components",
				ignore: ["**/*.ts"],
			},
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
			lemonCheckoutUrl: process.env.NUXT_PUBLIC_LEMON_CHECKOUT_URL || "",
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
			title: "znajdzfirmy.pl",

			meta: [
				{
					name: "description",
					content:
						"Zdobądź klientów B2B w 3 minuty — skanuj lokalne firmy, audytuj i kontaktuj się z leadami.",
				},
			],
			link: [
				{ rel: "icon", type: "image/x-icon", href: "/favicon.ico" },
				{ rel: "preconnect", href: "https://api.fontshare.com" },
				{
					rel: "stylesheet",
					href: "https://api.fontshare.com/v2/css?f[]=cabinet-grotesk@800&f[]=satoshi@400,500,700&display=swap",
				},
			],
		},
	},
});
