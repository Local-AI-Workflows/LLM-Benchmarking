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

      <!-- Best Prompts Highlight -->
      <v-card v-if="bestPrompts.length > 0" color="success" variant="tonal" class="mb-4">
        <v-card-title>
          <v-icon icon="mdi-trophy" class="mr-2"></v-icon>
          Best Performing Prompt{{ bestPrompts.length > 1 ? 's' : '' }}
        </v-card-title>
        <v-card-text>
          <v-chip color="success" size="large" class="mb-3">
            Accuracy: {{ bestPrompts[0].accuracy.toFixed(1) }}%
          </v-chip>
          <div v-for="(prompt, index) in bestPrompts" :key="index" class="mt-3">
            <div v-if="bestPrompts.length > 1" class="mb-2">
              <v-chip color="success" size="small" variant="flat" class="mr-2">
                Prompt {{ index + 1 }}
              </v-chip>
            </div>
            <div class="mt-2">
              <strong>Prompt{{ bestPrompts.length > 1 ? ` ${index + 1}` : '' }}:</strong>
              <pre class="prompt-full-text mt-2">{{ prompt.prompt }}</pre>
            </div>
            <v-divider v-if="index < bestPrompts.length - 1" class="my-3"></v-divider>
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

      <!-- Performance by Prompt and Category -->
      <v-card class="mb-4">
        <v-card-title>
          <v-icon icon="mdi-chart-box" class="mr-2"></v-icon>
          Performance by Prompt and Category
        </v-card-title>
        <v-card-text>
          <div style="height: 400px; position: relative;">
            <canvas ref="promptCategoryChart"></canvas>
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
          <!-- Dynamic Filters -->
          <div class="mb-3">
            <div class="d-flex align-center mb-2">
              <v-icon icon="mdi-filter" class="mr-2"></v-icon>
              <span class="text-subtitle-1">Filters</span>
              <v-spacer></v-spacer>
              <v-menu>
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    color="primary"
                    size="small"
                    variant="outlined"
                  >
                    <v-icon start icon="mdi-plus"></v-icon>
                    Add Filter
                  </v-btn>
                </template>
                <v-list>
                  <v-list-item
                    v-if="!activeFilters.includes('category')"
                    @click="addFilter('category')"
                  >
                    <v-list-item-title>
                      <v-icon icon="mdi-tag" class="mr-2"></v-icon>
                      Filter by Category
                    </v-list-item-title>
                  </v-list-item>
                  <v-list-item
                    v-if="!activeFilters.includes('prompt')"
                    @click="addFilter('prompt')"
                  >
                    <v-list-item-title>
                      <v-icon icon="mdi-text" class="mr-2"></v-icon>
                      Filter by Prompt
                    </v-list-item-title>
                  </v-list-item>
                  <v-list-item
                    v-if="!activeFilters.includes('correctness')"
                    @click="addFilter('correctness')"
                  >
                    <v-list-item-title>
                      <v-icon icon="mdi-check-circle" class="mr-2"></v-icon>
                      Filter by Correctness
                    </v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </div>
            
            <!-- Active Filters -->
            <v-row v-if="activeFilters.length > 0" class="mb-2">
              <v-col
                v-for="filterType in activeFilters"
                :key="filterType"
                cols="12"
                :md="activeFilters.length === 1 ? 12 : activeFilters.length === 2 ? 6 : 4"
              >
                <v-card variant="outlined" class="pa-2">
                  <div class="d-flex align-center">
                    <v-select
                      v-if="filterType === 'category'"
                      v-model="categoryFilter"
                      :items="categoryOptions"
                      label="Category"
                      clearable
                      variant="outlined"
                      density="compact"
                      hide-details
                      prepend-inner-icon="mdi-tag"
                      class="flex-grow-1"
                    ></v-select>
                    <v-select
                      v-else-if="filterType === 'prompt'"
                      v-model="promptFilter"
                      :items="promptOptions"
                      item-title="title"
                      item-value="value"
                      label="Instructional Prompt"
                      clearable
                      variant="outlined"
                      density="compact"
                      hide-details
                      prepend-inner-icon="mdi-text"
                      class="flex-grow-1"
                    >
                      <template v-slot:item="{ props, item }">
                        <v-tooltip location="right" max-width="500">
                          <template v-slot:activator="{ props: tooltipProps }">
                            <v-list-item v-bind="props" v-on="tooltipProps">
                              <template v-slot:title>
                                {{ item.raw.title }}
                              </template>
                            </v-list-item>
                          </template>
                          <pre class="prompt-full-text" style="max-height: 200px; overflow-y: auto;">{{ item.raw.value }}</pre>
                        </v-tooltip>
                      </template>
                    </v-select>
                    <v-select
                      v-else-if="filterType === 'correctness'"
                      v-model="correctnessFilter"
                      :items="correctnessOptions"
                      label="Correctness"
                      clearable
                      variant="outlined"
                      density="compact"
                      hide-details
                      prepend-inner-icon="mdi-check-circle"
                      class="flex-grow-1"
                    ></v-select>
                    <v-btn
                      @click="removeFilter(filterType)"
                      icon="mdi-close"
                      size="small"
                      variant="text"
                      color="error"
                      class="ml-2"
                    ></v-btn>
                  </div>
                </v-card>
              </v-col>
            </v-row>
          </div>
          
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
              <v-tooltip location="right" max-width="500">
                <template v-slot:activator="{ props }">
                  <div v-bind="props" style="max-width: 300px;">
                    <v-chip
                      size="small"
                      color="primary"
                      variant="outlined"
                    >
                      {{ getPromptNumber(item.instructional_prompt) ? `Prompt ${getPromptNumber(item.instructional_prompt)}` : 'N/A' }}
                    </v-chip>
                  </div>
                </template>
                <v-card v-if="item.instructional_prompt && item.instructional_prompt !== 'N/A'">
                  <v-card-title class="text-subtitle-1 pa-2">
                    <v-icon icon="mdi-text" class="mr-2"></v-icon>
                    Instructional Prompt
                  </v-card-title>
                  <v-card-text class="pa-2">
                    <pre class="prompt-full-text" style="max-height: 300px; overflow-y: auto;">{{ item.instructional_prompt }}</pre>
                  </v-card-text>
                </v-card>
              </v-tooltip>
            </template>
            <template v-slot:item.details="{ item }">
              <v-tooltip location="left" max-width="600">
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    icon="mdi-information-outline"
                    size="small"
                    variant="text"
                    color="primary"
                  ></v-btn>
                </template>
                <v-card>
                  <v-card-title class="text-subtitle-1 pa-3">
                    <v-icon icon="mdi-email" class="mr-2"></v-icon>
                    Complete Email
                  </v-card-title>
                  <v-card-text>
                    <pre class="email-full-content">{{ item.full_email_content }}</pre>
                  </v-card-text>
                </v-card>
              </v-tooltip>
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
      promptCategoryChart: null,
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
        { title: 'Instructional Prompt', key: 'instructional_prompt', sortable: true },
        { title: 'Details', key: 'details', sortable: false, width: '80px' }
      ],
      promptCategoryHeaders: [
        { title: 'Instructional Prompt', key: 'instructional_prompt', sortable: true },
        { title: 'Expected Category', key: 'expected_category', sortable: true },
        { title: 'Accuracy', key: 'accuracy', sortable: true },
        { title: 'Correct/Total', key: 'correct', sortable: true }
      ],
      categoryFilter: '',
      promptFilter: '',
      correctnessFilter: '',
      activeFilters: []
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
          
          // Find the best accuracy and mark all prompts with that accuracy
          const bestAccuracy = results.length > 0 ? results[0].accuracy : 0
          results.forEach((result, index) => {
            result.rank = index + 1
            result.isBest = result.accuracy === bestAccuracy
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
          isBest: false // Will be set after sorting
        }
      })
      
      // Sort by accuracy descending and add rank
      results.sort((a, b) => b.accuracy - a.accuracy)
      
      // Find the best accuracy (highest)
      const bestAccuracy = results.length > 0 ? results[0].accuracy : 0
      
      // Mark all prompts with best accuracy as isBest
      results.forEach((result, index) => {
        result.rank = index + 1
        result.isBest = result.accuracy === bestAccuracy
      })
      
      return results
    },
    bestPrompt() {
      // Return the first best prompt (for backward compatibility)
      return this.bestPrompts[0] || this.promptResults[0]
    },
    bestPrompts() {
      // Return all prompts with the best accuracy
      if (!this.promptResults || this.promptResults.length === 0) return []
      
      // Find the highest accuracy
      const maxAccuracy = Math.max(...this.promptResults.map(p => p.accuracy))
      
      // Return all prompts with that accuracy
      return this.promptResults.filter(p => p.accuracy === maxAccuracy)
    },
    emailDetails() {
      if (!this.resultData || !this.resultData.prompt_evaluations) return []
      
      console.log('Total prompt_evaluations:', this.resultData.prompt_evaluations.length)
      console.log('all_prompt_results keys:', Object.keys(this.resultData.metadata?.all_prompt_results || {}))
      
      // Don't group - show all email evaluations with their instructional prompts
      const details = this.resultData.prompt_evaluations.map(pe => {
        const evaluation = pe.evaluations?.[0]
        const metadata = evaluation?.metadata || {}
        
        // Extract email content from prompt (it's after the instructional prompt)
        const promptLines = pe.prompt?.split('\n') || []
        let emailSubject = 'N/A'
        let fullEmailContent = ''
        
        // Find the Subject line (it comes after the instructional prompt)
        let subjectIndex = -1
        for (let i = 0; i < promptLines.length; i++) {
          if (promptLines[i].startsWith('Subject:')) {
            emailSubject = promptLines[i].replace('Subject:', '').trim()
            subjectIndex = i
            break
          }
        }
        
        // Extract full email content (everything after the instructional prompt)
        // The email starts after the instructional prompt, which we need to identify
        const fullPrompt = pe.prompt || ''
        const allPrompts = this.resultData.metadata?.all_prompt_results || {}
        
        // Find where the email content starts (after the instructional prompt)
        let emailStartIndex = 0
        for (const [prompt, _] of Object.entries(allPrompts)) {
          const trimmedPrompt = prompt.trim()
          if (fullPrompt.startsWith(trimmedPrompt) || 
              fullPrompt.startsWith(trimmedPrompt + '\n') ||
              fullPrompt.startsWith(trimmedPrompt + '\n\n')) {
            emailStartIndex = trimmedPrompt.length
            // Skip newlines after the prompt
            while (emailStartIndex < fullPrompt.length && 
                   (fullPrompt[emailStartIndex] === '\n' || fullPrompt[emailStartIndex] === ' ')) {
              emailStartIndex++
            }
            break
          }
        }
        
        // If we found the start, extract the email content
        if (emailStartIndex > 0 && emailStartIndex < fullPrompt.length) {
          fullEmailContent = fullPrompt.substring(emailStartIndex).trim()
        } else if (subjectIndex > 0) {
          // Fallback: extract from subject line onwards
          fullEmailContent = promptLines.slice(subjectIndex).join('\n')
        } else {
          // Last resort: use the full prompt (though this shouldn't happen)
          fullEmailContent = fullPrompt
        }
        
        // Get instructional prompt - prioritize metadata, then normalize against all_prompt_results
        // This ensures we use the exact prompt text from all_prompt_results for consistent filtering
        // Reuse allPrompts declared above
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
          instructional_prompt: instructionalPrompt || 'N/A',
          full_email_content: fullEmailContent || pe.prompt || 'N/A'
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
      const sortedPrompts = Array.from(allPromptsSet).sort()
      
      // Return as items with title (Prompt N) and value (actual prompt)
      return sortedPrompts.map((prompt, index) => ({
        title: `Prompt ${index + 1}`,
        value: prompt
      }))
    },
    promptNumberMap() {
      // Create a map from prompt text to prompt number
      const allPrompts = this.resultData?.metadata?.all_prompt_results || {}
      const promptsFromMetadata = Object.keys(allPrompts).filter(p => p && p !== 'N/A')
      const sortedPrompts = promptsFromMetadata.sort()
      
      const map = {}
      sortedPrompts.forEach((prompt, index) => {
        if (prompt && typeof prompt === 'string') {
          map[prompt] = index + 1
        }
      })
      return map
    },
    correctnessOptions() {
      return [
        { title: 'Correct', value: 'correct' },
        { title: 'Incorrect', value: 'incorrect' }
      ]
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
      
      if (this.correctnessFilter) {
        if (this.correctnessFilter === 'correct') {
          filtered = filtered.filter(e => e.is_correct === true)
        } else if (this.correctnessFilter === 'incorrect') {
          filtered = filtered.filter(e => e.is_correct === false)
        }
      }
      
      return filtered
    },
    promptCategoryStats() {
      // Calculate statistics grouped by prompt and expected category
      if (!this.emailDetails || this.emailDetails.length === 0) return []
      
      // Group by prompt and category
      const statsMap = new Map()
      
      this.emailDetails.forEach(detail => {
        const prompt = detail.instructional_prompt || 'N/A'
        const category = detail.expected_category || 'N/A'
        const key = `${prompt}|||${category}`
        
        if (!statsMap.has(key)) {
          statsMap.set(key, {
            instructional_prompt: prompt,
            expected_category: category,
            correct: 0,
            total: 0
          })
        }
        
        const stats = statsMap.get(key)
        stats.total++
        if (detail.is_correct) {
          stats.correct++
        }
      })
      
      // Convert to array and calculate accuracy
      const stats = Array.from(statsMap.values()).map(item => ({
        ...item,
        accuracy: item.total > 0 ? (item.correct / item.total) * 100 : 0
      }))
      
      // Sort by prompt, then by category
      stats.sort((a, b) => {
        if (a.instructional_prompt !== b.instructional_prompt) {
          return a.instructional_prompt.localeCompare(b.instructional_prompt)
        }
        return a.expected_category.localeCompare(b.expected_category)
      })
      
      return stats
    }
  },
  mounted() {
    this.renderChart()
    this.renderPromptCategoryChart()
  },
  watch: {
    promptResults() {
      this.$nextTick(() => {
        this.renderChart()
      })
    },
    promptCategoryStats() {
      this.$nextTick(() => {
        this.renderPromptCategoryChart()
      })
    }
  },
  methods: {
    getPromptNumber(prompt) {
      if (!prompt || typeof prompt !== 'string') {
        return null
      }
      return this.promptNumberMap[prompt] || null
    },
    addFilter(filterType) {
      if (!this.activeFilters.includes(filterType)) {
        this.activeFilters.push(filterType)
      }
    },
    removeFilter(filterType) {
      const index = this.activeFilters.indexOf(filterType)
      if (index > -1) {
        this.activeFilters.splice(index, 1)
        // Clear the filter value when removing
        if (filterType === 'category') {
          this.categoryFilter = ''
        } else if (filterType === 'prompt') {
          this.promptFilter = ''
        } else if (filterType === 'correctness') {
          this.correctnessFilter = ''
        }
      }
    },
    getAccuracyColor(accuracy) {
      if (accuracy >= 90) return 'success'
      if (accuracy >= 70) return 'info'
      if (accuracy >= 50) return 'warning'
      return 'error'
    },
    renderPromptCategoryChart() {
      if (!this.$refs.promptCategoryChart || !this.promptCategoryStats || this.promptCategoryStats.length === 0) return
      
      if (this.promptCategoryChart) {
        this.promptCategoryChart.destroy()
      }
      
      // Group data by category, then by prompt
      const categories = [...new Set(this.promptCategoryStats.map(s => s.expected_category))].sort()
      const prompts = [...new Set(this.promptCategoryStats.map(s => s.instructional_prompt))].sort()
      
      // Create datasets for each prompt
      const colors = [
        'rgba(33, 150, 243, 0.8)',   // Blue
        'rgba(76, 175, 80, 0.8)',    // Green
        'rgba(255, 152, 0, 0.8)',    // Orange
        'rgba(156, 39, 176, 0.8)',   // Purple
        'rgba(244, 67, 54, 0.8)',    // Red
        'rgba(0, 188, 212, 0.8)'     // Cyan
      ]
      
      const datasets = prompts.map((prompt, promptIdx) => {
        const data = categories.map(category => {
          const stat = this.promptCategoryStats.find(s => 
            s.instructional_prompt === prompt && s.expected_category === category
          )
          return stat ? stat.accuracy : 0
        })
        
        // Truncate prompt name for label
        const promptLabel = prompt.length > 30 ? prompt.substring(0, 30) + '...' : prompt
        
        return {
          label: `Prompt ${promptIdx + 1}`,
          data: data,
          backgroundColor: colors[promptIdx % colors.length],
          borderColor: colors[promptIdx % colors.length].replace('0.8', '1'),
          borderWidth: 2
        }
      })
      
      const ctx = this.$refs.promptCategoryChart.getContext('2d')
      this.promptCategoryChart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: categories,
          datasets: datasets
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'top'
            },
            tooltip: {
              callbacks: {
                afterLabel: (context) => {
                  const category = categories[context.dataIndex]
                  const prompt = prompts[context.datasetIndex]
                  const stat = this.promptCategoryStats.find(s => 
                    s.instructional_prompt === prompt && s.expected_category === category
                  )
                  if (stat) {
                    return `Correct: ${stat.correct}/${stat.total}`
                  }
                  return ''
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              title: {
                display: true,
                text: 'Accuracy (%)'
              }
            },
            x: {
              title: {
                display: true,
                text: 'Expected Category'
              }
            }
          }
        }
      })
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

.email-full-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: monospace;
  font-size: 0.85em;
  line-height: 1.5;
  margin: 0;
  max-height: 400px;
  overflow-y: auto;
}
</style>

