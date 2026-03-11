export function formatDate(dt) {
	if (!dt) return "—";
	return new Date(dt).toLocaleDateString("pl-PL");
}

export function initials(name) {
	if (!name) return "?";
	return name
		.split(" ")
		.map((w) => w[0])
		.join("")
		.toUpperCase()
		.slice(0, 2);
}
