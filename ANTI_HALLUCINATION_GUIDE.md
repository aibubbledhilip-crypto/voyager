# Anti-Hallucination Guide

This guide explains how the system prevents LLM hallucinations and ensures accurate, trustworthy answers.

## What is Hallucination?

**Hallucination** occurs when an LLM generates information that:
- Isn't present in the provided context
- Is made up or fabricated
- Extrapolates beyond the actual data
- Mixes information from different contexts incorrectly

## Multi-Layer Anti-Hallucination System

### 1. Intelligent Query Routing

The system automatically routes queries to the most appropriate backend:

- **Analytics Queries** → Direct data access (Pandas + SQL)
  - "Find duplicates" - No LLM involved, pure data processing
  - "Count unique values" - Direct SQL/Pandas operations
  - "Sum revenue by region" - Exact aggregations
  - ✅ **0% hallucination risk** - Math doesn't lie!

- **Metadata Queries** → Database queries
  - "How many files?" - Direct database count
  - "List files" - Direct file listing
  - ✅ **0% hallucination risk** - Facts from database

- **Semantic Queries** → RAG with anti-hallucination measures
  - "What trends do you see?" - LLM analysis with safeguards
  - "Summarize the data" - Controlled LLM generation

### 2. Enhanced RAG Prompt

The RAG prompt includes explicit anti-hallucination rules:

```
CRITICAL RULES TO PREVENT HALLUCINATION:
1. ONLY use information explicitly present in the context below
2. DO NOT make assumptions or extrapolate beyond the given data
3. DO NOT use external knowledge or general information
4. If the context lacks sufficient information, clearly state:
   "The provided data does not contain enough information to answer this question."
5. ALWAYS cite which specific file(s) you're referencing
6. For numerical questions, ONLY provide numbers that appear in the context
7. If asked about data not present in the context, say:
   "I don't have data about [topic] in the uploaded files."
```

### 3. Temperature Control

**Temperature = 0.0** (configurable)

- Lower temperature = More deterministic, less creative
- 0.0 = Most factual, least hallucination
- Default: 0.0 for data analysis (accuracy over creativity)

**Configuration:**
```env
LLM_TEMPERATURE=0.0  # Recommended for data analysis
LLM_TEMPERATURE=0.3  # For creative insights (more risk)
LLM_TEMPERATURE=0.7  # For brainstorming (highest risk)
```

### 4. Answer Validation

Every RAG answer goes through validation that detects:

**Hallucination Markers:**
- "I think", "probably", "might be", "could be"
- "In general", "typically", "usually"
- "Based on my knowledge", "as far as I know"

**Missing Citations:**
- Checks if answer mentions source files
- Warns if no files are cited

**Honesty Detection (Good!):**
- "Don't have data about..."
- "Not enough information..."
- "Cannot determine from the context..."
- These are **positive** signs - the LLM is being honest!

### 5. Confidence Scoring

Each answer receives a confidence score:

- **High** ✅
  - No hallucination markers
  - Source files cited
  - Or: Honest about limitations

- **Medium** ⚠️
  - 1-2 minor warnings
  - Mostly grounded in data

- **Low** ❌
  - Multiple hallucination markers
  - No source citations
  - Uncertain language throughout

**Low confidence answers include automatic warnings:**
```
⚠️ Note: This answer may be uncertain. Validation warnings:
- Uncertain language detected: 'probably'
- Answer does not cite specific source files

Consider using analytics endpoints for exact data queries.
```

### 6. Source Document Retrieval

- Retrieves top **20 chunks** for context
- Provides source citations in response
- User can verify answers against sources

## Configuration Options

Edit `.env` or `backend/config.py`:

```env
# LLM Temperature (0 = most accurate, 1 = most creative)
LLM_TEMPERATURE=0.0

# Enable answer validation
ENABLE_ANSWER_VALIDATION=True

# Require source citations in answers
REQUIRE_SOURCE_CITATION=True
```

## Best Practices

### ✅ DO: Use Analytics for Exact Queries

Instead of: "How many duplicate MSISDNs are there?"
Use analytics: "Find duplicate MSISDNs" → Returns exact count with CSV

Analytics queries have **zero hallucination risk** because they use direct data processing.

### ✅ DO: Ask Specific Questions

Good: "What trends do you see in the sales data from Q1 2024?"
Bad: "Tell me about sales"

Specific questions get better context retrieval and more accurate answers.

### ✅ DO: Verify Important Findings

Always check the source citations for critical decisions.

### ❌ DON'T: Ask Questions Beyond Your Data

Bad: "What will sales be next year?"
- LLM might hallucinate predictions
- Not grounded in your uploaded data

### ❌ DON'T: Trust Uncertain Language

If answer says "probably" or "might be", treat it as speculation.

### ❌ DON'T: Use for Exact Counts Without Verification

For exact aggregations, use analytics endpoints instead of RAG.

## When Each Approach Works Best

| Query Type | Best Approach | Hallucination Risk |
|------------|---------------|-------------------|
| Find duplicates | Analytics | 0% |
| Count unique values | Analytics | 0% |
| Sum/Avg/Min/Max | Analytics | 0% |
| List files | Metadata | 0% |
| Trends & patterns | RAG | Low (with safeguards) |
| Summarize data | RAG | Low (with safeguards) |
| Predictions | ❌ Not recommended | High |
| External facts | ❌ Not supported | 100% |

## Monitoring Validation Results

Responses include validation metadata (when enabled):

```json
{
  "answer": "...",
  "validation": {
    "confidence": "high",
    "warnings": [],
    "is_valid": true
  }
}
```

Check logs for validation details:
```
Answer validation: confidence=high, warnings=0
Answer validation: confidence=low, warnings=3
```

## Troubleshooting Hallucinations

### Problem: LLM still making things up

**Solutions:**
1. ✅ Use analytics endpoints for exact queries
2. ✅ Lower temperature to 0.0
3. ✅ Enable answer validation
4. ✅ Check if question is too broad
5. ✅ Verify uploaded files contain relevant data

### Problem: Answers too cautious

**Solutions:**
1. Increase temperature slightly (0.1 - 0.3)
2. Upload more comprehensive data
3. Ask more specific questions
4. This is actually good - honesty about limitations!

### Problem: No source citations

**Check:**
1. Files were uploaded successfully
2. Data is relevant to the question
3. Source citation requirement is enabled

## Example: Good vs Bad

### ❌ Hallucinated Answer:
```
Q: How many subscribers do we have?
A: Based on typical telecom data, you probably have around
   100,000 subscribers. Most companies in this sector...
```
**Issues:** Made up numbers, external knowledge, "probably"

### ✅ Grounded Answer:
```
Q: How many unique MSISDNs are in the data?
A: Based on test_msisdn_file_01.csv through test_msisdn_file_20.csv,
   there are 1,250 unique MSISDNs across all uploaded files.
   [Via Analytics endpoint - exact count from direct data access]
```
**Good:** Specific files cited, exact count, analytics used

### ✅ Honest Answer:
```
Q: What is the customer churn rate?
A: The provided data does not contain enough information about
   customer churn rates. The uploaded files (test_msisdn_file_*.csv)
   contain subscriber data but do not include churn metrics.
```
**Good:** Honest about limitations, cites which files were checked

## Summary

The system uses **6 layers of protection**:

1. 🔀 Smart routing to analytics (no LLM for exact queries)
2. 📝 Anti-hallucination prompt
3. ❄️ Low temperature (deterministic output)
4. ✅ Answer validation
5. 📊 Confidence scoring
6. 📚 Source citation requirement

**Result:** Trustworthy, verifiable answers you can rely on for data analysis.

## Need More Accuracy?

For mission-critical queries requiring 100% accuracy:
- Use **Analytics endpoints** directly
- Download **CSV exports** for verification
- Cross-check with source files
- Use multiple queries to validate findings

---

**Remember:** The system is designed to be honest about what it doesn't know. An "I don't have enough information" answer is a GOOD answer - it means the system is working correctly!
