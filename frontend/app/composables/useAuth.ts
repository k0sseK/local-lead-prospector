import api from "../services/api";
import { useQuota } from "./useQuota";

interface User {
	id: number;
	email: string;
	role: string;
	created_at: string;
}

interface AuthResponse {
	access_token: string;
	token_type: string;
	user: User;
}

export function useAuth() {
	const token = useCookie<string | null>("auth_token", {
		maxAge: 60 * 60 * 24 * 7, // 7 days, matches backend
		sameSite: "lax",
		secure: false, // set to true in production (HTTPS)
	});
	const user = useState<User | null>("user", () => null);
	const { quota, invalidateQuota } = useQuota();

	const isAuthenticated = computed(() => !!token.value);

	async function login(
		email: string,
		password: string,
		cf_turnstile_response?: string,
	): Promise<void> {
		const response = await api.login({
			email,
			password,
			cf_turnstile_response,
		});
		const data = response.data as AuthResponse;
		token.value = data.access_token;
		user.value = data.user;

		quota.value = null;
		invalidateQuota();
		await navigateTo("/app");
	}

	async function register(
		email: string,
		password: string,
		cf_turnstile_response?: string,
	): Promise<void> {
		await api.register({
			email,
			password,
			cf_turnstile_response,
		});

		try {
			if (import.meta.client) {
				const { toast } = await import("vue-sonner");
				toast.success("Konto utworzone pomyślnie! Sprawdź swoją skrzynkę e-mail, aby potwierdzić adres przed logowaniem.", { duration: 8000 });
			}
		} catch (e) {
			// fallback
		}

		await navigateTo("/auth/verify?sent=1");
	}

	async function init(): Promise<void> {
		if (token.value && !user.value) {
			try {
				const response = await api.me();
				user.value = response.data as User;
			} catch {
				token.value = null;
			}
		}
	}

	function logout(): void {
		token.value = null;
		user.value = null;

		quota.value = null;
		invalidateQuota();
		navigateTo("/login");
	}

	return { token, user, isAuthenticated, login, register, logout, init };
}
