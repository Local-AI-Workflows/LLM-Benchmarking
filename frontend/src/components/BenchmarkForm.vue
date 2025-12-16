<template>
  <v-card class="mb-4">
    <v-card-title>
      <v-icon icon="mdi-rocket-launch" class="mr-2"></v-icon>
      Start New Benchmark
    </v-card-title>
    <v-card-text>
      <v-form @submit.prevent="handleSubmit">
        <v-text-field
          v-model="form.model_base_url"
          label="Model Base URL"
          placeholder="http://localhost:11434"
          prepend-inner-icon="mdi-server-network"
          variant="outlined"
          density="compact"
          hint="Base URL for the model under test (defaults to http://localhost:11434)"
          class="mb-2"
          @update:model-value="onHostnameChange"
        ></v-text-field>

        <v-row class="mb-2">
          <v-col cols="11">
            <v-select
              v-model="form.model_name"
              :items="availableModels"
              label="Model Name"
              placeholder="Select a model or use default"
              prepend-inner-icon="mdi-robot"
              variant="outlined"
              density="compact"
              :loading="loadingModels"
              :disabled="loadingModels"
              clearable
            >
              <template v-slot:no-data>
                <div class="pa-2 text-center">
                  <div v-if="loadingModels">Loading models...</div>
                  <div v-else>No models available. Click refresh to load models.</div>
                </div>
              </template>
            </v-select>
          </v-col>
          <v-col cols="1" class="d-flex align-center">
            <v-btn
              @click="refreshModels"
              icon="mdi-refresh"
              variant="text"
              :loading="loadingModels"
              :disabled="loadingModels"
              color="primary"
            ></v-btn>
          </v-col>
        </v-row>

        <v-select
          v-model="form.metric_type"
          :items="['standard', 'mcp', 'email_categorization']"
          label="Metric Type"
          prepend-inner-icon="mdi-ruler"
          variant="outlined"
          density="compact"
          @update:model-value="$emit('metric-type-change')"
          class="mb-2"
        ></v-select>

        <!-- Instructional Prompts for Email Categorization -->
        <v-expand-transition>
          <div v-if="form.metric_type === 'email_categorization'">
            <v-card variant="outlined" class="mb-2">
              <v-card-title class="text-subtitle-2">Instructional Prompts</v-card-title>
              <v-card-text>
                <div v-for="(prompt, index) in form.instructional_prompts" :key="index" class="mb-2">
                  <v-textarea
                    v-model="form.instructional_prompts[index]"
                    :label="`Prompt ${index + 1}`"
                    variant="outlined"
                    density="compact"
                    rows="3"
                    auto-grow
                  ></v-textarea>
                  <v-btn
                    @click="removeInstructionalPrompt(index)"
                    color="error"
                    size="small"
                    variant="text"
                    class="mt-1"
                  >
                    <v-icon start icon="mdi-delete"></v-icon>
                    Remove
                  </v-btn>
                </div>
                <v-btn
                  @click="addInstructionalPrompt"
                  color="primary"
                  size="small"
                  variant="outlined"
                  block
                >
                  <v-icon start icon="mdi-plus"></v-icon>
                  Add Instructional Prompt
                </v-btn>
              </v-card-text>
            </v-card>
          </div>
        </v-expand-transition>

        <v-select
          v-model="form.dataset_id"
          :items="datasets"
          item-title="name"
          item-value="id"
          label="Dataset"
          prepend-inner-icon="mdi-database"
          variant="outlined"
          density="compact"
          required
          class="mb-2"
        >
          <template v-slot:item="{ props, item }">
            <v-list-item v-bind="props">
              <template v-slot:title>
                {{ item.raw?.name || 'Unknown' }}
              </template>
              <template v-slot:subtitle>
                {{ Array.isArray(item.raw?.questions) ? item.raw.questions.length : 0 }} questions
              </template>
            </v-list-item>
          </template>
        </v-select>

        <!-- Metrics (hidden for email categorization) -->
        <v-expand-transition>
          <v-select
            v-if="form.metric_type !== 'email_categorization'"
            v-model="form.metric_ids"
            :items="filteredMetrics"
            item-title="name"
            item-value="id"
            label="Metrics"
            prepend-inner-icon="mdi-chart-bar"
            variant="outlined"
            density="compact"
            multiple
            chips
            closable-chips
            required
            class="mb-2"
          >
            <template v-slot:item="{ props, item }">
              <v-list-item v-bind="props">
                <template v-slot:title>
                  {{ item.raw?.name || 'Unknown' }}
                </template>
                <template v-slot:subtitle>
                  {{ item.raw?.description || '' }}
                </template>
              </v-list-item>
            </template>
          </v-select>
        </v-expand-transition>

        <!-- MCP Tools Configuration -->
        <v-expand-transition>
          <div v-if="form.metric_type === 'mcp'" class="mb-4">
            <v-card variant="outlined" class="pa-3">
              <v-card-title class="text-subtitle-1 mb-2">
                <v-icon icon="mdi-tools" class="mr-2"></v-icon>
                MCP Tools Configuration
              </v-card-title>
              <div v-for="(tool, index) in form.mcp_tools" :key="index" class="mb-3">
                <v-card variant="outlined" class="pa-3">
                  <v-text-field
                    v-model="tool.name"
                    label="Server Name"
                    placeholder="weather"
                    variant="outlined"
                    density="compact"
                    class="mb-2"
                  ></v-text-field>
                  <v-text-field
                    v-model="tool.url"
                    label="Server URL"
                    placeholder="http://localhost:8080"
                    variant="outlined"
                    density="compact"
                    class="mb-2"
                  ></v-text-field>
                  <v-text-field
                    v-model="tool.description"
                    label="Description"
                    variant="outlined"
                    density="compact"
                    class="mb-2"
                  ></v-text-field>
                  <v-text-field
                    v-model="tool.available_tools_str"
                    label="Available Tools (comma-separated)"
                    placeholder="get_weather,get_forecast"
                    variant="outlined"
                    density="compact"
                    class="mb-2"
                  ></v-text-field>
                  <v-btn
                    @click="removeMcpTool(index)"
                    color="error"
                    size="small"
                    variant="outlined"
                  >
                    <v-icon start icon="mdi-delete"></v-icon>
                    Remove
                  </v-btn>
                </v-card>
              </div>
              <v-btn
                @click="addMcpTool"
                color="primary"
                size="small"
                variant="outlined"
                block
              >
                <v-icon start icon="mdi-plus"></v-icon>
                Add MCP Tool
              </v-btn>
            </v-card>
          </div>
        </v-expand-transition>

        <!-- Evaluator Models (hidden for email categorization) -->
        <v-expand-transition>
          <div v-if="form.metric_type !== 'email_categorization'" class="mb-4">
            <v-card variant="outlined" class="pa-3">
              <v-card-title class="text-subtitle-1 mb-2">
                <v-icon icon="mdi-account-multiple" class="mr-2"></v-icon>
                Evaluator Models
              </v-card-title>
              <div v-for="(evalModel, index) in form.evaluator_models" :key="index" class="mb-2">
                <v-row>
                  <v-col cols="5">
                    <v-text-field
                      v-model="evalModel.base_url"
                      label="Base URL"
                      placeholder="http://localhost:11434"
                      variant="outlined"
                      density="compact"
                      @update:model-value="onEvaluatorHostnameChange(index)"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="6">
                    <v-select
                      v-model="evalModel.model_name"
                      :items="evaluatorAvailableModels[index] || []"
                      label="Model Name"
                      placeholder="Select a model or use default"
                      prepend-inner-icon="mdi-robot"
                      variant="outlined"
                      density="compact"
                      :loading="loadingEvaluatorModels[index] || false"
                      :disabled="loadingEvaluatorModels[index] || false"
                      clearable
                    >
                      <template v-slot:no-data>
                        <div class="pa-2 text-center">
                          <div v-if="loadingEvaluatorModels[index]">Loading models...</div>
                          <div v-else>No models available. Click refresh to load models.</div>
                        </div>
                      </template>
                    </v-select>
                  </v-col>
                  <v-col cols="1" class="d-flex align-center">
                    <v-btn
                      @click="refreshEvaluatorModels(index)"
                      icon="mdi-refresh"
                      variant="text"
                      :loading="loadingEvaluatorModels[index] || false"
                      :disabled="loadingEvaluatorModels[index] || false"
                      color="primary"
                      size="small"
                    ></v-btn>
                  </v-col>
                </v-row>
                <v-row>
                  <v-col cols="12" class="d-flex justify-end">
                    <v-btn
                      @click="removeEvaluator(index)"
                      color="error"
                      icon="mdi-delete"
                      variant="text"
                      size="small"
                    ></v-btn>
                  </v-col>
                </v-row>
              </div>
              <v-btn
                @click="addEvaluator"
                color="primary"
                size="small"
                variant="outlined"
                block
              >
                <v-icon start icon="mdi-plus"></v-icon>
                Add Evaluator Model
              </v-btn>
            </v-card>
          </div>
        </v-expand-transition>

        <v-btn
          type="submit"
          color="primary"
          block
          size="large"
          :loading="loading"
          :disabled="loading || !isFormValid"
        >
          <v-icon start icon="mdi-play"></v-icon>
          {{ loading ? 'Starting...' : 'Start Benchmark' }}
        </v-btn>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'BenchmarkForm',
  props: {
    datasets: {
      type: Array,
      default: () => []
    },
    metrics: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['submit', 'metric-type-change'],
  data() {
    return {
      form: {
        model_name: '',
        model_base_url: '',
        metric_type: 'standard',
        dataset_id: '',
        metric_ids: [],
        evaluator_models: [],
        mcp_tools: [],
        instructional_prompts: []
      },
      availableModels: [],
      loadingModels: false,
      refreshTimeout: null,
      evaluatorAvailableModels: {}, // Map of index -> available models
      loadingEvaluatorModels: {} // Map of index -> loading state
    }
  },
  computed: {
    filteredMetrics() {
      if (!this.form.metric_type) return this.metrics
      return this.metrics.filter(m => m.type === this.form.metric_type)
    },
    currentHostname() {
      return this.form.model_base_url || 'http://localhost:11434'
    },
    isValidUrl() {
      if (!this.form.model_base_url) return true // Empty is valid (will use default)
      try {
        const url = new URL(this.form.model_base_url)
        return url.protocol === 'http:' || url.protocol === 'https:'
      } catch {
        // Check if it's a valid IP address
        const ipRegex = /^(\d{1,3}\.){3}\d{1,3}(:\d+)?$/
        return ipRegex.test(this.form.model_base_url) || this.form.model_base_url.startsWith('http://') || this.form.model_base_url.startsWith('https://')
      }
    },
    isFormValid() {
      // Dataset is always required
      if (!this.form.dataset_id) {
        return false
      }

      // Validation for email_categorization
      if (this.form.metric_type === 'email_categorization') {
        // Must have at least one instructional prompt
        if (!this.form.instructional_prompts || this.form.instructional_prompts.length === 0) {
          return false
        }
        // All instructional prompts must be non-empty (after trimming)
        if (this.form.instructional_prompts.some(prompt => !prompt || !prompt.trim())) {
          return false
        }
        return true
      }

      // Validation for other metric types (standard, mcp)
      // Must have at least one metric selected
      if (!this.form.metric_ids || this.form.metric_ids.length === 0) {
        return false
      }

      // Must have at least one evaluator model
      if (!this.form.evaluator_models || this.form.evaluator_models.length === 0) {
        return false
      }

      // All evaluator models must have a model_name selected
      if (this.form.evaluator_models.some(evalModel => !evalModel.model_name || !evalModel.model_name.trim())) {
        return false
      }

      return true
    }
  },
  mounted() {
    // Load models on mount with default hostname
    this.refreshModels()
  },
  methods: {
    addMcpTool() {
      this.form.mcp_tools.push({
        name: '',
        url: '',
        description: '',
        available_tools_str: ''
      })
    },
    removeMcpTool(index) {
      this.form.mcp_tools.splice(index, 1)
    },
    addEvaluator() {
      const newIndex = this.form.evaluator_models.length
      this.form.evaluator_models.push({
        model_name: '',
        base_url: ''
      })
      // Initialize available models for this evaluator
      this.evaluatorAvailableModels[newIndex] = []
      this.loadingEvaluatorModels[newIndex] = false
      // Load models for localhost by default
      this.refreshEvaluatorModels(newIndex)
    },
    removeEvaluator(index) {
      this.form.evaluator_models.splice(index, 1)
      // Clean up available models - rebuild objects to maintain reactivity
      const newEvaluatorModels = {}
      const newLoadingModels = {}
      this.form.evaluator_models.forEach((evalModel, newIndex) => {
        const oldIndex = newIndex >= index ? newIndex + 1 : newIndex
        if (this.evaluatorAvailableModels[oldIndex] !== undefined) {
          newEvaluatorModels[newIndex] = this.evaluatorAvailableModels[oldIndex]
          newLoadingModels[newIndex] = this.loadingEvaluatorModels[oldIndex]
        }
      })
      this.evaluatorAvailableModels = newEvaluatorModels
      this.loadingEvaluatorModels = newLoadingModels
    },
    addInstructionalPrompt() {
      this.form.instructional_prompts.push('')
    },
    removeInstructionalPrompt(index) {
      this.form.instructional_prompts.splice(index, 1)
    },
    handleSubmit() {
      this.$emit('submit', { ...this.form })
    },
    async refreshModels() {
      this.loadingModels = true
      try {
        const hostname = this.form.model_base_url || 'http://localhost:11434'
        const response = await fetch(`/api/models/list?base_url=${encodeURIComponent(hostname)}`)
        if (response.ok) {
          const data = await response.json()
          this.availableModels = data.models || []
        } else {
          console.error('Failed to fetch models:', response.statusText)
          this.availableModels = []
        }
      } catch (error) {
        console.error('Error fetching models:', error)
        this.availableModels = []
      } finally {
        this.loadingModels = false
      }
    },
    onHostnameChange() {
      // Clear available models and selected model when hostname changes
      this.availableModels = []
      this.form.model_name = ''

      // Auto-refresh if URL is valid, or reload for localhost if cleared
      if (this.form.model_base_url && this.isValidUrl) {
        // Debounce the refresh
        clearTimeout(this.refreshTimeout)
        this.refreshTimeout = setTimeout(() => {
          this.refreshModels()
        }, 500)
      } else if (!this.form.model_base_url) {
        // Reload for localhost when hostname is cleared
        clearTimeout(this.refreshTimeout)
        this.refreshTimeout = setTimeout(() => {
          this.refreshModels()
        }, 500)
      }
    },
    async refreshEvaluatorModels(index) {
      this.loadingEvaluatorModels[index] = true
      try {
        const evalModel = this.form.evaluator_models[index]
        const hostname = evalModel?.base_url || 'http://localhost:11434'
        const response = await fetch(`/api/models/list?base_url=${encodeURIComponent(hostname)}`)
        if (response.ok) {
          const data = await response.json()
          this.evaluatorAvailableModels[index] = data.models || []
        } else {
          console.error(`Failed to fetch models for evaluator ${index}:`, response.statusText)
          this.evaluatorAvailableModels[index] = []
        }
      } catch (error) {
        console.error(`Error fetching models for evaluator ${index}:`, error)
        this.evaluatorAvailableModels[index] = []
      } finally {
        this.loadingEvaluatorModels[index] = false
      }
    },
    onEvaluatorHostnameChange(index) {
      const evalModel = this.form.evaluator_models[index]
      if (!evalModel) return

      // Clear available models and selected model when hostname changes
      this.evaluatorAvailableModels[index] = []
      evalModel.model_name = ''

      // Check if URL is valid
      const isValidUrl = (url) => {
        if (!url) return true // Empty is valid (will use default)
        try {
          const urlObj = new URL(url)
          return urlObj.protocol === 'http:' || urlObj.protocol === 'https:'
        } catch {
          // Check if it's a valid IP address
          const ipRegex = /^(\d{1,3}\.){3}\d{1,3}(:\d+)?$/
          return ipRegex.test(url) || url.startsWith('http://') || url.startsWith('https://')
        }
      }

      // Auto-refresh if URL is valid, or reload for localhost if cleared
      if (evalModel.base_url && isValidUrl(evalModel.base_url)) {
        // Debounce the refresh
        setTimeout(() => {
          this.refreshEvaluatorModels(index)
        }, 500)
      } else if (!evalModel.base_url) {
        // Reload for localhost when hostname is cleared
        setTimeout(() => {
          this.refreshEvaluatorModels(index)
        }, 500)
      }
    },
    resetForm() {
      this.form = {
        model_name: '',
        model_base_url: '',
        metric_type: 'standard',
        dataset_id: '',
        metric_ids: [],
        evaluator_models: [],
        mcp_tools: [],
        instructional_prompts: []
      }
      this.availableModels = []
      this.evaluatorAvailableModels = {}
      this.loadingEvaluatorModels = {}
    }
  }
}
</script>

