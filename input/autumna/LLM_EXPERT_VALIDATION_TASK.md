# 🔍 TECHNICAL SPECIFICATION: LLM Parsing Methodology Validation

**Project:** Autumna Care Home Data Extraction  
**Date:** November 9, 2025  
**Version:** 1.0  
**Status:** For External LLM Expert Review

---

## 📋 EXECUTIVE SUMMARY

We are requesting an independent validation of our LLM-based data extraction methodology for care home profiles from Autumna.co.uk. The expert should review:

1. **System Prompt Quality** - Is the prompt optimal for structured data extraction?
2. **JSON Schema Design** - Is the schema well-structured and complete?
3. **Extraction Accuracy** - Are the results accurate and complete?
4. **Token Efficiency** - Can the prompt be optimized further?
5. **Best Practices** - Are we following LLM best practices?

---

## 🎯 VALIDATION OBJECTIVES

### Primary Objectives:

1. **Validate extraction accuracy** - Verify that extracted data matches source content
2. **Assess prompt quality** - Evaluate if the system prompt is clear, comprehensive, and optimal
3. **Review schema design** - Check if JSON schema is well-structured and complete
4. **Identify improvements** - Suggest optimizations for better accuracy or efficiency
5. **Check compliance** - Verify adherence to LLM best practices

### Secondary Objectives:

1. **Token optimization** - Identify opportunities to reduce token usage
2. **Error prevention** - Find potential failure modes or edge cases
3. **Documentation quality** - Assess if documentation is sufficient
4. **Scalability** - Evaluate if methodology scales to production volumes

---

## 📁 INPUT FILES (Required for Validation)

### 1. System Prompt
**File:** `input/autumna/AUTUMNA_PARSING_PROMPT_v2_5_OPTIMIZED.md`

**Description:** The complete system prompt used for LLM extraction. Contains:
- Extraction instructions for 250+ fields
- Field-specific rules and examples
- Validation rules
- Critical distinctions (e.g., licenses vs care types)
- Golden rules for data extraction

**What to review:**
- Clarity and completeness of instructions
- Consistency of rules
- Presence of contradictions
- Optimal structure for LLM understanding
- Token efficiency opportunities

---

### 2. JSON Schema
**File:** `input/autumna/response_format_v2_4.json`

**Description:** OpenAI Structured Outputs JSON Schema defining the expected output structure. Contains:
- 250+ fields organized in hierarchical structure
- Required vs optional fields
- Data types and validation patterns
- Field descriptions

**What to review:**
- Schema completeness
- Field naming consistency
- Data type appropriateness
- Validation patterns correctness
- Required fields logic

---

### 3. Test Input Data
**File:** `input/autumna/Data-MD/html 1 /test1-md.md`

**Description:** Sample Markdown file containing a care home profile (Ladydale Care Home). This is the input content that LLM should parse.

**What to review:**
- Data completeness in source
- Clarity of information
- Presence of edge cases
- Ambiguities that might confuse LLM

---

### 4. Expected Results (Ground Truth)
**File:** `input/autumna/TEST_FILE_ANALYSIS.md`

**Description:** Manual analysis of test file with expected extracted values. Contains:
- Expected values for all key fields
- Source locations in markdown
- Potential extraction challenges
- Risk assessment

**What to review:**
- Accuracy of expected values
- Completeness of ground truth
- Reasonableness of expectations

---

### 5. Actual Extraction Results
**Files:**
- `input/autumna/Data-MD/html 1 /test1-parsed-result.json` (Markdown parsing result)
- `input/autumna/Data-MD/html 1 /test1-html-parsed-result.json` (HTML parsing result)

**Description:** Actual JSON output from LLM extraction using the system prompt and schema.

**What to review:**
- Accuracy compared to ground truth
- Completeness of extraction
- Data quality
- Consistency with schema

---

### 6. Comparison Reports
**Files:**
- `input/autumna/PARSING_RESULTS_REPORT.md` - Detailed parsing results
- `input/autumna/FIELD_COVERAGE_ANALYSIS.md` - Field coverage analysis
- `input/autumna/DETAILED_JSON_COMPARISON.md` - HTML vs Markdown comparison

**Description:** Analysis reports comparing expected vs actual results, field coverage statistics, and format comparisons.

**What to review:**
- Validation methodology
- Statistical analysis quality
- Conclusions drawn

---

## 🔍 VALIDATION TASKS

### Task 1: System Prompt Review

**Objective:** Evaluate the quality and optimality of the system prompt.

**Steps:**
1. Read the complete system prompt (`AUTUMNA_PARSING_PROMPT_v2_5_OPTIMIZED.md`)
2. Assess:
   - **Clarity:** Are instructions clear and unambiguous?
   - **Completeness:** Are all edge cases covered?
   - **Consistency:** Are rules consistent throughout?
   - **Structure:** Is the prompt well-organized?
   - **Token efficiency:** Can it be shortened without losing quality?
   - **Best practices:** Does it follow LLM prompt engineering best practices?

**Deliverable:** Written report with:
- Strengths of the prompt
- Weaknesses and issues found
- Specific recommendations for improvement
- Examples of problematic sections (if any)

---

### Task 2: JSON Schema Review

**Objective:** Evaluate the JSON schema design and completeness.

**Steps:**
1. Review the JSON schema (`response_format_v2_4.json`)
2. Assess:
   - **Completeness:** Are all necessary fields present?
   - **Structure:** Is hierarchical structure logical?
   - **Data types:** Are data types appropriate?
   - **Validation:** Are validation patterns correct?
   - **Required fields:** Is the required/optional logic correct?
   - **Schema compliance:** Does it follow JSON Schema standards?

**Deliverable:** Written report with:
- Schema quality assessment
- Missing fields (if any)
- Structural improvements
- Validation pattern corrections

---

### Task 3: Extraction Accuracy Validation

**Objective:** Verify that extracted data matches source content accurately.

**Steps:**
1. Read the test input file (`test1-md.md`)
2. Read the expected results (`TEST_FILE_ANALYSIS.md`)
3. Read the actual extraction results (`test1-parsed-result.json`)
4. Compare actual vs expected for all key fields:
   - Identity fields (name, cqc_location_id, provider_name)
   - Location fields (address, city, postcode)
   - Care services (care_residential, care_respite, etc.)
   - Capacity (beds_total, year_registered)
   - CQC ratings
   - Other important fields

**Deliverable:** Validation report with:
- Field-by-field accuracy assessment
- List of correctly extracted fields
- List of incorrectly extracted fields (if any)
- List of missing fields (if any)
- Accuracy percentage
- Root cause analysis for any errors

---

### Task 4: Token Efficiency Analysis

**Objective:** Identify opportunities to optimize token usage.

**Steps:**
1. Analyze the system prompt for redundancy
2. Check for verbose explanations that could be shortened
3. Look for duplicate information
4. Assess if examples are necessary or could be reduced
5. Calculate potential token savings

**Deliverable:** Optimization report with:
- Current token usage analysis
- Identified redundancies
- Specific recommendations for reduction
- Estimated token savings
- Risk assessment of optimizations

---

### Task 5: Best Practices Compliance

**Objective:** Verify adherence to LLM best practices.

**Steps:**
1. Review prompt engineering best practices:
   - Clear instructions
   - Proper use of examples
   - Structured format
   - Error prevention
   - Consistency
2. Review schema design best practices:
   - Proper use of required fields
   - Appropriate data types
   - Validation patterns
3. Review extraction methodology:
   - Use of structured outputs
   - Error handling
   - Quality scoring

**Deliverable:** Compliance report with:
- Best practices followed
- Best practices violated
- Recommendations for improvement

---

### Task 6: Edge Cases and Failure Modes

**Objective:** Identify potential failure modes and edge cases.

**Steps:**
1. Analyze the prompt for potential failure scenarios
2. Review test data for edge cases
3. Identify ambiguous situations
4. Check for missing error handling
5. Assess robustness

**Deliverable:** Risk assessment report with:
- Identified edge cases
- Potential failure modes
- Recommendations for handling
- Suggested test cases

---

## 📊 VALIDATION CRITERIA

### Accuracy Criteria:

- **Critical Fields:** 100% accuracy required (name, cqc_location_id, city, postcode)
- **Important Fields:** ≥95% accuracy expected
- **Optional Fields:** ≥80% accuracy acceptable

### Quality Criteria:

- **Data Quality Score:** Should be ≥85 (as per current results)
- **Extraction Confidence:** Should be "high" for valid data
- **Completeness:** All required fields must be present

### Efficiency Criteria:

- **Token Usage:** Should be reasonable (current: ~20K tokens for Markdown)
- **Cost Efficiency:** Should be optimized for production scale
- **Processing Speed:** Should be acceptable for batch processing

---

## 📝 EXPECTED DELIVERABLES

### 1. Executive Summary (1-2 pages)
- Overall assessment
- Key findings
- Critical recommendations
- Risk assessment

### 2. Detailed Validation Report (10-20 pages)
- Task-by-task analysis
- Detailed findings
- Specific recommendations
- Code examples (if applicable)

### 3. Improvement Recommendations (2-5 pages)
- Prioritized list of improvements
- Implementation suggestions
- Expected impact
- Risk assessment

### 4. Comparison with Best Practices (2-3 pages)
- Industry standards comparison
- Best practices compliance
- Gap analysis

---

## 🔧 VALIDATION METHODOLOGY

### Phase 1: Document Review (Week 1)
- Read all input files
- Understand the methodology
- Identify initial concerns
- Prepare questions

### Phase 2: Analysis (Week 2)
- Perform detailed analysis
- Compare with best practices
- Test edge cases (if possible)
- Document findings

### Phase 3: Reporting (Week 3)
- Write validation report
- Prepare recommendations
- Create improvement plan
- Finalize deliverables

---

## 📋 SPECIFIC VALIDATION CHECKLIST

### System Prompt Checklist:

- [ ] Instructions are clear and unambiguous
- [ ] All field extraction rules are present
- [ ] Examples are helpful and not redundant
- [ ] Critical distinctions are clearly explained
- [ ] No contradictions between sections
- [ ] Token usage is optimized
- [ ] Follows prompt engineering best practices
- [ ] Error prevention measures are in place

### JSON Schema Checklist:

- [ ] All necessary fields are present
- [ ] Required fields are correctly marked
- [ ] Data types are appropriate
- [ ] Validation patterns are correct
- [ ] Hierarchical structure is logical
- [ ] Field descriptions are clear
- [ ] Schema follows standards

### Extraction Results Checklist:

- [ ] All critical fields extracted correctly
- [ ] Data matches source content
- [ ] No hallucinations detected
- [ ] Data quality score is reasonable
- [ ] Extraction confidence is appropriate
- [ ] No missing required fields
- [ ] Data types are correct

---

## 🎯 KEY QUESTIONS TO ANSWER

1. **Is the system prompt optimal for this task?**
   - Could it be improved?
   - Are there missing instructions?
   - Are there redundant sections?

2. **Is the JSON schema well-designed?**
   - Are all fields necessary?
   - Is the structure logical?
   - Are validation patterns correct?

3. **Is the extraction accurate?**
   - Do results match source content?
   - Are there any errors?
   - What is the accuracy rate?

4. **Can the methodology be optimized?**
   - Token usage optimization
   - Cost reduction opportunities
   - Speed improvements

5. **Are there any risks or failure modes?**
   - Edge cases not handled
   - Potential errors
   - Scalability concerns

6. **Does it follow best practices?**
   - LLM prompt engineering
   - Schema design
   - Data extraction methodology

---

## 📁 FILE STRUCTURE REFERENCE

```
input/autumna/
├── AUTUMNA_PARSING_PROMPT_v2_5_OPTIMIZED.md    # System prompt
├── response_format_v2_4.json                  # JSON Schema
├── Data-MD/html 1 /
│   ├── test1-md.md                             # Test input (Markdown)
│   ├── test1-html.html                         # Test input (HTML)
│   ├── test1-parsed-result.json                # Markdown extraction result
│   └── test1-html-parsed-result.json           # HTML extraction result
├── TEST_FILE_ANALYSIS.md                       # Expected results (ground truth)
├── PARSING_RESULTS_REPORT.md                   # Parsing results analysis
├── FIELD_COVERAGE_ANALYSIS.md                  # Field coverage statistics
└── DETAILED_JSON_COMPARISON.md                 # HTML vs Markdown comparison
```

---

## 🔍 VALIDATION APPROACH

### Recommended Approach:

1. **Start with understanding:**
   - Read the system prompt completely
   - Understand the JSON schema structure
   - Review the test data

2. **Perform extraction test (optional):**
   - Run the prompt with test data
   - Compare results with provided outputs
   - Identify any discrepancies

3. **Analyze systematically:**
   - Go through each validation task
   - Document findings as you go
   - Cross-reference with best practices

4. **Synthesize findings:**
   - Identify patterns in issues
   - Prioritize recommendations
   - Assess overall quality

---

## 📊 SUCCESS CRITERIA

### Validation is successful if:

1. ✅ All critical fields are extracted accurately (100%)
2. ✅ Important fields have ≥95% accuracy
3. ✅ System prompt is clear and comprehensive
4. ✅ JSON schema is well-designed
5. ✅ Methodology follows best practices
6. ✅ Recommendations are actionable
7. ✅ Risk assessment is complete

---

## 📞 CONTACT & QUESTIONS

If you have questions during validation:

1. **Technical questions:** Review the provided documentation first
2. **Clarifications:** Document assumptions and proceed
3. **Missing information:** Note in the report for follow-up

---

## 📅 TIMELINE

**Expected Duration:** 2-3 weeks

- **Week 1:** Document review and initial analysis
- **Week 2:** Detailed validation and testing
- **Week 3:** Report writing and finalization

---

## ✅ DELIVERABLE CHECKLIST

- [ ] Executive Summary
- [ ] Detailed Validation Report
- [ ] Improvement Recommendations
- [ ] Best Practices Comparison
- [ ] Code examples (if applicable)
- [ ] Prioritized action items

---

**Version:** 1.0  
**Last Updated:** November 9, 2025  
**Status:** Ready for Expert Review

