<template>
  <div>
    <v-card v-if="!resultData" class="pa-4">
      <v-alert type="info">No result data available</v-alert>
    </v-card>
    
    <div v-else>
      <!-- Overview Stats Cards -->
      <v-row class="mb-4">
        <v-col cols="12" sm="6" md="3">
          <v-card color="primary" variant="flat">
            <v-card-text>
              <div class="text-h6 text-white">Overall Score</div>
              <div class="text-h3 text-white font-weight-bold">{{ overallScore.toFixed(1) }}/5</div>
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

      <!-- RAG Metric Cards -->
      <v-row class="mb-4">
        <v-col cols="12" sm="6" md="3" v-for="metric in ragMetricSummaries" :key="metric.name">
          <v-card :color="getMetricCardColor(metric.name)" variant="tonal">
            <v-card-text class="text-center">
              <v-icon :icon="getMetricIcon(metric.name)" size="32" class="mb-2"></v-icon>
              <div class="text-subtitle-1 font-weight-bold">{{ formatMetricName(metric.name) }}</div>
              <div class="text-h4 font-weight-bold">{{ metric.average.toFixed(2) }}</div>
              <div class="text-caption">
                Min: {{ metric.min.toFixed(1) }} | Max: {{ metric.max.toFixed(1) }}
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- RAG Metrics Radar Chart -->
      <v-card class="mb-4">
        <v-card-title>
          <v-icon icon="mdi-radar" class="mr-2"></v-icon>
          RAG Quality Dimensions
        </v-card-title>
        <v-card-text>
          <div style="height: 400px;">
            <canvas ref="radarChart"></canvas>
          </div>
        </v-card-text>
      </v-card>

      <!-- Metrics Bar Chart -->
      <v-card class="mb-4">
        <v-card-title>
          <v-icon icon="mdi-chart-bar" class="mr-2"></v-icon>
          Average Scores by RAG Metric
        </v-card-title>
        <v-card-text>
          <div style="height: 300px;">
            <canvas ref="metricsChart"></canvas>
          </div>
        </v-card-text>
      </v-card>

      <!-- Detailed Evaluations Table -->
      <v-card class="mb-4">
        <v-card-title class="d-flex align-center flex-wrap">
          <div class="d-flex align-center">
            <v-icon icon="mdi-table-eye" class="mr-2"></v-icon>
            Detailed RAG Evaluations
          </div>
          <v-spacer></v-spacer>
          <v-select
            v-model="selectedMetricFilter"
            :items="availableMetrics"
            label="Filter by Metric"
            clearable
            density="compact"
            variant="outlined"
            style="max-width: 250px;"
            class="ml-4"
            hide-details
          >
            <template v-slot:prepend-inner>
              <v-icon icon="mdi-filter" size="small"></v-icon>
            </template>
          </v-select>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="detailedHeaders"
            :items="filteredDetailedEvaluations"
            :items-per-page="20"
            class="elevation-0"
            density="compact"
          >
            <template v-slot:item.question="{ item }">
              <v-menu open-on-hover :close-on-content-click="false" location="top" max-width="600">
                <template v-slot:activator="{ props }">
                  <div 
                    v-bind="props" 
                    style="max-width: 250px; word-wrap: break-word; cursor: help;"
                    class="text-truncate-hover"
                  >
                    {{ item.question.substring(0, 60) }}{{ item.question.length > 60 ? '...' : '' }}
                  </div>
                </template>
                <v-card max-width="600">
                  <v-card-title class="text-subtitle-2 bg-primary text-white py-2">
                    <v-icon icon="mdi-email" size="small" class="mr-1"></v-icon>
                    E-Mail Anfrage
                  </v-card-title>
                  <v-card-text class="pa-3" style="max-height: 400px; overflow-y: auto; white-space: pre-wrap;">
                    {{ item.question }}
                  </v-card-text>
                </v-card>
              </v-menu>
            </template>
            <template v-slot:item.response="{ item }">
              <v-menu open-on-hover :close-on-content-click="false" location="top" max-width="500">
                <template v-slot:activator="{ props }">
                  <div 
                    v-bind="props" 
                    style="max-width: 250px; word-wrap: break-word; cursor: help;"
                    class="text-truncate-hover"
                  >
                    {{ item.response.substring(0, 60) }}{{ item.response.length > 60 ? '...' : '' }}
                  </div>
                </template>
                <v-card max-width="500">
                  <v-card-title class="text-subtitle-2 bg-success text-white py-2">
                    <v-icon icon="mdi-message-reply-text" size="small" class="mr-1"></v-icon>
                    Full Response
                  </v-card-title>
                  <v-card-text class="pa-3" style="max-height: 400px; overflow-y: auto; white-space: pre-wrap;">
                    {{ item.response }}
                  </v-card-text>
                </v-card>
              </v-menu>
            </template>
            <template v-slot:item.metric="{ item }">
              <v-chip
                :color="getMetricChipColor(item.metric)"
                size="small"
                variant="flat"
              >
                {{ formatMetricName(item.metric) }}
              </v-chip>
            </template>
            <template v-slot:item.score="{ item }">
              <v-chip
                :color="getScoreColor(item.score)"
                size="small"
                variant="flat"
              >
                {{ item.score.toFixed(1) }}/5
              </v-chip>
            </template>
            <template v-slot:item.rationale="{ item }">
              <v-menu open-on-hover :close-on-content-click="false" location="top" max-width="500">
                <template v-slot:activator="{ props }">
                  <div 
                    v-bind="props" 
                    style="max-width: 300px; word-wrap: break-word; cursor: help;"
                    class="text-truncate-hover"
                  >
                    {{ item.rationale.substring(0, 80) }}{{ item.rationale.length > 80 ? '...' : '' }}
                  </div>
                </template>
                <v-card max-width="500">
                  <v-card-title class="text-subtitle-2 bg-info text-white py-2">
                    <v-icon icon="mdi-text-box-outline" size="small" class="mr-1"></v-icon>
                    Full Rationale
                  </v-card-title>
                  <v-card-text class="pa-3" style="max-height: 400px; overflow-y: auto; white-space: pre-wrap;">
                    {{ item.rationale }}
                  </v-card-text>
                </v-card>
              </v-menu>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>

      <!-- Question Detail Cards -->
      <v-card>
        <v-card-title>
          <v-icon icon="mdi-help-circle" class="mr-2"></v-icon>
          Question Details
        </v-card-title>
        <v-card-text>
          <v-expansion-panels>
            <v-expansion-panel v-for="(question, idx) in questionData" :key="idx">
              <v-expansion-panel-title>
                <div class="d-flex align-center justify-space-between" style="width: 100%;">
                  <div style="max-width: 60%;">
                    <strong>Q{{ idx + 1 }}:</strong> {{ question.prompt.substring(0, 80) }}...
                  </div>
                  <v-chip :color="getScoreColor(question.avgScore)" size="small" class="ml-2">
                    Avg: {{ question.avgScore.toFixed(1) }}/5
                  </v-chip>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-row>
                  <v-col cols="12">
                    <div class="mb-3">
                      <strong>Query:</strong>
                      <div class="pa-2 bg-grey-lighten-4 rounded mt-1" style="white-space: pre-wrap;">
                        {{ question.prompt }}
                      </div>
                    </div>
                    <div class="mb-3">
                      <strong>Response:</strong>
                      <div class="pa-2 bg-blue-lighten-5 rounded mt-1" style="white-space: pre-wrap;">
                        {{ question.response }}
                      </div>
                    </div>
                    <div>
                      <strong>Metric Scores:</strong>
                      <v-row class="mt-2">
                        <v-col cols="12" sm="6" md="4" v-for="(score, metric) in question.metricScores" :key="metric">
                          <v-card variant="outlined" class="pa-2">
                            <div class="text-caption text-grey">{{ formatMetricName(metric) }}</div>
                            <v-chip :color="getScoreColor(score)" size="small" class="mt-1">
                              {{ score.toFixed(1) }}/5
                            </v-chip>
                          </v-card>
                        </v-col>
                      </v-row>
                    </div>
                  </v-col>
                </v-row>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'RAGResults',
  props: {
    resultData: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      metricsChart: null,
      radarChart: null,
      selectedMetricFilter: null,  // Filter for detailed evaluations table
      detailedHeaders: [
        { title: 'E-Mail', key: 'question', sortable: false },
        { title: 'Response', key: 'response', sortable: false },
        { title: 'Metric', key: 'metric', sortable: true },
        { title: 'Score', key: 'score', sortable: true },
        { title: 'Rationale', key: 'rationale', sortable: false }
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
    ragMetricSummaries() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return []
      
      const metricStats = {}
      
      this.resultData.prompt_evaluations.forEach(pe => {
        pe.evaluations.forEach(evaluation => {
          if (evaluation.score !== undefined) {
            const metricName = evaluation.metric_name || 'unknown'
            if (!metricStats[metricName]) {
              metricStats[metricName] = { scores: [], name: metricName }
            }
            metricStats[metricName].scores.push(evaluation.score)
          }
        })
      })
      
      return Object.values(metricStats).map(stat => ({
        name: stat.name,
        average: stat.scores.reduce((a, b) => a + b, 0) / stat.scores.length,
        min: Math.min(...stat.scores),
        max: Math.max(...stat.scores),
        count: stat.scores.length
      }))
    },
    detailedEvaluations() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return []
      
      const evaluations = []
      this.resultData.prompt_evaluations.forEach((pe, questionIndex) => {
        pe.evaluations.forEach(evaluation => {
          // Use original_query from metadata if available (just the email), otherwise fall back to full prompt
          const displayQuestion = pe.metadata?.original_query || pe.prompt
          evaluations.push({
            question: displayQuestion,
            fullPrompt: pe.prompt,  // Keep full prompt for reference
            response: pe.response,
            questionIndex: questionIndex + 1,
            metric: evaluation.metric_name || 'unknown',
            score: evaluation.score,
            rationale: evaluation.rationale || ''
          })
        })
      })
      
      return evaluations
    },
    // Get unique metric names for filter dropdown
    availableMetrics() {
      if (!this.detailedEvaluations.length) return []
      const metrics = [...new Set(this.detailedEvaluations.map(e => e.metric))]
      return metrics.sort()
    },
    // Filtered evaluations based on selected metric
    filteredDetailedEvaluations() {
      if (!this.selectedMetricFilter) {
        return this.detailedEvaluations
      }
      return this.detailedEvaluations.filter(e => e.metric === this.selectedMetricFilter)
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
            metricScores[metricName] = evaluation.score
            totalScore += evaluation.score
            scoreCount++
          }
        })
        
        return {
          prompt: pe.prompt,
          response: pe.response,
          avgScore: scoreCount > 0 ? totalScore / scoreCount : 0,
          metricScores
        }
      })
    },
    radarChartData() {
      if (!this.ragMetricSummaries || this.ragMetricSummaries.length === 0) return null
      
      const labels = this.ragMetricSummaries.map(m => this.formatMetricName(m.name))
      const data = this.ragMetricSummaries.map(m => m.average)
      
      return { labels, data }
    },
    metricsChartData() {
      if (!this.ragMetricSummaries || this.ragMetricSummaries.length === 0) return null
      
      const labels = this.ragMetricSummaries.map(m => this.formatMetricName(m.name))
      const data = this.ragMetricSummaries.map(m => m.average)
      
      return { labels, data }
    }
  },
  mounted() {
    this.renderCharts()
  },
  watch: {
    resultData() {
      this.$nextTick(() => {
        this.renderCharts()
      })
    }
  },
  methods: {
    formatMetricName(name) {
      if (!name) return 'Unknown'
      return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase())
    },
    getMetricIcon(name) {
      const icons = {
        'faithfulness': 'mdi-shield-check',
        'relevance': 'mdi-target',
        'language_quality': 'mdi-text-box-check',
        'grammatical_correctness': 'mdi-spellcheck',
        'overall_rag_score': 'mdi-star'
      }
      return icons[name] || 'mdi-chart-box'
    },
    getMetricCardColor(name) {
      const colors = {
        'faithfulness': 'green',
        'relevance': 'blue',
        'language_quality': 'purple',
        'grammatical_correctness': 'teal',
        'overall_rag_score': 'amber'
      }
      return colors[name] || 'grey'
    },
    getMetricChipColor(name) {
      const colors = {
        'faithfulness': 'green',
        'relevance': 'blue',
        'language_quality': 'purple',
        'grammatical_correctness': 'teal',
        'overall_rag_score': 'amber'
      }
      return colors[name] || 'grey'
    },
    getScoreColor(score) {
      // RAG scores are 1-5
      if (score >= 4) return 'success'
      if (score >= 3) return 'info'
      if (score >= 2) return 'warning'
      return 'error'
    },
    renderCharts() {
      this.renderRadarChart()
      this.renderBarChart()
    },
    renderRadarChart() {
      if (!this.$refs.radarChart || !this.radarChartData) return
      
      if (this.radarChart) {
        this.radarChart.destroy()
      }
      
      const ctx = this.$refs.radarChart.getContext('2d')
      this.radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
          labels: this.radarChartData.labels,
          datasets: [{
            label: 'RAG Quality Score',
            data: this.radarChartData.data,
            backgroundColor: 'rgba(33, 150, 243, 0.2)',
            borderColor: 'rgba(33, 150, 243, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(33, 150, 243, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(33, 150, 243, 1)'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            r: {
              beginAtZero: true,
              max: 5,
              ticks: {
                stepSize: 1
              }
            }
          },
          plugins: {
            legend: {
              display: false
            }
          }
        }
      })
    },
    renderBarChart() {
      if (!this.$refs.metricsChart || !this.metricsChartData) return
      
      if (this.metricsChart) {
        this.metricsChart.destroy()
      }
      
      const ctx = this.$refs.metricsChart.getContext('2d')
      const colors = this.metricsChartData.labels.map((_, idx) => {
        const palette = [
          'rgba(76, 175, 80, 0.7)',  // green
          'rgba(33, 150, 243, 0.7)', // blue
          'rgba(156, 39, 176, 0.7)', // purple
          'rgba(0, 150, 136, 0.7)',  // teal
          'rgba(255, 193, 7, 0.7)'   // amber
        ]
        return palette[idx % palette.length]
      })
      
      this.metricsChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: this.metricsChartData.labels,
          datasets: [{
            label: 'Average Score',
            data: this.metricsChartData.data,
            backgroundColor: colors,
            borderColor: colors.map(c => c.replace('0.7', '1')),
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              max: 5,
              ticks: {
                stepSize: 1
              }
            }
          },
          plugins: {
            legend: {
              display: false
            }
          }
        }
      })
    }
  },
  beforeUnmount() {
    if (this.metricsChart) {
      this.metricsChart.destroy()
    }
    if (this.radarChart) {
      this.radarChart.destroy()
    }
  }
}
</script>

<style scoped>
.text-truncate-hover {
  transition: background-color 0.2s ease;
  padding: 4px 6px;
  border-radius: 4px;
}

.text-truncate-hover:hover {
  background-color: rgba(var(--v-theme-primary), 0.08);
}
</style>