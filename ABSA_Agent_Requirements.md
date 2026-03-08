# ABSA Agent System — Requirements Specification

**Document ID:** SRS-ABSA-2026-001 · **Version:** 1.4 · **Date:** March 8, 2026

---

## 1. Overview

The ABSA Agent System automates the processing of customer reviews for a restaurant chain. It operates as an orchestrated multi-agent pipeline that screens reviews for toxicity, extracts aspects, classifies sentiment, evaluates business policies and escalation rules, generates personalized responses, and validates those responses through an output guardrail before publishing.

Each review arrives with: `review_id`, `restaurant_id`, `customer_id`, `review_text`, `review_timestamp`, and `source_platform`.

---

## 2. Pipeline Architecture

```
Review Ingestion
       │
       ▼
1. Toxicity Detection ──► TOXIC? ──► Terminate (no response)
       │ CLEAN
       ▼
2. Aspect Extraction
       │
       ▼
3. Sentiment Analysis (per aspect)
       │
       ▼
4. Policy Evaluation & Escalation ──► Alerts / Tickets (JSON file)
       │
       ▼
5. Response Generation
       │
       ▼
6. Output Guardrail ──► PASS ──► Publish to Review Platform
                    ──► FAIL ──► Revise (loop to 5) or Queue for Human Review
```

The **Orchestrator Agent** manages the pipeline state, routes data between stages, handles branching (terminate on toxicity, degrade on service failures), and persists the full execution to an audit trail.

---

## 3. Subagent Requirements

### 3.1 Toxicity Detection Agent

**Purpose:** Determine whether a review contains toxic, abusive, or harmful content. Per policy, toxic reviews receive no automated response.

**Input:** Review text and metadata.

**Output:** `is_toxic` (boolean), `toxicity_score` (0.0–1.0), `toxicity_categories` (profanity, hate speech, threat, harassment, etc.), `pipeline_action` (CONTINUE or TERMINATE).

**Key Rules:**
- Toxicity threshold is configurable (default: 0.7), retrievable from the Policy Configuration Service, and may differ by platform or restaurant.
- Frustration and strong language (e.g., "the food was damn cold") must be distinguished from genuine abuse. The model must be calibrated accordingly.
- Rating-only reviews (no text) pass through with score 0.0.
- Reviews exceeding 10,000 characters are truncated for analysis.
- All classifications are logged to the Audit Trail with model version and threshold applied.

---

### 3.2 Aspect Extraction Agent

**Purpose:** Identify all distinct aspects of the restaurant experience mentioned in the review and map them to a canonical taxonomy.

**Output per aspect:** `aspect_code`, `mention_text`, character offsets, `confidence` score, and `is_implicit` flag.

**Canonical Taxonomy (configurable, versioned):**

| Code | Aspect | Example Mentions |
|------|--------|-----------------|
| FOOD_QUALITY | Food Quality | taste, freshness, portion |
| SERVICE | Customer Service | staff, waiter, rude, helpful |
| AMBIANCE | Ambiance | decor, noise, lighting, vibe |
| CLEANLINESS | Cleanliness | clean, dirty, restroom |

**Key Rules:**
- Extract both explicit aspects ("the food was great") and implicit ones ("it was filthy in there" → CLEANLINESS).
- Handle multi-aspect sentences by producing separate entries per aspect.
- Confidence threshold ≥ 0.6 (configurable). Below-threshold extractions are discarded.
- Unrecognized mentions are reported separately to support taxonomy evolution.
- If zero aspects are extracted, assign a default GENERAL aspect and flag for manual review.

---

### 3.3 Sentiment Analysis Agent

**Purpose:** Classify sentiment toward each extracted aspect independently. A single review may be positive on one aspect and negative on another.

**Output per aspect:** `sentiment_label` (VERY_POSITIVE / POSITIVE / NEUTRAL / NEGATIVE / VERY_NEGATIVE), `sentiment_score` (−1.0 to 1.0), `confidence`, and `supporting_text`.

Also produces `overall_sentiment` and `overall_sentiment_score` as a weighted average (weights configurable per aspect).

**Key Rules:**
- Handle negation, sarcasm, and conditional sentiment ("would have been great if it weren't ice cold" → NEGATIVE).
- Detect mixed sentiment within a single aspect and produce multiple entries when appropriate.
- Include the supporting text span for traceability.

---

### 3.4 Policy Evaluation and Escalation Agent

**Purpose:** Evaluate sentiment results against a running policy document that encompasses both operational alerting rules and customer-tier-based escalation rules. This single agent reads the full policy configuration, fires alarms or notifications when thresholds are breached, and creates callback tickets for eligible customers.

Escalation tickets are written to a JSON file (`data/escalation_tickets.json`) rather than a database. The file stores a JSON array of ticket objects and supports deduplication (same customer + restaurant within 7 days).

**Policy Document Structure:** The policy document (managed in the Policy Configuration Service) contains two categories of rules evaluated in sequence:

**Category A — Operational Alert Policies.** Each rule specifies: `target_aspect_codes`, `target_restaurant_ids`, `condition_type`, `threshold_value`, `action_type`, `action_recipients`, and `cooldown_period`.

- **Condition Types:** SINGLE_REVIEW_BELOW.
- **Action Types:** ALARM, NOTIFICATION, EMAIL_ESCALATION, DASHBOARD_FLAG, SLACK_ALERT.

**Category B — Customer Tier Escalation Policies.** Each rule specifies: `target_tier`, `trigger_condition`, `ticket_priority`, `ticket_sla`, and `assignment_routing`.

**Default Tier Escalation Rules:**

| Tier | Trigger | Action |
|------|---------|--------|
| Platinum | Any negative aspect | HIGH priority ticket, 4-hour SLA |
| Gold | Overall sentiment NEGATIVE or worse | MEDIUM priority ticket, 24-hour SLA |
| Silver | Overall sentiment VERY_NEGATIVE | LOW priority ticket, 48-hour SLA |
| Standard | — | No ticket; automated response only |

**Key Rules:**
- The agent retrieves all active policies (both categories) from the Policy Configuration Service applicable to the current restaurant, aspects, and customer.
- Multiple policies may fire for the same review; all are evaluated independently.
- Cooldown periods prevent repeated firings of the same operational alert within a configured window.
- For tier escalation, the agent queries the CRM to retrieve the customer's tier, lifetime value, and loyalty status. If the CRM lookup fails, default to Standard tier and log the failure.
- Callback tickets include full context: review text, aspects, sentiments, customer profile, restaurant details, and any operational alerts that were triggered.
- Tickets are assigned to the team matching the primary negative aspect (e.g., SERVICE → Service Quality team).
- De-duplicate: if an OPEN ticket for the same customer + restaurant exists within 7 days (configurable), append the new review context to the existing ticket instead of creating a duplicate.
- All policy evaluations (triggered, not triggered, suppressed by cooldown) and all ticket actions (created, appended, skipped) are logged to the Audit Trail.

---

### 3.5 Response Generation Agent

**Purpose:** Compose a personalized, brand-consistent response to the customer review. The generated response is passed to the Output Guardrail Agent for validation before publishing.

**Key Rules:**
- Address every negative aspect specifically — never ignore or gloss over complaints. Acknowledge positives with gratitude.
- For negative aspects: acknowledge → apologize → provide a concrete next step or remediation.
- If a callback ticket was created, inform the customer that someone will reach out and include the approximate timeframe.
- Personalize using customer name (if available), restaurant location name, and specific review details. Generic templates are prohibited.
- Adhere to Brand Voice Guidelines (externally configurable).
- Maximum 300 words (configurable per platform).
- Never disclose internal data (scores, tiers, toxicity classifications, policy triggers).
- Support a human-in-the-loop review mode (queue for approval instead of auto-publish).

---

### 3.6 Output Guardrail Agent

**Purpose:** Validate the generated response against a configurable set of guardrail rules covering brand voice, tone, style, content safety, and completeness before the response is published. This agent acts as the final quality gate in the pipeline.

**Guardrail Rule Categories:**

| Category | What It Checks |
|----------|---------------|
| Brand Voice Compliance | Vocabulary, phrasing, and sign-off conventions match the brand guidelines document |
| Tone Consistency | Response tone matches the expected register (empathetic for complaints, warm for praise); no passive-aggressive, dismissive, or overly casual language |
| Style & Formatting | Sentence structure, paragraph length, capitalization, punctuation, and platform-specific formatting rules |
| Content Safety | No profanity, no inflammatory language, no statements that could create legal liability (e.g., admissions of negligence) |
| Internal Data Leakage | No disclosure of sentiment scores, toxicity classifications, customer tier, policy triggers, or any system-internal metadata |
| Completeness | Every aspect with negative sentiment is addressed in the response; no complaints are skipped |
| Factual Consistency | Claims in the response do not contradict the review content (e.g., not thanking for a positive dining experience when the review was entirely negative) |
| Length & Platform Rules | Response does not exceed the configured word limit and conforms to platform-specific constraints |

**Output:** `guardrail_passed` (boolean), `violations` (array of `{rule_category, description, severity}`), `guardrail_action` (PUBLISH, REVISE, or ESCALATE_TO_HUMAN).

**Key Rules:**
- The guardrail rules are externally configurable via the Policy Configuration Service. New rules can be added, and existing rules can be enabled/disabled or adjusted without redeployment.
- Each violation is classified by severity: CRITICAL (blocks publishing), WARNING (flags for review but may pass), or INFO (logged only).
- If the response fails with CRITICAL violations, the Orchestrator loops back to the Response Generation Agent with the violation feedback appended to the prompt context. The regeneration is attempted a maximum of 2 times (configurable).
- If the response still fails after the maximum regeneration attempts, the guardrail sets `guardrail_action` to ESCALATE_TO_HUMAN and the response is queued for manual review rather than published.
- If only WARNING-level violations are present, the response may be auto-published based on a configurable policy (default: publish with warnings logged). Alternatively, warnings can be configured to block publishing for specific restaurants or platforms.
- All guardrail evaluations (pass, fail, violation details, regeneration attempts) are logged to the Audit Trail.

---

## 4. Pipeline State Object

The Orchestrator maintains a cumulative state object per review containing: `pipeline_id`, `review_input`, `pipeline_status` (IN_PROGRESS / COMPLETED / TERMINATED / FAILED), `current_stage`, outputs from each subagent, per-stage timestamps, and any errors. This object is persisted in full to the audit trail.

---

## 5. Orchestration Rules

**Execution Flow:** Stages 1–6 run sequentially. If Stage 1 terminates the pipeline (toxic), no further stages execute. Stages 5 and 6 may loop: if the guardrail rejects the response, the Orchestrator sends violation feedback back to Stage 5 for regeneration (max 2 retries).

**Branching:** Zero aspects extracted → assign GENERAL aspect, continue. External service failure → degrade gracefully with defaults/cache, flag in state. Guardrail failure after max retries → queue for human review (ESCALATE_TO_HUMAN).

**Retries:** Max 2 retries per subagent with exponential backoff (1s base). Reviews failing all retries go to a dead letter queue. Alert if dead letter queue exceeds 50 items.

**Idempotency:** Re-submitting the same `review_id` must not produce duplicate responses, tickets, or score updates.

---

## 6. External Integrations

| System | Direction | Used By | On Failure |
|--------|-----------|---------|------------|
| Review Aggregation Service | Inbound | Orchestrator | Queue backlog |
| Policy Configuration Service | Read | Agents 1,2,4,5,6 | Use cached config |
| CRM | Read | Agent 4 | Default to Standard tier |
| Ticketing System (JSON file) | Write | Agent 4 | Queue for retry |
| Review Platform APIs | Write | Agent 6 (on pass) | Queue for retry |
| Notification Service | Write | Agent 4 | Queue for retry |
| Audit Trail Service | Write | All | Buffer locally, retry |

---

## 7. Non-Functional Requirements

**Performance:** End-to-end P95 latency ≤ 45 seconds (includes up to 2 guardrail regeneration loops). Single-pass P95 latency (no regeneration) ≤ 30 seconds. Sustained throughput ≥ 100 reviews/min. Individual subagent P99 ≤ 5 seconds.

**Availability:** 99.5% monthly uptime. Graceful degradation on external service failures.

**Scalability:** Independent scaling per subagent. Support up to 5,000 restaurant locations.

**Security:** PII encrypted at rest and in transit. GDPR/CCPA compliant. Role-based access to configuration and audit logs.

**Accuracy Targets:** Toxicity F1 ≥ 0.90 (false positive rate < 5%). Aspect extraction F1 ≥ 0.85. Sentiment accuracy ≥ 0.80. Response quality ≥ 4.0/5.0 on monthly human audit.

---

## 8. Configuration

All thresholds, taxonomies, escalation rules, policies, and brand guidelines are externally configurable via the Policy Configuration Service without redeployment. Changes propagate within 60 seconds. Configuration supports scoping at global, regional, and per-restaurant levels (specific overrides general). All changes are versioned and rollback-capable.

---

## 9. Acceptance Criteria

| ID | Criterion | Target |
|----|-----------|--------|
| AC-001 | Toxic reviews never receive automated responses | 100% |
| AC-002 | All review aspects extracted and addressed in response | ≥ 90% |
| AC-003 | Aspect-level sentiment accuracy on benchmark | ≥ 80% |
| AC-004 | Policy alerts and tier escalation tickets fire correctly per policy document | 100% |
| AC-005 | Callback tickets created for eligible customers with correct priority and SLA | 100% |
| AC-006 | Response quality on human audit | ≥ 4.0/5.0 |
| AC-007 | Output guardrail catches all CRITICAL violations before publishing | 100% |
| AC-008 | No brand voice, tone, or style violations in published responses | ≥ 98% |
| AC-009 | No internal data leaked in customer-facing responses | 100% |
| AC-010 | End-to-end pipeline latency P95 (including guardrail loop) | ≤ 45 sec |
| AC-011 | System availability (monthly) | ≥ 99.5% |
| AC-012 | Full audit trail for every pipeline execution | 100% |
