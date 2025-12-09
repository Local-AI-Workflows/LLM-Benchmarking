<template>
  <div>
    <!-- Metrics Section -->
    <v-card class="mb-4">
      <v-card-title>
        <v-icon icon="mdi-ruler" class="mr-2"></v-icon>
        Metrics
        <v-spacer></v-spacer>
        <v-select
          v-model="metricFilter"
          :items="[
            { label: 'All Types', value: '' },
            { label: 'Standard', value: 'standard' },
            { label: 'MCP', value: 'mcp' }
          ]"
          item-title="label"
          item-value="value"
          label="Filter by Type"
          variant="outlined"
          density="compact"
          style="max-width: 200px;"
          class="mr-2"
          @update:model-value="loadMetrics"
        ></v-select>
        <v-btn
          @click="showMetricForm = true; editingMetric = null"
          color="primary"
          prepend-icon="mdi-plus"
        >
          Add Metric
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-data-table
          :headers="metricHeaders"
          :items="metrics"
          :loading="loadingMetrics"
          item-value="id"
          class="elevation-0"
        >
          <template v-slot:item.type="{ item }">
            <v-chip
              :color="item.type === 'mcp' ? 'purple' : 'blue'"
              size="small"
              variant="flat"
            >
              {{ item.type }}
            </v-chip>
          </template>
          <template v-slot:item.enabled="{ item }">
            <v-switch
              :model-value="item.enabled"
              @update:model-value="toggleMetric(item.id, $event)"
              hide-details
              density="compact"
              color="success"
            ></v-switch>
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              @click="editMetric(item)"
              icon="mdi-pencil"
              size="small"
              variant="text"
              color="primary"
            ></v-btn>
            <v-btn
              @click="deleteMetric(item.id)"
              icon="mdi-delete"
              size="small"
              variant="text"
              color="error"
            ></v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Metric Form Dialog -->
    <v-dialog v-model="showMetricForm" max-width="800" scrollable>
      <v-card>
        <v-card-title>
          <v-icon icon="mdi-ruler" class="mr-2"></v-icon>
          {{ editingMetric ? 'Edit Metric' : 'Add Metric' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveMetric">
            <v-text-field
              v-model="metricForm.name"
              label="Name"
              required
              :disabled="!!editingMetric"
              variant="outlined"
              prepend-inner-icon="mdi-tag"
              class="mb-2"
            ></v-text-field>

            <v-select
              v-model="metricForm.type"
              :items="['standard', 'mcp']"
              label="Type"
              required
              :disabled="!!editingMetric"
              variant="outlined"
              prepend-inner-icon="mdi-shape"
              class="mb-2"
            ></v-select>

            <v-textarea
              v-model="metricForm.description"
              label="Description"
              variant="outlined"
              rows="3"
              prepend-inner-icon="mdi-text"
              class="mb-2"
            ></v-textarea>

            <v-textarea
              v-model="metricForm.evaluation_instructions"
              label="Evaluation Instructions (Prompt)"
              variant="outlined"
              rows="10"
              prepend-inner-icon="mdi-file-document-edit"
              hint="The main prompt that tells the evaluator how to score responses"
              persistent-hint
              class="mb-2"
            ></v-textarea>

            <v-row>
              <v-col cols="6">
                <v-text-field
                  v-model.number="metricForm.scale_min"
                  label="Scale Minimum"
                  type="number"
                  min="0"
                  max="10"
                  variant="outlined"
                  prepend-inner-icon="mdi-minus"
                  class="mb-2"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model.number="metricForm.scale_max"
                  label="Scale Maximum"
                  type="number"
                  min="1"
                  max="10"
                  variant="outlined"
                  prepend-inner-icon="mdi-plus"
                  class="mb-2"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-textarea
              v-model="metricForm.custom_format"
              label="Custom Format (optional)"
              variant="outlined"
              rows="4"
              prepend-inner-icon="mdi-code-tags"
              hint="Custom format for evaluator responses. If empty, uses default format."
              persistent-hint
              class="mb-2"
            ></v-textarea>

            <v-textarea
              v-model="metricForm.additional_context"
              label="Additional Context (optional)"
              variant="outlined"
              rows="3"
              prepend-inner-icon="mdi-information"
              hint="Extra context that will be included in the evaluation prompt"
              persistent-hint
              class="mb-2"
            ></v-textarea>

            <v-switch
              v-model="metricForm.enabled"
              label="Enabled"
              color="success"
              class="mb-2"
            ></v-switch>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showMetricForm = false" variant="text">Cancel</v-btn>
          <v-btn @click="saveMetric" color="primary" variant="flat">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Datasets Section -->
    <v-card class="mb-4">
      <v-card-title>
        <v-icon icon="mdi-database" class="mr-2"></v-icon>
        Datasets
        <v-spacer></v-spacer>
        <v-btn
          @click="showDatasetForm = true; editingDataset = null"
          color="primary"
          prepend-icon="mdi-plus"
          class="mr-2"
        >
          Add Dataset
        </v-btn>
        <v-btn
          @click="showImportForm = true"
          color="success"
          prepend-icon="mdi-upload"
        >
          Import Dataset
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-data-table
          :headers="datasetHeaders"
          :items="datasets"
          :loading="loadingDatasets"
          item-value="id"
          class="elevation-0"
        >
          <template v-slot:item.enabled="{ item }">
            <v-switch
              :model-value="item.enabled"
              @update:model-value="toggleDataset(item.id, $event)"
              hide-details
              density="compact"
              color="success"
            ></v-switch>
          </template>
          <template v-slot:item.actions="{ item }">
            <v-btn
              @click="editDataset(item)"
              icon="mdi-pencil"
              size="small"
              variant="text"
              color="primary"
            ></v-btn>
            <v-btn
              @click="deleteDataset(item.id)"
              icon="mdi-delete"
              size="small"
              variant="text"
              color="error"
            ></v-btn>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- Dataset Form Dialog -->
    <v-dialog v-model="showDatasetForm" max-width="900" scrollable>
      <v-card>
        <v-card-title>
          <v-icon icon="mdi-database" class="mr-2"></v-icon>
          {{ editingDataset ? 'Edit Dataset' : 'Add Dataset' }}
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="saveDataset">
            <v-text-field
              v-model="datasetForm.name"
              label="Name"
              required
              variant="outlined"
              prepend-inner-icon="mdi-tag"
              class="mb-2"
            ></v-text-field>

            <v-textarea
              v-model="datasetForm.description"
              label="Description"
              variant="outlined"
              rows="2"
              prepend-inner-icon="mdi-text"
              class="mb-2"
            ></v-textarea>

            <v-card variant="outlined" class="pa-3 mb-4">
              <v-card-title class="text-subtitle-1 mb-2">
                <v-icon icon="mdi-help-circle" class="mr-2"></v-icon>
                Questions
              </v-card-title>
              <div v-for="(question, index) in datasetForm.questions" :key="index" class="mb-3">
                <v-card variant="outlined" class="pa-3">
                  <div class="d-flex justify-space-between align-center mb-2">
                    <v-chip size="small" color="primary">Question {{ index + 1 }}</v-chip>
                    <v-btn
                      @click="removeQuestion(index)"
                      icon="mdi-delete"
                      size="small"
                      variant="text"
                      color="error"
                    ></v-btn>
                  </div>
                  <v-textarea
                    v-model="question.text"
                    label="Text"
                    required
                    variant="outlined"
                    rows="2"
                    density="compact"
                    class="mb-2"
                  ></v-textarea>
                  <v-text-field
                    v-model="question.context"
                    label="Context (optional)"
                    variant="outlined"
                    density="compact"
                    class="mb-2"
                  ></v-text-field>
                  <v-text-field
                    v-model="question.instructions"
                    label="Instructions (optional)"
                    variant="outlined"
                    density="compact"
                  ></v-text-field>
                </v-card>
              </div>
              <v-btn
                @click="addQuestion"
                color="primary"
                variant="outlined"
                block
                prepend-icon="mdi-plus"
              >
                Add Question
              </v-btn>
            </v-card>

            <v-switch
              v-model="datasetForm.enabled"
              label="Enabled"
              color="success"
            ></v-switch>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showDatasetForm = false" variant="text">Cancel</v-btn>
          <v-btn @click="saveDataset" color="primary" variant="flat">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Import Dataset Dialog -->
    <v-dialog v-model="showImportForm" max-width="700">
      <v-card>
        <v-card-title>
          <v-icon icon="mdi-upload" class="mr-2"></v-icon>
          Import Dataset
        </v-card-title>
        <v-card-text>
          <v-form @submit.prevent="importDataset">
            <v-text-field
              v-model="importForm.name"
              label="Dataset Name"
              required
              variant="outlined"
              prepend-inner-icon="mdi-tag"
              class="mb-2"
            ></v-text-field>

            <v-select
              v-model="importForm.format"
              :items="['json', 'csv', 'yaml', 'txt']"
              label="File Format"
              required
              variant="outlined"
              prepend-inner-icon="mdi-file-code"
              class="mb-2"
            ></v-select>

            <v-textarea
              v-model="importForm.content"
              label="File Content"
              required
              variant="outlined"
              rows="10"
              prepend-inner-icon="mdi-file-document"
              hint="Paste file content here..."
              persistent-hint
            ></v-textarea>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showImportForm = false" variant="text">Cancel</v-btn>
          <v-btn
            @click="importDataset"
            color="primary"
            variant="flat"
            :loading="importing"
            :disabled="importing"
          >
            {{ importing ? 'Importing...' : 'Import' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from 'axios'

const API_BASE = '/api'

export default {
  name: 'SettingsPage',
  data() {
    return {
      metrics: [],
      datasets: [],
      metricFilter: '',
      loadingMetrics: false,
      loadingDatasets: false,
      showMetricForm: false,
      editingMetric: null,
      metricForm: {
        name: '',
        type: 'standard',
        description: '',
        enabled: true,
        evaluation_instructions: '',
        scale_min: 0,
        scale_max: 10,
        custom_format: '',
        additional_context: ''
      },
      metricHeaders: [
        { title: 'Name', key: 'name', sortable: true },
        { title: 'Type', key: 'type', sortable: true },
        { title: 'Description', key: 'description', sortable: false },
        { title: 'Scale', key: 'scale', sortable: false },
        { title: 'Enabled', key: 'enabled', sortable: false },
        { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
      ],
      showDatasetForm: false,
      editingDataset: null,
      datasetForm: {
        name: '',
        description: '',
        questions: [],
        enabled: true
      },
      datasetHeaders: [
        { title: 'Name', key: 'name', sortable: true },
        { title: 'Description', key: 'description', sortable: false },
        { title: 'Questions', key: 'questionCount', sortable: false },
        { title: 'Enabled', key: 'enabled', sortable: false },
        { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
      ],
      showImportForm: false,
      importing: false,
      importForm: {
        name: '',
        format: 'json',
        content: ''
      },
      error: null,
      success: null
    }
  },
  mounted() {
    this.loadMetrics()
    this.loadDatasets()
  },
  methods: {
    async loadMetrics() {
      this.loadingMetrics = true
      try {
        const params = {}
        if (this.metricFilter) {
          params.metric_type = this.metricFilter
        }
        const response = await axios.get(`${API_BASE}/metrics`, { params })
        this.metrics = response.data.map(m => ({
          ...m,
          scale: `${m.scale_min}-${m.scale_max}`
        }))
      } catch (err) {
        this.error = `Failed to load metrics: ${err.message}`
      } finally {
        this.loadingMetrics = false
      }
    },
    async loadDatasets() {
      this.loadingDatasets = true
      try {
        const response = await axios.get(`${API_BASE}/datasets`)
        this.datasets = response.data.map(d => ({
          ...d,
          questionCount: Array.isArray(d.questions) ? d.questions.length : 0
        }))
      } catch (err) {
        this.error = `Failed to load datasets: ${err.message}`
      } finally {
        this.loadingDatasets = false
      }
    },
    async toggleMetric(id, enabled) {
      try {
        await axios.put(`${API_BASE}/metrics/${id}`, { enabled })
        await this.loadMetrics()
        this.success = 'Metric updated'
      } catch (err) {
        this.error = `Failed to update metric: ${err.message}`
      }
    },
    async toggleDataset(id, enabled) {
      try {
        await axios.put(`${API_BASE}/datasets/${id}`, { enabled })
        await this.loadDatasets()
        this.success = 'Dataset updated'
      } catch (err) {
        this.error = `Failed to update dataset: ${err.message}`
      }
    },
    editMetric(metric) {
      this.editingMetric = metric
      this.metricForm = {
        name: metric.name,
        type: metric.type,
        description: metric.description || '',
        enabled: metric.enabled !== undefined ? metric.enabled : true,
        evaluation_instructions: metric.evaluation_instructions || '',
        scale_min: metric.scale_min !== undefined ? metric.scale_min : 0,
        scale_max: metric.scale_max !== undefined ? metric.scale_max : 10,
        custom_format: metric.custom_format || '',
        additional_context: metric.additional_context || ''
      }
      this.showMetricForm = true
    },
    async saveMetric() {
      try {
        const payload = {
          ...this.metricForm,
          custom_format: this.metricForm.custom_format?.trim() || null,
          additional_context: this.metricForm.additional_context?.trim() || null
        }
        
        if (this.editingMetric) {
          await axios.put(`${API_BASE}/metrics/${this.editingMetric.id}`, payload)
          this.success = 'Metric updated'
        } else {
          await axios.post(`${API_BASE}/metrics`, payload)
          this.success = 'Metric created'
        }
        this.showMetricForm = false
        this.editingMetric = null
        this.metricForm = {
          name: '',
          type: 'standard',
          description: '',
          enabled: true,
          evaluation_instructions: '',
          scale_min: 0,
          scale_max: 10,
          custom_format: '',
          additional_context: ''
        }
        await this.loadMetrics()
      } catch (err) {
        this.error = `Failed to save metric: ${err.response?.data?.detail || err.message}`
      }
    },
    async deleteMetric(id) {
      if (!confirm('Are you sure you want to delete this metric?')) return
      try {
        await axios.delete(`${API_BASE}/metrics/${id}`)
        this.success = 'Metric deleted'
        await this.loadMetrics()
      } catch (err) {
        this.error = `Failed to delete metric: ${err.message}`
      }
    },
    editDataset(dataset) {
      this.editingDataset = dataset
      // Need to get full dataset with questions
      axios.get(`${API_BASE}/datasets/${dataset.id}`).then(response => {
        const fullDataset = response.data
        this.datasetForm = {
          name: fullDataset.name,
          description: fullDataset.description,
          questions: fullDataset.questions.map(q => ({
            text: q.text || '',
            context: q.context || '',
            instructions: q.instructions || '',
            expected_answer: q.expected_answer || '',
            ...q
          })),
          enabled: fullDataset.enabled
        }
        this.showDatasetForm = true
      }).catch(err => {
        this.error = `Failed to load dataset: ${err.message}`
      })
    },
    addQuestion() {
      this.datasetForm.questions.push({
        text: '',
        context: '',
        instructions: '',
        expected_answer: ''
      })
    },
    removeQuestion(index) {
      this.datasetForm.questions.splice(index, 1)
    },
    async saveDataset() {
      try {
        const payload = {
          ...this.datasetForm,
          questions: this.datasetForm.questions.filter(q => q.text.trim())
        }
        if (this.editingDataset) {
          await axios.put(`${API_BASE}/datasets/${this.editingDataset.id}`, payload)
          this.success = 'Dataset updated'
        } else {
          await axios.post(`${API_BASE}/datasets`, payload)
          this.success = 'Dataset created'
        }
        this.showDatasetForm = false
        this.editingDataset = null
        this.datasetForm = {
          name: '',
          description: '',
          questions: [],
          enabled: true
        }
        await this.loadDatasets()
      } catch (err) {
        this.error = `Failed to save dataset: ${err.response?.data?.detail || err.message}`
      }
    },
    async importDataset() {
      this.importing = true
      try {
        await axios.post(`${API_BASE}/datasets/import`, {
          file_content: this.importForm.content,
          file_format: this.importForm.format,
          name: this.importForm.name
        })
        this.success = 'Dataset imported'
        this.showImportForm = false
        this.importForm = {
          name: '',
          format: 'json',
          content: ''
        }
        await this.loadDatasets()
      } catch (err) {
        this.error = `Failed to import dataset: ${err.response?.data?.detail || err.message}`
      } finally {
        this.importing = false
      }
    },
    async deleteDataset(id) {
      if (!confirm('Are you sure you want to delete this dataset?')) return
      try {
        await axios.delete(`${API_BASE}/datasets/${id}`)
        this.success = 'Dataset deleted'
        await this.loadDatasets()
      } catch (err) {
        this.error = `Failed to delete dataset: ${err.message}`
      }
    }
  }
}
</script>
