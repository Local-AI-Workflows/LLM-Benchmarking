"""
HTML Dashboard Generator for LLM benchmarking results.

This module generates static HTML dashboards with interactive charts
and detailed analysis of benchmark results.
"""

import json
import os
from typing import Dict, Any, List
from datetime import datetime
from jinja2 import Template
from .data_processor import DashboardDataProcessor


class HTMLDashboardGenerator:
    """Generates static HTML dashboards for benchmark results."""
    
    def __init__(self, data_processor: DashboardDataProcessor):
        """
        Initialize the HTML dashboard generator.
        
        Args:
            data_processor: Processed benchmark data
        """
        self.data_processor = data_processor
        self.processed_data = data_processor.processed_data
    
    def generate_dashboard(self, output_path: str = "results/dashboard.html") -> str:
        """
        Generate a complete HTML dashboard.
        
        Args:
            output_path: Path where to save the HTML dashboard
            
        Returns:
            Path to the generated HTML file
        """
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Generate the HTML content
        html_content = self._generate_html()
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def _generate_html(self) -> str:
        """Generate the complete HTML dashboard content."""
        template = Template(self._get_html_template())
        
        return template.render(
            data=self.processed_data,
            data_json=json.dumps(self.processed_data, default=str),
            generation_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            title=f"LLM Benchmark Dashboard - {self.processed_data['overview']['model_name']}"
        )
    
    def _get_html_template(self) -> str:
        """Get the HTML template for the dashboard."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    
    <!-- External Libraries -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    
    <style>
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
        }
        .radar-chart {
            height: 500px;
        }
        .heatmap-container {
            height: 600px;
        }
        .score-excellent { background-color: #10b981; }
        .score-good { background-color: #3b82f6; }
        .score-fair { background-color: #f59e0b; }
        .score-poor { background-color: #ef4444; }
        .difficulty-easy { color: #10b981; }
        .difficulty-medium { color: #f59e0b; }
        .difficulty-hard { color: #ef4444; }
        .difficulty-very-hard { color: #7c2d12; }
        
        /* Custom scrollbar */
        .custom-scrollbar::-webkit-scrollbar {
            width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
            background: #f1f5f9;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
            background: #94a3b8;
        }
        
        /* Tab styling */
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .tab-button.active {
            background-color: #3b82f6;
            color: white;
        }
    </style>
</head>
<body class="bg-gray-50 font-sans">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold text-gray-900">LLM Benchmark Dashboard</h1>
                    <p class="text-gray-600">Model: <span class="font-semibold">{{ data.overview.model_name }}</span></p>
                </div>
                <div class="text-right text-sm text-gray-500">
                    <p>Generated: {{ generation_time }}</p>
                    <p>{{ data.overview.num_questions }} questions • {{ data.overview.num_metrics }} metrics • {{ data.overview.num_evaluators }} evaluators</p>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        <!-- Overview Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="bg-yellow-500 p-3 rounded-lg flex items-center">
                <span class="text-white font-bold text-sm">⭐</span>
                <div class="ml-3 text-white">
                    <div class="font-semibold">Overall Score</div>
                    <div class="text-2xl font-bold">{{ "%.1f"|format(data.overview.overall_score) }}/10</div>
                </div>
            </div>
            
            <div class="bg-blue-500 p-3 rounded-lg flex items-center">
                <span class="text-white font-bold text-sm">📊</span>
                <div class="ml-3 text-white">
                    <div class="font-semibold">Total Questions</div>
                    <div class="text-2xl font-bold">{{ data.overview.num_questions }}</div>
                </div>
            </div>
            
            <div class="bg-green-500 p-3 rounded-lg flex items-center">
                <span class="text-white font-bold text-sm">🤖</span>
                <div class="ml-3 text-white">
                    <div class="font-semibold">Model Used</div>
                    <div class="text-lg font-bold">{{ data.overview.model_name }}</div>
                </div>
            </div>
            
            <div class="bg-purple-500 p-3 rounded-lg flex items-center">
                <span class="text-white font-bold text-sm">📏</span>
                <div class="ml-3 text-white">
                    <div class="font-semibold">Metrics</div>
                    <div class="text-2xl font-bold">{{ data.overview.num_metrics }}</div>
                </div>
            </div>
            
            <div class="bg-orange-500 p-3 rounded-lg flex items-center">
                <span class="text-white font-bold text-sm">👥</span>
                <div class="ml-3 text-white">
                    <div class="font-semibold">Evaluators</div>
                    <div class="text-2xl font-bold">{{ data.evaluators|length }}</div>
                </div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <div class="bg-white rounded-lg shadow mb-8">
            <div class="border-b border-gray-200">
                <nav class="-mb-px flex space-x-8 px-6">
                    <button class="tab-button active py-4 px-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300" onclick="showTab('overview')">
                        Overview
                    </button>
                    <button class="tab-button py-4 px-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300" onclick="showTab('metrics')">
                        Metrics Analysis
                    </button>
                    <button class="tab-button py-4 px-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300" onclick="showTab('questions')">
                        Questions Analysis
                    </button>
                    <button class="tab-button py-4 px-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300" onclick="showTab('evaluators')">
                        Evaluators Analysis
                    </button>
                    <button class="tab-button py-4 px-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300" onclick="showTab('detailed')">
                        Detailed View
                    </button>
                </nav>
            </div>

            <!-- Tab Contents -->
            
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">Performance Overview</h2>
                
                <!-- Metrics Bar Chart - Full Width -->
                <div class="bg-gray-50 rounded-lg p-6 mb-8">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Average Scores by Metric</h3>
                    <div class="chart-container">
                        <canvas id="metricsBarChart"></canvas>
                    </div>
                </div>
                
                <!-- Score Distribution -->
                {% if data.overview.score_distribution %}
                <div class="bg-gray-50 rounded-lg p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Score Distribution</h3>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-gray-900">{{ "%.1f"|format(data.overview.score_distribution.min) }}</div>
                            <div class="text-sm text-gray-500">Minimum</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-gray-900">{{ "%.1f"|format(data.overview.score_distribution.median) }}</div>
                            <div class="text-sm text-gray-500">Median</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-gray-900">{{ "%.1f"|format(data.overview.score_distribution.max) }}</div>
                            <div class="text-sm text-gray-500">Maximum</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-gray-900">{{ "%.2f"|format(data.overview.score_distribution.std_dev) }}</div>
                            <div class="text-sm text-gray-500">Std Dev</div>
                        </div>
                    </div>
                </div>
                {% endif %}
            </div>

            <!-- Metrics Tab -->
            <div id="metrics" class="tab-content p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">Metrics Analysis</h2>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                    <!-- Correlation Matrix -->
                    <div class="bg-gray-50 rounded-lg p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Metric Correlations</h3>
                        <div class="heatmap-container">
                            <div id="correlationHeatmap"></div>
                        </div>
                    </div>
                    
                    <!-- Metrics Summary Table -->
                    <div class="bg-gray-50 rounded-lg p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Metrics Summary</h3>
                        <div class="overflow-x-auto">
                            <table class="min-w-full divide-y divide-gray-200">
                                <thead class="bg-gray-50">
                                    <tr>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Metric</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Min</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Max</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Std</th>
                                    </tr>
                                </thead>
                                <tbody class="bg-white divide-y divide-gray-200">
                                    {% for metric in data.metrics %}
                                    <tr>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ metric.name }}</td>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ "%.1f"|format(metric.average_score) }}</td>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ "%.1f"|format(metric.min_score) }}</td>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ "%.1f"|format(metric.max_score) }}</td>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ "%.2f"|format(metric.std_dev) }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Questions Tab -->
            <div id="questions" class="tab-content p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">Questions Analysis</h2>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                    <!-- Question Difficulty Chart -->
                    <div class="bg-gray-50 rounded-lg p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Question Difficulty</h3>
                        <div class="chart-container">
                            <canvas id="difficultyChart"></canvas>
                        </div>
                    </div>
                    
                    <!-- Per-Question Heatmap -->
                    <div class="bg-gray-50 rounded-lg p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Scores by Question & Evaluator</h3>
                        <div class="heatmap-container">
                            <div id="questionHeatmap"></div>
                        </div>
                    </div>
                </div>
                
                <!-- Questions Table -->
                <div class="bg-gray-50 rounded-lg p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Questions Details</h3>
                    <div class="overflow-x-auto custom-scrollbar" style="max-height: 600px;">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50 sticky top-0">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Question</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Difficulty</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Score</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                {% for question in data.questions %}
                                <tr>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Q{{ question.id }}</td>
                                    <td class="px-6 py-4 text-sm text-gray-900" style="max-width: 300px;">
                                        <div class="truncate" title="{{ question.full_text }}">{{ question.text }}</div>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                                        <span class="difficulty-{{ question.difficulty.lower().replace(' ', '-') }} font-medium">{{ question.difficulty }}</span>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ "%.1f"|format(question.average_score) }}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                                        <button onclick="showQuestionDetail({{ question.id }})" class="text-blue-600 hover:text-blue-800">View Details</button>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Evaluators Tab -->
            <div id="evaluators" class="tab-content p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">Evaluators Analysis</h2>
                
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
                    <!-- Evaluator Performance Chart -->
                    <div class="bg-gray-50 rounded-lg p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Evaluator Performance</h3>
                        <div class="chart-container">
                            <canvas id="evaluatorChart"></canvas>
                        </div>
                    </div>
                    
                    <!-- Agreement Analysis -->
                    <div class="bg-gray-50 rounded-lg p-6">
                        <h3 class="text-lg font-semibold text-gray-900 mb-4">Evaluator Agreement</h3>
                        <div class="chart-container">
                            <canvas id="agreementChart"></canvas>
                        </div>
                    </div>
                </div>
                
                <!-- Evaluators Table -->
                <div class="bg-gray-50 rounded-lg p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">Evaluator Details</h3>
                    <div class="overflow-x-auto">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Evaluator</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Score</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Evaluations</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Std Dev</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Range</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                {% for evaluator in data.evaluators %}
                                <tr>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ evaluator.name }}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ "%.1f"|format(evaluator.average_score) }}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ evaluator.total_evaluations }}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ "%.2f"|format(evaluator.std_dev) }}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ "%.1f"|format(evaluator.min_score) }} - {{ "%.1f"|format(evaluator.max_score) }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Detailed View Tab -->
            <div id="detailed" class="tab-content p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-6">Detailed Raw Data</h2>
                
                <!-- Raw Scores Table -->
                <div class="bg-gray-50 rounded-lg p-6">
                    <h3 class="text-lg font-semibold text-gray-900 mb-4">All Evaluations</h3>
                    <div class="overflow-x-auto custom-scrollbar" style="max-height: 800px;">
                        <table class="min-w-full divide-y divide-gray-200">
                            <thead class="bg-gray-50 sticky top-0">
                                <tr>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Q#</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider" style="min-width: 300px;">Question</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Metric</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Evaluator</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider" style="min-width: 400px;">Rationale</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white divide-y divide-gray-200">
                                {% for score in data.raw_scores %}
                                <tr>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{{ score.question_id }}</td>
                                    <td class="px-6 py-4 text-sm text-gray-900" style="max-width: 300px; word-wrap: break-word; white-space: normal;">
                                        <div class="expandable-text" onclick="toggleText(this)">
                                            <span class="short-text">{{ score.question_text[:100] }}{% if score.question_text|length > 100 %}...{% endif %}</span>
                                            <span class="full-text" style="display: none;">{{ score.question_text }}</span>
                                            {% if score.question_text|length > 100 %}
                                            <button class="text-blue-600 hover:text-blue-800 ml-2 text-xs">Show More</button>
                                            {% endif %}
                                        </div>
                                    </td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ score.metric }}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ score.evaluator }}</td>
                                    <td class="px-6 py-4 whitespace-nowrap text-sm">
                                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                                            {% if score.score >= 9 %}bg-green-100 text-green-800
                                            {% elif score.score >= 7 %}bg-blue-100 text-blue-800
                                            {% elif score.score >= 5 %}bg-yellow-100 text-yellow-800
                                            {% else %}bg-red-100 text-red-800{% endif %}">
                                            {{ "%.1f"|format(score.score) }}
                                        </span>
                                    </td>
                                    <td class="px-6 py-4 text-sm text-gray-900" style="max-width: 400px; word-wrap: break-word; white-space: normal;">
                                        <div class="expandable-text" onclick="toggleText(this)">
                                            <span class="short-text">{{ score.rationale[:150] }}{% if score.rationale|length > 150 %}...{% endif %}</span>
                                            <span class="full-text" style="display: none;">{{ score.rationale }}</span>
                                            {% if score.rationale|length > 150 %}
                                            <button class="text-blue-600 hover:text-blue-800 ml-2 text-xs">Show More</button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- Question Detail Modal -->
    <div id="questionModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 hidden z-50">
        <div class="flex items-center justify-center min-h-screen px-4">
            <div class="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-screen overflow-y-auto">
                <div class="px-6 py-4 border-b border-gray-200">
                    <div class="flex justify-between items-center">
                        <h3 class="text-lg font-medium text-gray-900" id="modalTitle">Question Details</h3>
                        <button onclick="closeQuestionModal()" class="text-gray-400 hover:text-gray-600">
                            <span class="sr-only">Close</span>
                            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                </div>
                <div class="px-6 py-4" id="modalContent">
                    <!-- Content will be populated by JavaScript -->
                </div>
            </div>
        </div>
    </div>

    <script>
        // Global data
        const dashboardData = {{ data_json|safe }};
        
        // Tab functionality
        function showTab(tabName) {
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all tab buttons
            document.querySelectorAll('.tab-button').forEach(button => {
                button.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked button
            event.target.classList.add('active');
            
            // Initialize charts for the active tab
            setTimeout(() => initializeChartsForTab(tabName), 100);
        }
        
        // Initialize charts based on active tab
        function initializeChartsForTab(tabName) {
            switch(tabName) {
                case 'overview':
                    initializeOverviewCharts();
                    break;
                case 'metrics':
                    initializeMetricsCharts();
                    break;
                case 'questions':
                    initializeQuestionCharts();
                    break;
                case 'evaluators':
                    initializeEvaluatorCharts();
                    break;
            }
        }
        
        // Initialize overview charts
        function initializeOverviewCharts() {
            // Metrics Bar Chart
            const metricsCtx = document.getElementById('metricsBarChart');
            if (metricsCtx && !metricsCtx.chart) {
                const metrics = Object.keys(dashboardData.overview.metrics_scores);
                const scores = Object.values(dashboardData.overview.metrics_scores);
                
                metricsCtx.chart = new Chart(metricsCtx, {
                    type: 'bar',
                    data: {
                        labels: metrics,
                        datasets: [{
                            label: 'Average Score',
                            data: scores,
                            backgroundColor: 'rgba(59, 130, 246, 0.5)',
                            borderColor: 'rgba(59, 130, 246, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 10
                            }
                        }
                    }
                });
            }
        }
        
        // Initialize metrics charts
        function initializeMetricsCharts() {
            // Correlation Heatmap
            initializeCorrelationHeatmap();
        }
        
        // Initialize question charts
        function initializeQuestionCharts() {
            // Question Difficulty Chart
            const difficultyCtx = document.getElementById('difficultyChart');
            if (difficultyCtx && !difficultyCtx.chart) {
                const questions = dashboardData.questions.map(q => `Q${q.id}`);
                const scores = dashboardData.questions.map(q => q.average_score);
                
                difficultyCtx.chart = new Chart(difficultyCtx, {
                    type: 'bar',
                    data: {
                        labels: questions,
                        datasets: [{
                            label: 'Average Score',
                            data: scores,
                            backgroundColor: scores.map(score => {
                                if (score >= 8) return 'rgba(16, 185, 129, 0.5)';
                                if (score >= 6) return 'rgba(245, 158, 11, 0.5)';
                                if (score >= 4) return 'rgba(239, 68, 68, 0.5)';
                                return 'rgba(124, 45, 18, 0.5)';
                            }),
                            borderColor: scores.map(score => {
                                if (score >= 8) return 'rgba(16, 185, 129, 1)';
                                if (score >= 6) return 'rgba(245, 158, 11, 1)';
                                if (score >= 4) return 'rgba(239, 68, 68, 1)';
                                return 'rgba(124, 45, 18, 1)';
                            }),
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 10
                            }
                        }
                    }
                });
            }
            
            // Question Heatmap
            initializeQuestionHeatmap();
        }
        
        // Initialize evaluator charts
        function initializeEvaluatorCharts() {
            // Check if we have evaluator data
            if (!dashboardData.evaluators || dashboardData.evaluators.length === 0) {
                // Show message if no evaluator data
                const evaluatorCtx = document.getElementById('evaluatorChart');
                if (evaluatorCtx) {
                    evaluatorCtx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-8">No evaluator data available</p>';
                }
                const agreementCtx = document.getElementById('agreementChart');
                if (agreementCtx) {
                    agreementCtx.parentElement.innerHTML = '<p class="text-gray-500 text-center py-8">No agreement data available</p>';
                }
                return;
            }
            
            // Evaluator Performance Chart
            const evaluatorCtx = document.getElementById('evaluatorChart');
            if (evaluatorCtx && !evaluatorCtx.chart) {
                const evaluators = dashboardData.evaluators.map(e => e.name);
                const scores = dashboardData.evaluators.map(e => e.average_score);
                
                evaluatorCtx.chart = new Chart(evaluatorCtx, {
                    type: 'bar',
                    data: {
                        labels: evaluators,
                        datasets: [{
                            label: 'Average Score',
                            data: scores,
                            backgroundColor: 'rgba(147, 51, 234, 0.5)',
                            borderColor: 'rgba(147, 51, 234, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 10
                            }
                        }
                    }
                });
            }
            
            // Agreement Chart
            const agreementCtx = document.getElementById('agreementChart');
            if (agreementCtx && !agreementCtx.chart) {
                const evaluators = dashboardData.evaluators.map(e => e.name);
                const stdDevs = dashboardData.evaluators.map(e => e.std_dev);
                
                agreementCtx.chart = new Chart(agreementCtx, {
                    type: 'bar',
                    data: {
                        labels: evaluators,
                        datasets: [{
                            label: 'Standard Deviation (Lower = More Agreement)',
                            data: stdDevs,
                            backgroundColor: 'rgba(245, 158, 11, 0.5)',
                            borderColor: 'rgba(245, 158, 11, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
        }
        
        // Initialize correlation heatmap using D3
        function initializeCorrelationHeatmap() {
            const container = d3.select("#correlationHeatmap");
            if (container.select("svg").empty()) {
                const correlations = dashboardData.correlations;
                const metrics = correlations.metrics;
                const matrix = correlations.matrix;
                
                // Calculate required margins based on longest metric name
                const maxNameLength = Math.max(...metrics.map(m => m.length));
                const dynamicMargin = Math.max(80, maxNameLength * 6); // 6px per character, minimum 80px
                
                const margin = {top: dynamicMargin, right: 50, bottom: dynamicMargin, left: dynamicMargin};
                const width = 400 - margin.left - margin.right;
                const height = 400 - margin.top - margin.bottom;
                
                const svg = container.append("svg")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom);
                
                const g = svg.append("g")
                    .attr("transform", `translate(${margin.left},${margin.top})`);
                
                const cellSize = Math.min(width, height) / metrics.length;
                
                const colorScale = d3.scaleSequential(d3.interpolateRdBu)
                    .domain([-1, 1]);
                
                // Create cells
                metrics.forEach((metric1, i) => {
                    metrics.forEach((metric2, j) => {
                        const corrValue = typeof matrix[metric1][metric2] === 'object' 
                            ? matrix[metric1][metric2].correlation 
                            : matrix[metric1][metric2];
                        
                        g.append("rect")
                            .attr("x", j * cellSize)
                            .attr("y", i * cellSize)
                            .attr("width", cellSize)
                            .attr("height", cellSize)
                            .attr("fill", colorScale(corrValue))
                            .attr("stroke", "white")
                            .attr("stroke-width", 1);
                        
                        g.append("text")
                            .attr("x", j * cellSize + cellSize/2)
                            .attr("y", i * cellSize + cellSize/2)
                            .attr("text-anchor", "middle")
                            .attr("dominant-baseline", "middle")
                            .attr("fill", Math.abs(corrValue) > 0.5 ? "white" : "black")
                            .attr("font-size", "10px")
                            .text(corrValue.toFixed(2));
                    });
                });
                
                // Add row labels with better positioning
                g.selectAll(".row-label")
                    .data(metrics)
                    .enter().append("text")
                    .attr("class", "row-label")
                    .attr("x", -15) // More space from the heatmap
                    .attr("y", (d, i) => i * cellSize + cellSize/2)
                    .attr("text-anchor", "end")
                    .attr("dominant-baseline", "middle")
                    .attr("font-size", "12px")
                    .text(d => d);
                
                // Add column labels with better positioning
                g.selectAll(".col-label")
                    .data(metrics)
                    .enter().append("text")
                    .attr("class", "col-label")
                    .attr("x", (d, i) => i * cellSize + cellSize/2)
                    .attr("y", -15) // More space from the heatmap
                    .attr("text-anchor", "middle")
                    .attr("dominant-baseline", "end")
                    .attr("font-size", "12px")
                    .text(d => d);
            }
        }
        
        // Initialize question heatmap
        function initializeQuestionHeatmap() {
            const container = d3.select("#questionHeatmap");
            if (container.select("svg").empty() && dashboardData.questions && dashboardData.evaluators) {
                const questions = dashboardData.questions;
                const evaluators = dashboardData.evaluators;
                
                if (questions.length === 0 || evaluators.length === 0) {
                    container.append("div")
                        .style("padding", "20px")
                        .style("text-align", "center")
                        .style("color", "#666")
                        .text("No data available for question-evaluator heatmap");
                    return;
                }
                
                // Calculate required left margin based on longest evaluator name
                const maxNameLength = Math.max(...evaluators.map(e => e.name.length));
                const leftMargin = Math.max(100, maxNameLength * 8); // 8px per character, minimum 100px
                
                const margin = {top: 50, right: 50, bottom: 50, left: leftMargin};
                const width = 500 - margin.left - margin.right;
                const height = 300 - margin.top - margin.bottom;
                
                const svg = container.append("svg")
                    .attr("width", width + margin.left + margin.right)
                    .attr("height", height + margin.top + margin.bottom);
                
                const g = svg.append("g")
                    .attr("transform", `translate(${margin.left},${margin.top})`);
                
                const cellWidth = width / questions.length;
                const cellHeight = height / evaluators.length;
                
                const colorScale = d3.scaleSequential(d3.interpolateRdYlGn)
                    .domain([0, 10]);
                
                // Create heatmap cells
                questions.forEach((question, i) => {
                    evaluators.forEach((evaluator, j) => {
                        // Use question average score as placeholder
                        const score = question.average_score;
                        
                        g.append("rect")
                            .attr("x", i * cellWidth)
                            .attr("y", j * cellHeight)
                            .attr("width", cellWidth)
                            .attr("height", cellHeight)
                            .attr("fill", colorScale(score))
                            .attr("stroke", "white")
                            .attr("stroke-width", 1);
                        
                        g.append("text")
                            .attr("x", i * cellWidth + cellWidth/2)
                            .attr("y", j * cellHeight + cellHeight/2)
                            .attr("text-anchor", "middle")
                            .attr("dominant-baseline", "middle")
                            .attr("fill", score > 5 ? "white" : "black")
                            .attr("font-size", "10px")
                            .text(score.toFixed(1));
                    });
                });
                
                // Add question labels
                g.selectAll(".question-label")
                    .data(questions)
                    .enter().append("text")
                    .attr("class", "question-label")
                    .attr("x", (d, i) => i * cellWidth + cellWidth/2)
                    .attr("y", -10)
                    .attr("text-anchor", "middle")
                    .attr("font-size", "10px")
                    .text((d, i) => `Q${i+1}`);
                
                // Add evaluator labels with better positioning
                g.selectAll(".evaluator-label")
                    .data(evaluators)
                    .enter().append("text")
                    .attr("class", "evaluator-label")
                    .attr("x", -15) // More space from the heatmap
                    .attr("y", (d, i) => i * cellHeight + cellHeight/2)
                    .attr("text-anchor", "end")
                    .attr("dominant-baseline", "middle")
                    .attr("font-size", "11px") // Slightly larger font
                    .text(d => d.name); // Show full name instead of truncated
            }
        }
        
        // Text expansion functionality
        function toggleText(element) {
            const shortText = element.querySelector('.short-text');
            const fullText = element.querySelector('.full-text');
            const button = element.querySelector('button');
            
            if (fullText.style.display === 'none') {
                shortText.style.display = 'none';
                fullText.style.display = 'inline';
                if (button) button.textContent = 'Show Less';
            } else {
                shortText.style.display = 'inline';
                fullText.style.display = 'none';
                if (button) button.textContent = 'Show More';
            }
        }
        
        // Question detail modal functions
        function showQuestionDetail(questionId) {
            const modal = document.getElementById('questionModal');
            const title = document.getElementById('modalTitle');
            const content = document.getElementById('modalContent');
            
            const question = dashboardData.questions.find(q => q.id === questionId);
            if (!question) return;
            
            title.textContent = `Question ${questionId} Details`;
            
            content.innerHTML = `
                <div class="space-y-6">
                    <div>
                        <h4 class="text-lg font-medium text-gray-900 mb-2">Question</h4>
                        <p class="text-gray-700 bg-gray-50 p-4 rounded-lg">${question.full_text}</p>
                    </div>
                    
                    <div>
                        <h4 class="text-lg font-medium text-gray-900 mb-2">Response</h4>
                        <p class="text-gray-700 bg-gray-50 p-4 rounded-lg">${question.full_response}</p>
                    </div>
                    
                    <div>
                        <h4 class="text-lg font-medium text-gray-900 mb-2">Scores by Metric</h4>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            ${Object.entries(question.metric_scores).map(([metric, score]) => `
                                <div class="bg-gray-50 p-4 rounded-lg">
                                    <div class="flex justify-between items-center">
                                        <span class="font-medium">${metric}</span>
                                        <span class="text-lg font-bold ${score >= 7 ? 'text-green-600' : score >= 5 ? 'text-yellow-600' : 'text-red-600'}">${score.toFixed(1)}</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div>
                        <h4 class="text-lg font-medium text-gray-900 mb-2">Summary</h4>
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <p><strong>Difficulty:</strong> <span class="difficulty-${question.difficulty.toLowerCase().replace(' ', '-')}">${question.difficulty}</span></p>
                            <p><strong>Average Score:</strong> ${question.average_score.toFixed(1)}/10</p>
                            <p><strong>Metrics Evaluated:</strong> ${question.num_metrics}</p>
                        </div>
                    </div>
                </div>
            `;
            
            modal.classList.remove('hidden');
        }
        
        function closeQuestionModal() {
            document.getElementById('questionModal').classList.add('hidden');
        }
        
        // Initialize default charts on page load
        document.addEventListener('DOMContentLoaded', function() {
            initializeOverviewCharts();
        });
        
        // Close modal when clicking outside
        document.getElementById('questionModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeQuestionModal();
            }
        });
    </script>
</body>
</html>'''
    
    def generate_standalone_dashboard(self, output_path: str = "results/dashboard.html") -> str:
        """
        Generate a standalone HTML dashboard with all resources embedded.
        
        Args:
            output_path: Path where to save the HTML dashboard
            
        Returns:
            Path to the generated HTML file
        """
        return self.generate_dashboard(output_path) 