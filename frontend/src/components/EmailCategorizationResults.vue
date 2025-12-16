<template>
  <div>
    <v-card v-if="!resultData" class="pa-4">
      <v-alert type="info">No result data available</v-alert>
    </v-card>
    
    <div v-else>
      <!-- Overview Stats -->
      <v-row class="mb-4">
        <v-col cols="12" sm="6" md="4">
          <v-card color="primary" variant="flat">
            <v-card-text>
              <div class="text-h6 text-white">Overall Accuracy</div>
              <div class="text-h3 text-white font-weight-bold">{{ overallAccuracy.toFixed(1) }}%</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="4">
          <v-card color="success" variant="flat">
            <v-card-text>
              <div class="text-h6 text-white">Total Emails</div>
              <div class="text-h3 text-white font-weight-bold">{{ totalEmails }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="4">
          <v-card color="info" variant="flat">
            <v-card-text>
              <div class="text-h6 text-white">Correct</div>
              <div class="text-h3 text-white font-weight-bold">{{ correctCount }}/{{ totalEmails }}</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Instructional Prompts Comparison -->
      <v-card v-if="promptResults.length > 0" class="mb-4">
        <v-card-title>
          <v-icon icon="mdi-compare" class="mr-2"></v-icon>
          Instructional Prompts Comparison
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="promptHeaders"
            :items="promptResults"
            :items-per-page="10"
            class="elevation-0"
            item-value="prompt"
          >
            <template v-slot:item.prompt="{ item }">
              <div class="prompt-text">
                <v-expansion-panels variant="accordion">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <div class="d-flex align-center">
                        <v-icon icon="mdi-text" class="mr-2"></v-icon>
                        <span class="text-truncate" style="max-width: 500px;">
                          {{ item.prompt.substring(0, 100) }}{{ item.prompt.length > 100 ? '...' : '' }}
                        </span>
                      </div>
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <pre class="prompt-full-text">{{ item.prompt }}</pre>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </div>
            </template>
            <template v-slot:item.accuracy="{ item }">
              <v-chip
                :color="getAccuracyColor(item.accuracy)"
                size="large"
                variant="flat"
                class="font-weight-bold"
              >
                {{ item.accuracy.toFixed(1) }}%
              </v-chip>
            </template>
            <template v-slot:item.correct="{ item }">
              <v-chip
                color="success"
                size="small"
                variant="flat"
              >
                {{ item.correct }}/{{ item.total }}
              </v-chip>
            </template>
            <template v-slot:item.rank="{ item }">
              <v-chip
                v-if="item.rank === 1"
                color="gold"
                size="small"
                variant="flat"
              >
                <v-icon start icon="mdi-trophy"></v-icon>
                Best
              </v-chip>
              <v-chip
                v-else
                :color="item.rank === 2 ? 'grey' : 'default'"
                size="small"
                variant="outlined"
              >
                #{{ item.rank }}
              </v-chip>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>

      <!-- Best Prompt Highlight -->
      <v-card v-if="bestPrompt" color="success" variant="tonal" class="mb-4">
        <v-card-title>
          <v-icon icon="mdi-trophy" class="mr-2"></v-icon>
          Best Performing Prompt
        </v-card-title>
        <v-card-text>
          <v-chip color="success" size="large" class="mb-2">
            Accuracy: {{ bestPrompt.accuracy.toFixed(1) }}%
          </v-chip>
          <div class="mt-2">
            <strong>Prompt:</strong>
            <pre class="prompt-full-text mt-2">{{ bestPrompt.prompt }}</pre>
          </div>
        </v-card-text>
      </v-card>

      <!-- Detailed Results by Prompt -->
      <v-card v-if="promptResults.length > 1" class="mb-4">
        <v-card-title>
          <v-icon icon="mdi-chart-line" class="mr-2"></v-icon>
          Accuracy Comparison Chart
        </v-card-title>
        <v-card-text>
          <div style="height: 300px;">
            <canvas ref="accuracyChart"></canvas>
          </div>
        </v-card-text>
      </v-card>

      <!-- Email Categorization Details -->
      <v-card>
        <v-card-title>
          <v-icon icon="mdi-email-multiple" class="mr-2"></v-icon>
          Email Categorization Details
        </v-card-title>
        <v-card-text>
          <!-- Filters -->
          <v-row class="mb-3">
            <v-col cols="12" md="6">
              <v-select
                v-model="categoryFilter"
                :items="categoryOptions"
                label="Filter by Category"
                clearable
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-filter"
              ></v-select>
            </v-col>
            <v-col cols="12" md="6">
              <v-select
                v-model="promptFilter"
                :items="promptOptions"
                label="Filter by Instructional Prompt"
                clearable
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-filter"
              >
                <template v-slot:item="{ props, item }">
                  <v-list-item v-bind="props">
                    <template v-slot:title>
                      <div class="text-truncate" style="max-width: 400px;">
                        {{ item.raw }}
                      </div>
                    </template>
                  </v-list-item>
                </template>
              </v-select>
            </v-col>
          </v-row>
          
          <v-data-table
            :headers="emailHeaders"
            :items="filteredEmailDetails"
            :items-per-page="20"
            class="elevation-0"
            density="compact"
          >
            <template v-slot:item.email_subject="{ item }">
              <div style="max-width: 200px; word-wrap: break-word;">
                {{ item.email_subject || 'N/A' }}
              </div>
            </template>
            <template v-slot:item.expected_category="{ item }">
              <v-chip size="small" color="info" variant="outlined">
                {{ item.expected_category }}
              </v-chip>
            </template>
            <template v-slot:item.predicted_category="{ item }">
              <v-chip
                size="small"
                :color="item.is_correct ? 'success' : 'error'"
                variant="flat"
              >
                {{ item.predicted_category || 'N/A' }}
              </v-chip>
            </template>
            <template v-slot:item.is_correct="{ item }">
              <v-icon
                :color="item.is_correct ? 'success' : 'error'"
                :icon="item.is_correct ? 'mdi-check-circle' : 'mdi-close-circle'"
              ></v-icon>
            </template>
            <template v-slot:item.instructional_prompt="{ item }">
              <div style="max-width: 300px;">
                <v-expansion-panels variant="accordion">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <div class="text-truncate" style="max-width: 250px;">
                        {{ item.instructional_prompt.substring(0, 50) }}{{ item.instructional_prompt.length > 50 ? '...' : '' }}
                      </div>
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <pre class="prompt-full-text">{{ item.instructional_prompt }}</pre>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
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

Chart.register(...registerables)

export default {
  name: 'EmailCategorizationResults',
  props: {
    resultData: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      accuracyChart: null,
      promptHeaders: [
        { title: 'Rank', key: 'rank', sortable: true },
        { title: 'Instructional Prompt', key: 'prompt', sortable: false },
        { title: 'Accuracy', key: 'accuracy', sortable: true },
        { title: 'Correct/Total', key: 'correct', sortable: true }
      ],
      emailHeaders: [
        { title: 'Email Subject', key: 'email_subject', sortable: true },
        { title: 'Expected Category', key: 'expected_category', sortable: true },
        { title: 'Predicted Category', key: 'predicted_category', sortable: true },
        { title: 'Correct', key: 'is_correct', sortable: true },
        { title: 'Instructional Prompt', key: 'instructional_prompt', sortable: true }
      ],
      categoryFilter: '',
      promptFilter: ''
    }
  },
  computed: {
    overallAccuracy() {
      if (!this.resultData || !this.resultData.metadata) return 0
      
      // Use metadata accuracy_percentage if available
      const accuracy = this.resultData.metadata.accuracy_percentage
      if (accuracy !== undefined && accuracy !== null) {
        return Number(accuracy)
      }
      
      // Calculate from prompt_evaluations
      if (this.resultData.prompt_evaluations && this.resultData.prompt_evaluations.length > 0) {
        const total = this.resultData.prompt_evaluations.length
        if (total === 0) return 0
        
        const correct = this.resultData.prompt_evaluations.filter(pe => {
          const evaluation = pe.evaluations?.[0]
          if (!evaluation) return false
          
          // Check multiple ways: metadata.is_correct, score === 10 (as number or string)
          const score = evaluation.score
          const isCorrectFlag = evaluation.metadata?.is_correct
          
          return isCorrectFlag === true ||
                 isCorrectFlag === 'true' ||
                 score === 10.0 ||
                 score === 10 ||
                 score === '10' ||
                 score === '10.0'
        }).length
        
        return total > 0 ? (correct / total) * 100 : 0
      }
      
      return 0
    },
    totalEmails() {
      if (!this.resultData || !this.resultData.metadata) return 0
      
      // Use metadata total_count if available
      const total = this.resultData.metadata.total_count
      if (total !== undefined && total !== null) {
        return Number(total)
      }
      
      // Fallback: Calculate from prompt_evaluations
      if (this.resultData.prompt_evaluations) {
        return this.resultData.prompt_evaluations.length
      }
      
      return 0
    },
    correctCount() {
      if (!this.resultData || !this.resultData.metadata) return 0
      
      // Use metadata correct_count if available
      const correct = this.resultData.metadata.correct_count
      if (correct !== undefined && correct !== null) {
        return Number(correct)
      }
      
      // Fallback: Calculate from prompt_evaluations
      if (this.resultData.prompt_evaluations) {
        return this.resultData.prompt_evaluations.filter(pe => {
          const evaluation = pe.evaluations?.[0]
          if (!evaluation) return false
          
          // Check score === 10 or metadata.is_correct === true
          return evaluation.score === 10 || 
                 evaluation.score === 10.0 ||
                 evaluation.metadata?.is_correct === true
        }).length
      }
      
      return 0
    },
    promptResults() {
      if (!this.resultData || !this.resultData.metadata) {
        // Fallback: try to extract from prompt_evaluations if metadata doesn't have all_prompt_results
        if (this.resultData?.prompt_evaluations) {
          const promptMap = new Map()
          
          this.resultData.prompt_evaluations.forEach(pe => {
            const evaluation = pe.evaluations?.[0]
            const metadata = evaluation?.metadata || {}
            const prompt = metadata.instructional_prompt || 'Default Prompt'
            
            if (!promptMap.has(prompt)) {
              promptMap.set(prompt, { correct: 0, total: 0 })
            }
            
            const stats = promptMap.get(prompt)
            stats.total++
            // Check multiple ways: metadata.is_correct, score === 10 (as number or string)
            const score = evaluation?.score
            const isCorrect = metadata.is_correct === true ||
                             metadata.is_correct === 'true' ||
                             score === 10.0 ||
                             score === 10 ||
                             score === '10' ||
                             score === '10.0'
            if (isCorrect) {
              stats.correct++
            }
          })
          
          const results = Array.from(promptMap.entries()).map(([prompt, stats]) => ({
            prompt,
            accuracy: stats.total > 0 ? (stats.correct / stats.total) * 100 : 0,
            correct: stats.correct,
            total: stats.total,
            isBest: false
          }))
          
          results.sort((a, b) => b.accuracy - a.accuracy)
          if (results.length > 0) {
            results[0].isBest = true
          }
          results.forEach((result, index) => {
            result.rank = index + 1
          })
          
          return results
        }
        return []
      }
      
      const allPrompts = this.resultData.metadata.all_prompt_results || {}
      const bestPrompt = this.resultData.metadata.best_prompt
      
      // Get total count from metadata (should be same for all prompts)
      // Use total_count from metadata, or fall back to prompt_evaluations length
      const totalEmails = this.resultData.metadata.total_count || 
                         this.resultData.prompt_evaluations?.length || 
                         100 // Default fallback
      
      // Convert to array and add rank
      const results = Object.entries(allPrompts).map(([prompt, accuracy]) => {
        const accuracyNum = Number(accuracy)
        
        // Calculate correct count from accuracy percentage
        // accuracy is already a percentage (e.g., 68 means 68%)
        const correct = Math.round((accuracyNum / 100) * totalEmails)
        
        // For the best prompt, try to get actual counts from prompt_evaluations if available
        let finalCorrect = correct
        let finalTotal = totalEmails
        
        if (prompt === bestPrompt && this.resultData.prompt_evaluations) {
          // This is the best prompt, so prompt_evaluations should contain its results
          const promptEvals = this.resultData.prompt_evaluations.filter(pe => {
            const evalMetadata = pe.evaluations?.[0]?.metadata || {}
            const evalPrompt = evalMetadata.instructional_prompt
            // Match exact prompt or check if it's contained in the prompt_evaluation prompt
            return evalPrompt === prompt || 
                   (pe.prompt && pe.prompt.startsWith(prompt))
          })
          
          if (promptEvals.length > 0) {
            finalTotal = promptEvals.length
            finalCorrect = promptEvals.filter(pe => {
              const evaluation = pe.evaluations?.[0]
              if (!evaluation) return false
              
              // Check score === 10 or metadata.is_correct === true
              return evaluation.score === 10 || 
                     evaluation.score === 10.0 ||
                     evaluation.metadata?.is_correct === true
            }).length
          }
        }
        
        return {
          prompt,
          accuracy: accuracyNum,
          correct: finalCorrect,
          total: finalTotal,
          isBest: prompt === bestPrompt
        }
      })
      
      // Sort by accuracy descending and add rank
      results.sort((a, b) => b.accuracy - a.accuracy)
      results.forEach((result, index) => {
        result.rank = index + 1
      })
      
      return results
    },
    bestPrompt() {
      return this.promptResults.find(p => p.isBest) || this.promptResults[0]
    },
    emailDetails() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return []
      
      console.log('Total prompt_evaluations:', this.resultData.prompt_evaluations.length)
      console.log('all_prompt_results keys:', Object.keys(this.resultData.metadata?.all_prompt_results || {}))
      
      // Don't group - show all email evaluations with their instructional prompts
      const details = this.resultData.prompt_evaluations.map(pe => {
        const evaluation = pe.evaluations?.[0]
        const metadata = evaluation?.metadata || {}
        
        // Extract email subject from prompt (it's after the instructional prompt)
        const promptLines = pe.prompt?.split('\n') || []
        let emailSubject = 'N/A'
        
        // Find the Subject line (it comes after the instructional prompt)
        for (let i = 0; i < promptLines.length; i++) {
          if (promptLines[i].startsWith('Subject:')) {
            emailSubject = promptLines[i].replace('Subject:', '').trim()
            break
          }
        }
        
        // Get instructional prompt - prioritize metadata, then normalize against all_prompt_results
        // This ensures we use the exact prompt text from all_prompt_results for consistent filtering
        const allPrompts = this.resultData.metadata?.all_prompt_results || {}
        let instructionalPrompt = null
        
        // Priority 1: Use instructional_prompt from evaluation metadata
        if (metadata.instructional_prompt && metadata.instructional_prompt !== 'N/A') {
          const metadataPrompt = metadata.instructional_prompt
          // Try to find exact or close match in all_prompt_results
          for (const [prompt, _] of Object.entries(allPrompts)) {
            // Exact match
            if (prompt === metadataPrompt) {
              instructionalPrompt = prompt
              break
            }
            // Trimmed match (handle whitespace differences)
            if (prompt.trim() === metadataPrompt.trim()) {
              instructionalPrompt = prompt
              break
            }
            // One contains the other (for partial matches)
            if (prompt.includes(metadataPrompt) || metadataPrompt.includes(prompt)) {
              instructionalPrompt = prompt
              break
            }
          }
          // If no match found in all_prompt_results, use metadata prompt as-is
          if (!instructionalPrompt) {
            instructionalPrompt = metadataPrompt
          }
        }
        
        // Priority 2: Try to match full prompt against all_prompt_results
        if (!instructionalPrompt) {
          const fullPrompt = pe.prompt || ''
          let bestMatch = null
          let bestMatchLength = 0
          
          for (const [prompt, _] of Object.entries(allPrompts)) {
            const trimmedPrompt = prompt.trim()
            // Check if the full prompt starts with this instructional prompt
            // Handle different separators (newline, double newline, etc.)
            if (fullPrompt.startsWith(trimmedPrompt) || 
                fullPrompt.startsWith(trimmedPrompt + '\n') ||
                fullPrompt.startsWith(trimmedPrompt + '\n\n') ||
                fullPrompt.startsWith(trimmedPrompt + ' ')) {
              // Use the longest matching prompt (most specific)
              if (trimmedPrompt.length > bestMatchLength) {
                bestMatch = prompt
                bestMatchLength = trimmedPrompt.length
              }
            }
          }
          
          if (bestMatch) {
            instructionalPrompt = bestMatch
          }
        }
        
        // Priority 3: Extract from prompt text (everything before "Subject:")
        if (!instructionalPrompt) {
          const subjectIndex = promptLines.findIndex(line => line.startsWith('Subject:'))
          if (subjectIndex > 0) {
            const extracted = promptLines.slice(0, subjectIndex).join('\n').trim()
            // Try to match extracted prompt against all_prompt_results
            for (const [prompt, _] of Object.entries(allPrompts)) {
              if (extracted === prompt.trim() || 
                  prompt.trim().startsWith(extracted) || 
                  extracted.startsWith(prompt.trim())) {
                instructionalPrompt = prompt
                break
              }
            }
            // If no match found, use extracted as fallback
            if (!instructionalPrompt) {
              instructionalPrompt = extracted
            }
          }
        }
        
        // Priority 4: Last resort - use result metadata
        if (!instructionalPrompt) {
          instructionalPrompt = this.resultData.metadata?.instructional_prompt || 'N/A'
        }
        
        // Final fallback
        if (!instructionalPrompt || instructionalPrompt === '') {
          instructionalPrompt = 'N/A'
        }
        
        return {
          email_subject: metadata.email_subject || emailSubject,
          expected_category: metadata.expected_category || 'N/A',
          predicted_category: metadata.predicted_category || 'N/A',
          is_correct: metadata.is_correct || false,
          instructional_prompt: instructionalPrompt || 'N/A'
        }
      })
      
      // Debug: count prompts
      const promptCounts = {}
      details.forEach(d => {
        const prompt = d.instructional_prompt
        promptCounts[prompt] = (promptCounts[prompt] || 0) + 1
      })
      console.log('Email details by prompt:', promptCounts)
      console.log('Total email details:', details.length)
      
      return details
    },
    categoryOptions() {
      const categories = [...new Set(this.emailDetails.map(e => e.expected_category).filter(Boolean))]
      return categories.sort()
    },
    promptOptions() {
      // Get prompts from emailDetails (actual evaluations)
      const promptsFromDetails = [...new Set(this.emailDetails.map(e => e.instructional_prompt).filter(p => p !== 'N/A'))]
      
      // Also get prompts from all_prompt_results (all prompts that were tested)
      const allPrompts = this.resultData?.metadata?.all_prompt_results || {}
      const promptsFromMetadata = Object.keys(allPrompts).filter(p => p && p !== 'N/A')
      
      // Combine and deduplicate
      const allPromptsSet = new Set([...promptsFromDetails, ...promptsFromMetadata])
      return Array.from(allPromptsSet).sort()
    },
    filteredEmailDetails() {
      let filtered = this.emailDetails
      
      if (this.categoryFilter) {
        filtered = filtered.filter(e => e.expected_category === this.categoryFilter)
      }
      
      if (this.promptFilter) {
        // Filter by instructional prompt - use exact match with the prompt from all_prompt_results
        filtered = filtered.filter(e => {
          const prompt = e.instructional_prompt
          if (!prompt || prompt === 'N/A') return false
          
          // Exact match (should work since we use prompts from all_prompt_results)
          // Also handle trimmed comparison for safety
          return prompt === this.promptFilter || prompt.trim() === this.promptFilter.trim()
        })
      }
      
      return filtered
    }
  },
  mounted() {
    this.renderChart()
  },
  watch: {
    promptResults() {
      this.$nextTick(() => {
        this.renderChart()
      })
    }
  },
  methods: {
    getAccuracyColor(accuracy) {
      if (accuracy >= 90) return 'success'
      if (accuracy >= 70) return 'info'
      if (accuracy >= 50) return 'warning'
      return 'error'
    },
    renderChart() {
      if (!this.$refs.accuracyChart || this.promptResults.length <= 1) return
      
      if (this.accuracyChart) {
        this.accuracyChart.destroy()
      }
      
      const ctx = this.$refs.accuracyChart.getContext('2d')
      this.accuracyChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: this.promptResults.map((p, i) => `Prompt ${i + 1}`),
          datasets: [{
            label: 'Accuracy (%)',
            data: this.promptResults.map(p => p.accuracy),
            backgroundColor: this.promptResults.map(p => 
              p.isBest ? 'rgba(76, 175, 80, 0.8)' : 'rgba(33, 150, 243, 0.6)'
            ),
            borderColor: this.promptResults.map(p => 
              p.isBest ? 'rgba(76, 175, 80, 1)' : 'rgba(33, 150, 243, 1)'
            ),
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: {
                callback: function(value) {
                  return value + '%'
                }
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
                  const index = context.dataIndex
                  const prompt = this.promptResults[index]
                  return `Accuracy: ${prompt.accuracy.toFixed(1)}% (${prompt.correct}/${prompt.total})`
                }.bind(this)
              }
            }
          }
        }
      })
    }
  },
  beforeUnmount() {
    if (this.accuracyChart) {
      this.accuracyChart.destroy()
    }
  }
}
</script>

<style scoped>
.prompt-text {
  max-width: 600px;
}

.prompt-full-text {
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
  max-height: 300px;
  overflow-y: auto;
}
</style>

