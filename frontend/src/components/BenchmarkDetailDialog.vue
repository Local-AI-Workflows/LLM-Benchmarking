<template>
  <v-dialog v-model="show" max-width="600">
    <v-card v-if="benchmark">
      <v-card-title>
        <v-icon icon="mdi-information" class="mr-2"></v-icon>
        Benchmark Details
      </v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item>
            <v-list-item-title>ID</v-list-item-title>
            <v-list-item-subtitle>{{ benchmark.id }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Status</v-list-item-title>
            <v-list-item-subtitle>
              <v-chip
                :color="getStatusColor(benchmark.status)"
                size="small"
                variant="flat"
              >
                {{ benchmark.status }}
              </v-chip>
            </v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Model</v-list-item-title>
            <v-list-item-subtitle>{{ benchmark.model_name || 'N/A' }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Dataset</v-list-item-title>
            <v-list-item-subtitle>{{ benchmark.dataset_name || 'N/A' }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Metric Type</v-list-item-title>
            <v-list-item-subtitle>{{ benchmark.metric_type || 'N/A' }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Metrics</v-list-item-title>
            <v-list-item-subtitle>{{ benchmark.metrics.join(', ') || 'N/A' }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Created</v-list-item-title>
            <v-list-item-subtitle>{{ formatDate(benchmark.created_at) }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item v-if="benchmark.error_message">
            <v-list-item-title>Error</v-list-item-title>
            <v-list-item-subtitle class="text-error">{{ benchmark.error_message }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          v-if="benchmark.status === 'completed'"
          @click="$emit('view-results', benchmark.id)"
          color="success"
        >
          <v-icon start icon="mdi-chart-box"></v-icon>
          View Results
        </v-btn>
        <v-btn @click="show = false" color="primary">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'BenchmarkDetailDialog',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    benchmark: {
      type: Object,
      default: null
    }
  },
  emits: ['update:modelValue', 'view-results'],
  computed: {
    show: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    }
  },
  methods: {
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

