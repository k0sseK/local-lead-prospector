import { defineContentConfig, defineCollection } from "@nuxt/content";

export default defineContentConfig({
	collections: {
		wiedza: defineCollection({
			type: "page",
			source: "wiedza/**",
		}),
	},
});
