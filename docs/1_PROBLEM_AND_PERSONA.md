# 1. Problem & Persona Definition

## The Problem

Nigerian fintechs and banks face a compliance crisis that threatens their operations and growth:

### Three Urgent Challenges

**Challenge 1: Manual KYC is Slow and Expensive**
- Customer onboarding takes 3-5 days
- Manual verification of NIN, BVN, and ID documents
- High error rates (human fatigue, fake IDs)
- Cost: ₦2,000 per verification
- Result: Customer drop-off, lost revenue

**Challenge 2: Real-Time AML Monitoring is Now Mandatory**
- CBN March 2026 Baseline Standards require real-time transaction monitoring
- Manual review can't keep up with millions of daily transactions
- Late STR filing (>24 hours) results in ₦500M+ fines
- 87.5% of fintechs say compliance costs kill innovation
- Major fintechs fined ₦1 billion each in 2025 for KYC/AML failures

**Challenge 3: FIRS TIN Mandate Creates Operational Chaos**
- All bank accounts must have verified TIN (effective January 2026)
- Accounts without TIN restricted above ₦500,000 (April 2026)
- Fintechs have millions of existing customers to verify
- Manual TIN verification takes 3 months for 10M customers
- Cost: ₦20M in temporary staff, 60% accuracy rate

### The Core Issue

**Compliance is backward-looking and point-in-time.**

Institutions only discover they're non-compliant during audits — months after the violation. By then, fines have been issued, customers are angry, and reputation is damaged.

There is no real-time compliance monitoring system that works across KYC, AML, and Tax obligations simultaneously.

---

## Primary Personas

### Persona 1: Ngozi — Compliance Officer at Moniepoint

**Background:**
- 32 years old, MBA in Finance
- Manages compliance for 10 million customers
- Reports to Chief Risk Officer
- Team of 8 compliance analysts

**Pain Points:**
- Drowning in manual work: reviewing flagged transactions, chasing missing TINs
- Constantly worried about CBN audits and fines
- Can't keep up with regulatory changes (CBN, FIRS, SEC, FCCPC)
- Spends 3 hours/day reading regulatory circulars
- No real-time view of compliance posture

**Goals:**
- Automate repetitive compliance tasks
- Get real-time alerts for high-risk transactions
- Never miss a regulatory deadline
- Reduce compliance costs by 50%
- Sleep better at night

**Quote:**
"I need a system that tells me we're compliant before the CBN auditor arrives, not after."

---

### Persona 2: Emeka — CTO at Kuda Bank

**Background:**
- 38 years old, Computer Science degree
- Built Kuda's tech stack from scratch
- Manages 50-person engineering team
- Responsible for API integrations and system uptime

**Pain Points:**
- Compliance systems are slow and don't integrate well
- Building in-house compliance tools diverts engineering resources from product features
- Every new CBN regulation requires custom development work
- Compliance team constantly requests new reports and dashboards
- Worried about system downtime during high-volume periods

**Goals:**
- API-first compliance solution that integrates in hours, not months
- Offload compliance logic to a specialized platform
- Focus engineering team on customer-facing features
- Ensure 99.9% uptime for compliance monitoring
- Reduce technical debt

**Quote:**
"I don't want to build a compliance platform. I want to integrate one and move on."

---

### Persona 3: Dr. Adeyemi — CBN Regulator (SupTech User)

**Background:**
- 45 years old, PhD in Economics
- Head of Fintech Supervision at CBN
- Oversees 200+ licensed fintechs and PSPs
- Responsible for sector-wide compliance monitoring

**Pain Points:**
- No real-time visibility into sector compliance
- Relies on annual self-reports from institutions (often inaccurate)
- Discovers compliance failures only during audits
- Can't identify at-risk institutions proactively
- Manual data aggregation across 200+ institutions takes weeks

**Goals:**
- Real-time dashboard showing sector-wide compliance posture
- Early warning system for at-risk institutions
- Automated compliance reporting from all institutions
- Data-driven regulatory intervention
- Reduce audit burden on compliant institutions

**Quote:**
"I need to see which fintechs are at risk before they fail, not after."

---

## Problem Statement (One Sentence)

Nigerian financial institutions lack a unified, real-time compliance platform that automates KYC verification, AML transaction monitoring, and TIN reconciliation while providing regulators with sector-wide visibility — resulting in high costs, regulatory fines, and backward-looking compliance posture.

---

## Success Metrics

| Metric | Current State | Target with WeGoComply |
|--------|---------------|------------------------|
| KYC Onboarding Time | 3-5 days | <2 minutes |
| Compliance Cost | ₦50M+/year | ₦15M/year (70% reduction) |
| AML False Positives | 40-60% | 10-20% |
| TIN Verification Time | 3 months (manual) | 6 hours (automated) |
| STR Generation Time | 2-4 hours | <1 minute |
| Regulatory Fines | ₦1B+ (2025 actual) | ₦0 (target) |
| Compliance Visibility | Point-in-time (audits) | Real-time (continuous) |
