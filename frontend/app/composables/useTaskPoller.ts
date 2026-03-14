/**
 * useTaskPoller — composable do pollingu statusu zadania Celery.
 *
 * Odpytuje GET /api/tasks/{task_id} co 2s aż do SUCCESS lub FAILURE.
 * Max 90 prób (3 minuty) — po przekroczeniu zwraca timeout error.
 */
import api from "@/services/api";

export type TaskStatus = "PENDING" | "STARTED" | "SUCCESS" | "FAILURE";

export interface TaskResult {
	task_id: string;
	status: TaskStatus;
	result: Record<string, unknown> | null;
}

export interface PollOptions {
	/** Wywołane po pomyślnym ukończeniu taska. result zawiera dane zwrócone przez task. */
	onSuccess: (result: Record<string, unknown>) => void;
	/** Wywołane gdy task się nie powiódł lub upłynął timeout. */
	onError: (message: string) => void;
	/** Interwał pollingu w ms (domyślnie 2000) */
	intervalMs?: number;
	/** Maks. liczba prób (domyślnie 90 = 3 min przy 2s interwale) */
	maxAttempts?: number;
}

export function useTaskPoller() {
	function pollTask(taskId: string, options: PollOptions): () => void {
		const {
			onSuccess,
			onError,
			intervalMs = 2000,
			maxAttempts = 90,
		} = options;

		let attempts = 0;

		const intervalId = setInterval(async () => {
			attempts++;

			if (attempts > maxAttempts) {
				clearInterval(intervalId);
				onError("Timeout — audyt trwa zbyt długo. Sprawdź logi serwera.");
				return;
			}

			try {
				const res = await api.getTaskStatus(taskId);
				const data: TaskResult = res.data;

				if (data.status === "SUCCESS") {
					clearInterval(intervalId);
					onSuccess(data.result ?? {});
				} else if (data.status === "FAILURE") {
					clearInterval(intervalId);
					const msg =
						(data.result as { error?: string } | null)?.error ||
						"Zadanie nie powiodło się.";
					onError(msg);
				}
				// PENDING / STARTED — czekamy dalej
			} catch {
				// Błąd sieci — nie przerywamy, próbujemy dalej
			}
		}, intervalMs);

		// Zwracamy funkcję anulującą polling (np. gdy komponent zostanie zniszczony)
		return () => clearInterval(intervalId);
	}

	return { pollTask };
}
