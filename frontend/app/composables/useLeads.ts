/**
 * useLeads.ts — Global leads state with TTL-based cache.
 *
 * Prevents duplicate GET /api/leads calls when the user navigates
 * between pages that all need the same dataset (index, scan-results, export).
 * Data is considered fresh for STALE_MS milliseconds; after that the next
 * fetchLeads() call will re-hit the API.
 */
import api from "@/services/api";

const STALE_MS = 60_000; // 1 minute

/** Mirrors the backend Lead schema (schemas.py → class Lead). */
export interface Lead {
	id: number;
	user_id: number | null;
	company_name: string;
	place_id: string | null;
	phone: string | null;
	address: string | null;
	rating: number | null;
	reviews_count: number | null;
	website_uri: string | null;
	email: string | null;
	has_ssl: boolean | null;
	audited: boolean;
	audit_report: Record<string, unknown> | null;
	status: string;
	notes: string | null;
	created_at: string;
}

export function useLeads() {
	// Shared across ALL component instances via Nuxt's useState SSR-safe store
	const leads = useState<Lead[]>("leads", () => []);
	const loading = useState<boolean>("leads:loading", () => false);
	const _fetchedAt = useState<number>("leads:ts", () => 0);

	/**
	 * Load leads, honouring the TTL cache unless force=true.
	 * @param force - bypass cache and always hit the API
	 */
	async function fetchLeads(force = false): Promise<void> {
		// Skip if data is still fresh
		if (
			!force &&
			leads.value.length > 0 &&
			Date.now() - _fetchedAt.value < STALE_MS
		) {
			return;
		}

		// Prevent concurrent fetches (e.g. two pages mounting simultaneously)
		if (loading.value) return;

		loading.value = true;
		try {
			const response = await api.getLeads();
			leads.value = response.data as Lead[];
			_fetchedAt.value = Date.now();
		} catch (err) {
			console.error("[useLeads] fetchLeads failed:", err);
			throw err; // let the caller show an error toast
		} finally {
			loading.value = false;
		}
	}

	/** Force-refresh after a mutation (e.g. after a new scan populates leads). */
	function refreshLeads(): Promise<void> {
		return fetchLeads(true);
	}

	/** Invalidate the cache without triggering a fetch. */
	function invalidateLeads(): void {
		_fetchedAt.value = 0;
	}

	return { leads, loading, fetchLeads, refreshLeads, invalidateLeads };
}
