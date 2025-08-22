# RAG-Powered Historical Intelligence Platform - Complete Implementation Guide

## Project Overview

Build a comprehensive NPS Intelligence Platform that predicts and prevents student churn using RAG-powered historical intelligence. The system consists of a FastAPI backend with PostgreSQL, ChromaDB vector database, and a React TypeScript frontend with real-time capabilities. 

## Backend Implementation

### Tech Stack

- **Framework**: FastAPI with Python
- **Database**: PostgreSQL for structured data
- **Vector Database**: ChromaDB for embeddings and similarity search
- **Embeddings**: nomic-ai/nomic-embed-text-v1 using api key
- **LLM Chain**: Primary: Gemini → Fallback 1: Groq → Fallback 2: OpenAI
- **Real-time**: WebSockets for live updates
- **Background Tasks**: Celery for async processing
- **Langchain**: For all the RAG related tasks. Use Langchain version above 0.3.0 only

## CRITICAL: Real Data Format vs Requirements Mismatch

### Actual Data Structure Analysis

#### NPS CSV File Reality (24 columns):

The real NPS CSV file has a completely different structure than specified in the PRD:

**Real Headers:**
1. Timestamp
2. Student code (maps to student_id)
3. Main NPS Question (verbose): "Congratulations on taking a step towards launching your career with Masai School...how likely are you to recommend Masai school to someone like you?" (maps to nps_score)
4. Improvement Feedback: "What can we do to make sure you rate us 10..." (maps to comments part 1)
5-9. **Course A ratings** (5 different aspects): Lecture experience, Instructor content delivery, Course A Sherpa Support, Ask & Learn Hour effectiveness, PP session
10-14. **Course B ratings** (5 different aspects): Same aspects for Course B
15-17. **CSBT ratings** (3 different aspects): CSBT Curriculum design, CSBT Instructor support, CSBT Support
18. **Dost support rating**: "How is the support provided by your Dost (Experience Champion)?"
19-23. **Product support ratings** (5 different aspects): Course Platform LMS, Assess Platform, Ticketing System, PSC Sessions, PAI Evaluation
24. **Additional feedback**: "If you have any further questions, queries or suggestions, please tell us."

**Total: 24 columns instead of expected 9 columns**

#### Demographics CSV File (Matches Requirements):
- student_id, demographic_type, current_grade, attendance_rate

### Required Data Mapping Logic

#### Intelligent Header Detection Strategy:

The Groq API header detection must be enhanced to:
- Parse verbose question headers and map to simple field names
- Select the most relevant 3 aspects from 20+ available ratings for aspect_1_score, aspect_2_score, aspect_3_score
- Combine multiple comment fields (columns 4 and 24) into single comments field
- Handle missing required fields (course_id, week_number) with intelligent defaults
- Validate data quality and provide confidence scores for mappings

#### Specific Field Mapping Requirements:

**REQUIRED SCHEMA MAPPING:**
- `student_id` ← "Student code" (column 2)
- `timestamp` ← "Timestamp" (column 1)  
- `nps_score` ← Main NPS question response (column 3)
- `course_id` ← It will the value from the student_id, the value before underscore is course_id (missing in actual data)
- `week_number` ← CALCULATE from timestamp difference from course start OR default to survey sequence
- `aspect_1_score` ← Course A Lecture experience (column 5) - Most fundamental learning aspect
- `aspect_2_score` ← Course B Lecture experience (column 10) - Advanced learning progression  
- `aspect_3_score` ← CSBT Curriculum design (column 15) - Career preparation aspect
- `comments` ← INTELLIGENTLY COMBINE columns 4 and 24:
   - If column 4 has content: "Improvement needed: [column 4 content]"
   - If column 24 has content: "Additional feedback: [column 24 content]"  
   - If both: combine with separator
   - If neither: "No additional feedback provided"

### Enhanced Data Processing Pipeline:

1. **VALIDATE FILE STRUCTURE:**
   - Check if file has 24 columns (real format) vs 9 columns (expected format)
   - Handle both scenarios gracefully

2. **INTELLIGENT HEADER MAPPING (Using Groq):**
   - Send first 3 rows to Groq for intelligent column identification
   - Map verbose headers to required schema fields
   - Generate confidence scores for each mapping
   - Flag uncertain mappings for manual review

3. **DATA EXTRACTION & TRANSFORMATION:**
   - Extract NPS score from verbose question response (handle 0-10 scale)
   - Select 3 most representative aspect scores from 20+ available
   - Concatenate improvement feedback + additional feedback for comments
   - Calculate week_number from timestamp (assume course start date)
   - Generate course_id from context or default

4. **DATA QUALITY VALIDATION:**
   - Ensure student_id exists in both NPS and demographics files
   - Validate NPS scores are in 0-10 range
   - Check for missing critical data points
   - Generate data quality report

5. **TEXT CLEANING & STANDARDIZATION:**
   - Remove emoticons and special characters from comments
   - Standardize text encoding
   - Handle empty/null comment fields
   - Normalize aspect scores to consistent scale

6. **POSTGRESQL STORAGE:**
   - Store with additional metadata about data source complexity
   - Include mapping confidence scores
   - Preserve original verbose headers for reference

7. **CHROMADB EMBEDDING PREPARATION:**
   - Use ALL 20+ aspect scores as rich context for embeddings
   - Include domain-specific educational terminology
   - Embed combined comment text with full context

## Core API Endpoints

### 1. Enhanced File Upload Endpoint

**POST** `/api/upload`
**Content-Type**: multipart/form-data

**Request:**
- `nps_file`: CSV/Excel file (REAL FORMAT: 24 columns of educational survey data)
- `demographics_file`: CSV/Excel file (4 columns as specified)

**Enhanced Processing Pipeline:**

1. **DETECT FILE FORMAT:**
   - Check if NPS file has expected 9 columns OR real 24 columns
   - Adapt processing strategy accordingly

2. **INTELLIGENT HEADER MAPPING:**
   - Use Groq API (llama-3.1-8b-instant) for complex header interpretation
   - Handle verbose educational survey questions
   - Map to simplified schema while preserving data richness

3. **ADVANCED DATA CLEANING:**
   - Clean verbose survey responses
   - Combine multiple comment fields intelligently  
   - Handle missing fields (course_id, week_number) with context-aware defaults
   - Remove emoticons and standardize text format

4. **CROSS-FILE VALIDATION:**
   - Validate student_id matching between 24-column NPS file and 4-column demographics
   - Handle ID format variations (case sensitivity, whitespace)
   - Generate data quality metrics

5. **RICH EMBEDDING GENERATION using nomic-ai/nomic-embed-text-v1:**
   - Student journey narratives with full context from 20+ aspects
   - Comment sentiment analysis with educational domain awareness
   - Historical intervention patterns with success metrics
   - Complex student profile embeddings

6. **CHROMADB STORAGE with Enhanced Metadata:**
   - Store embeddings with rich educational context
   - Include all aspect scores as searchable metadata
   - Preserve data source complexity information

7. **BACKGROUND ANALYSIS:**
   - Trigger comprehensive analysis tasks
   - Generate initial insights with confidence scores
   - Prepare RAG context for query system

8. **REAL-TIME UPDATES:**
   - Send WebSocket updates about processing progress
   - Include data quality alerts
   - Notify about mapping uncertainties

**Response:**
```json
{
  "status": "success",
  "message": "Files processed successfully", 
  "summary": {
    "students_processed": 150,
    "nps_responses": 450,
    "data_format": "complex_educational_survey",
    "mapping_confidence": 0.95,
    "data_quality_score": 0.87,
    "aspects_analyzed": 20,
    "processing_time": "4.2s"
  },
  "data_quality_report": {
    "missing_fields": ["course_id"], 
    "generated_fields": ["week_number"],
    "comment_sources": 2,
    "aspect_coverage": "comprehensive"
  }
}
```

### 2. Enhanced Chat Query Endpoint

**POST** `/api/chat`

**Request:**
```json
{
  "query": "Generate weekly report for current batch",
  "session_id": "unique_session_id",
  "context": {}
}
```

**Enhanced Processing Pipeline:**

1. **QUERY CLASSIFICATION:**
   - weekly_report, individual_analysis, segmentation_analysis, sentiment_analysis
   - aspect_specific_analysis (NEW: for specific course aspects)
   - comparative_analysis (NEW: between different aspects/demographics)

2. **ENHANCED EMBEDDING GENERATION:**
   - Use nomic-ai/nomic-embed-text-v1 with educational context
   - Account for complex survey structure in similarity matching

3. **COMPREHENSIVE CHROMADB QUERYING:**
   - Query across student_journeys with rich aspect data
   - Search intervention_strategies with educational context
   - Analyze comment_analysis with domain-specific patterns
   - Retrieve weekly_patterns with comprehensive metrics

4. **CONTEXTUAL RAG RETRIEVAL:**
   - Find similar complex educational patterns
   - Include aspect-specific historical performance
   - Retrieve successful interventions for specific course components

5. **LLM CHAIN RESPONSE GENERATION:**
   - Primary: Gemini with educational domain prompts
   - Fallback 1: Groq with survey analysis context
   - Fallback 2: OpenAI with comprehensive prompting
   - Include aspect-specific insights in responses

6. **ENHANCED RESPONSE FORMATTING:**
   - Format according to PRD specifications
   - Include aspect-specific breakdowns
   - Provide confidence scores based on data richness
   - Add educational domain insights

## Response Formats by Query Type:

### Enhanced Weekly Report:
```json
{
  "type": "weekly_report", 
  "content": "📊 NPS Intelligence Report - Week Ending [Date]\n════════════════════════════════════════════\n📈 OVERALL METRICS\nCurrent NPS: 7.2 (↓0.5 from last week) ⚠\nPromoters: 45% | Passives: 32% | Detractors: 23%\nResponse Rate: 87%\nData Richness: 20+ aspects analyzed per student\n\n🧠 INSIGHTS FROM PAST COHORTS\nThis Week 5 dip happened in 73% of previous batches\n• Course A→B transition challenges: 68% of students affected\n• CSBT readiness concerns: 45% mention career preparation anxiety\n• Teams that acted now: 82% recovered\n• Teams that waited: Only 41% recovered\n• What worked best: Extra Module 3 workshop + Career counseling\n\n📚 ASPECT-SPECIFIC ANALYSIS\nCourse A Performance:\n• Lecture Experience: 7.8/10 (↑0.3)\n• Instructor Delivery: 8.1/10 (stable)\n• Sherpa Support: 7.5/10 (↓0.2) ⚠\n\nCourse B Performance:\n• Lecture Experience: 7.2/10 (↓0.4) ⚠\n• Content Complexity Jump: 65% mention difficulty\n• Historical Pattern: Normal Week 5-6 challenge\n\nCSBT Readiness:\n• Curriculum Design: 7.9/10 (↑0.1)\n• Career Preparation Anxiety: 43% express concerns\n• Job Market Readiness: 72% feel underprepared\n\n...[continue with full PRD format plus aspect-specific insights]",
  "metadata": {
    "confidence_score": 0.92,
    "data_sources": ["comprehensive_survey", "historical_cohorts", "aspect_analysis"],
    "aspects_analyzed": 20,
    "response_richness": "high",
    "generated_at": "2025-08-21T10:30:00Z"
  }
}
```

### Enhanced Individual Student Analysis:
```json
{
  "type": "individual_analysis",
  "content": "👤 STUDENT PROFILE: fsd25_08001\nDemographic: Fresh Graduate | Grade: 88.5 | Attendance: 94.2%\n\nJourney Overview:\n• Overall NPS: 9/10 → 'Excellent support overall'\n• Course A Performance: Strong across all aspects (5/5 average)\n• Course B Performance: Consistent high performance (5/5 average)  \n• CSBT Readiness: High confidence (5/5 average)\n• Support Systems: Excellent ratings across all touchpoints\n\n📊 DETAILED ASPECT BREAKDOWN:\nCourse A: Lecture(5), Instructor(5), Sherpa(4), Ask&Learn(5), PP(5)\nCourse B: Lecture(5), Instructor(5), Sherpa(5), Ask&Learn(5), PP(5)\nCSBT: Curriculum(5), Instructor(5), Support(5)\nSupport: Dost(5), LMS(5), Assessment(5), Ticketing(5), PSC(5), PAI(5)\n\n🧠 HISTORICAL COMPARISON:\nFound 12 similar high-performing fresh graduate patterns:\n• 94% successfully complete program\n• 89% achieve job placement within 3 months\n• Typical challenge: Mid-program motivation maintenance\n• Risk Level: VERY LOW (2% dropout probability)\n\n💡 RECOMMENDED ACTIONS:\n• Maintain current support level - student is thriving\n• Consider as peer mentor for struggling students\n• Include in success story case studies\n• Monitor for mid-program motivation dip (Week 8-10)",
  "student_id": "fsd25_08001",
  "risk_level": "very_low",
  "aspect_scores": {},
  "recommended_actions": []
}
```

### Enhanced Segmentation Analysis:
```json
{
  "type": "segmentation_analysis",
  "content": "📊 COMPREHENSIVE DEMOGRAPHIC ANALYSIS\n\nWorking Professionals (n=3 in sample)\n• Average Overall NPS: 7.3\n• Course A Average: 4.3/5 (Strong foundation learning)\n• Course B Average: 4.2/5 (Handling complexity well)\n• CSBT Average: 4.3/5 (Career transition focus)\n• Main Challenge: Time management (mentioned in 67% of feedback)\n• Support Needs: Flexible scheduling, recorded sessions\n• Historical Success Rate: 78% with targeted interventions\n\nFresh Graduates (n=4 in sample)\n• Average Overall NPS: 9.5 (Highest satisfaction)\n• Course A Average: 5.0/5 (Excellent engagement)\n• Course B Average: 5.0/5 (Adapting well to complexity)\n• CSBT Average: 5.0/5 (High career confidence)\n• Strength: High engagement, positive attitude\n• Challenge: Job market anxiety in later weeks\n• Historical Success Rate: 91% completion, 83% placement\n\nCareer Switchers (n=3 in sample)\n• Average Overall NPS: 8.3\n• Course A Average: 4.7/5 (Strong foundational grasp)\n• Course B Average: 4.3/5 (Managing transition complexity)\n• CSBT Average: 4.7/5 (High motivation for career change)\n• Main Need: Confidence building, skill validation\n• Support Focus: Foundational reinforcement\n• Historical Success Rate: 85% with mentorship support\n\n🎯 TARGETED RECOMMENDATIONS:\nWorking Professionals: Implement evening session recordings\nFresh Graduates: Maintain current approach, add job prep\nCareer Switchers: Increase 1-on-1 mentoring sessions",
  "segments": {}
}
```

### New Query Type - Aspect-Specific Analysis:
```json
{
  "type": "aspect_analysis",
  "content": "📚 COURSE A SHERPA SUPPORT ANALYSIS\n\nCurrent Performance: 4.3/5 average (↓0.2 from last period)\n\n🔍 DETAILED BREAKDOWN:\nFresh Graduates: 4.0/5 - Slightly below segment average\nWorking Professionals: 4.5/5 - Above average, appreciating flexibility\nCareer Switchers: 4.3/5 - Meeting expectations\n\n📋 FEEDBACK THEMES:\n• Positive (67%): 'Helpful guidance', 'Always available'\n• Concerns (33%): 'Need more proactive check-ins', 'Response time could be faster'\n\n🧠 HISTORICAL CONTEXT:\nSherpa Support typically dips in Week 3-5 as students become more independent\n• Similar pattern in 78% of past cohorts\n• Recovery strategies that worked:\n  - Weekly proactive outreach (improved scores by 0.4 points)\n  - Group Sherpa sessions (85% positive response)\n  - Quick-response protocol (<2 hours): 91% satisfaction\n\n💡 RECOMMENDED INTERVENTIONS:\n1. Implement weekly proactive student outreach\n2. Reduce response time target to under 2 hours\n3. Add optional group Sherpa sessions twice weekly\nExpected Impact: +0.5 point improvement within 2 weeks",
  "aspect": "course_a_sherpa_support",
  "current_score": 4.3,
  "trend": "declining", 
  "interventions": []
}
```

## Database Schema Design

### Enhanced PostgreSQL Tables

```sql
-- Core student data (unchanged)
CREATE TABLE students (
    student_id VARCHAR PRIMARY KEY,
    demographic_type VARCHAR NOT NULL,
    current_grade DECIMAL,
    attendance_rate DECIMAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced NPS responses table for complex survey data
CREATE TABLE nps_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR REFERENCES students(student_id),
    timestamp TIMESTAMP NOT NULL,
    course_id VARCHAR DEFAULT 'masai_fsd_2025',
    week_number INTEGER, -- calculated or derived
    nps_score INTEGER CHECK (nps_score >= 0 AND nps_score <= 10),
    
    -- Core simplified aspects (mapped from complex survey)
    aspect_1_score INTEGER, -- Course A Lecture Experience
    aspect_2_score INTEGER, -- Course B Lecture Experience  
    aspect_3_score INTEGER, -- CSBT Curriculum Design
    
    -- Combined comments field
    comments TEXT,
    
    -- Additional rich data from 24-column survey
    course_a_scores JSONB, -- All 5 Course A aspect scores
    course_b_scores JSONB, -- All 5 Course B aspect scores
    csbt_scores JSONB,     -- All 3 CSBT aspect scores
    dost_support_score INTEGER,
    product_support_scores JSONB, -- All 5 product support scores
    
    -- Processing metadata
    data_source VARCHAR DEFAULT 'complex_survey',
    mapping_confidence DECIMAL DEFAULT 1.0,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced analysis cache for complex queries
CREATE TABLE analysis_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR UNIQUE NOT NULL,
    query_type VARCHAR NOT NULL,
    results JSONB NOT NULL,
    confidence_score DECIMAL,
    data_richness_score DECIMAL, -- NEW: indicates how comprehensive the source data was
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced intervention tracking with aspect-specific data
CREATE TABLE interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR REFERENCES students(student_id),
    intervention_type VARCHAR NOT NULL,
    target_aspect VARCHAR, -- NEW: which specific aspect the intervention targets
    recommended_at TIMESTAMP NOT NULL,
    implemented_at TIMESTAMP,
    success_rating INTEGER,
    aspect_improvement_score DECIMAL, -- NEW: specific improvement in targeted aspect
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- NEW: Aspect performance tracking table
CREATE TABLE aspect_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id VARCHAR REFERENCES students(student_id),
    response_id UUID REFERENCES nps_responses(id),
    aspect_category VARCHAR NOT NULL, -- 'course_a', 'course_b', 'csbt', 'support'
    aspect_name VARCHAR NOT NULL,    -- specific aspect within category
    score INTEGER NOT NULL,
    week_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Enhanced ChromaDB Collections Structure

### Collection 1: comprehensive_student_journeys

**Purpose**: Store rich student progression narratives with all aspect data

**Documents**: "Student fsd25_08001 (Fresh Graduate, Grade: 88.5): Excellent across all dimensions - Course A perfect scores (Lecture:5, Instructor:5, Sherpa:4, Ask&Learn:5, PP:5), Course B maintaining excellence (all 5s), CSBT highly confident (all 5s), strong support satisfaction. Pattern shows high-achiever trajectory typical of top 15% fresh graduates..."

**Metadata**: `{"student_id": "fsd25_08001", "demographic": "Fresh Graduate", "overall_nps": 9, "course_a_avg": 4.8, "course_b_avg": 5.0, "csbt_avg": 5.0, "support_avg": 5.0, "risk_level": "very_low", "data_richness": "comprehensive"}`

### Collection 2: aspect_specific_interventions

**Purpose**: Store successful intervention methods for specific course aspects

**Documents**: "Course A Sherpa Support improvement intervention: Weekly proactive outreach + <2hr response time + optional group sessions. Applied to 23 students showing Sherpa scores <4.0. Results: 87% improved by average 0.6 points within 2 weeks. Most effective for Fresh Graduates and Career Switchers, moderate effect on Working Professionals..."

**Metadata**: `{"intervention_type": "sherpa_support_improvement", "target_aspect": "course_a_sherpa", "success_rate": 0.87, "avg_improvement": 0.6, "applicable_demographics": ["Fresh Graduate", "Career Switcher"], "implementation_time": "2_weeks"}`

### Collection 3: rich_comment_analysis

**Purpose**: Store sentiment-analyzed comments with educational context and aspect-specific feedback

**Documents**: "Mixed feedback from Working Professional Week 5: 'Need more hands-on practice sessions' indicates practical application gap in Course A content delivery. Combined with improvement suggestion and positive overall NPS (8/10) suggests engagement but seeks enhanced practical focus. Similar pattern in 73% of working professionals at complexity transition point..."

**Metadata**: `{"sentiment": "constructive_mixed", "topics": ["practical_application", "course_a_content"], "demographic": "working_professional", "nps_score": 8, "urgency": "medium", "week": 5, "aspect_concern": "course_a_delivery"}`

### Collection 4: comprehensive_weekly_patterns

**Purpose**: Store detailed weekly performance patterns across all aspects

**Documents**: "Week 5 comprehensive pattern analysis: Overall NPS dip from 7.7 to 7.2 driven by Course A→B transition complexity. Course A scores stable (avg 4.6), Course B showing initial adaptation challenges (avg 4.2, down from 4.5). CSBT confidence remains high (4.8). Support systems maintaining strong performance. Historical recovery: 82% of cohorts recover by Week 7 with targeted Course B support interventions..."

**Metadata**: `{"week": 5, "pattern_type": "course_transition_challenge", "affected_aspects": ["course_b_lecture", "course_b_content"], "recovery_rate": 0.82, "best_interventions": ["extra_workshops", "peer_study_groups"], "timeline": "week_7_recovery"}`

### Collection 5: demographic_aspect_patterns (NEW)

**Purpose**: Store aspect-specific performance patterns by demographic

**Documents**: "Working Professionals Course B performance pattern: Consistent 0.3-point lower scores in Lecture Experience due to time constraints for live sessions. Compensated by higher PP Session engagement (+0.4 vs other demographics). Optimal support: recorded lectures + flexible PP scheduling. Success rate: 89% when accommodations provided..."

**Metadata**: `{"demographic": "working_professional", "aspect_focus": "course_b_lecture", "performance_delta": -0.3, "compensation_strength": "pp_sessions", "optimal_intervention": "flexible_scheduling", "success_rate": 0.89}`

## Enhanced LLM Integration Strategy

### Advanced Fallback Chain Implementation

```
Primary: Gemini API (Educational Domain Optimized)
├── Specialized for: Educational survey analysis, comprehensive sentiment analysis, aspect-specific insights
├── Prompts: Enhanced with educational terminology, survey interpretation, multi-dimensional analysis
├── 
├── Fallback 1: Groq API (llama-3.1-8b-instant) 
├── Specialized for: Quick header detection, basic pattern recognition, survey structure understanding
├── 
├── Fallback 2: OpenAI GPT-4
├── Specialized for: Complex reasoning, nuanced educational insights, comprehensive report generation
├──
└── Error Handling: Graceful degradation with cached educational templates and basic analytics
```

## Enhanced Prompt Engineering for Complex Educational Data

### Weekly Report Prompt Template for Complex Survey Data:

```
You are an NPS Intelligence Analyst specializing in educational bootcamp survey analysis. Generate a comprehensive weekly report analyzing 20+ educational aspects per student.

CONTEXT: You have access to rich survey data including:
- Course A aspects: Lecture experience, Instructor delivery, Sherpa support, Ask & Learn effectiveness, PP sessions
- Course B aspects: Same 5 aspects for advanced course content
- CSBT aspects: Curriculum design, Instructor support, General support
- Support systems: Dost support, LMS platform, Assessment platform, Ticketing, PSC sessions, PAI evaluation
- Student feedback: Improvement suggestions + additional comments

Generate report in EXACTLY this format:
📊 NPS Intelligence Report – Week Ending [DATE]
════════════════════════════════════════════

📈 OVERALL METRICS
[Include standard NPS metrics plus data richness indicators]

🧠 INSIGHTS FROM PAST COHORTS  
[Use historical patterns from similar complex survey data]

📚 COMPREHENSIVE ASPECT ANALYSIS
[Break down by Course A, Course B, CSBT, and Support Systems performance]

🚨 STUDENTS NEEDING IMMEDIATE ATTENTION
[Include aspect-specific risk indicators]

👥 DEMOGRAPHIC SEGMENT ANALYSIS
[Compare aspect performance across Fresh Graduates, Working Professionals, Career Switchers]

📉 INDIVIDUAL ALERTS
[Highlight students with concerning patterns in specific aspects]

🎭 ADVANCED SENTIMENT PATTERNS
[Analyze improvement suggestions + additional feedback for hidden insights]

📚 ASPECT-SPECIFIC ISSUES TO FIX
[Prioritize issues by aspect category and impact scope]

💡 COMPREHENSIVE ACTION PLAN
[Include aspect-specific interventions with historical success rates]

📊 NEXT WEEK PREDICTION
[Predict performance across all major aspect categories]

Historical Context: {retrieved_comprehensive_patterns}
Current Rich Data: {current_week_comprehensive_data}  
Aspect Performance: {detailed_aspect_breakdown}
Demographic Patterns: {segment_specific_insights}

Maintain professional educational tone and include confidence levels for all recommendations.
```

### Individual Student Analysis Prompt for Complex Data:

```
Analyze individual student performance across comprehensive educational survey data.

STUDENT CONTEXT:
- Demographics: {demographic_info}
- Overall NPS Journey: {nps_progression}
- Course A Performance: {course_a_detailed_scores}
- Course B Performance: {course_b_detailed_scores}  
- CSBT Readiness: {csbt_detailed_scores}
- Support System Usage: {support_scores_breakdown}
- Feedback Analysis: {improvement_suggestions_and_comments}

HISTORICAL COMPARISON:
- Similar student patterns: {matched_historical_cases}
- Success/risk indicators: {predictive_patterns}
- Intervention effectiveness: {relevant_intervention_history}

Generate analysis in this format:
👤 COMPREHENSIVE STUDENT PROFILE: {student_id}
[Include demographic context and grade/attendance]

📊 DETAILED ASPECT BREAKDOWN:
[Show performance across all 20+ surveyed aspects]

🧠 HISTORICAL COMPARISON:  
[Compare with similar students from past cohorts]

⚠️ RISK ASSESSMENT:
[Include aspect-specific risk indicators]

💡 TARGETED RECOMMENDATIONS:
[Provide aspect-specific interventions with success probabilities]

Include confidence scores and specify which aspects need immediate attention.
```

## Enhanced WebSocket Implementation

### Real-time Update Events for Complex Data

**Connection**: `ws://localhost:8000/ws/{session_id}`

**Enhanced Events:**

1. **upload_progress**: 
   - File processing progress with complexity indicators
   - Header mapping confidence scores
   - Data quality validation updates

2. **complex_analysis_complete**: 
   - Comprehensive analysis across 20+ aspects finished
   - Aspect-specific insight generation complete
   - Rich embedding creation status

3. **enhanced_chat_response**:
   - Streaming responses with aspect-specific insights
   - Real-time confidence scoring
   - Progressive detail addition

4. **aspect_specific_alert**: 
   - Critical performance drops in specific aspects
   - Cross-aspect correlation warnings
   - Demographic-specific urgent patterns

5. **comprehensive_report_ready**:
   - Full weekly reports with rich aspect analysis
   - Segment-specific breakdowns available
   - Historical comparison insights generated

### Enhanced Event Format:

```json
{
  "event_type": "enhanced_chat_response",
  "data": {
    "content": "Analyzing comprehensive student data across 20+ aspects...",
    "progress": 0.65,
    "current_analysis": "course_b_performance_patterns",
    "confidence_building": 0.89,
    "aspects_processed": 15,
    "complete": false,
    "metadata": {
      "data_richness": "comprehensive",
      "analysis_depth": "detailed",
      "historical_matches": 34
    }
  },
  "timestamp": "2025-08-21T10:30:00Z"
}
```

## Frontend Implementation

### Enhanced Tech Stack

- **Framework**: Vite + React 18 with TypeScript
- **State Management**: Zustand for global state management
- **HTTP Client**: Axios with enhanced interceptors for complex data handling
- **Visualizations**:
  - Chart.js for comprehensive educational analytics (20+ aspect radar charts, trend lines)
  - Recharts for complex multi-dimensional analysis (correlation matrices, segment comparisons)
- **Real-time**: WebSocket integration with complex event handling
- **Styling**: Tailwind CSS with educational UI components
- **UI Components**: Custom educational dashboard components

## Simplified Frontend Routes Structure

### Core Application Routes (3 main routes):

#### 1. `/` or `/dashboard` - Overview Dashboard
- High-level metrics and current batch status
- Quick visual summaries (NPS trends, risk alerts)
- Navigation to upload and chat
- Real-time WebSocket updates for critical alerts

#### 2. `/upload` - Data Upload & Processing
- Handle complex 24-column NPS + 4-column demographics files
- Header mapping preview with Groq API results
- Data quality reports and processing status
- One-time setup per batch/cohort

#### 3. `/chat` - RAG-Powered Intelligence Hub
**All analysis types through natural language queries:**
- "Generate weekly report for current batch"
- "Analyze student fsd25_08001 performance"
- "Show demographic segmentation analysis"
- "Analyze Course A Sherpa support issues"
- "Compare Fresh Graduates vs Working Professionals"

### Why This Simplified Approach is Better:

1. **Unified Experience**: Users get all insights through conversational interface
2. **Natural Workflow**: Ask questions naturally instead of navigating complex menus
3. **Flexibility**: RAG can handle complex, nuanced queries that fixed UI forms can't
4. **Reduced Development**: Less frontend complexity, more focus on RAG quality
5. **Better UX**: Chat interface can provide exactly what users need without pre-defining all possibilities

### Enhanced Chat Interface Features:
- **Query Templates**: Quick buttons for common queries ("Weekly Report", "Individual Analysis", "Segment Analysis")