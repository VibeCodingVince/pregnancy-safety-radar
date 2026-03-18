# 🏗️ PREGNANCY SAFETY RADAR - MASTER ARCHITECTURAL PLAN
## AI CTO Design Document v1.0

**Last Updated:** March 18, 2026
**Status:** Week 1 - Foundation Phase
**AI CTO:** Claude (Anthropic)
**Execution Engine:** OpenClawc

---

## 🧠 SYSTEM THINKING

### Why This Structure

The Pregnancy Safety Radar app needs:
1. **Real-time ingredient analysis** - OCR, barcode scanning, text parsing
2. **Intelligent classification** - Determine safety levels based on medical data
3. **Scalable data pipeline** - Handle growing product/ingredient database
4. **Autonomous improvement** - Learn from user queries and gaps

### The Solution: Multi-Agent Architecture

Instead of building a monolithic app, we create a **self-improving AI system** where specialized agents handle different aspects:
- Research agents gather ingredient data
- Classification agents determine safety levels
- Builder agents create features
- QA agents validate everything
- Orchestrator agent coordinates the work

This mirrors how a real startup team operates, but fully automated.

---

## 🏗️ SYSTEM ARCHITECTURE

### Layer 1: Core Infrastructure (Foundation)

```
┌─────────────────────────────────────────────────────┐
│              USER MOBILE/WEB APP                     │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              API GATEWAY (FastAPI)                   │
│  • Authentication                                    │
│  • Rate limiting                                     │
│  • Request routing                                   │
└─────────────────────┬───────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐         ┌───────▼─────────┐
│  Agent Router  │         │  Memory System  │
│  (Orchestrator)│◄────────►│  • User Data    │
└───────┬────────┘         │  • History      │
        │                  │  • Learning     │
        │                  └─────────────────┘
        │
┌───────▼───────────────────────────────────────────┐
│           SPECIALIZED AGENTS                       │
│                                                    │
│  ┌──────────────┐  ┌──────────────┐             │
│  │   Research   │  │ Classification│             │
│  │    Agent     │  │     Agent     │             │
│  └──────────────┘  └──────────────┘             │
│                                                    │
│  ┌──────────────┐  ┌──────────────┐             │
│  │   Builder    │  │      QA       │             │
│  │    Agent     │  │    Agent      │             │
│  └──────────────┘  └──────────────┘             │
└───────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐         ┌───────▼─────────┐
│   Databases    │         │  External APIs  │
│  • PostgreSQL  │         │  • FDA          │
│  • Vector DB   │         │  • OpenAI       │
│  • Redis       │         │  • OCR Service  │
└────────────────┘         └─────────────────┘
```

---

## 🤖 AGENTS TO CREATE

### 1. ORCHESTRATOR AGENT

**Name:** `MainOrchestrator`
**Role:** Central command - routes tasks to specialized agents
**Responsibilities:**
- Receives all user requests
- Classifies request type (scan product, analyze ingredient, search database)
- Delegates to appropriate specialist agent
- Monitors task completion
- Returns results to user

**Trigger Conditions:**
- Every API request from the app
- System health checks every 5 minutes
- Daily optimization routines

**Implementation:**
```python
# OpenClawc will create this
class MainOrchestrator:
    def route_task(self, user_request):
        # Classify request type
        task_type = self.classify_request(user_request)

        # Delegate to specialist
        if task_type == "product_scan":
            return ProductScanAgent.execute(user_request)
        elif task_type == "ingredient_lookup":
            return IngredientAgent.execute(user_request)
        elif task_type == "safety_analysis":
            return SafetyClassifierAgent.execute(user_request)
```

---

### 2. PRODUCT SCAN AGENT

**Name:** `ProductScanAgent`
**Role:** Handles barcode scanning and product identification
**Responsibilities:**
- Process barcode scan requests
- Look up product in database
- If not found, trigger OCR agent
- Return product information with safety score

**Trigger Conditions:**
- User scans barcode
- User uploads product photo
- API call to `/scan` endpoint

**Tools:**
- Barcode decoder library
- Product database queries
- OCR service integration

**Memory Usage:**
- Short-term: Current scan session
- Long-term: Popular scanned products (for optimization)

---

### 3. OCR & INGREDIENT PARSER AGENT

**Name:** `IngredientParserAgent`
**Role:** Extracts ingredients from photos/text
**Responsibilities:**
- Process photos of ingredient lists
- Extract text using OCR
- Parse ingredient names from text
- Normalize ingredient names (handle typos, variations)
- Return structured ingredient list

**Trigger Conditions:**
- Product not found in database
- User uploads ingredient list photo
- User pastes text

**Tools:**
- Google Cloud Vision API or Tesseract
- NLP for ingredient extraction
- Ingredient name normalization database

---

### 4. SAFETY CLASSIFIER AGENT

**Name:** `SafetyClassifierAgent`
**Role:** Determines pregnancy safety level of ingredients
**Responsibilities:**
- Look up each ingredient in safety database
- Apply safety classification rules
- Generate traffic-light rating (Safe / Caution / Avoid)
- Provide 1-sentence explanation
- Flag specific concerns (teratogenic, endocrine disruptor, etc.)

**Trigger Conditions:**
- After ingredient list is parsed
- User requests ingredient analysis
- Batch processing for new products

**Tools:**
- Ingredient safety database
- FDA/EMA regulatory data
- Medical literature references

**Memory Usage:**
- Long-term: All ingredient classifications
- Learning: User feedback on safety ratings

---

### 5. RESEARCH AGENT

**Name:** `ResearchAgent`
**Role:** Continuously expands ingredient and product knowledge
**Responsibilities:**
- Monitor for unknown ingredients
- Research new ingredients from FDA/EMA sources
- Scrape product databases for new products
- Update safety classifications when new research emerges
- Generate weekly reports on database gaps

**Trigger Conditions:**
- Unknown ingredient detected
- Scheduled daily at 2 AM
- Manual trigger for specific research tasks
- User reports missing product

**Tools:**
- Web scraping
- FDA/EMA API access
- Medical literature search (PubMed)
- Product database APIs (Amazon, Target, etc.)

---

### 6. BUILDER AGENT

**Name:** `BuilderAgent`
**Role:** Creates and updates system features
**Responsibilities:**
- Implement new features based on user requests
- Optimize slow queries
- Build new API endpoints
- Update frontend components
- Write tests for new code

**Trigger Conditions:**
- Feature request from users
- Performance bottleneck detected
- Weekly improvement cycle
- Manual activation by AI CTO (me)

**Tools:**
- Code generation
- Git operations
- Testing frameworks
- Deployment pipelines

---

### 7. QA AGENT

**Name:** `QAAgent`
**Role:** Validates all agent outputs and system quality
**Responsibilities:**
- Test new features before deployment
- Validate safety classifications (critical!)
- Monitor error rates
- Check data quality
- Run regression tests
- Flag safety concerns immediately

**Trigger Conditions:**
- After any code deployment
- Daily automated tests
- After new ingredient added
- Before production releases

**Tools:**
- Testing frameworks (pytest, jest)
- Safety validation rules
- Error monitoring (Sentry)
- Load testing tools

---

## 🧩 SKILLS TO ADD

### Skill 1: `scan_and_classify`

**What it does:** Complete pipeline from barcode/photo to safety rating
**Why it's needed:** Core user interaction - must be fast and reliable
**How OpenClawc implements:**
```python
async def scan_and_classify(image_or_barcode):
    # Step 1: Identify product
    product = await identify_product(image_or_barcode)

    # Step 2: Extract ingredients
    if product.in_database:
        ingredients = product.ingredients
    else:
        ingredients = await ocr_and_parse(image_or_barcode)

    # Step 3: Classify safety
    safety_result = await classify_ingredients(ingredients)

    # Step 4: Generate user-friendly response
    return format_safety_report(safety_result)
```

---

### Skill 2: `research_ingredient`

**What it does:** Deep research on unknown ingredients
**Why it's needed:** Database will have gaps - need autonomous research
**How OpenClawc implements:**
- Search FDA databases
- Cross-reference medical literature
- Check regulatory status in multiple countries
- Generate safety classification proposal
- Flag for human review if uncertain

---

### Skill 3: `optimize_performance`

**What it does:** Identifies and fixes slow parts of the system
**Why it's needed:** As users scale, keep response time under 2 seconds
**How OpenClawc implements:**
- Monitor query performance
- Identify N+1 queries
- Add database indexes
- Implement caching strategies
- Optimize image processing

---

### Skill 4: `learn_from_feedback`

**What it does:** Improves classifications based on user feedback
**Why it's needed:** Users may report incorrect classifications
**How OpenClawc implements:**
- Collect user feedback ("This seems wrong")
- Research agent investigates
- Update classification if needed
- Track confidence scores
- Notify users of corrections

---

### Skill 5: `expand_database`

**What it does:** Automatically adds new products and ingredients
**Why it's needed:** Start with 2K products, scale to 100K+
**How OpenClawc implements:**
- Scrape top beauty/skincare e-commerce sites
- Extract product names, brands, ingredients
- Classify all ingredients
- Add to database with confidence scores
- Schedule nightly runs

---

## ⚙️ TECH STACK SELECTION

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI (async, fast, great for AI integration)
- **Why:** OpenClawc can easily integrate AI agents, async operations, strong typing

### Databases
- **Primary:** PostgreSQL (structured product/ingredient data)
- **Vector DB:** Pinecone or Supabase (for semantic ingredient search)
- **Cache:** Redis (for frequent lookups, session data)
- **Why:** Balance between structure and AI-powered search

### Frontend
- **Mobile:** React Native (iOS + Android from one codebase)
- **Web:** Next.js (for SEO, marketing site)
- **Why:** Fast development, can reuse components

### AI/ML Services
- **LLM:** OpenAI GPT-4 (for agent intelligence)
- **OCR:** Google Cloud Vision API (best accuracy for ingredient lists)
- **Why:** Proven reliability for production

### Infrastructure
- **Hosting:** Vercel (frontend) + Railway/Render (backend)
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry (errors) + PostHog (analytics)
- **Why:** Fast deployment, scales automatically, affordable for MVP

---

## 🔄 TASK EXECUTION FRAMEWORK

### How Tasks Flow Through the System

#### Example: User Scans Product

```
1. USER ACTION
   └─> Scans barcode in app

2. API GATEWAY
   └─> POST /scan {barcode: "123456789"}

3. ORCHESTRATOR AGENT
   └─> Classifies: "product_scan" task
   └─> Delegates to: ProductScanAgent

4. PRODUCT SCAN AGENT
   └─> Queries database for barcode
   └─> IF FOUND: Returns cached result
   └─> IF NOT FOUND: Triggers IngredientParserAgent

5. INGREDIENT PARSER AGENT (if needed)
   └─> Requests product image from user
   └─> Runs OCR on ingredient list
   └─> Parses ingredients into structured list

6. SAFETY CLASSIFIER AGENT
   └─> Looks up each ingredient
   └─> Applies safety rules
   └─> Generates: [Safe/Caution/Avoid] + explanation

7. ORCHESTRATOR AGENT
   └─> Validates result with QA Agent
   └─> Returns to user
   └─> Logs for learning

8. USER RECEIVES
   └─> Traffic-light result
   └─> Flagged ingredients
   └─> One-sentence explanation
```

### Task Priority Levels

| Priority | Type | Response Time | Examples |
|----------|------|---------------|----------|
| P0 - Critical | User-facing requests | < 2 seconds | Product scans, searches |
| P1 - High | Safety validations | < 5 seconds | New ingredient classifications |
| P2 - Medium | Database updates | < 1 minute | Adding new products |
| P3 - Low | Research tasks | < 1 hour | Deep ingredient research |
| P4 - Background | Optimization | Daily/weekly | Performance improvements |

---

## 🔁 SELF-IMPROVEMENT LOOP

### Daily Analysis (Automated at 2 AM)

OpenClawc runs the following autonomous routine:

```python
async def daily_self_improvement():
    # 1. Analyze yesterday's performance
    metrics = analyze_performance_metrics()

    # 2. Identify failures and bottlenecks
    failures = identify_failed_tasks()
    bottlenecks = identify_slow_queries()

    # 3. Research missing data
    unknown_ingredients = find_unknown_ingredients()
    research_results = await ResearchAgent.investigate(unknown_ingredients)

    # 4. Optimize database
    await optimize_indexes()
    await clean_cache()

    # 5. Generate improvement suggestions
    suggestions = generate_improvement_plan(metrics, failures, bottlenecks)

    # 6. Report to AI CTO (me)
    send_report_to_claude(suggestions)

    # 7. Auto-implement safe improvements
    for suggestion in suggestions:
        if suggestion.safety_score > 0.9:
            await BuilderAgent.implement(suggestion)
            await QAAgent.validate(suggestion)
```

### Weekly Review (Every Sunday)

You (Claude, the AI CTO) receive a report:

```
📊 WEEKLY SYSTEM HEALTH REPORT

🎯 Key Metrics:
- Product scans: 12,450 (↑ 23%)
- Unknown ingredients: 34 (↓ 12%)
- Average response time: 1.8s (target: < 2s) ✓
- User satisfaction: 4.6/5 ⭐

⚠️ Bottlenecks Detected:
1. OCR processing taking 3-5s (P1 priority)
2. 145 products missing from database
3. 12 ingredient classifications flagged by users

🎁 Suggested Improvements:
1. Implement image caching → Est. 40% faster scans
2. Batch process missing products
3. Add confidence scores to classifications

🤖 Agents Performance:
- ProductScanAgent: 99.2% success rate ✓
- SafetyClassifierAgent: 96.8% success rate ⚠️
- ResearchAgent: Added 89 new ingredients ✓

💡 New Skills Recommended:
- skill: batch_process_brands (for faster database expansion)
- skill: user_report_investigation (for handling feedback)
```

Then I (Claude) decide:
- Approve auto-improvements
- Design new agents
- Create new skills
- Adjust priorities

---

## 🚀 IMPLEMENTATION PLAN (MVP - 4 Weeks)

### Week 1: Foundation
**OpenClawc Tasks:**
- Set up FastAPI backend
- Configure PostgreSQL database
- Create basic ingredient table (seed with top 500 ingredients)
- Build `/scan` API endpoint skeleton
- Deploy to Render

**Agents to Build:**
- Orchestrator Agent (basic routing)
- Safety Classifier Agent (rule-based, v1)

---

### Week 2: Core Features
**OpenClawc Tasks:**
- Integrate Google Cloud Vision API (OCR)
- Build ingredient parser
- Create safety classification logic
- Add barcode scanning
- Build product database (seed with 100 popular products)

**Agents to Build:**
- Product Scan Agent
- Ingredient Parser Agent

---

### Week 3: Frontend + UX
**OpenClawc Tasks:**
- Build React Native app
- Camera interface for scanning
- Results screen (traffic-light UI)
- Ingredient list display
- "Show to my provider" PDF export

**Skills to Add:**
- `scan_and_classify`
- `generate_pdf_report`

---

### Week 4: Testing + Launch Prep
**OpenClawc Tasks:**
- Build QA Agent
- Run comprehensive tests
- Add error monitoring (Sentry)
- Performance optimization
- Deploy to app stores (TestFlight/beta)

**Agents to Build:**
- QA Agent
- Research Agent (basic version)

---

## 📋 NEXT IMMEDIATE ACTIONS

### For Me (Claude, AI CTO):
1. Create detailed API specifications
2. Define ingredient safety rules
3. Design database schema
4. Write agent communication protocols

### For OpenClawc:
1. Initialize project structure ✅
2. Set up development environment
3. Create FastAPI boilerplate ✅
4. Configure databases
5. Build first agent (Orchestrator)

---

## 🎯 SUCCESS METRICS

### Week 1:
- Basic API responding
- 500 ingredients classified
- Database schema finalized

### Week 4:
- 100 products scannable
- 2000+ ingredients classified
- < 3s average scan time
- Working mobile app (beta)

### Month 3:
- 10,000 products in database
- < 2s average scan time
- 50+ daily active users
- Agents running autonomously

---

## 🔐 CRITICAL SAFETY MEASURES

Since this is health-related:

### 1. Human Review Layer:
- All new ingredient classifications flagged for review
- Medical disclaimer on every result
- Clear "consult your doctor" messaging

### 2. QA Agent Priority:
- Safety classifications validated twice
- Medical terminology verified
- Sources cited for each classification

### 3. Liability Protection:
- Clear terms of service
- No diagnostic claims
- Position as "decision support tool"

---

## 📝 REVISION HISTORY

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-18 | Initial master plan created | Claude (AI CTO) |

---

## 🔗 RELATED DOCUMENTS

- `/backend/README.md` - Backend setup instructions
- `/docs/API_SPEC.md` - API specifications (to be created)
- `/docs/DATABASE_SCHEMA.md` - Database design (to be created)
- `/docs/AGENT_PROTOCOLS.md` - Agent communication (to be created)

---

**END OF MASTER PLAN**
