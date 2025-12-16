<template>
  <v-card class="mb-4">
    <v-card-title>
      <v-icon icon="mdi-rocket-launch" class="mr-2"></v-icon>
      Start New Benchmark
    </v-card-title>
    <v-card-text>
      <v-form @submit.prevent="handleSubmit">
        <v-text-field
          v-model="form.model_name"
          label="Model Name"
          placeholder="llama3.2:latest"
          required
          prepend-inner-icon="mdi-robot"
          variant="outlined"
          density="compact"
          class="mb-2"
        ></v-text-field>

        <v-text-field
          v-model="form.model_base_url"
          label="Model Base URL (optional)"
          placeholder="http://localhost:11434"
          prepend-inner-icon="mdi-server-network"
          variant="outlined"
          density="compact"
          hint="Base URL for the model under test"
          class="mb-2"
        ></v-text-field>

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

        <v-select
          v-model="form.metric_ids"
          :items="filteredMetrics"
          item-title="name"
          item-value="id"
          :label="form.metric_type === 'email_categorization' ? 'Metrics (optional - auto-created if empty)' : 'Metrics'"
          prepend-inner-icon="mdi-chart-bar"
          variant="outlined"
          density="compact"
          multiple
          chips
          closable-chips
          :required="form.metric_type !== 'email_categorization'"
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
                      v-model="evalModel.model_name"
                      label="Model Name"
                      placeholder="deepseek-r1:1.5b"
                      variant="outlined"
                      density="compact"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="5">
                    <v-text-field
                      v-model="evalModel.base_url"
                      label="Base URL (optional)"
                      variant="outlined"
                      density="compact"
                    ></v-text-field>
                  </v-col>
                  <v-col cols="2">
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
          :disabled="loading"
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
        model_name: 'llama3.2:latest',
        model_base_url: '',
        metric_type: 'standard',
        dataset_id: '',
        metric_ids: [],
        evaluator_models: [],
        mcp_tools: [],
        instructional_prompts: []
      }
    }
  },
  computed: {
    filteredMetrics() {
      if (!this.form.metric_type) return this.metrics
      return this.metrics.filter(m => m.type === this.form.metric_type)
    }
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
      this.form.evaluator_models.push({
        model_name: '',
        base_url: ''
      })
    },
    removeEvaluator(index) {
      this.form.evaluator_models.splice(index, 1)
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
    resetForm() {
      this.form = {
        model_name: 'llama3.2:latest',
        model_base_url: '',
        metric_type: 'standard',
        dataset_id: '',
        metric_ids: [],
        evaluator_models: [],
        mcp_tools: [],
        instructional_prompts: []
      }
    }
  }
}
</script>

