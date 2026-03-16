/**
 * useQuota.ts — Global quota/usage state with TTL-based cache.
 *
 * Prevents duplicate GET /api/usage calls from the dashboard layout
 * AND individual pages (index, export) that all display the same counters.
 * Data is considered fresh for STALE_MS ms; mutating actions (scan, audit,
 * send-email) should call refreshQuota() to force a re-fetch.
 */
import api from "@/services/api";

const STALE_MS = 5 * 60_000; // 5 minutes — quota changes only after user actions

interface QuotaData {
	plan: string;
	monthly_credits: number;
	monthly_credits_limit: number;
	credits_balance: number;
	total_credits: number;
	credits_reset_at: string | null;
	is_verified: boolean;
	action_costs: { scan: number; ai_audit: number; email_sequence: number };
}

export function useQuota() {
	const quota = useState<QuotaData | null>("quota", () => null);
	const _fetchedAt = useState<number>("quota:ts", () => 0);
	const _loading = useState<boolean>("quota:loading", () => false);

	/**
	 * Load quota, honouring the TTL cache unless force=true.
	 * Non-blocking: errors are swallowed so quota display never blocks UI.
	 */
	async function fetchQuota(force = false): Promise<void> {
		if (!force && quota.value && Date.now() - _fetchedAt.value < STALE_MS) {
			return; // data is fresh
		}
		if (_loading.value) return; // prevent concurrent fetches

		_loading.value = true;
		try {
			const res = await api.getUsage();
			quota.value = res.data as QuotaData;
			_fetchedAt.value = Date.now();
		} catch {
			// Non-blocking — quota display is secondary; don't crash the UI
		} finally {
			_loading.value = false;
		}
	}

	/** Force-refresh quota after a mutation (scan, AI audit, email send). */
	function refreshQuota(): Promise<void> {
		return fetchQuota(true);
	}

	/** Invalidate cache without triggering a fetch. */
	function invalidateQuota(): void {
		_fetchedAt.value = 0;
	}

	return { quota, fetchQuota, refreshQuota, invalidateQuota };
}
