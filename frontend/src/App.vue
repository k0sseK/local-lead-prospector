<script setup>
import { ref, onMounted } from "vue";
import api from "./services/api.js";

const leads = ref([]);
const loading = ref(true);
const error = ref(null);

const fetchLeads = async () => {
	try {
		loading.value = true;
		const response = await api.getLeads();
		leads.value = response.data;
	} catch (err) {
		error.value =
			"Failed to load leads from the API. Make sure the backend is running.";
		console.error(err);
	} finally {
		loading.value = false;
	}
};

const changeStatus = async (lead, newStatus) => {
	try {
		const response = await api.updateLeadStatus(lead.id, newStatus);
		// Update local state
		lead.status = response.data.status;
	} catch (err) {
		console.error("Failed to update status", err);
	}
};

onMounted(() => {
	fetchLeads();
});
</script>

<template>
	<div class="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
		<div class="max-w-4xl mx-auto">
			<h1 class="text-3xl font-bold text-gray-900 mb-8 text-center">
				B2B Lead Generator MVP
			</h1>

			<div v-if="loading" class="text-center text-gray-500">
				Loading leads...
			</div>

			<div
				v-else-if="error"
				class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4"
			>
				{{ error }}
			</div>

			<div v-else class="bg-white shadow overflow-hidden sm:rounded-md">
				<ul role="list" class="divide-y divide-gray-200">
					<li
						v-for="lead in leads"
						:key="lead.id"
						class="px-4 py-4 sm:px-6 flex items-center justify-between"
					>
						<div
							class="flex-1 min-w-0 flex flex-col justify-center"
						>
							<p
								class="text-sm font-medium text-indigo-600 truncate"
							>
								{{ lead.company_name }}
							</p>
							<p class="mt-1 text-sm text-gray-500 truncate">
								Address: {{ lead.address || "N/A" }} <br />
								Phone: {{ lead.phone || "N/A" }}
							</p>
							<p class="mt-1 text-xs text-gray-400">
								Created:
								{{ new Date(lead.created_at).toLocaleString() }}
							</p>
						</div>

						<div
							class="flex flex-col sm:flex-row items-center gap-2 ml-4"
						>
							<span
								class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize"
								:class="{
									'bg-yellow-100 text-yellow-800':
										lead.status === 'new',
									'bg-green-100 text-green-800':
										lead.status === 'contacted',
									'bg-red-100 text-red-800':
										lead.status === 'rejected',
								}"
							>
								{{ lead.status }}
							</span>
							<div
								class="flex gap-2 mt-2 sm:mt-0 flex-wrap justify-end"
							>
								<button
									v-if="lead.status !== 'contacted'"
									@click="changeStatus(lead, 'contacted')"
									class="text-xs bg-green-50 text-green-700 hover:bg-green-100 px-2 py-1 rounded border border-green-200 transition-colors"
								>
									Contacted
								</button>
								<button
									v-if="lead.status !== 'rejected'"
									@click="changeStatus(lead, 'rejected')"
									class="text-xs bg-red-50 text-red-700 hover:bg-red-100 px-2 py-1 rounded border border-red-200 transition-colors"
								>
									Reject
								</button>
								<button
									v-if="lead.status !== 'new'"
									@click="changeStatus(lead, 'new')"
									class="text-xs bg-gray-50 text-gray-700 hover:bg-gray-100 px-2 py-1 rounded border border-gray-200 transition-colors"
								>
									Reset
								</button>
							</div>
						</div>
					</li>

					<li
						v-if="leads.length === 0"
						class="px-4 py-4 sm:px-6 text-center text-gray-500"
					>
						No leads found. Run the scraper script to generate mock
						data!
					</li>
				</ul>
			</div>
		</div>
	</div>
</template>
