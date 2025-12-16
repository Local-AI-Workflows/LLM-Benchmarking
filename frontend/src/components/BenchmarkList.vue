<template>
  <v-card>
    <v-card-title>
      <v-icon icon="mdi-format-list-bulleted" class="mr-2"></v-icon>
      Benchmarks
      <v-spacer></v-spacer>
      <v-btn
        @click="$emit('refresh')"
        icon="mdi-refresh"
        variant="text"
        size="small"
      ></v-btn>
    </v-card-title>
    <v-card-text>
      <!-- Filters -->
      <v-row class="mb-3">
        <v-col cols="12" md="6">
          <v-select
            v-model="typeFilter"
            :items="typeOptions"
            label="Filter by Type"
            clearable
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-filter"
          ></v-select>
        </v-col>
        <v-col cols="12" md="6">
          <v-select
            v-model="datasetFilter"
            :items="datasetOptions"
            label="Filter by Dataset"
            clearable
            variant="outlined"
            density="compact"
            prepend-inner-icon="mdi-filter"
          ></v-select>
        </v-col>
      </v-row>
      
      <v-data-table
        :headers="headers"
        :items="filteredBenchmarks"
        :loading="loading"
        item-value="id"
        class="elevation-0"
      >
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="getStatusColor(item.raw?.status || item.status)"
            size="small"
            variant="flat"
          >
            {{ item.raw?.status || item.status }}
          </v-chip>
        </template>
        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.raw?.created_at || item.created_at) }}
        </template>
        <template v-slot:item.metric_type="{ item }">
          <v-chip
            size="small"
            variant="outlined"
            :color="getTypeColor(item.raw?.metric_type || item.metric_type)"
          >
            {{ item.raw?.metric_type || item.metric_type || 'N/A' }}
          </v-chip>
        </template>
        <template v-slot:item.dataset_name="{ item }">
          {{ item.raw?.dataset_name || item.dataset_name || 'N/A' }}
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn
            @click="$emit('view', item.raw || item)"
            icon="mdi-eye"
            size="small"
            variant="text"
            color="primary"
          ></v-btn>
          <v-btn
            v-if="(item.raw?.status || item.status) === 'completed'"
            @click="$emit('view-results', item.raw || item)"
            icon="mdi-chart-box"
            size="small"
            variant="text"
            color="success"
          ></v-btn>
          <v-btn
            @click="$emit('delete', item.raw || item)"
            icon="mdi-delete"
            size="small"
            variant="text"
            color="error"
          ></v-btn>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'BenchmarkList',
  props: {
    benchmarks: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['refresh', 'view', 'view-results', 'delete'],
  data() {
    return {
      headers: [
        { title: 'ID', key: 'displayId', sortable: false },
        { title: 'Model', key: 'model_name', sortable: true },
        { title: 'Type', key: 'metric_type', sortable: true },
        { title: 'Dataset', key: 'dataset_name', sortable: true },
        { title: 'Status', key: 'status', sortable: true },
        { title: 'Created', key: 'created_at', sortable: true },
        { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
      ],
      typeFilter: '',
      datasetFilter: ''
    }
  },
  computed: {
    typeOptions() {
      const types = [...new Set(this.benchmarks.map(b => b.metric_type || b.raw?.metric_type).filter(Boolean))]
      return types.sort()
    },
    datasetOptions() {
      const datasets = [...new Set(this.benchmarks.map(b => b.dataset_name || b.raw?.dataset_name).filter(Boolean))]
      return datasets.sort()
    },
    filteredBenchmarks() {
      let filtered = this.benchmarks
      
      if (this.typeFilter) {
        filtered = filtered.filter(b => {
          const type = b.metric_type || b.raw?.metric_type
          return type === this.typeFilter
        })
      }
      
      if (this.datasetFilter) {
        filtered = filtered.filter(b => {
          const dataset = b.dataset_name || b.raw?.dataset_name
          return dataset === this.datasetFilter
        })
      }
      
      // Ensure displayId is set for filtered items
      return filtered.map(b => ({
        ...b,
        displayId: b.displayId || (b.id ? b.id.substring(0, 8) + '...' : 'N/A')
      }))
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
    },
    getTypeColor(type) {
      const colors = {
        standard: 'blue',
        mcp: 'purple',
        email_categorization: 'green'
      }
      return colors[type] || 'grey'
    }
  }
}
</script>

