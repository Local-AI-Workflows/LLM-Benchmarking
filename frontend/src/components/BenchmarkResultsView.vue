<template>
  <div>
    <v-card v-if="loading" class="pa-4">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
      <span class="ml-4">Loading results...</span>
    </v-card>

    <v-alert v-else-if="error" type="error" class="mb-4">
      {{ error }}
    </v-alert>

    <div v-else-if="!benchmarkData" class="text-center pa-4">
      <v-icon icon="mdi-alert-circle" size="48" color="grey"></v-icon>
      <p class="mt-2">No benchmark selected</p>
    </div>

    <div v-else>
      <!-- Benchmark Info Header -->
      <v-card class="mb-4">
        <v-card-title>
          <v-icon icon="mdi-chart-box" class="mr-2"></v-icon>
          Benchmark Results
          <v-spacer></v-spacer>
          <v-btn @click="$emit('close')" color="primary" prepend-icon="mdi-arrow-left">
            Back to Benchmarks
          </v-btn>
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-list>
                <v-list-item>
                  <v-list-item-title>ID</v-list-item-title>
                  <v-list-item-subtitle>{{ benchmarkData.id }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Model</v-list-item-title>
                  <v-list-item-subtitle>{{ benchmarkData.model_name || 'N/A' }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Dataset</v-list-item-title>
                  <v-list-item-subtitle>{{ benchmarkData.dataset_name || 'N/A' }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>
            <v-col cols="12" md="6">
              <v-list>
                <v-list-item>
                  <v-list-item-title>Status</v-list-item-title>
                  <v-list-item-subtitle>
                    <v-chip
                      :color="getStatusColor(benchmarkData.status)"
                      size="small"
                      variant="flat"
                    >
                      {{ benchmarkData.status }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>Created</v-list-item-title>
                  <v-list-item-subtitle>{{ formatDate(benchmarkData.created_at) }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item v-if="benchmarkData.completed_at">
                  <v-list-item-title>Completed</v-list-item-title>
                  <v-list-item-subtitle>{{ formatDate(benchmarkData.completed_at) }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Results Visualization -->
      <v-card v-if="resultData">
        <BenchmarkVisualization :result-data="resultData" />
      </v-card>
      <v-card v-else-if="benchmarkData.status === 'completed'" class="pa-4">
        <v-alert type="warning">
          No result data available for this benchmark.
        </v-alert>
      </v-card>
      <v-card v-else class="pa-4">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
        <span class="ml-4">Benchmark is not completed yet. Status: {{ benchmarkData.status }}</span>
      </v-card>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import BenchmarkVisualization from './BenchmarkVisualization.vue'

const API_BASE = '/api'

export default {
  name: 'BenchmarkResultsView',
  components: {
    BenchmarkVisualization
  },
  props: {
    benchmarkId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      benchmarkData: null,
      resultData: null,
      loading: true,
      error: null
    }
  },
  mounted() {
    this.loadBenchmark()
  },
  watch: {
    benchmarkId() {
      this.loadBenchmark()
    }
  },
  methods: {
    async loadBenchmark() {
      this.loading = true
      this.error = null
      
      try {
        const benchmarkResponse = await axios.get(`${API_BASE}/benchmarks/${this.benchmarkId}`)
        this.benchmarkData = benchmarkResponse.data
        
        if (this.benchmarkData.status === 'completed') {
          try {
            const resultResponse = await axios.get(`${API_BASE}/benchmarks/${this.benchmarkId}/result`)
            this.resultData = resultResponse.data.result_data
          } catch (err) {
            if (err.response?.status !== 400) {
              this.error = `Failed to load results: ${err.message}`
            }
          }
        }
      } catch (err) {
        this.error = `Failed to load benchmark: ${err.message}`
      } finally {
        this.loading = false
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleString()
    },
    getStatusColor(status) {
      const colors = {
        pending: 'orange',
        running: 'blue',
        completed: 'green',
        failed: 'red'
      }
      return colors[status] || 'grey'
    }
  }
}
</script>
