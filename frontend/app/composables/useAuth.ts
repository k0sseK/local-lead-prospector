import api from "../services/api"

interface User {
  id: number
  email: string
  role: string
  created_at: string
}

interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export function useAuth() {
  const token = useCookie<string | null>("auth_token", {
    maxAge: 60 * 60 * 24 * 7, // 7 days, matches backend
    sameSite: "lax",
    secure: false, // set to true in production (HTTPS)
  })
  const user = useState<User | null>("user", () => null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string): Promise<void> {
    const response = await api.login({ email, password })
    const data = response.data as AuthResponse
    token.value = data.access_token
    user.value = data.user
    await navigateTo("/app")
  }

  async function register(email: string, password: string): Promise<void> {
    const response = await api.register({ email, password })
    const data = response.data as AuthResponse
    token.value = data.access_token
    user.value = data.user
    await navigateTo("/app")
  }

  function logout(): void {
    token.value = null
    user.value = null
    navigateTo("/login")
  }

  return { token, user, isAuthenticated, login, register, logout }
}
