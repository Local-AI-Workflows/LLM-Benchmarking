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
      <v-data-table
        :headers="headers"
        :items="benchmarks"
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
        { title: 'Status', key: 'status', sortable: true },
        { title: 'Created', key: 'created_at', sortable: true },
        { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
      ]
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

