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

      <!-- Detailed Evaluations Table -->
      <v-card class="mb-4">
        <v-card-title>
          <v-icon icon="mdi-table-eye" class="mr-2"></v-icon>
          Detailed Evaluations
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="detailedHeaders"
            :items="detailedEvaluations"
            :items-per-page="20"
            class="elevation-0"
            density="compact"
          >
            <template v-slot:item.question="{ item }">
              <div style="max-width: 300px; word-wrap: break-word;">
                {{ item.question.substring(0, 80) }}{{ item.question.length > 80 ? '...' : '' }}
              </div>
            </template>
            <template v-slot:item.response="{ item }">
              <div style="max-width: 300px; word-wrap: break-word;">
                {{ item.response.substring(0, 80) }}{{ item.response.length > 80 ? '...' : '' }}
              </div>
            </template>
            <template v-slot:item.evaluator="{ item }">
              <v-chip
                size="small"
                :variant="item.isCombined ? 'flat' : 'outlined'"
                :color="item.isCombined ? 'primary' : 'default'"
              >
                {{ item.evaluator }}
                <v-icon v-if="item.isCombined" size="x-small" class="ml-1">mdi-chart-line-variant</v-icon>
              </v-chip>
            </template>
            <template v-slot:item.score="{ item }">
              <v-chip
                :color="getScoreColor(item.score)"
                size="small"
                variant="flat"
              >
                {{ item.score.toFixed(1) }}
              </v-chip>
            </template>
            <template v-slot:item.rationale="{ item }">
              <div style="max-width: 400px; word-wrap: break-word;">
                {{ item.rationale.substring(0, 100) }}{{ item.rationale.length > 100 ? '...' : '' }}
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>

      <!-- Questions Table -->
      <v-card>
        <v-card-title>
          <v-icon icon="mdi-help-circle" class="mr-2"></v-icon>
          Question Summary
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="questionHeaders"
            :items="questionData"
            :items-per-page="10"
            class="elevation-0"
            show-expand
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
            <template v-slot:expanded-row="{ item }">
              <tr>
                <td colspan="3">
                  <div class="pa-4">
                    <div class="mb-2"><strong>Full Prompt:</strong></div>
                    <div class="mb-4" style="white-space: pre-wrap; background: #f5f5f5; padding: 12px; border-radius: 4px;">
                      {{ item.prompt }}
                    </div>
                    <div class="mb-2"><strong>Response:</strong></div>
                    <div class="mb-4" style="white-space: pre-wrap; background: #f5f5f5; padding: 12px; border-radius: 4px;">
                      {{ item.response }}
                    </div>
                    <div v-for="(evaluation, idx) in item.evaluations" :key="idx" class="mb-3">
                      <v-card variant="outlined">
                        <v-card-title class="text-subtitle-1">
                          {{ evaluation.metric_name }}
                        </v-card-title>
                        <v-card-text>
                          <div class="mb-2">
                            <strong>Score:</strong> 
                            <v-chip :color="getScoreColor(evaluation.score)" size="small" variant="flat">
                              {{ evaluation.score.toFixed(1) }}
                            </v-chip>
                          </div>
                          <div><strong>Rationale:</strong> {{ evaluation.rationale }}</div>
                        </v-card-text>
                      </v-card>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'StandardResults',
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
      ],
      detailedHeaders: [
        { title: 'Question', key: 'question', sortable: false },
        { title: 'Response', key: 'response', sortable: false },
        { title: 'Metric', key: 'metric', sortable: true },
        { title: 'Evaluator', key: 'evaluator', sortable: true },
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
    detailedEvaluations() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return []
      
      const evaluations = []
      this.resultData.prompt_evaluations.forEach((pe, questionIndex) => {
        pe.evaluations.forEach(evaluation => {
          // Add combined evaluation
          evaluations.push({
            question: pe.prompt,
            response: pe.response,
            questionIndex: questionIndex + 1,
            metric: evaluation.metric_name || 'unknown',
            evaluator: 'Average',
            score: evaluation.score,
            rationale: evaluation.rationale || '',
            isCombined: true
          })
          
          // Add individual evaluator responses
          if (evaluation.individual_responses && evaluation.individual_responses.length > 0) {
            evaluation.individual_responses.forEach(individual => {
              evaluations.push({
                question: pe.prompt,
                response: pe.response,
                questionIndex: questionIndex + 1,
                metric: evaluation.metric_name || 'unknown',
                evaluator: individual.model_name,
                score: individual.score,
                rationale: individual.rationale || '',
                isCombined: false
              })
            })
          }
        })
      })
      
      return evaluations
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
          response: pe.response,
          avgScore: scoreCount > 0 ? totalScore / scoreCount : 0,
          metricScores: avgMetricScores,
          evaluations: pe.evaluations || []
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
      
      return { labels, data }
    }
  },
  mounted() {
    this.renderChart()
  },
  watch: {
    metricsChartData() {
      this.$nextTick(() => {
        this.renderChart()
      })
    }
  },
  methods: {
    getScoreColor(score) {
      if (score >= 8) return 'success'
      if (score >= 6) return 'info'
      if (score >= 4) return 'warning'
      return 'error'
    },
    renderChart() {
      if (!this.$refs.metricsChart || !this.metricsChartData) return
      
      if (this.metricsChart) {
        this.metricsChart.destroy()
      }
      
      const ctx = this.$refs.metricsChart.getContext('2d')
      this.metricsChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: this.metricsChartData.labels,
          datasets: [{
            label: 'Average Score',
            data: this.metricsChartData.data,
            backgroundColor: 'rgba(33, 150, 243, 0.6)',
            borderColor: 'rgba(33, 150, 243, 1)',
            borderWidth: 2
          }]
        },
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
  }
}
</script>


