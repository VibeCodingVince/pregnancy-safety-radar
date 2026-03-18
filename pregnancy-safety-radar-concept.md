# Pregnancy Safety Radar - Market Research & Concept

## 1. What TikTok users are actually doing

### Observed behavior
- Pregnant users and TTC (trying to conceive) users search and watch content under hashtags like #pregnancysafeskincare, #pregnancysafemakeup, and #ingredientchecker.
- Creators walk through ingredient lists on camera, often with screenshots of product pages or zoomed-in labels, explaining which ingredients to avoid and why.
- TikTok discovery pages explicitly highlight "app to check for pregnancy safe products" and "best app for tracking if products are pregnancy safe," indicating sustained search demand.

### User comments & friction (from TikTok + forums)
Users frequently ask variants of:
- "Is there an app for this lol?" under videos where creators manually check labels.
- "My midwife said be careful with ingredients but didn't say which ones…"
- On Reddit's r/pregnant, users request "apps/websites that tell you safe ingredients (food/skincare)," mentioning they feel overwhelmed reading labels and Googling each item.

### Manual "hacks" and multi-app behavior
People currently rely on:
- General ingredient scanners like Yuka for cosmetics, which rate products on health but not pregnancy-specific safety.
- Specialty pregnancy apps (Ovia, others) mainly for food guidance, not detailed cosmetic ingredient safety.
- Niche pregnancy-safety apps such as Little Bean and MamaSkin, plus websites like 15minutebeauty.com, often used together.

**This multi-app behavior signals demand that is not fully satisfied by any single, trusted, simple tool.**

## 2. Existing solutions and where they fall short

### Representative existing app: MamaSkin
MamaSkin positions itself as "#1 pregnancy-safe skincare & beauty ingredient checker" with:
- A database of 85,000+ products and 9,000+ brands.
- Ingredient safety scoring based on FDA, EMA, and NHS guidance.
- Ingredient flagging with a dedicated "MamaSkin Safety Score" and detailed explanations.

There are also other apps like Little Bean and Doola that cover food and skincare, sometimes on a subscription model.

### Gaps and failure modes
From TikTok activity plus Reddit feedback, you can infer several pain-points that existing apps still do not nail:

**Fragmentation and scope confusion**
- Some apps handle food, some skincare, some both—but users still ask for "apps/websites that tell you safe ingredients (food/skincare)" in one place.
- Users might use Yuka for safety scores, MamaSkin/Little Bean for pregnancy safety, and Google or niche blogs for edge cases.

**Trust and transparency**
- Pregnancy is high-anxiety: users want to know "where does this guidance come from?"
- MamaSkin emphasizes evidence-based scores and medical vocabulary (teratogenic, contraindicated, endocrine disruptor, fetotoxic) with plain-language explanations, which helps—but smaller or less transparent apps don't always do this.
- Users still often double-check apps by visiting blogs like 15minutebeauty.com or asking their provider.

**UX friction at the point of use**
- Most current tools are product-first: scan a barcode and see a score. That works in stores but not as well when:
  - Buying from international or indie brands that may not be in the database.
  - Copy-pasting ingredients from an online listing.
- Users often end up manually typing or visually scanning ingredients in multiple places.

**Narrow focus (cosmetics only) vs real user mental model (everything I put in/on my body)**
- TikTok and Reddit users think in terms of "is this safe to use in pregnancy?" across skincare, makeup, haircare, and sometimes medications or supplements, not just cosmetics.
- There is a clear interest in a more holistic "safety hub," at least as a roadmap, even if v1 focuses on skincare.

**These gaps create an opening for a focused, highly usable app even if competing products exist.**

## 3. Refined app concept: "Pregnancy Safety Radar"

### Core positioning
A "Pregnancy Safety Radar" app that acts as a single, easy, trustworthy layer between:
- Product labels / ingredient lists.
- High-quality regulatory data and medical literature (abstracted away from the user).

**Clear, emotionally resonant promise:** "Snap or paste any ingredient list and get a traffic-light answer plus one-sentence reasoning."

### 3.1 Core features (MVP)

**Multi-mode input for real life**
- Barcode scan for common products (where database coverage exists).
- Photo of ingredient list (OCR) for:
  - International brands.
  - Online shopping (user screenshots the page).
- Paste-in mode for copying ingredient lists from websites or TikTok captions/descriptions.

**Traffic-light answer with targeted detail**

Output:
- "Generally considered safe in pregnancy"
- "Use with caution / talk to provider"
- "Avoid in pregnancy"

Each result includes:
- 1-line explanation (e.g., "Contains retinoid derivative, often avoided in pregnancy due to potential teratogenic risk.").
- List of flagged ingredients with simple labels: "Potential endocrine disruptor," "Limited pregnancy data," etc., mirroring MamaSkin's evidence-based style but simplified.

**Scope v1: skincare & cosmetics**
- Start where TikTok content is the hottest: skincare and makeup.
- Cover everyday products: cleansers, moisturizers, serums, sunscreens, foundations, concealers, lip products, and hair treatments.

**"Ask a pharmacist/doctor" handoff**
For edge cases or ambiguous results, the app can:
- Generate a PDF or note summarizing ingredients and flags to show to a provider.
- Provide "questions to ask your doctor/midwife," which many users lack.

### 3.2 Differentiators vs existing players
- **Input flexibility:** not just barcode scanning; heavy emphasis on OCR and copy-paste to match how real users shop and consume TikTok content.
- **Opinionated simplicity:** only pregnancy-related risk signal + very short reason, not generalized health/nutrition scoring like Yuka.
- **Honest uncertainty:** explicit "We don't know / limited data" state for some ingredients, which actually increases trust in this category.
- **Future-proof roadmap:** ability to add modules later (food, over-the-counter meds, supplements) in a consistent UX.

## 4. Data, safety, and regulatory approach (high-level)
This category is sensitive, so the product has to feel responsible from day one.

### Evidence sources
MamaSkin openly states they rely on peer-reviewed research from FDA, EMA, and NHS.

A similar approach would:
- Compile a curated, versioned ingredient dataset with: name, aliases, regulatory status, known pregnancy concerns (if any), and evidence rating.
- Distill into a simple risk band + status for consumer use, similar to the "No known risks / Minor cautions / Avoid or specialist discussion" bands MamaSkin uses.

### Risk communication
Emulate best practices visible in MamaSkin's public explanation:
- Use medical terms (teratogenic, endocrine disruptor, fetotoxic) but always accompanied by plain-language explanation.
- Avoid absolute claims ("safe" vs "unsafe") and instead use "no known pregnancy-specific concerns at typical concentrations," etc.

### Legal positioning
Very clear disclaimers:
- "This app does not provide medical advice. Always consult your healthcare provider before making decisions."
- Emphasize "decision support" not diagnostic claims.

## 5. MVP scope, tech, and UX tightly defined

### MVP scope (3–4 months of focused build)

**Backend & data**
- Seed with 1–2k of the most common skincare ingredients, each tagged with:
  - Hazard band (no known risk / minor caution / avoid).
  - Short explanation sentence.
- Simple product database for 1–2 major markets (e.g., North America + EU) with a few thousand high-traffic products.

**Core flows**

*Onboarding:*
- Ask "Pregnant, TTC, or breastfeeding?" to adjust framing and disclaimers.

*Use flow:*
- Open app → scan barcode or take photo → show traffic-light result with explanation and flagged ingredients.

*"Unknown product" fallback:*
- If product not in DB: run OCR on ingredient list → match ingredients → compute safety band → show result.

**UX principles**
- One main screen: camera scanner + paste box.
- Result page with: status pill, 1 explanation sentence, list of flagged ingredients, and a "Show this to my provider" export.
- No account required for basic use to reduce friction.

**Tech implications**
- OCR and barcode scanning can be done with off-the-shelf SDKs.
- Ingredient matching can be rule-based initially (normalized names, regex for common aliases).
- Data entry can start manual/curated and be expanded over time.

## 6. Monetization, growth, and virality

### Monetization

**Freemium**
- Free:
  - X scans per month (e.g., 15), basic traffic-light result, simple explanations.
- Paid (subscription):
  - Unlimited scans.
  - Detailed ingredient breakdown and history log.
  - Priority coverage requests (ask for new products/brands to be added).

**Affiliate revenue**
- When a product is flagged as high-risk, suggest safe alternatives available at major retailers or online shops (with affiliate links).

### Virality hooks (TikTok-native)
- Auto-generate "green / red flag" screenshots of product results that users can share in their TikToks and stories.
- Provide an in-app "creator mode" that:
  - Generates a simple script + overlay for creators doing ingredient breakdown videos.
  - Displays your brand watermark, turning their content into your distribution.

### Why this can be habit-forming
- Many pregnant users re-scan the same products as pregnancy progresses or when they change routines.
- New products and recommendations from TikTok and Instagram provide constant triggers to "just check it quickly."
- A lightweight history ("Recently checked") gives a sense of progress and reduces anxiety—users see a growing list of "ok" products.

## 7. Next steps and positioning in a crowded niche
Even though apps like MamaSkin, Little Bean, and Doola exist, the space is far from saturated:

TikTok and Reddit show continued "is there an app for this?" questions, indicating that existing solutions are not yet dominant or fully trusted.
