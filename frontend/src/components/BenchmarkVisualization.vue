<template>
  <div>
    <v-card v-if="!resultData" class="pa-4">
      <v-alert type="info">No result data available</v-alert>
    </v-card>
    
    <div v-else>
      <!-- Overview Stats -->
      <v-row class="mb-4">
        <v-col cols="12" sm="6" md="3">
          <v-card color="primary" variant="flat">
            <v-card-text>
              <div class="text-h6 text-white">Overall Score</div>
              <div class="text-h3 text-white font-weight-bold">{{ overallScore.toFixed(1) }}/10</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card color="success" variant="flat">
            <v-card-text>
              <div class="text-h6 text-white">Questions</div>
              <div class="text-h3 text-white font-weight-bold">{{ numQuestions }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card color="info" variant="flat">
            <v-card-text>
              <div class="text-h6 text-white">Metrics</div>
              <div class="text-h3 text-white font-weight-bold">{{ numMetrics }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card color="warning" variant="flat">
            <v-card-text>
              <div class="text-h6 text-white">Evaluators</div>
              <div class="text-h3 text-white font-weight-bold">{{ numEvaluators }}</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Metrics Chart -->
      <v-card class="mb-4">
        <v-card-title>
          <v-icon icon="mdi-chart-bar" class="mr-2"></v-icon>
          Average Scores by Metric
        </v-card-title>
        <v-card-text>
          <div style="height: 400px;">
            <canvas ref="metricsChart"></canvas>
          </div>
        </v-card-text>
      </v-card>

      <!-- Questions Table -->
      <v-card>
        <v-card-title>
          <v-icon icon="mdi-help-circle" class="mr-2"></v-icon>
          Question Details
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="questionHeaders"
            :items="questionData"
            :items-per-page="10"
            class="elevation-0"
          >
            <template v-slot:item.prompt="{ item }">
              <div style="max-width: 400px;">
                {{ item.prompt.substring(0, 100) }}{{ item.prompt.length > 100 ? '...' : '' }}
              </div>
            </template>
            <template v-slot:item.avgScore="{ item }">
              <v-chip
                :color="getScoreColor(item.avgScore)"
                size="small"
                variant="flat"
              >
                {{ item.avgScore.toFixed(1) }}
              </v-chip>
            </template>
            <template v-slot:item.metricScores="{ item }">
              <div v-for="(score, metric) in item.metricScores" :key="metric" class="mb-1">
                <v-chip
                  size="x-small"
                  variant="outlined"
                  class="mr-1"
                >
                  <strong>{{ metric }}:</strong> {{ score.toFixed(1) }}
                </v-chip>
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js'
import { Bar } from 'vue-chartjs'

Chart.register(...registerables)

export default {
  name: 'BenchmarkVisualization',
  components: {
    Bar
  },
  props: {
    resultData: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      metricsChart: null,
      questionHeaders: [
        { title: 'Question', key: 'prompt', sortable: false },
        { title: 'Average Score', key: 'avgScore', sortable: true },
        { title: 'Metrics', key: 'metricScores', sortable: false }
      ]
    }
  },
  computed: {
    overallScore() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return 0
      const allScores = []
      this.resultData.prompt_evaluations.forEach(pe => {
        pe.evaluations.forEach(evaluation => {
          if (evaluation.score !== undefined) {
            allScores.push(evaluation.score)
          }
        })
      })
      if (allScores.length === 0) return 0
      return allScores.reduce((a, b) => a + b, 0) / allScores.length
    },
    numQuestions() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return 0
      return this.resultData.prompt_evaluations.length
    },
    numMetrics() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return 0
      const metrics = new Set()
      this.resultData.prompt_evaluations.forEach(pe => {
        pe.evaluations.forEach(evaluation => {
          if (evaluation.metric_name) {
            metrics.add(evaluation.metric_name)
          }
        })
      })
      return metrics.size
    },
    numEvaluators() {
      if (!this.resultData || !this.resultData.metadata) return 0
      const evaluators = this.resultData.metadata.evaluator_models || []
      return evaluators.length || 1
    },
    questionData() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return []
      
      return this.resultData.prompt_evaluations.map(pe => {
        const metricScores = {}
        let totalScore = 0
        let scoreCount = 0
        
        pe.evaluations.forEach(evaluation => {
          if (evaluation.score !== undefined) {
            const metricName = evaluation.metric_name || 'unknown'
            if (!metricScores[metricName]) {
              metricScores[metricName] = []
            }
            metricScores[metricName].push(evaluation.score)
            totalScore += evaluation.score
            scoreCount++
          }
        })
        
        // Calculate average per metric
        const avgMetricScores = {}
        Object.keys(metricScores).forEach(metric => {
          const scores = metricScores[metric]
          avgMetricScores[metric] = scores.reduce((a, b) => a + b, 0) / scores.length
        })
        
        return {
          prompt: pe.prompt,
          avgScore: scoreCount > 0 ? totalScore / scoreCount : 0,
          metricScores: avgMetricScores
        }
      })
    },
    metricsChartData() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return null
      
      const metricAverages = {}
      const metricCounts = {}
      
      this.resultData.prompt_evaluations.forEach(pe => {
        pe.evaluations.forEach(evaluation => {
          if (evaluation.score !== undefined) {
            const metricName = evaluation.metric_name || 'unknown'
            if (!metricAverages[metricName]) {
              metricAverages[metricName] = 0
              metricCounts[metricName] = 0
            }
            metricAverages[metricName] += evaluation.score
            metricCounts[metricName]++
          }
        })
      })
      
      const labels = Object.keys(metricAverages)
      const data = labels.map(metric => {
        return metricAverages[metric] / metricCounts[metric]
      })
      
      return {
        labels,
        datasets: [{
          label: 'Average Score',
          data,
          backgroundColor: 'rgba(25, 118, 210, 0.6)',
          borderColor: 'rgba(25, 118, 210, 1)',
          borderWidth: 2
        }]
      }
    }
  },
  mounted() {
    this.renderChart()
  },
  watch: {
    resultData() {
      this.$nextTick(() => {
        this.renderChart()
      })
    }
  },
  methods: {
    renderChart() {
      if (!this.metricsChartData || !this.$refs.metricsChart) return
      
      if (this.metricsChart) {
        this.metricsChart.destroy()
      }
      
      const ctx = this.$refs.metricsChart.getContext('2d')
      this.metricsChart = new Chart(ctx, {
        type: 'bar',
        data: this.metricsChartData,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              max: 10,
              ticks: {
                stepSize: 1
              }
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  return `Score: ${context.parsed.y.toFixed(2)}`
                }
              }
            }
          }
        }
      })
    },
    getScoreColor(score) {
      if (score >= 8) return 'success'
      if (score >= 6) return 'info'
      if (score >= 4) return 'warning'
      return 'error'
    }
  },
  beforeUnmount() {
    if (this.metricsChart) {
      this.metricsChart.destroy()
    }
  }
}
</script>

<style scoped>
canvas {
  max-height: 400px;
}
</style>
