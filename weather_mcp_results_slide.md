---
layout: default
---

# MCP Weather Benchmark - Ergebnisse

<div class="grid grid-cols-1 gap-4 mt-4">

<div class="grid grid-cols-2 gap-6">

<div>
<v-clicks>

#### **Test-Setup**
• Dataset: 15 Wetter-Anfragen  
• Schwierigkeit: easy → expert  
• MCP Tools: 3 Weather APIs  
• Judge Models: 3 Evaluatoren  
  (llama3.2, deepseek-r1, mistral)

<div class="mt-6"></div>

#### **Tool Usage**
• 20/20 Calls erfolgreich  
• 100% Success Rate  
• Alle APIs funktional

</v-clicks>
</div>

<div>
<v-click>

#### **Ergebnisse**

<div class="text-xs">

| Metrik | Mistral | Mixtral |
|--------|---------|---------|
| Tool Usage | 7.09 | **7.14** |
| Tool Selection | **7.60** | 6.91 |
| Info Retrieval | **7.17** | 6.47 |
| Context Aware | 5.71 | **6.06** |
| **OVERALL** | **6.89** | 6.64 |

</div>

<div class="mt-2 bg-yellow-900 bg-opacity-30 p-2 rounded-lg text-xs">
💡 Mistral (7.2B) übertrifft Mixtral (46.7B)
</div>

</v-click>
</div>

</div>

<v-click>

<div class="mt-4 bg-green-900 bg-opacity-30 p-3 rounded-lg">

#### **Key Findings**

<div class="text-m">
• Erfolgreiche MCP-Integration bestätigt<br>
• Modellgröße ≠ bessere Tool-Nutzung<br>
• Kleineres Modell effizienter bei Tool-Auswahl
</div>

</div>

</v-click>

</div>

