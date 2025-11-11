<template>
  <div>
    <div v-if="!resultData" class="loading">No result data available</div>
    
    <div v-else>
      <!-- Overview Stats -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
        <div class="stat-card">
          <h3>Overall Score</h3>
          <div class="stat-value">{{ overallScore.toFixed(1) }}/10</div>
        </div>
        <div class="stat-card">
          <h3>Questions</h3>
          <div class="stat-value">{{ numQuestions }}</div>
        </div>
        <div class="stat-card">
          <h3>Metrics</h3>
          <div class="stat-value">{{ numMetrics }}</div>
        </div>
        <div class="stat-card">
          <h3>Evaluators</h3>
          <div class="stat-value">{{ numEvaluators }}</div>
        </div>
      </div>

      <!-- Metrics Chart -->
      <div class="chart-container">
        <h3>Average Scores by Metric</h3>
        <canvas ref="metricsChart"></canvas>
      </div>

      <!-- Questions Table -->
      <div style="margin-top: 30px;">
        <h3>Question Details</h3>
        <table class="table">
          <thead>
            <tr>
              <th>Question</th>
              <th>Average Score</th>
              <th>Metrics</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(question, idx) in questionData" :key="idx">
              <td>{{ question.prompt.substring(0, 100) }}{{ question.prompt.length > 100 ? '...' : '' }}</td>
              <td>{{ question.avgScore.toFixed(1) }}</td>
              <td>
                <div v-for="(score, metric) in question.metricScores" :key="metric" style="margin: 2px 0;">
                  <strong>{{ metric }}:</strong> {{ score.toFixed(1) }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default {
  name: 'BenchmarkVisualization',
  props: {
    resultData: {
      type: Object,
      required: true
    }
  },
  data() {
    return {
      chart: null
    }
  },
  computed: {
    overallScore() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return 0
      let total = 0
      let count = 0
      this.resultData.prompt_evaluations.forEach(pe => {
        pe.evaluations.forEach(eval => {
          total += eval.score
          count++
        })
      })
      return count > 0 ? total / count : 0
    },
    numQuestions() {
      return this.resultData?.prompt_evaluations?.length || 0
    },
    numMetrics() {
      if (!this.resultData?.prompt_evaluations) return 0
      const metrics = new Set()
      this.resultData.prompt_evaluations.forEach(pe => {
        pe.evaluations.forEach(eval => {
          metrics.add(eval.metric_name)
        })
      })
      return metrics.size
    },
    numEvaluators() {
      if (!this.resultData?.prompt_evaluations) return 0
      const evaluators = new Set()
      this.resultData.prompt_evaluations.forEach(pe => {
        pe.evaluations.forEach(eval => {
          eval.individual_responses?.forEach(ir => {
            evaluators.add(ir.model_name)
          })
        })
      })
      return evaluators.size
    },
    questionData() {
      if (!this.resultData?.prompt_evaluations) return []
      return this.resultData.prompt_evaluations.map(pe => {
        const metricScores = {}
        let total = 0
        let count = 0
        pe.evaluations.forEach(eval => {
          metricScores[eval.metric_name] = eval.score
          total += eval.score
          count++
        })
        return {
          prompt: pe.prompt,
          avgScore: count > 0 ? total / count : 0,
          metricScores
        }
      })
    },
    metricsData() {
      if (!this.resultData?.prompt_evaluations) return {}
      const metrics = {}
      this.resultData.prompt_evaluations.forEach(pe => {
        pe.evaluations.forEach(eval => {
          if (!metrics[eval.metric_name]) {
            metrics[eval.metric_name] = []
          }
          metrics[eval.metric_name].push(eval.score)
        })
      })
      const averages = {}
      Object.keys(metrics).forEach(metric => {
        const scores = metrics[metric]
        averages[metric] = scores.reduce((a, b) => a + b, 0) / scores.length
      })
      return averages
    }
  },
  mounted() {
    this.renderChart()
  },
  watch: {
    resultData: {
      handler() {
        this.$nextTick(() => {
          this.renderChart()
        })
      },
      deep: true
    }
  },
  methods: {
    renderChart() {
      if (!this.$refs.metricsChart || !this.resultData) return
      
      if (this.chart) {
        this.chart.destroy()
      }
      
      const metrics = Object.keys(this.metricsData)
      const scores = Object.values(this.metricsData)
      
      this.chart = new Chart(this.$refs.metricsChart, {
        type: 'bar',
        data: {
          labels: metrics,
          datasets: [{
            label: 'Average Score',
            data: scores,
            backgroundColor: 'rgba(52, 152, 219, 0.6)',
            borderColor: 'rgba(52, 152, 219, 1)',
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              max: 10,
              title: {
                display: true,
                text: 'Score (0-10)'
              }
            },
            x: {
              title: {
                display: true,
                text: 'Metrics'
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
                  return `Score: ${context.parsed.y.toFixed(1)}/10`
                }
              }
            }
          }
        }
      })
    }
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.destroy()
    }
  }
}
</script>

<style scoped>
.stat-card {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}

.stat-card h3 {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #2c3e50;
}

.chart-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin: 20px 0;
}
</style>

