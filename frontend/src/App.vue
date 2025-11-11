<template>
  <div class="container">
    <div class="header">
      <h1>LLM Benchmark Dashboard</h1>
      <p>Manage and visualize your LLM benchmark tests</p>
    </div>

    <div v-if="error" class="error">{{ error }}</div>
    <div v-if="success" class="success">{{ success }}</div>

    <div class="card">
      <h2>Start New Benchmark</h2>
      <form @submit.prevent="startBenchmark">
        <div class="form-group">
          <label>Model Name</label>
          <input v-model="form.model_name" type="text" placeholder="llama3.2:latest" required>
        </div>
        
        <div class="form-group">
          <label>Dataset File (optional)</label>
          <input v-model="form.dataset_file" type="text" placeholder="path/to/dataset.json">
        </div>
        
        <div class="form-group">
          <label>Dataset Format (optional)</label>
          <select v-model="form.dataset_format">
            <option value="">Auto-detect</option>
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
            <option value="yaml">YAML</option>
            <option value="txt">TXT</option>
          </select>
        </div>
        
        <div class="form-group">
          <label>Metrics (comma-separated, leave empty for all)</label>
          <input v-model="form.metrics" type="text" placeholder="relevance,hallucinations,bias">
        </div>
        
        <div class="form-group">
          <label>Evaluator Models (comma-separated, optional)</label>
          <input v-model="form.evaluator_models" type="text" placeholder="deepseek-r1:1.5b,gemma3:1b">
        </div>
        
        <button type="submit" class="btn btn-primary" :disabled="loading">
          {{ loading ? 'Starting...' : 'Start Benchmark' }}
        </button>
      </form>
    </div>

    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h2>Benchmarks</h2>
        <button @click="loadBenchmarks" class="btn btn-primary">Refresh</button>
      </div>
      
      <div v-if="loadingBenchmarks" class="loading">Loading benchmarks...</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Model</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="benchmark in benchmarks" :key="benchmark.id">
            <td>{{ benchmark.id.substring(0, 8) }}...</td>
            <td>{{ benchmark.model_name || 'N/A' }}</td>
            <td>
              <span :class="`badge badge-${benchmark.status}`">
                {{ benchmark.status }}
              </span>
            </td>
            <td>{{ formatDate(benchmark.created_at) }}</td>
            <td>
              <button 
                @click="viewBenchmark(benchmark.id)" 
                class="btn btn-primary"
                style="margin-right: 5px;"
              >
                View
              </button>
              <button 
                v-if="benchmark.status === 'completed'"
                @click="viewResults(benchmark.id)" 
                class="btn btn-success"
                style="margin-right: 5px;"
              >
                Results
              </button>
              <button 
                @click="deleteBenchmark(benchmark.id)" 
                class="btn btn-danger"
              >
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Benchmark Detail Modal -->
    <div v-if="selectedBenchmark" class="card">
      <h2>Benchmark Details</h2>
      <div v-if="selectedBenchmark">
        <p><strong>ID:</strong> {{ selectedBenchmark.id }}</p>
        <p><strong>Status:</strong> 
          <span :class="`badge badge-${selectedBenchmark.status}`">
            {{ selectedBenchmark.status }}
          </span>
        </p>
        <p><strong>Model:</strong> {{ selectedBenchmark.model_name || 'N/A' }}</p>
        <p><strong>Dataset:</strong> {{ selectedBenchmark.dataset_name || 'N/A' }}</p>
        <p><strong>Metrics:</strong> {{ selectedBenchmark.metrics.join(', ') || 'N/A' }}</p>
        <p><strong>Created:</strong> {{ formatDate(selectedBenchmark.created_at) }}</p>
        <p v-if="selectedBenchmark.error_message">
          <strong>Error:</strong> {{ selectedBenchmark.error_message }}
        </p>
        <button @click="selectedBenchmark = null" class="btn btn-primary">Close</button>
      </div>
    </div>

    <!-- Results Visualization -->
    <div v-if="benchmarkResults" class="card">
      <h2>Benchmark Results</h2>
      <BenchmarkVisualization :result-data="benchmarkResults" />
      <button @click="benchmarkResults = null" class="btn btn-primary">Close</button>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import BenchmarkVisualization from './components/BenchmarkVisualization.vue'

const API_BASE = '/api'

export default {
  name: 'App',
  components: {
    BenchmarkVisualization
  },
  data() {
    return {
      benchmarks: [],
      loadingBenchmarks: false,
      loading: false,
      error: null,
      success: null,
      selectedBenchmark: null,
      benchmarkResults: null,
      form: {
        model_name: 'llama3.2:latest',
        dataset_file: '',
        dataset_format: '',
        metrics: '',
        evaluator_models: ''
      }
    }
  },
  mounted() {
    this.loadBenchmarks()
    // Auto-refresh every 5 seconds
    setInterval(() => {
      this.loadBenchmarks()
    }, 5000)
  },
  methods: {
    async loadBenchmarks() {
      this.loadingBenchmarks = true
      try {
        const response = await axios.get(`${API_BASE}/benchmarks`)
        this.benchmarks = response.data.benchmarks
      } catch (err) {
        this.error = `Failed to load benchmarks: ${err.message}`
      } finally {
        this.loadingBenchmarks = false
      }
    },
    async startBenchmark() {
      this.loading = true
      this.error = null
      this.success = null
      
      try {
        const payload = {
          model_name: this.form.model_name,
          dataset_file: this.form.dataset_file || null,
          dataset_format: this.form.dataset_format || null,
          metrics: this.form.metrics ? this.form.metrics.split(',').map(m => m.trim()) : null,
          evaluator_models: this.form.evaluator_models ? this.form.evaluator_models.split(',').map(m => m.trim()) : null
        }
        
        const response = await axios.post(`${API_BASE}/benchmarks`, payload)
        this.success = `Benchmark started with ID: ${response.data.id}`
        this.form = {
          model_name: 'llama3.2:latest',
          dataset_file: '',
          dataset_format: '',
          metrics: '',
          evaluator_models: ''
        }
        await this.loadBenchmarks()
      } catch (err) {
        this.error = `Failed to start benchmark: ${err.message}`
      } finally {
        this.loading = false
      }
    },
    async viewBenchmark(id) {
      try {
        const response = await axios.get(`${API_BASE}/benchmarks/${id}`)
        this.selectedBenchmark = response.data
      } catch (err) {
        this.error = `Failed to load benchmark: ${err.message}`
      }
    },
    async viewResults(id) {
      try {
        const response = await axios.get(`${API_BASE}/benchmarks/${id}/result`)
        this.benchmarkResults = response.data.result_data
      } catch (err) {
        this.error = `Failed to load results: ${err.message}`
      }
    },
    async deleteBenchmark(id) {
      if (!confirm('Are you sure you want to delete this benchmark?')) {
        return
      }
      
      try {
        await axios.delete(`${API_BASE}/benchmarks/${id}`)
        this.success = 'Benchmark deleted successfully'
        await this.loadBenchmarks()
      } catch (err) {
        this.error = `Failed to delete benchmark: ${err.message}`
      }
    },
    formatDate(dateString) {
      if (!dateString) return 'N/A'
      return new Date(dateString).toLocaleString()
    }
  }
}
</script>

