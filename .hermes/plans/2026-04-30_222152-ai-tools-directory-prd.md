# Vertical AI Tools Directory PRD

> **For Hermes:** This is a planning artifact only. Do not implement from this file without a separate execution step.

**Goal:** Build a niche AI tools discovery, evaluation, and monetization platform that helps a specific audience choose the right tools faster, starting with an MVP that can launch quickly on a near-zero-cost stack.

**Architecture:** The product starts as a content-driven discovery platform: structured tool listings, category pages, comparison pages, and editorial reviews. The moat is not the directory itself but the decision-support layer: Chinese-friendly guidance, scenario-based recommendations, and practical comparison content.

**Tech Stack:** Cloudflare Pages, Cloudflare Workers, Neon or Supabase Postgres, Cloudflare R2, Resend, UptimeRobot.

---

## 1. Product Summary

### 1.1 Product Name
Working name: Vertical AI Tools Directory

### 1.2 One-Sentence Description
A curated AI tools discovery platform that helps a defined user segment quickly find, compare, and choose the right tools for real-world workflows.

### 1.3 Product Positioning
This is not a generic "AI tools list" site. It is a vertical decision-support platform for one audience, one set of use cases, and one language/context advantage.

### 1.4 Recommended Initial Positioning
Start with one narrow segment instead of a general AI catalog. Candidate directions:
- AI tools for Chinese content creators
- AI tools for job seekers and students
- AI tools for indie hackers and small teams
- AI tools for cross-border sellers and marketers

Recommended default for MVP:
- AI tools for Chinese content creators and operators

Reason:
- User pain is clear
- Tool usage is frequent
- Comparison intent is strong
- Content and SEO opportunities are rich
- Monetization can include affiliate, sponsorship, and consulting/services

---

## 2. Problem Statement

Users interested in AI tools face three problems:
- Too many tools, too little trustworthy guidance
- Generic tool directories do not answer scenario-specific questions
- International reviews often ignore Chinese language support, domestic accessibility, payment friction, and local workflow fit

As a result, users waste time testing tools, choose poor-fit products, or abandon adoption altogether.

---

## 3. Product Vision

Create the most useful Chinese decision-support destination for a targeted class of AI tools by combining:
- structured listings
- honest editorial evaluation
- scenario-based recommendations
- comparison content
- practical onboarding guidance

Long-term, the site should function as:
- a discovery engine for users
- a distribution channel for tool vendors
- a lead-generation and media asset for higher-margin services

---

## 4. Goals and Non-Goals

### 4.1 MVP Goals
- Launch a polished vertical directory with enough content to feel credible
- Help users answer "which tool should I use for this scenario?"
- Capture SEO traffic from long-tail, high-intent keywords
- Create the foundation for affiliate revenue and paid placement
- Validate whether users engage more with reviews, comparisons, or category pages

### 4.2 Business Goals
- Reach first organic traffic without paid acquisition
- Generate first monetizable clicks via affiliate or partner links
- Collect early submissions from tool makers
- Build an email list for repeat traffic and future sponsorship inventory

### 4.3 Non-Goals for MVP
- No large-scale community features
- No user-generated public reviews at launch
- No complex account system for normal visitors
- No fully automated bulk scraping pipeline as the main content engine
- No "all AI tools" positioning

---

## 5. Target Users

### 5.1 Primary Users
Chinese-speaking operators, creators, and small teams who want practical AI tools for specific workflows.

Examples:
- Xiaohongshu operators
- public account editors
- short-video script creators
- small business marketers
- freelancers handling content production

### 5.2 Secondary Users
- Tool founders seeking exposure
- power users looking for alternatives, comparisons, and updates
- agencies needing faster internal tool selection

### 5.3 User Needs
Primary questions the product must answer:
- Which tool is best for my scenario?
- Is it free or worth the price?
- Does it support Chinese well?
- Can I use it smoothly from China?
- What are the tradeoffs compared with alternatives?
- Is there a better tool for beginners or teams?

---

## 6. Core Value Proposition

For users:
- Save research time
- Reduce trial-and-error cost
- Get scenario-based recommendations instead of generic lists

For tool vendors:
- Reach qualified, intent-rich traffic
- Gain sponsored visibility opportunities
- Get leads from a trusted, niche audience

For the business:
- Build compounding SEO assets
- Monetize through affiliate, sponsorship, and services
- Use content as a funnel into higher-value consulting or implementation

---

## 7. MVP Scope

### 7.1 Must-Have Pages
- Home page
- Category pages
- Tool detail pages
- Comparison / alternative pages
- Submission page for tool listing requests
- About / methodology page
- Basic newsletter/email capture module

### 7.2 Must-Have Functional Features
- Search by tool name
- Filter by category, pricing, Chinese support, domestic accessibility, use case
- Structured metadata for each tool
- Outbound click tracking
- Admin content entry or lightweight CMS workflow
- SEO metadata management
- Submission form for new tools

### 7.3 Must-Have Content Types
- Tool listing entries
- Category landing pages
- Scenario pages
- Comparison pages
- Best-of / ranking articles

### 7.4 Explicitly Out of Scope for MVP
- User accounts for end users
- Commenting system
- Public rating and review system
- Browser extension
- Advanced personalized recommendation engine
- Full scraping-based self-updating corpus

---

## 8. Information Architecture

### 8.1 Core Entities
- Tool
- Category
- Tag
- Use case
- Editorial review
- Comparison page
- Submission
- Outbound click event
- Newsletter subscriber

### 8.2 Suggested Site Structure
- `/`
- `/categories/[slug]`
- `/tools/[slug]`
- `/compare/[slug]`
- `/best/[slug]`
- `/use-cases/[slug]`
- `/submit`
- `/about`

### 8.3 Navigation Model
Top navigation:
- Categories
- Best Tools
- Comparisons
- Use Cases
- Submit a Tool

Home page sections:
- Hero + search
- Featured categories
- Editor picks
- Latest comparisons
- Best tools by scenario
- New tools or updated tools
- Email subscribe CTA

---

## 9. Detailed Feature Requirements

### 9.1 Home Page
Purpose:
- explain value instantly
- drive users into high-intent paths
- build trust with curated content

Requirements:
- clear niche positioning headline
- search bar
- featured categories
- featured tools
- comparison content blocks
- newsletter CTA
- partner/sponsor area reserved but optional for launch

Success criteria:
- users can navigate to a relevant category or tool within one click

### 9.2 Category Page
Purpose:
- rank for long-tail keywords
- organize options for a scenario or tool class

Requirements:
- intro copy with category context
- list of tools with filters and sort options
- editor recommendations
- related comparison links
- FAQ block for SEO

Possible filters:
- free / paid
- Chinese support
- available in China
- beginner-friendly
- team-friendly
- API support

### 9.3 Tool Detail Page
Purpose:
- help users decide whether to click through or keep comparing

Required fields:
- tool name
- tagline
- official URL
- pricing summary
- Chinese support status
- domestic accessibility notes
- main use cases
- key features
- pros
- cons
- suitable for
- not suitable for
- alternatives
- screenshots
- editorial verdict
- last updated date

Required modules:
- outbound CTA button
- related tools
- comparison links
- alternative tools block
- structured FAQ or notes section

### 9.4 Comparison Page
Purpose:
- capture high-commercial-intent keywords
- improve affiliate and outbound conversion

Examples:
- `tool-a-vs-tool-b`
- `best-ai-writing-tools-for-xiaohongshu`
- `chatgpt-alternatives-for-chinese-users`

Requirements:
- side-by-side comparison table
- scenario recommendation summary
- pricing comparison
- who should choose which tool
- direct CTA links

### 9.5 Use Case / Best-of Pages
Purpose:
- capture scenario and search-intent traffic
- provide editorial entry points

Examples:
- best AI tools for Xiaohongshu content planning
- best AI tools for Chinese social media copywriting
- best AI tools for short-video script writing

Requirements:
- intent-matched intro
- curated recommendations
- ranking logic or methodology note
- internal links to detail and comparison pages

### 9.6 Tool Submission Page
Purpose:
- collect founder/vendor interest
- create future monetization pipeline

Fields:
- tool name
- website URL
- contact email
- category
- short description
- target audience
- pricing info
- Chinese support status
- notes

Optional future fields:
- apply for featured placement
- sponsorship interest

### 9.7 Admin Content Workflow
MVP approach:
- lightweight internal admin or manual DB/CMS entry

Needs:
- create/edit tools
- create/edit categories
- mark featured tools
- publish/unpublish content
- review incoming submissions

Recommended implementation direction:
- simplest possible internal form or headless CMS-like workflow
- avoid overbuilding a full back-office initially

### 9.8 Analytics and Tracking
Track:
- page views
- search usage
- filter usage
- outbound tool clicks
- click-through rate per tool
- submission form conversion
- email subscription conversion

Use the data to learn:
- which categories attract demand
- which tools get clicks but low retention
- which page types convert best

---

## 10. Content Strategy

### 10.1 Launch Content Minimum
Before launch, aim for:
- 30 to 50 tool entries
- 5 to 8 category pages
- 10 comparison pages
- 5 best-of pages
- 1 methodology page explaining evaluation criteria

### 10.2 Editorial Standards
Every tool entry should answer:
- who is this for
- what problem does it solve
- what are the tradeoffs
- what are the realistic alternatives
- what local usage friction exists for Chinese users

### 10.3 Differentiation Rules
Do not publish thin pages that only contain:
- tool logo
- one-line description
- raw feature list
- outbound link

Each page must include actual decision-support value.

### 10.4 SEO Principles
Prioritize long-tail intent pages such as:
- best tools for a scenario
- tool alternatives
- tool comparisons
- pricing and worth-it analysis
- beginner-friendly recommendations

---

## 11. Monetization Model

### 11.1 Phase 1: Affiliate Revenue
Primary early monetization path.

Requirements:
- place trackable outbound links
- prioritize comparison and best-of pages
- label partnerships transparently when needed

### 11.2 Phase 2: Sponsored Placement
Examples:
- featured category slot
- homepage featured block
- newsletter mention
- sponsored review or launch post

Guardrails:
- clearly label sponsorships
- do not compromise overall trust

### 11.3 Phase 3: Lead Generation / Services
Potential services:
- AI tool selection consulting
- workflow setup for teams
- content automation stack recommendations
- private recommendation lists for niche user groups

### 11.4 Phase 4: Newsletter / Media Asset
Build an owned audience for recurring monetization through:
- sponsorships
- curated updates
- premium content later if demand exists

---

## 12. Success Metrics

### 12.1 Product Metrics
- organic landing page count
- average pages per session
- category-to-detail click-through rate
- detail-page outbound click-through rate
- search usage rate
- email subscription rate
- tool submission count

### 12.2 Business Metrics
- affiliate clicks
- affiliate conversion rate if measurable
- sponsor inquiries
- paid placement revenue
- cost to maintain content

### 12.3 MVP Validation Benchmarks
Within the first validation cycle, look for:
- repeated organic traffic to a few high-intent pages
- consistent outbound clicks from comparison/detail pages
- manual submissions from vendors or founders
- at least one monetization signal before scaling content effort

---

## 13. Risks and Mitigations

### 13.1 Risk: Generic Positioning
Risk:
- product becomes another undifferentiated AI directory

Mitigation:
- force narrow audience and scenario focus
- publish locally relevant decision criteria

### 13.2 Risk: Thin SEO Content
Risk:
- search engines treat pages as low-value directory spam

Mitigation:
- require editorial commentary on every important page
- favor fewer high-quality pages over bulk generation

### 13.3 Risk: Low Monetization Despite Traffic
Risk:
- visitors browse but do not convert into revenue

Mitigation:
- prioritize commercial-intent page types early
- add comparison content, alternatives, and explicit CTA paths

### 13.4 Risk: Maintenance Overhead
Risk:
- tools change pricing/features rapidly

Mitigation:
- store `last_updated`
- prioritize high-traffic pages for refreshes
- keep launch corpus intentionally small and curated

### 13.5 Risk: Overbuilding the Product
Risk:
- too much engineering before validating content-market fit

Mitigation:
- build the smallest credible content platform first
- optimize manual workflows before automation

---

## 14. Assumptions

- Organic search will be a primary acquisition channel
- Users care about Chinese support and China accessibility enough to create differentiation
- High-intent comparison content will monetize better than generic listings
- A narrow niche has better odds than a broad AI tools catalog
- Manual curation is acceptable for MVP and preferable to automated low-quality ingestion

---

## 15. Open Questions

These should be resolved before implementation begins:
- Which exact niche should be chosen for launch?
- Should the site prioritize editorial reviews or structured database pages first?
- Is the first monetization target affiliate, paid inclusion, or sponsor leads?
- Should the admin workflow be database-first or headless CMS-first?
- Will email capture be a core CTA from day one or secondary?
- What evaluation framework should be visible to users?

---

## 16. Recommended MVP Launch Sequence

### Phase 0: Positioning Decision
Choose one niche and define:
- target user
- top 3 scenarios
- evaluation criteria
- content thesis

### Phase 1: Content Foundation
Prepare:
- first 30 to 50 tools
- category taxonomy
- first 10 comparison pages
- first 5 scenario pages

### Phase 2: Product Build
Implement:
- directory browsing
- tool detail pages
- search/filtering
- submissions
- click tracking
- basic analytics

### Phase 3: Soft Launch
Launch to:
- niche communities
- social content channels
- founder groups
- direct outreach for tool submissions

### Phase 4: Learn and Iterate
Analyze:
- which page type attracts traffic
- which page type converts clicks
- which category has the strongest interest

Then narrow harder instead of broadening too early.

---

## 17. Files Likely to Be Created Later During Execution

If the project is implemented, likely artifacts include:
- `docs/prd/vertical-ai-tools-directory.md`
- `docs/ia/vertical-ai-tools-sitemap.md`
- `docs/schema/tool-directory-data-model.md`
- `docs/seo/content-plan.md`
- `docs/launch/mvp-launch-checklist.md`

If implementation happens in a dedicated app repo, the execution plan should define exact app paths separately.

---

## 18. Validation Checklist

A PRD consumer should be able to answer these questions after reading:
- Who exactly is the MVP for?
- Why will users prefer it over a generic AI directory?
- Which pages are in scope for launch?
- What content needs to exist before launch?
- How does the product make money?
- What metrics determine whether to continue?

If any answer is unclear, refine the niche and scope before building.
