<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-app-bar-title>
        <v-icon icon="mdi-chart-line" class="mr-2"></v-icon>
        LLM Benchmark Dashboard
      </v-app-bar-title>
      <v-spacer></v-spacer>
      <v-chip color="success" variant="flat" v-if="activeBenchmarks > 0">
        {{ activeBenchmarks }} Running
      </v-chip>
    </v-app-bar>

    <v-main>
      <v-container fluid>
        <!-- Alerts -->
        <v-alert
          v-if="error"
          type="error"
          dismissible
          @click:close="error = null"
          class="mb-4"
        >
          {{ error }}
        </v-alert>
        <v-alert
          v-if="success"
          type="success"
          dismissible
          @click:close="success = null"
          class="mb-4"
        >
          {{ success }}
        </v-alert>

        <!-- Tabs -->
        <v-tabs v-model="activeTab" class="mb-4">
          <v-tab value="benchmarks">
            <v-icon start icon="mdi-play-circle"></v-icon>
            Benchmarks
          </v-tab>
          <v-tab value="results" :disabled="!selectedBenchmarkId">
            <v-icon start icon="mdi-chart-box"></v-icon>
            Results
          </v-tab>
          <v-tab value="settings">
            <v-icon start icon="mdi-cog"></v-icon>
            Settings
          </v-tab>
        </v-tabs>

        <!-- Benchmarks Tab -->
        <v-window v-model="activeTab">
          <v-window-item value="benchmarks">
            <v-row>
              <v-col cols="12" md="4">
                <BenchmarkForm
                  ref="benchmarkForm"
                  :datasets="datasets"
                  :metrics="availableMetrics"
                  :loading="loading"
                  @submit="startBenchmark"
                  @metric-type-change="loadMetrics"
                />
              </v-col>

              <v-col cols="12" md="8">
                <BenchmarkList
                  :benchmarks="benchmarks"
                  :loading="loadingBenchmarks"
                  @refresh="loadBenchmarks"
                  @view="viewBenchmark"
                  @view-results="viewResults"
                  @delete="deleteBenchmark"
                />
              </v-col>
            </v-row>

            <!-- Benchmark Detail Dialog -->
            <BenchmarkDetailDialog
              v-model="showBenchmarkDetail"
              :benchmark="selectedBenchmark"
              @view-results="viewResults"
            />
          </v-window-item>

          <!-- Results Tab -->
          <v-window-item value="results">
            <BenchmarkResultsView
              v-if="selectedBenchmarkId"
              :benchmark-id="selectedBenchmarkId"
              @close="activeTab = 'benchmarks'; selectedBenchmarkId = null"
            />
          </v-window-item>

          <!-- Settings Tab -->
          <v-window-item value="settings">
            <SettingsPage />
          </v-window-item>
        </v-window>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
import axios from 'axios'
import SettingsPage from './components/SettingsPage.vue'
import BenchmarkResultsView from './components/BenchmarkResultsView.vue'
import BenchmarkForm from './components/BenchmarkForm.vue'
import BenchmarkList from './components/BenchmarkList.vue'
import BenchmarkDetailDialog from './components/BenchmarkDetailDialog.vue'

const API_BASE = '/api'

export default {
  name: 'App',
  components: {
    SettingsPage,
    BenchmarkResultsView,
    BenchmarkForm,
    BenchmarkList,
    BenchmarkDetailDialog
  },
  data() {
    return {
      activeTab: 'benchmarks',
      benchmarks: [],
      datasets: [],
      availableMetrics: [],
      loadingBenchmarks: false,
      loading: false,
      error: null,
      success: null,
      selectedBenchmark: null,
      selectedBenchmarkId: null,
      showBenchmarkDetail: false,
      refreshInterval: null
    }
  },
  computed: {
    activeBenchmarks() {
      return this.benchmarks.filter(b => b.status === 'running').length
    }
  },
  mounted() {
    this.loadBenchmarks()
    this.loadDatasets()
    this.loadMetrics()
    // Auto-refresh every 5 seconds, but only if there are running benchmarks
    // This prevents unnecessary polling when all benchmarks are completed
    this.refreshInterval = setInterval(() => {
      if (this.activeTab === 'benchmarks' && this.activeBenchmarks > 0) {
        this.loadBenchmarks()
      }
    }, 5000)
  },
  beforeUnmount() {
    // Clean up the interval when component is destroyed
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  },
  methods: {
    async loadBenchmarks() {
      this.loadingBenchmarks = true
      try {
        const response = await axios.get(`${API_BASE}/benchmarks`)
        this.benchmarks = response.data.benchmarks.map(b => ({
          ...b,
          displayId: b.id.substring(0, 8) + '...'  // Keep full ID, add display version
        }))
      } catch (err) {
        this.error = `Failed to load benchmarks: ${err.message}`
      } finally {
        this.loadingBenchmarks = false
      }
    },
    async loadDatasets() {
      try {
        const response = await axios.get(`${API_BASE}/datasets?enabled_only=true`)
        this.datasets = Array.isArray(response.data) ? response.data : []
      } catch (err) {
        this.error = `Failed to load datasets: ${err.message}`
        this.datasets = []
      }
    },
    async loadMetrics() {
      try {
        const response = await axios.get(`${API_BASE}/metrics?enabled_only=true`)
        this.availableMetrics = Array.isArray(response.data) ? response.data : []
      } catch (err) {
        this.error = `Failed to load metrics: ${err.message}`
        this.availableMetrics = []
      }
    },
    async startBenchmark(formData) {
      this.loading = true
      this.error = null
      this.success = null
      
      try {
        const mcp_tools = formData.mcp_tools.map(tool => ({
          name: tool.name,
          url: tool.url,
          description: tool.description || '',
          available_tools: tool.available_tools_str 
            ? tool.available_tools_str.split(',').map(t => t.trim())
            : []
        }))
        
        const evaluator_models = formData.evaluator_models.length > 0
          ? formData.evaluator_models
              .filter(e => e.model_name.trim())
              .map(e => ({
                model_name: e.model_name.trim(),
                base_url: e.base_url.trim() || null
              }))
          : null
        
        const payload = {
          model_name: formData.model_name,
          model_base_url: formData.model_base_url.trim() || null,
          metric_type: formData.metric_type,
          dataset_id: formData.dataset_id,
          metric_ids: formData.metric_ids,
          evaluator_models: evaluator_models,
          mcp_tools: formData.metric_type === 'mcp' && mcp_tools.length > 0 ? mcp_tools : null
        }
        
        const response = await axios.post(`${API_BASE}/benchmarks`, payload)
        this.success = `Benchmark started with ID: ${response.data.id}`
        this.$refs.benchmarkForm.resetForm()
        await this.loadBenchmarks()
      } catch (err) {
        this.error = `Failed to start benchmark: ${err.response?.data?.detail || err.message}`
      } finally {
        this.loading = false
      }
    },
    async viewBenchmark(benchmark) {
      try {
        // Get the benchmark object (handle Vuetify wrapping)
        const benchmarkObj = benchmark.raw || benchmark
        
        // Always get the ID from our stored benchmarks array to ensure we have the full ID
        // Find by matching the ID (even if truncated) or other unique properties
        let benchmarkId = benchmarkObj.id
        let storedBenchmark = null
        
        if (benchmarkId) {
          // Try to find exact match first
          storedBenchmark = this.benchmarks.find(b => b.id === benchmarkId)
          
          // If not found and ID looks truncated, try prefix match
          if (!storedBenchmark && benchmarkId.length < 24) {
            storedBenchmark = this.benchmarks.find(b => b.id && b.id.startsWith(benchmarkId))
          }
        }
        
        // If still not found, try matching by other properties
        if (!storedBenchmark) {
          storedBenchmark = this.benchmarks.find(b => 
            b.model_name === benchmarkObj.model_name &&
            b.status === benchmarkObj.status &&
            Math.abs(new Date(b.created_at) - new Date(benchmarkObj.created_at)) < 1000 // Within 1 second
          )
        }
        
        if (storedBenchmark && storedBenchmark.id) {
          benchmarkId = storedBenchmark.id
        } else if (!benchmarkId) {
          this.error = 'Invalid benchmark: missing ID'
          console.error('Benchmark object:', benchmark)
          console.error('Available benchmarks:', this.benchmarks.map(b => ({ id: b.id, displayId: b.displayId })))
          return
        }
        
        // Validate ID format (MongoDB ObjectIds are 24 hex characters)
        if (benchmarkId.length !== 24 || !/^[0-9a-fA-F]{24}$/.test(benchmarkId)) {
          this.error = `Invalid benchmark ID format: ${benchmarkId}`
          console.error('Invalid ID format. Benchmark object:', benchmarkObj)
          console.error('Stored benchmark:', storedBenchmark)
          return
        }
        
        console.log('Fetching benchmark with ID:', benchmarkId)
        const response = await axios.get(`${API_BASE}/benchmarks/${benchmarkId}`)
        this.selectedBenchmark = response.data
        this.showBenchmarkDetail = true
      } catch (err) {
        const errorMsg = err.response?.data?.detail || err.message || 'Unknown error'
        this.error = `Failed to load benchmark: ${errorMsg}`
        console.error('Error loading benchmark:', err)
        console.error('Benchmark object that failed:', benchmark)
        console.error('Attempted ID:', benchmark.raw?.id || benchmark.id)
        
        // If 404, the benchmark might have been deleted - refresh the list
        if (err.response?.status === 404) {
          console.log('Benchmark not found (404), refreshing benchmarks list...')
          await this.loadBenchmarks()
          this.error = 'Benchmark not found. The list has been refreshed.'
        }
      }
    },
    async viewResults(benchmark) {
      console.log('viewResults called with:', benchmark)
      
      // Handle case where benchmark is already just an ID string
      if (typeof benchmark === 'string') {
        this.selectedBenchmarkId = benchmark
        this.selectedBenchmark = null
        this.showBenchmarkDetail = false
        
        // Use nextTick to ensure the tab is rendered before switching
        await this.$nextTick()
        this.activeTab = 'results'
        
        console.log('Tab switched to results, selectedBenchmarkId:', this.selectedBenchmarkId, 'activeTab:', this.activeTab)
        return
      }
      
      // In Vuetify 3 data table, item might be wrapped with .raw property
      const benchmarkObj = benchmark.raw || benchmark
      console.log('benchmarkObj:', benchmarkObj)
      
      let benchmarkId = benchmarkObj.id || benchmarkObj._id
      
      // If still no ID, try to find it in the original benchmarks array
      if (!benchmarkId) {
        const storedBenchmark = this.benchmarks.find(b => 
          b.model_name === benchmarkObj.model_name &&
          b.status === benchmarkObj.status &&
          b.created_at === benchmarkObj.created_at
        )
        if (storedBenchmark) {
          benchmarkId = storedBenchmark.id
          console.log('Found benchmark in stored array:', benchmarkId)
        }
      }
      
      // If ID is truncated, find the full one
      if (benchmarkId && benchmarkId.length < 24) {
        const fullBenchmark = this.benchmarks.find(b => b.id && b.id.startsWith(benchmarkId))
        if (fullBenchmark) {
          benchmarkId = fullBenchmark.id
          console.log('Found full ID:', benchmarkId)
        }
      }
      
      if (!benchmarkId) {
        this.error = 'Invalid benchmark: missing ID'
        console.error('No benchmark ID found. Benchmark object:', benchmarkObj)
        console.error('Available benchmarks:', this.benchmarks.map(b => ({ id: b.id, model: b.model_name })))
        return
      }
      
      console.log('Setting selectedBenchmarkId to:', benchmarkId)
      this.selectedBenchmarkId = benchmarkId
      this.selectedBenchmark = null
      this.showBenchmarkDetail = false
      
      // Use nextTick to ensure the tab is rendered before switching
      await this.$nextTick()
      this.activeTab = 'results'
      
      console.log('Tab switched to results, selectedBenchmarkId:', this.selectedBenchmarkId, 'activeTab:', this.activeTab)
    },
    async deleteBenchmark(benchmark) {
      if (!confirm('Are you sure you want to delete this benchmark?')) {
        return
      }
      
      try {
        // In Vuetify 3 data table, item might be wrapped with .raw property
        const benchmarkObj = benchmark.raw || benchmark
        let benchmarkId = benchmarkObj.id
        
        // If still no ID, try to find it in the original benchmarks array
        if (!benchmarkId) {
          const storedBenchmark = this.benchmarks.find(b => 
            b.model_name === benchmarkObj.model_name &&
            b.status === benchmarkObj.status &&
            b.created_at === benchmarkObj.created_at
          )
          if (storedBenchmark) {
            benchmarkId = storedBenchmark.id
          }
        }
        
        // If ID is truncated, find the full one
        if (benchmarkId && benchmarkId.length < 24) {
          const fullBenchmark = this.benchmarks.find(b => b.id && b.id.startsWith(benchmarkId))
          if (fullBenchmark) {
            benchmarkId = fullBenchmark.id
          }
        }
        
        if (!benchmarkId) {
          this.error = 'Invalid benchmark: missing ID'
          return
        }
        
        await axios.delete(`${API_BASE}/benchmarks/${benchmarkId}`)
        this.success = 'Benchmark deleted successfully'
        await this.loadBenchmarks()
      } catch (err) {
        this.error = `Failed to delete benchmark: ${err.message}`
      }
    }
  }
}
</script>

<style>
/* Custom styles if needed */
</style>
