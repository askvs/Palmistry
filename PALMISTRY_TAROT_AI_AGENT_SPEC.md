Create UI wireframes and workflow planning.
Setup frontend and backend environments.Create UI wireframes and workflow planning.
Setup frontend and backend environments.# PALMISTRY & TAROT INTELLIGENCE PLATFORM — AI AGENT BUILD SPECIFICATION

## 0. Agent Mission

You are the primary AI software engineering agent responsible for implementing the complete Palmistry & Tarot Intelligence Platform described in this document. Treat this document as the authoritative implementation contract. Build a real, integrated, maintainable, testable application; do not merely create mock screens, placeholder APIs, or disconnected modules.

## 0.1 Non-Negotiable Agent Rules

1. Inspect the existing repository before changing anything. Preserve useful existing work.
2. Do not implement the entire platform in one uncontrolled pass. Work milestone-by-milestone and task-by-task.
3. Before implementation, create or update `AGENT_PROGRESS.md` with the current state, completed requirements, pending requirements, blockers, and decisions.
4. Use the architecture, modules, workflows, technology stack, and acceptance criteria in this document as the implementation baseline.
5. When a detail is not explicitly fixed, use the defaults in Section 49 instead of asking unnecessary clarification questions.
6. You may improve implementation details, but do not remove a required capability or silently replace a required technology.
7. Keep provider-specific integrations behind adapters so alternatives can be swapped later.
8. Build vertical slices that work end-to-end before adding breadth.
9. Every backend feature must have validation, error handling, logging, and tests.
10. Every frontend feature must have loading, success, empty, and error states.
11. Every AI/ML feature must expose model/version metadata and confidence/relevance information where applicable.
12. Never fabricate model accuracy, user data, or external service responses. Use clearly marked mock data only in development/test environments.
13. Never expose secrets in application code. Use environment variables and `.env.example`.
14. Store user-local dates/times consistently and use UTC internally.
15. Use database migrations; never rely on manual schema edits.
16. Prefer asynchronous/background processing for long-running model inference, report generation, notifications, and scheduled tasks.
17. Maintain API versioning under `/api/v1`.
18. Keep services modular even if the first deployment uses a modular monolith. Split into independently deployable services only when operationally justified.
19. Run automated tests after each major task and run integration tests before marking a milestone complete.
20. Do not mark a requirement complete until the feature is implemented, integrated, tested, and demonstrable.
21. For palmistry, tarot, health, finance, or life-trend language, present generated content as interpretive guidance and self-reflection, never as guaranteed facts, diagnosis, or professional advice.
22. If an external credential, paid service account, or unavailable dataset prevents completion, implement the adapter, configuration, validation, and test path, document the blocker, and continue with the rest of the system.
23. Do not repeatedly ask the project owner questions that can be resolved using the defaults in this document. Ask only when the decision would materially change the architecture, cost, legal posture, or user experience and cannot reasonably be chosen by the defaults.

## 0.2 Required Working Loop

```text
Inspect repository
      ↓
Read specification + current AGENT_PROGRESS.md
      ↓
Select next incomplete task
      ↓
Inspect dependencies
      ↓
Implement backend/data/AI/UI pieces needed for one working slice
      ↓
Run unit + integration tests
      ↓
Run lint/type checks/build
      ↓
Update AGENT_PROGRESS.md
      ↓
Move to next task
```

## 0.3 Required Agent Artifacts

The implementation repository must maintain:

- `AGENT_PROGRESS.md` — living implementation status.
- `ARCHITECTURE.md` — current architecture and important decisions.
- `.env.example` — all required configuration keys without secrets.
- `README.md` — setup, run, test, deployment, and usage instructions.
- `CHANGELOG.md` — major implementation changes.
- `docs/decisions/` — architecture and provider decisions that materially affect the project.
- `tests/` — automated tests across backend, AI/ML utilities, frontend, and end-to-end flows.

---

# Palmistry & Tarot Intelligence Platform — Master Project Specification

> **Document purpose:** Authoritative project specification for an AI coding/development agent.
>
> **Label rule:** `[REQUIRED]` means mandatory functionality; `[SYSTEM FLOW]` means a consolidated workflow; `[DEFAULT]` means the implementation choice the agent should use unless explicitly overridden.
>
> **Decision rule:** When an implementation detail is not directly fixed, use the defaults in Section 49. Do not invent a different default unless the project owner explicitly changes it.

---

# 1. Project Overview

## 1.1 Project Name

**[REQUIRED]** Palmistry & Tarot Intelligence Platform.

## 1.2 One-Line Description

**[REQUIRED]** Build an AI-powered platform that analyzes palm images and tarot card selections to generate personalized spiritual insights related to personality traits, relationships, career growth, life trends, strengths, opportunities, and self-reflection.  


## 1.3 Detailed Description

**[REQUIRED]** The platform combines:

- Computer vision.
- AI interpretation models.
- Symbolic analysis.
- Tarot reading workflows.
- Interactive guidance systems.

The goal is to create engaging and customized spiritual experiences for users.  


## 1.4 Intended Users / Target Audiences

**[REQUIRED]** The platform is designed for:

- Spiritual enthusiasts.
- Wellness platforms.
- Tarot practitioners.
- Life coaches.
- Personal development communities.



## 1.5 Expected Outcomes

**[REQUIRED]** The completed platform is expected to provide:

1. An AI-powered spiritual intelligence platform.
2. Secure authentication and role-based access control.
3. Palm image analysis and palm feature detection workflows.
4. Tarot reading and card interpretation systems.
5. AI-powered insight generation and guidance modules.
6. Personality profiling and life trend analysis engines.
7. Dashboards for reading history, insights, and engagement analytics.
8. Docker-based deployment using cloud deployment platforms such as AWS or Azure.



## 1.6 Problem Statement

The project uses the following problem statement:

**[SYSTEM FLOW]** The project can be understood as addressing the need for a single interactive platform that combines palm-image analysis, tarot workflows, AI interpretation, personalization, guidance, reporting, analytics, and role-based user experiences.

> **Interpretation:** This describes the practical project purpose for implementation.

## 1.7 Motivation / Purpose

**[REQUIRED]** The purpose is to create customized spiritual experiences by combining:

- Palm analysis.
- Tarot readings.
- AI interpretation.
- Personality intelligence.
- Trend analysis.
- Recommendations.
- Interactive guidance.

No separate business justification or commercial-platform comparison is required for implementation.

---

# 2. Project Objectives

## 2.1 Primary Objectives

**[REQUIRED]**

- Build the Palmistry & Tarot Intelligence Platform.
- Implement palm image analysis.
- Implement tarot reading workflows.
- Generate AI-powered interpretations and personalized guidance.
- Implement personality intelligence.
- Implement life trend analysis.
- Implement recommendation capabilities.
- Provide dashboards, analytics, and reports.
- Deploy the system using Docker and cloud services.

## 2.2 Technical Objectives

**[REQUIRED]**

- Implement secure authentication.
- Implement JWT authentication.
- Implement OAuth2 login.
- Implement role-based access control.
- Build frontend and backend integration.
- Build API validation and testing.
- Build end-to-end workflows.
- Perform security testing.
- Optimize performance.
- Set up monitoring and logging.
- Containerize using Docker.
- Deploy to production.
- Provide documentation and user guides.

## 2.3 User-Facing Objectives

**[REQUIRED]**

- Allow users to create profiles and manage preferences.
- Allow palm image upload.
- Allow tarot spread selection and card interactions.
- Generate personalized readings.
- Provide reading history.
- Provide personality insights.
- Provide palm and tarot reports.
- Provide recommendations and guidance.
- Provide dashboards and visual analytics.
- Provide document and Excel report export.
- Provide notifications and engagement features.

---

# 3. Scope

## 3.1 In Scope

**[REQUIRED]** The project scope includes the following major capability groups:

1. User authentication and role-based access.
2. User profile management.
3. Palm analysis engine.
4. Tarot reading engine.
5. AI interpretation engine.
6. Personality intelligence.
7. Life trend analysis.
8. Spiritual guidance scoring.
9. Recommendation engine.
10. Dashboards and analytics.
11. Notification and engagement system.
12. Reports and export.
13. Final integration, testing, and deployment.

## 3.2 Out of Scope

No additional out-of-scope items are required beyond the explicit project scope.

> Only explicitly listed project capabilities are mandatory scope; do not add unrelated product features.

## 3.3 Future Scope / Optional Features

No separate future-scope list is required; optionality is controlled by the technology-selection rules and implementation decisions below.

Some architecture elements are presented as alternatives, such as AWS/Azure, Stripe/Razorpay, and SendGrid/Twilio. These are implementation alternatives shown by the specification, not necessarily separate future features.

---

# 4. Roles and Access Model

## 4.1 User Roles

**[REQUIRED]** The architecture diagram identifies these roles:

- User.
- Tarot Reader.
- Spiritual Consultant.
- Administrator.

 Architecture diagram, project section 2; role list continues onto page 3.

## 4.2 Role-Based Access Control

**[REQUIRED]**

- Implement role-based access control.
- Protect functionality according to the user's role.
- Provide role-specific dashboards.

Use the default RBAC permission matrix defined in Section 49 unless a later project decision overrides it.

---

# 5. System Architecture

## 5.1 Architecture Summary

**[REQUIRED]** The architecture diagram on page 2 depicts a layered system consisting of:

1. Clients / Users.
2. API Gateway.
3. Microservices layer.
4. AI / ML & Intelligence Engine.
5. Data Layer.
6. External Services & External Data.
7. Monitoring & Logging.
8. Backup & Security.

The architecture uses synchronous HTTP/HTTPS flows, asynchronous message-queue-style flows, data flows, external-service integration, and internal-service communication as indicated by the diagram legend.

## 5.2 Architecture Diagram — Textual Representation

The following is a textual reconstruction of the architecture diagram shown on **project section 2**.

```text
CLIENTS / USERS
│
├── User Roles
│   ├── User
│   ├── Tarot Reader
│   ├── Spiritual Consultant
│   └── Administrator
│
├── Access Channels
│   ├── Web Application
│   ├── Mobile Application
│   ├── Android App
│   ├── iOS App
│   └── API Access
│
└── User Actions
    ├── Upload Palm Image
    ├── Select Tarot Spread
    ├── Draw Cards
    ├── Get Readings
    ├── View History
    ├── Track History
    ├── Get Recommendations
    └── Export Reports

                │ HTTP / HTTPS / REST API
                ▼

API GATEWAY — FastAPI
├── Routing
├── Authentication
├── Rate Limiting
├── Request Validation
├── Load Balancing
├── CORS
└── Logging

                │
                ▼

MICROSERVICES LAYER
├── User Service
│   ├── Authentication
│   ├── Role Management
│   └── Profile Management
│
├── Profile Service
│   ├── Profile Creation
│   ├── Interests & Goals
│   ├── Reading Preferences
│   ├── History Management
│   └── Customization
│
├── Palm Analysis Service
│   ├── Image Upload
│   ├── Preprocessing
│   ├── Feature Extraction
│   ├── Line Detection
│   └── Pattern Recognition
│
├── Tarot Reading Service
│   ├── Deck Management
│   ├── Card Shuffle Logic
│   ├── Spread Management
│   ├── Card Selection
│   └── Reading Generation
│
├── AI Interpretation Service
│   ├── Palm Interpretation
│   ├── Tarot Interpretation
│   ├── Context Understanding
│   └── Insight Generation
│
├── Personality & Insights Service
│   ├── Personality Profiles
│   ├── Strengths & Weaknesses
│   ├── Behavioral Analysis
│   └── Life Path Analysis
│
├── Trend Analysis Service
│   ├── Life Trend Analysis
│   ├── Future Projection
│   ├── Challenges Forecast
│   ├── Growth Potential
│   └── Pattern Trends
│
├── Recommendation Service
│   ├── Guidance Suggestions
│   ├── Relationship Advice
│   ├── Career Guidance
│   ├── Goal Alignment
│   └── Spiritual Development
│
├── Notification Service
│   ├── Reading Reminders
│   ├── Daily Guidance
│   ├── Progress Alerts
│   └── Push Notifications
│
├── Analytics Service
│   ├── User Engagement
│   ├── Trend Analytics
│   ├── KPI Calculations
│   └── Insight Metrics
│
├── Report Service
│   ├── Report Generation
│   ├── document Export
│   ├── Excel Export
│   └── Scheduled Reports
│
└── Admin Service
    ├── User Management
    ├── Content Management
    ├── System Monitoring
    ├── Configuration
    └── Audit Logs

                │
                ├──────────────► EXTERNAL SERVICES / EXTERNAL DATA
                │                 ├── Cloud Storage
                │                 │   └── AWS S3 / Azure Blob
                │                 ├── AI / NLP APIs
                │                 │   └── OpenAI / Hugging Face / LangChain
                │                 ├── Image Processing APIs
                │                 │   └── OpenCV / YOLO
                │                 ├── Spiritual & Tarot Knowledge Base
                │                 ├── Payment Gateway
                │                 │   └── Stripe / Razorpay
                │                 ├── Email / SMS Service
                │                 │   └── SendGrid / Twilio
                │                 └── Analytics Services
                │                     └── Google Analytics, etc.
                │
                ▼

AI / ML & INTELLIGENCE ENGINE
├── Palm Line Detection Model (CNN)
├── Palm Feature Recognition Model
├── Tarot Card Classification Model
├── NLP Interpretation Model (LLM)
├── Insight Generation Engine
├── Recommendation Engine
├── Personality Profiling Model
└── Trend Prediction Model

                │
                ▼

DATA LAYER
├── PostgreSQL (Relational DB)
│   ├── Users
│   ├── Profiles
│   ├── Readings
│   ├── Payments
│   └── Reports
│
├── MongoDB (Document DB)
│   ├── Palm Features
│   ├── Tarot Data
│   ├── Insights
│   ├── Notifications
│   └── Logs
│
├── Redis Cache
│   ├── Session State
│   ├── Cache Data
│   └── Temporary Data
│
├── Elasticsearch
│   ├── Reading Search
│   ├── User Search
│   ├── Tarot Search
│   └── Trend Search
│
├── Vector DB (FAISS / Chroma)
│   ├── Embeddings
│   ├── Insight Embeddings
│   └── Semantic Search
│
├── Media Storage
│   ├── Palm Images
│   ├── Tarot Card Images
│   ├── User Avatars
│   └── Reports
│
├── Knowledge Graph (Neo4j)
│   ├── Symbol Relations
│   ├── Card Meanings
│   ├── Palm Patterns
│   └── Interactions
│
└── Time-Series DB (InfluxDB)
    ├── User Trends
    ├── Engagement Data
    ├── Reading Trends
    └── Performance Data

MONITORING & LOGGING
├── Application Monitoring
├── Performance Monitoring
├── Log Management
└── Alert Management

BACKUP & SECURITY
├── Automated Backups
├── Data Encryption
├── Security Monitoring
├── Access Control
└── Disaster Recovery
```

 Architecture diagram, project section 2.

## 5.3 Architecture Components

### 5.3.1 Client / Access Layer

**[REQUIRED]**

Supported access channels shown in the architecture diagram:

- Web application.
- Mobile application.
- Android app.
- iOS app.
- API access.

Supported user actions shown in the architecture diagram:

- Upload palm image.
- Select tarot spread.
- Draw cards.
- Get readings.
- View history.
- Track history.
- Get recommendations.
- Export reports.

## 5.4 API Gateway

**[REQUIRED]** The architecture diagram identifies **FastAPI** as the API Gateway technology.

Responsibilities shown:

- Routing.
- Authentication.
- Rate limiting.
- Request validation.
- Load balancing.
- CORS.
- Logging.

## 5.5 Microservices Layer

**[REQUIRED]** The architecture diagram separates functionality into User, Profile, Palm Analysis, Tarot Reading, AI Interpretation, Personality & Insights, Trend Analysis, Recommendation, Notification, Analytics, Report, and Admin services.

Detailed responsibilities are specified in the module sections below.

## 5.6 AI / ML & Intelligence Layer

**[REQUIRED]** The architecture diagram identifies:

- Palm Line Detection Model (CNN).
- Palm Feature Recognition Model.
- Tarot Card Classification Model.
- NLP Interpretation Model (LLM).
- Insight Generation Engine.
- Recommendation Engine.
- Personality Profiling Model.
- Trend Prediction Model.

## 5.7 Data Layer

**[REQUIRED]** The architecture diagram identifies:

- PostgreSQL.
- MongoDB.
- Redis Cache.
- Elasticsearch.
- Vector DB using FAISS / Chroma.
- Media Storage.
- Neo4j Knowledge Graph.
- InfluxDB Time Series DB.

## 5.8 External Services and External Data

**[REQUIRED]** The architecture diagram identifies:

- Cloud Storage: AWS S3 / Azure Blob.
- AI / NLP APIs: OpenAI / Hugging Face / LangChain.
- Image Processing APIs: OpenCV / YOLO.
- Spiritual & Tarot Knowledge Base.
- Payment Gateway: Stripe / Razorpay.
- Email / SMS Service: SendGrid / Twilio.
- Analytics Services: Google Analytics, etc.

## 5.9 Monitoring, Logging, Backup, and Security

**[REQUIRED]**

Monitoring & Logging:

- Application monitoring.
- Performance monitoring.
- Log management.
- Alert management.

Backup & Security:

- Automated backups.
- Data encryption.
- Security monitoring.
- Access control.
- Disaster recovery.

---

# 6. Complete End-to-End System Workflow

**[SYSTEM FLOW]**

The platform should support the following high-level flow:

```text
User
  ↓
Authentication / Role Check
  ↓
User Profile + Preferences / Context
  ↓
Choose Reading Type
  ├── Palm Analysis
  │     ↓
  │   Palm Image Upload
  │     ↓
  │   Image Preprocessing
  │     ↓
  │   Palm Feature Extraction
  │     ↓
  │   Palm Line / Pattern Detection
  │     ↓
  │   Palm Interpretation
  │
  └── Tarot Reading
        ↓
      Deck Selection
        ↓
      Shuffle Simulation
        ↓
      Spread Generation
        ↓
      Card Selection
        ↓
      Card Interpretation

           ↓
     AI Interpretation
           ↓
     Context-Aware Insight
           ↓
     Personality Intelligence
           ↓
     Life Trend Analysis
           ↓
     Spiritual Guidance Scoring
           ↓
     Recommendation Engine
           ↓
     Reading Synthesis
           ↓
     Dashboard / Report
           ↓
   History / Analytics / Notifications
```

Use the workflow below as the canonical end-to-end workflow for implementation.

---

# 7. Functional Requirements

## FR-001 — User Registration and Login

**Type:** Functional  


**Requirement:** The system must provide user registration and login.

**Expected behavior:**
- User can register.
- User can log in.
- Authenticated access must be established.

**Input:** User registration/login information.  
**Processing:** Authentication through the authentication service.  
**Output:** Authenticated user session/access.  
**Dependencies:** Authentication module.  
**Priority:** Use the project default defined in Section 49.

---

## FR-002 — JWT Authentication

**Type:** Security / Functional  


**Requirement:** Implement JWT authentication.

**Input:** Authentication credentials/token.  
**Processing:** JWT-based authentication.  
**Output:** Authenticated access context.  
**Priority:** Use the project default defined in Section 49.

---

## FR-003 — OAuth2 Login

**Type:** Security / Functional  


**Requirement:** Implement OAuth2 login.

**Provider:** Use the project default defined in Section 49.

---

## FR-004 — Role-Based Access Control

**Type:** Security / Functional  


**Requirement:** Implement role-based access control.

**Roles explicitly identified:**

- User.
- Tarot Reader.
- Spiritual Consultant.
- Administrator.

**Permissions matrix:** Use the project default defined in Section 49.

---

## FR-005 — User Profile Management

**Type:** Functional  


**Requirement:** Implement user profile management.

**Features:**

- Profile creation.
- Reading preferences.
- Spiritual interests.
- Reading history.
- Goal management.
- Profile customization.

**User information fields explicitly identified:**

- Name.
- Age Group.
- Interests.
- Spiritual Goals.
- Reading Preferences.
- Session History.

---

## FR-006 — Palm Image Upload

**Type:** Functional / AI  


**Requirement:** Provide palm image upload functionality.

**Input:** Palm image.  
**Processing:** Palm preprocessing, feature extraction, line detection, and pattern recognition.  
**Output:** Palm features suitable for interpretation.

**Accepted file formats:** Use the project default defined in Section 49.

---

## FR-007 — Palm Preprocessing

**Type:** AI / Computer Vision  


**Requirement:** Implement palm preprocessing.

**Technology context:** OpenCV, Pillow, and Albumentations are listed in the technology stack.

**Exact preprocessing operations:** Use the project default defined in Section 49.

---

## FR-008 — Palm Feature Extraction

**Type:** AI / Computer Vision  


**Requirement:** Implement palm feature extraction.

---

## FR-009 — Palm Line Detection

**Type:** AI / Computer Vision  


**Requirement:** Detect important palm lines.

**Lines explicitly listed:**

- Life Line.
- Head Line.
- Heart Line.
- Fate Line.
- Sun Line.

The architecture diagram additionally identifies a **Palm Line Detection Model (CNN)**.

---

## FR-010 — Palm Pattern Recognition

**Type:** AI / Computer Vision  


**Requirement:** Implement palm pattern recognition.

Use the Section 49 CNN transfer-learning default for the palm line model.

---

## FR-011 — Palm Shape and Finger Analysis

**Type:** AI / Palm Analysis  


The following palm features are explicitly identified:

- Palm Shape.
- Finger Structure.

---

## FR-012 — Tarot Deck Selection

**Type:** Functional  


**Requirement:** Allow tarot deck selection.

**Available decks:** Use the project default defined in Section 49.

---

## FR-013 — Card Shuffling Simulation

**Type:** Functional  


**Requirement:** Implement a tarot card shuffling simulation.

Default shuffle: cryptographically secure Fisher-Yates shuffle; record a seed/reference for reproducibility in test mode only.

---

## FR-014 — Card Selection Workflow

**Type:** Functional  


**Requirement:** Implement a card selection workflow.

---

## FR-015 — Spread Generation

**Type:** Functional  


**Requirement:** Generate tarot spreads.

### Supported Spreads

**[REQUIRED]**

1. Single Card Reading.
2. Three Card Reading.
3. Relationship Spread.
4. Career Spread.
5. Celtic Cross Spread.
6. Life Path Spread.

---

## FR-016 — Tarot Card Interpretation

**Type:** AI / Functional  


**Requirement:** Implement card interpretation and generate tarot interpretations.

---

## FR-017 — Palm Interpretation Generation

**Type:** AI  


**Requirement:** Generate interpretations from analyzed palm information.

---

## FR-018 — Context-Aware Insight Generation

**Type:** AI  


**Requirement:** Generate insights using relevant context.

Default context: age group, interests, spiritual goals, reading preferences, recent reading history, current reading type, detected palm features, tarot cards/spread, and prior insight summaries.

---

## FR-019 — Personalized Guidance Creation

**Type:** AI / Functional  


**Requirement:** Generate personalized guidance.

---

## FR-020 — Reading Synthesis

**Type:** AI  


**Requirement:** Combine relevant interpretation outputs into a synthesized reading.

---

## FR-021 — Insight Categories

**Type:** Functional / AI  


The platform must support the following insight categories:

- Personality.
- Relationships.
- Career.
- Finance.
- Health & Wellness.
- Personal Growth.
- Life Opportunities.

The project does not define detailed output templates for each category.

---

## FR-022 — Personality Profiling

**Type:** AI  


**Requirement:** Build personality profiles.

---

## FR-023 — Strength Analysis

**Type:** AI  


**Requirement:** Analyze strengths.

---

## FR-024 — Weakness Analysis

**Type:** AI  


**Requirement:** Analyze weaknesses.

---

## FR-025 — Behavioral Insights

**Type:** AI  


**Requirement:** Generate behavioral insights.

---

## FR-026 — Personal Development Recommendations

**Type:** AI / Recommendation  


**Requirement:** Generate personal development recommendations.

---

## FR-027 — Life Path Analysis

**Type:** AI  


**Requirement:** Perform life path analysis.

---

## FR-028 — Opportunity Identification

**Type:** AI / Trend Analysis  


**Requirement:** Identify opportunities.

---

## FR-029 — Challenge Forecasting

**Type:** AI / Trend Analysis  


**Requirement:** Forecast challenges.

Default trend approach: rule-based symbolic trend synthesis plus model/LLM interpretation; never present future outcomes as guaranteed facts.

---

## FR-030 — Trend Monitoring

**Type:** AI / Analytics  


**Requirement:** Monitor trends.

---

## FR-031 — Growth Potential Assessment

**Type:** AI  


**Requirement:** Assess growth potential.

---

## FR-032 — Spiritual Guidance Scoring

**Type:** AI / Scoring  


The scoring engine must support:

- Personality alignment scoring.
- Reading confidence scoring.
- Guidance relevance scoring.
- Self-development scoring.
- Overall insight score.

---

## FR-033 — Weighted Insight Score

**Type:** AI / Scoring  


The specification explicitly provides:

\[
\text{Insight Score}
=
0.30(\text{Palm Analysis Confidence})
+
0.25(\text{Tarot Interpretation Relevance})
+
0.20(\text{Personality Alignment})
+
0.15(\text{User Context Relevance})
+
0.10(\text{Reading Consistency})
\]

Equivalent percentage representation:

| Component | Weight |
|---|---:|
| Palm Analysis Confidence | 30% |
| Tarot Interpretation Relevance | 25% |
| Personality Alignment | 20% |
| User Context Relevance | 15% |
| Reading Consistency | 10% |
| **Total** | **100%** |

Normalize every component score to 0–100 before applying the stated weights. Overall score is 0–100. Labels: 0–39 Low, 40–69 Moderate, 70–84 High, 85–100 Very High.

---

## FR-034 — Recommendation Engine

**Type:** AI / Functional  


The recommendation engine must support:

- Personal growth recommendations.
- Relationship guidance.
- Career suggestions.
- Goal alignment recommendations.
- Spiritual development insights.

---

## FR-035 — User Dashboard

**Type:** UI / Functional  


The User Dashboard must provide:

- Reading history.
- Personality insights.
- Tarot reports.
- Palm reports.
- Personalized guidance.

---

## FR-036 — Tarot Reader Dashboard

**Type:** UI / Functional  


The Tarot Reader Dashboard must support:

- Reading analytics.
- User engagement insights.
- Session tracking.
- Report management.

---

## FR-037 — Spiritual Consultant Dashboard

**Type:** UI / Functional  


The Spiritual Consultant Dashboard must support:

- User trend analysis.
- Guidance effectiveness.
- Consultation insights.

---

## FR-038 — Admin Dashboard

**Type:** UI / Functional  


The Admin Dashboard must support:

- User management.
- Platform analytics.
- Reading statistics.
- System reports.

---

## FR-039 — Notification & Engagement System

**Type:** Functional  


The platform must support:

- Daily guidance notifications.
- Reading reminders.
- Insight updates.
- Spiritual growth alerts.
- Platform announcements.

Default channels: in-app notifications first, email for important reminders, SMS only for explicitly enabled critical notifications. Use scheduled background jobs with UTC storage and user-local display times.

---

## FR-040 — Report Generation

**Type:** Functional  


The reporting system must support:

- Palmistry reports.
- Tarot reports.
- Personality reports.
- Spiritual guidance reports.
- Insight trend reports.

---

## FR-041 — document Export

**Type:** Functional  


Reports must be exportable as document.

---

## FR-042 — Excel Export

**Type:** Functional  


Reports must be exportable as Excel.

---

## FR-043 — Final Integration and Testing

**Type:** Technical / Functional  


The project must include:

- Frontend and backend integration.
- API validation and testing.
- End-to-end workflow testing.
- Security testing.
- Performance optimization.
- Docker containerization.
- Production deployment.
- Monitoring and logging setup.
- Documentation and user guides.

---

# 8. Detailed Module Specifications

# Module 1 — User Authentication & Role-Based Access



## Purpose

Provide secure user access and role-based permissions.

## Required Capabilities

- User registration.
- User login.
- JWT authentication.
- OAuth2 login.
- Role-based access control.
- User profile management.

## Roles

- User.
- Tarot Reader.
- Spiritual Consultant.
- Administrator.

## Inputs

Authentication information and user registration information.

## Outputs

Authenticated and authorized access.

## Dependencies

FastAPI API layer, authentication mechanisms, profile management.

## Detailed Permissions

Use the project default defined in Section 49.

---

# Module 2 — User Profile Management



## Purpose

Store and manage user identity, preferences, interests, goals, and history.

## Required Capabilities

- Profile creation.
- Reading preferences.
- Spiritual interests.
- Reading history.
- Goal management.
- Profile customization.

## Explicit User Information

- Name.
- Age Group.
- Interests.
- Spiritual Goals.
- Reading Preferences.
- Session History.

## Outputs

A persisted user profile and personalization context.

---

# Module 3 — Palm Analysis Engine



## Purpose

Analyze palm images and identify meaningful palm features.

## Required Pipeline

```text
Palm Image Upload
      ↓
Palm Preprocessing
      ↓
Palm Feature Extraction
      ↓
Palm Line Detection
      ↓
Palm Pattern Recognition
      ↓
Palm Feature Results
```

## Features to Analyze

- Life Line.
- Head Line.
- Heart Line.
- Fate Line.
- Sun Line.
- Palm Shape.
- Finger Structure.

## AI/ML Context

Architecture diagram:

- Palm Line Detection Model (CNN).
- Palm Feature Recognition Model.

Technology stack:

- OpenCV.
- YOLO.
- MediaPipe.
- TensorFlow.
- PyTorch.
- Pillow.
- Albumentations.

Use the Section 49 model-training defaults and record dataset size, hyperparameters, checkpoints, and thresholds in model metadata.

---

# Module 4 — Tarot Reading Engine



## Purpose

Manage tarot decks, cards, spreads, selection, and reading generation.

## Required Capabilities

- Tarot deck selection.
- Card shuffling simulation.
- Card selection workflow.
- Spread generation.
- Card interpretation.

## Supported Spreads

| Spread | Required |
|---|---|
| Single Card Reading | Yes |
| Three Card Reading | Yes |
| Relationship Spread | Yes |
| Career Spread | Yes |
| Celtic Cross Spread | Yes |
| Life Path Spread | Yes |

## Inputs

- Selected deck.
- Selected spread.
- Card selection.

## Outputs

Tarot reading interpretation and downstream insights.

---

# Module 5 — AI Interpretation Engine



## Purpose

Convert palm and tarot information into personalized interpretations.

## Required Capabilities

- Palm interpretation generation.
- Tarot interpretation generation.
- Context-aware insight generation.
- Personalized guidance creation.
- Reading synthesis.

## Architecture Context

The architecture diagram identifies an **NLP Interpretation Model (LLM)** and an **Insight Generation Engine**.

## External AI/NLP Context

The architecture diagram identifies:

- OpenAI.
- Hugging Face.
- LangChain.

The technology stack identifies:

- LangChain.
- Hugging Face Transformers.
- OpenAI APIs.
- Sentence Transformers.

Default AI provider: OpenAI API for interpretation/orchestration, Hugging Face for local/open models where needed, LangChain for workflow orchestration, and Sentence Transformers for embeddings.

---

# Module 6 — Personality Intelligence Module



## Required Capabilities

- Personality profiling.
- Strength analysis.
- Weakness analysis.
- Behavioral insights.
- Personal development recommendations.

## Architecture Context

The architecture diagram identifies a **Personality Profiling Model**.

---

# Module 7 — Life Trend Analysis Engine



## Required Capabilities

- Life path analysis.
- Opportunity identification.
- Challenge forecasting.
- Trend monitoring.
- Growth potential assessment.

## Architecture Context

The architecture diagram identifies a **Trend Prediction Model** and a Trend Analysis Service.

---

# Module 8 — Spiritual Guidance Scoring Engine



## Required Scores

- Personality alignment score.
- Reading confidence score.
- Guidance relevance score.
- Self-development score.
- Overall insight score.

## Weighted Model

```text
Insight Score
=
Palm Analysis Confidence × 30%
+
Tarot Interpretation Relevance × 25%
+
Personality Alignment × 20%
+
User Context Relevance × 15%
+
Reading Consistency × 10%
```

Normalize each component to 0–100 before applying the stated weights. Overall score is 0–100 using the specified formula.

---

# Module 9 — Recommendation Engine



## Required Recommendation Types

- Personal growth recommendations.
- Relationship guidance.
- Career suggestions.
- Goal alignment recommendations.
- Spiritual development insights.

## Architecture Context

A Recommendation Engine and Recommendation Service are shown in the architecture.

---

# Module 10 — Dashboard & Analytics



## User Dashboard

- Reading history.
- Personality insights.
- Tarot reports.
- Palm reports.
- Personalized guidance.

## Tarot Reader Dashboard

- Reading analytics.
- User engagement insights.
- Session tracking.
- Report management.

## Spiritual Consultant Dashboard

- User trend analysis.
- Guidance effectiveness.
- Consultation insights.

## Admin Dashboard

- User management.
- Platform analytics.
- Reading statistics.
- System reports.

---

# Module 11 — Notification & Engagement System



## Required Notifications

- Daily guidance notifications.
- Reading reminders.
- Insight updates.
- Spiritual growth alerts.
- Platform announcements.

Use in-app and email notifications by default, with SMS available through Twilio when enabled.

---

# Module 12 — Reports & Export System



## Report Types

- Palmistry reports.
- Tarot reports.
- Personality reports.
- Spiritual guidance reports.
- Insight trend reports.

## Export Formats

- document.
- Excel.

## Architecture Context

The Report Service includes:

- Report generation.
- PDF export.
- Excel export.
- Scheduled reports.

Scheduled reports are part of the Report Service and should use the default scheduling configuration in Section 49.

---

# Module 13 — Final Integration, Testing & Deployment



## Required Activities

1. Frontend and backend integration.
2. API validation and testing.
3. End-to-end workflow testing.
4. Security testing.
5. Performance optimization.
6. Docker containerization.
7. Production deployment.
8. Monitoring and logging setup.
9. Documentation and user guides.

---

# 9. AI / ML Specification

## 9.1 AI/ML Components Explicitly Identified

**[REQUIRED]**

| Component | Role / Context |
|---|---|
| Palm Line Detection Model (CNN) | Palm line detection |
| Palm Feature Recognition Model | Palm feature analysis |
| Tarot Card Classification Model | Tarot card recognition/classification |
| NLP Interpretation Model (LLM) | Interpretation generation |
| Insight Generation Engine | Generate synthesized insights |
| Recommendation Engine | Generate recommendations |
| Personality Profiling Model | Personality analysis |
| Trend Prediction Model | Trend/life trend prediction |

 Architecture diagram, project section 2.

## 9.2 Computer Vision Technologies

**[REQUIRED]**

- OpenCV.
- YOLO.
- MediaPipe.
- TensorFlow.
- PyTorch.

## 9.3 NLP / Interpretation Technologies

**[REQUIRED]**

- LangChain.
- Hugging Face Transformers.
- OpenAI APIs.
- Sentence Transformers.

## 9.4 Image Processing

**[REQUIRED]**

- OpenCV.
- Pillow.
- Albumentations.

## 9.5 Training Data / Datasets

The project requires these dataset categories these datasets:

### Palmistry Image Dataset

**Purpose:**

- Palm line detection.
- Palm feature extraction.
- Palm classification.

### Hand Landmark Dataset

**Purpose:**

- Hand segmentation.
- Palm structure analysis.
- Finger pattern detection.

### Tarot Card Image Dataset

**Purpose:**

- Tarot card recognition.
- Card classification.
- Card interpretation support.



Default dataset policy: select reputable, license-compatible datasets; record dataset name, version, license, URL, classes, annotation format, and checksum in `data/README.md`. Use 70/15/15 train/validation/test splits unless a dataset already defines a standard split.

## 9.6 AI Training Defaults

Use the following implementation defaults:

- Exact model architecture for most models.
- Training epochs.
- Batch sizes.
- Optimizers.
- Learning rates.
- Loss functions.
- Dataset sizes.
- Train/validation/test split ratios.
- Hardware requirements.
- GPU specifications.
- Model versioning procedure.
- Exact LLM model name.
- Prompt templates.
- Embedding model name.
- Vector dimensions.
- Retrieval top-k values.
- Fine-tuning procedure.

These must not be invented as project requirements.

---

# 10. Data Specification

## 10.1 Data Categories

**[REQUIRED]** The architecture identifies data related to:

### User / Relational Data

PostgreSQL:

- Users.
- Profiles.
- Readings.
- Payments.
- Reports.

### Document Data

MongoDB:

- Palm Features.
- Tarot Data.
- Insights.
- Notifications.
- Logs.

### Cached / Session Data

Redis:

- Session State.
- Cache Data.
- Temporary Data.

### Search Data

Elasticsearch:

- Reading Search.
- User Search.
- Tarot Search.
- Trend Search.

### Vector / Semantic Data

Vector DB (FAISS / Chroma):

- Embeddings.
- Insight Embeddings.
- Semantic Search.

### Media

Media Storage:

- Palm Images.
- Tarot Card Images.
- User Avatars.
- Reports.

### Knowledge Graph

Neo4j:

- Symbol Relations.
- Card Meanings.
- Palm Patterns.
- Interactions.

### Time-Series Data

InfluxDB:

- User Trends.
- Engagement Data.
- Reading Trends.
- Performance Data.

## 10.2 Database Schema Details

Use the database schema defaults defined in Section 49 and implement migrations from the beginning.

**Status:** Use the project default defined in Section 49.

## 10.3 Data Formats

Use JSON for API payloads, JPG/JPEG/PNG/WEBP for images, PDF for document reports, and XLSX for spreadsheet reports.

---

# 11. API Specification

## 11.1 API Framework

**[REQUIRED]** FastAPI.

## 11.2 API Gateway Responsibilities

**[REQUIRED]**

- Routing.
- Authentication.
- Rate limiting.
- Request validation.
- Load balancing.
- CORS.
- Logging.

## 11.3 API Endpoints

Use the API contract defaults defined in Section 49 and implement versioned REST endpoints under `/api/v1`.

> **API endpoint specification:** Use the project default defined in Section 49.

## 11.4 External API / Service Providers Identified

The architecture diagram identifies:

- OpenAI.
- Hugging Face.
- LangChain.
- AWS S3 / Azure Blob.
- Stripe / Razorpay.
- SendGrid / Twilio.
- Google Analytics, etc.

Use environment-based credentials, pinned SDK versions, API adapters, and the Section 49 rate limits and API conventions.

---

# 12. Database Specification

## 12.1 Primary Database

**PostgreSQL**

Purpose shown in architecture:

- Users.
- Profiles.
- Readings.
- Payments.
- Reports.

## 12.2 Secondary Database

**MongoDB**

Purpose shown in architecture:

- Palm Features.
- Tarot Data.
- Insights.
- Notifications.
- Logs.

## 12.3 Cache

**Redis**

Purpose:

- Session State.
- Cache Data.
- Temporary Data.

## 12.4 Search Engine

**Elasticsearch**

Purpose:

- Reading Search.
- User Search.
- Tarot Search.
- Trend Search.

## 12.5 Vector Database

**FAISS / Chroma**

Purpose:

- Embeddings.
- Insight Embeddings.
- Semantic Search.

Default selection: Chroma for the initial implementation; keep the vector layer abstract so FAISS can replace it later.

## 12.6 Knowledge Graph

**Neo4j**

Purpose:

- Symbol Relations.
- Card Meanings.
- Palm Patterns.
- Interactions.

## 12.7 Time-Series Database

**InfluxDB**

Purpose:

- User Trends.
- Engagement Data.
- Reading Trends.
- Performance Data.

## 12.8 Media Storage

The architecture diagram identifies media storage for:

- Palm Images.
- Tarot Card Images.
- User Avatars.
- Reports.

The concrete media storage technology is not named separately; cloud storage is represented as AWS S3 / Azure Blob.

---

# 13. Frontend / UI Specification

## 13.1 Frontend Technologies

**[REQUIRED]**

- JavaScript.
- React.js.

The framework/libraries section additionally lists:

- React.js.
- Next.js.
- Tailwind CSS.
- Chart.js.
- Plotly.

Default frontend: Next.js with React.js and Tailwind CSS. Treat React.js as the UI framework and Next.js as the application framework.

## 13.2 Required User-Facing Areas

**[REQUIRED]**

- Registration / login.
- User profile.
- Palm upload workflow.
- Tarot spread selection.
- Card selection/drawing.
- Reading display.
- Reading history.
- Recommendations.
- User dashboard.
- Reports.
- Export functionality.

## 13.3 Dashboards

- User Dashboard.
- Tarot Reader Dashboard.
- Spiritual Consultant Dashboard.
- Admin Dashboard.

## 13.4 Visualizations

The technology stack lists:

- Chart.js.
- Plotly.

The architecture includes analytics and dashboard services.

Exact chart types, layouts, filters, and interaction specifications are not provided.

## 13.5 Responsive UI

The architecture diagram references a responsive web application, while the access channels include web and mobile platforms.

Use a mobile-first responsive design with Tailwind CSS; define reusable typography, spacing, and component tokens in the frontend.

---

# 14. Backend Specification

## 14.1 Backend Framework

**FastAPI**

## 14.2 Backend Services

The architecture identifies:

- User Service.
- Profile Service.
- Palm Analysis Service.
- Tarot Reading Service.
- AI Interpretation Service.
- Personality & Insights Service.
- Trend Analysis Service.
- Recommendation Service.
- Notification Service.
- Analytics Service.
- Report Service.
- Admin Service.

## 14.3 Backend Responsibilities

**[REQUIRED]**

- Authentication.
- Authorization.
- Profile management.
- Palm processing.
- Tarot reading workflows.
- AI interpretation.
- Personality analysis.
- Trend analysis.
- Recommendations.
- Notifications.
- Analytics.
- Reporting.
- Administration.

## 14.4 Validation and Error Handling

The API Gateway requires request validation, and the final integration phase requires API validation and testing.

Use the validation and error-handling defaults defined in Section 49.

---

# 15. Repository File / Folder Structure

> **[DEFAULT]** Use the following repository structure as the implementation organization unless the existing repository already has an equivalent structure.

```text
palmistry-tarot-platform/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── services/
│   │   ├── hooks/
│   │   ├── charts/
│   │   └── assets/
│   └── package.json
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── services/
│   │   │   ├── user/
│   │   │   ├── profile/
│   │   │   ├── palm_analysis/
│   │   │   ├── tarot/
│   │   │   ├── interpretation/
│   │   │   ├── personality/
│   │   │   ├── trends/
│   │   │   ├── recommendations/
│   │   │   ├── notifications/
│   │   │   ├── analytics/
│   │   │   ├── reports/
│   │   │   └── admin/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── db/
│   │   ├── middleware/
│   │   ├── utils/
│   │   └── main.py
│   └── requirements.txt
│
├── ai/
│   ├── palm/
│   ├── tarot/
│   ├── interpretation/
│   ├── personality/
│   ├── trends/
│   ├── recommendations/
│   └── embeddings/
│
├── data/
│   ├── palmistry/
│   ├── landmarks/
│   └── tarot/
│
├── models/
├── tests/
├── docker/
├── config/
├── scripts/
├── docs/
├── .env.example
├── docker-compose.yml
└── README.md
```

**Organization rationale:** This structure keeps frontend, backend services, AI/ML, data, testing, deployment, and configuration separated.

---

# 16. Technology Stack

The following table consolidates the named technologies from the document.

| Layer / Area | Technology | Purpose / Context | Status |
|---|---|---|---|
| Programming Language | Python | Backend / AI development | Required |
| Backend | FastAPI | Backend framework / API Gateway | Required |
| Frontend | JavaScript | Frontend development | Required |
| Frontend | React.js | Frontend framework | Required |
| Frontend | Next.js | Listed in libraries/frameworks | Required in tech list |
| Styling | Tailwind CSS | Frontend styling | Required in tech list |
| Primary DB | PostgreSQL | Relational data | Required |
| Secondary DB | MongoDB | Document data | Required |
| Cache | Redis | Session/cache state | Required by architecture |
| Search | Elasticsearch | Search and discovery | Required by architecture |
| Vector DB | FAISS / Chroma | Embeddings / semantic search | Alternative |
| Knowledge Graph | Neo4j | Symbolic relationships | Required by architecture |
| Time-Series DB | InfluxDB | Trends/engagement/performance | Required by architecture |
| Computer Vision | OpenCV | Image processing | Required |
| Computer Vision | YOLO | Image processing / detection | Required |
| Computer Vision | MediaPipe | Hand/palm analysis | Required |
| ML | TensorFlow | AI/ML | Required |
| ML | PyTorch | AI/ML | Required |
| NLP | LangChain | Interpretation / orchestration context | Required |
| NLP | Hugging Face Transformers | NLP / interpretation | Required |
| AI API | OpenAI APIs | NLP / LLM integration | Required |
| Embeddings | Sentence Transformers | Embedding generation | Required |
| Image Processing | Pillow | Image processing | Required |
| Augmentation | Albumentations | Image preprocessing/augmentation | Required |
| Containerization | Docker | Deployment | Required |
| Cloud | AWS / Azure | Cloud deployment | Required |
| Charts | Chart.js | Dashboard visualization | Required |
| Charts | Plotly | Dashboard visualization | Required |
| VCS | Git & GitHub | Development/version control | Required |
| CI/CD | GitHub Actions | Dev/deployment tooling | Required |
| API Testing | Postman | API testing | Required |
| Cloud Storage | AWS S3 / Azure Blob | Media/cloud storage | Alternative |
| Payment | Stripe / Razorpay | Payment gateway | Alternative |
| Email/SMS | SendGrid / Twilio | Notifications | Alternative |
| Analytics | Google Analytics, etc. | Analytics service | Required by architecture |

### Technology Selection Rule

Where the document lists alternatives (for example, **AWS / Azure**, **FAISS / Chroma**, **Stripe / Razorpay**, **SendGrid / Twilio**), preserve the alternatives unless a later project decision explicitly selects one.

Do not silently replace a specified technology with another technology.

---

# 17. Development Timeline / Implementation Plan

## Milestone 1 — Week 1 & 2: Project Initialization, Design Process & Core Setup



### Tasks

1. Define project objectives and reading workflows.
2. Design system architecture and database schema.
3. Create UI wireframes and workflow planning.
4. Set up frontend and backend environments.
5. Implement authentication and role-based access system.
6. Build user profile management workflows.
7. Collect palmistry and tarot reference datasets.

### Recommended Datasets

- Palmistry Image Dataset.
- Hand Landmark Dataset.
- Tarot Card Image Dataset.

### Outcomes

- Understand palmistry and tarot intelligence workflows.
- Learn system architecture and database design concepts.
- Build frontend and backend project initialization.
- Working authentication and profile management system.

---

## Milestone 2 — Week 3 & 4: Palm Analysis & Tarot Intelligence



### Tasks

1. Implement palm analysis engine.
2. Build palm feature extraction workflows.
3. Develop tarot card interpretation engine.
4. Create reading generation workflows.
5. Generate reading reports.

### Outcomes

- Palm analysis engine operational.
- Tarot reading engine functional.
- Reading generation workflows completed.

---

## Milestone 3 — Week 5 & 6: AI Interpretation & Recommendations



### Tasks

1. Implement AI interpretation engine.
2. Build personality intelligence workflows.
3. Develop recommendation engine.
4. Generate life trend analysis.
5. Create personalized dashboards.

### Outcomes

- AI interpretation engine operational.
- Recommendation system functional.
- Personalized guidance workflows completed.

---

## Milestone 4 — Week 7 & 8: Analytics, Testing & Deployment



### Tasks

1. Build executive dashboards.
2. Add reports and visualization modules.
3. Implement testing and validations.
4. Deploy the platform using Docker and cloud services.
5. Prepare final documentation and presentation.

### Outcomes

- Fully deployed production-ready platform.
- Spiritual intelligence systems operational.
- Complete end-to-end reading workflow demonstrable.

---

# 18. Development Task Breakdown

> **[SYSTEM FLOW]** The following tasks translate the document's stated milestones and modules into AI-agent-friendly task units. The IDs and sequencing are organizational aids, not IDs assigned by the provided project requirements.

## TASK-001 — Initialize Project

**Goal:** Set up frontend and backend project environments.

**Requirements:**

- Python backend.
- FastAPI.
- JavaScript/React frontend.
- Development toolchain.

**Dependencies:** None.

**Expected Output:** Initial project structure and runnable development environment.

---

## TASK-002 — Design Architecture and Database Plan

**Goal:** Implement the architecture represented in the document.

**Requirements:**

- API Gateway.
- Microservices/service boundaries.
- Data layer.
- AI/ML layer.
- External services.
- Monitoring/logging.
- Backup/security.

**Dependencies:** TASK-001.

**Expected Output:** Architecture-aligned implementation plan and database design.

---

## TASK-003 — Implement Authentication

**Goal:** Implement registration, login, JWT, OAuth2, and RBAC.

**Requirements:**

- User registration.
- Login.
- JWT.
- OAuth2.
- Role-based access.

**Dependencies:** TASK-001.

---

## TASK-004 — Implement User Profile Management

**Requirements:**

- Profile creation.
- Reading preferences.
- Spiritual interests.
- Reading history.
- Goal management.
- Profile customization.

**Dependencies:** TASK-003.

---

## TASK-005 — Integrate Reference Datasets

**Requirements:**

- Palmistry image dataset.
- Hand landmark dataset.
- Tarot card image dataset.

**Dependencies:** TASK-001.

**Important:** Actual dataset specifications and files are not provided by the document and must be obtained/selected separately.

---

## TASK-006 — Implement Palm Analysis

**Requirements:**

- Image upload.
- Preprocessing.
- Feature extraction.
- Line detection.
- Pattern recognition.
- Palm shape and finger structure analysis.

**Dependencies:** TASK-005.

---

## TASK-007 — Implement Tarot Reading

**Requirements:**

- Deck selection.
- Shuffle simulation.
- Card selection.
- Spread generation.
- Supported spreads.
- Card interpretation.

**Dependencies:** TASK-005.

---

## TASK-008 — Implement AI Interpretation Engine

**Requirements:**

- Palm interpretation.
- Tarot interpretation.
- Context-aware insight generation.
- Personalized guidance.
- Reading synthesis.

**Dependencies:** TASK-006, TASK-007.

---

## TASK-009 — Implement Personality Intelligence

**Requirements:**

- Personality profiling.
- Strengths.
- Weaknesses.
- Behavioral insights.
- Personal development recommendations.

**Dependencies:** TASK-008.

---

## TASK-010 — Implement Life Trend Analysis

**Requirements:**

- Life path analysis.
- Opportunity identification.
- Challenge forecasting.
- Trend monitoring.
- Growth potential assessment.

**Dependencies:** TASK-008.

---

## TASK-011 — Implement Guidance Scoring

**Requirements:**

Implement the Required weighted scoring model.

**Dependencies:** TASK-006, TASK-008, TASK-009.

---

## TASK-012 — Implement Recommendation Engine

**Requirements:**

- Personal growth.
- Relationship guidance.
- Career.
- Goal alignment.
- Spiritual development.

**Dependencies:** TASK-009, TASK-010, TASK-011.

---

## TASK-013 — Build Dashboards

**Requirements:**

- User Dashboard.
- Tarot Reader Dashboard.
- Spiritual Consultant Dashboard.
- Admin Dashboard.
- Analytics and visualizations.

**Dependencies:** Core application services.

---

## TASK-014 — Implement Notifications

**Requirements:**

- Daily guidance notifications.
- Reading reminders.
- Insight updates.
- Spiritual growth alerts.
- Platform announcements.

**Dependencies:** User/profile and insight systems.

---

## TASK-015 — Implement Reports and Exports

**Requirements:**

- Palmistry report.
- Tarot report.
- Personality report.
- Spiritual guidance report.
- Insight trend report.
- PDF export.
- Excel export.

**Dependencies:** Reading and insight generation.

---

## TASK-016 — Integrate External Services

**Services named by document:**

- Cloud storage.
- AI/NLP services.
- Image processing services.
- Payment gateway.
- Email/SMS.
- Analytics.

**Dependencies:** Applicable service modules.

**Note:** Concrete provider selection is not fully fixed where alternatives are listed.

---

## TASK-017 — Integrate Monitoring, Logging, Backup, and Security

**Requirements:**

- Application monitoring.
- Performance monitoring.
- Log management.
- Alert management.
- Automated backups.
- Data encryption.
- Security monitoring.
- Access control.
- Disaster recovery.

---

## TASK-018 — Testing

**Requirements:**

- API validation and testing.
- End-to-end workflow testing.
- Security testing.
- Performance validation.

---

## TASK-019 — Dockerization and Deployment

**Requirements:**

- Docker containerization.
- Production deployment.
- Cloud services such as AWS/Azure.
- Monitoring/logging setup.

---

## TASK-020 — Documentation and Presentation

**Requirements:**

- Documentation.
- User guides.
- Final presentation.

---

# 19. Dependency Map

**[SYSTEM FLOW]**

```text
Project Initialization
        ↓
Architecture + Database Design
        ↓
Authentication + RBAC
        ↓
User Profile Management
        ↓
Reference Datasets
        ↓
 ┌───────────────┬────────────────┐
 ↓               ↓                │
Palm Analysis   Tarot Engine      │
 └───────┬───────┘                │
         ↓                         │
   AI Interpretation              │
         ↓                         │
 ┌───────┴────────┐               │
 ↓                ↓               │
Personality    Trend Analysis     │
 └───────┬────────┘               │
         ↓                         │
   Guidance Scoring               │
         ↓                         │
   Recommendation Engine          │
         ↓                         │
Dashboards + Reports + Notifications
         ↓
Testing + Security + Performance
         ↓
Docker + Cloud Deployment
         ↓
Monitoring + Documentation
```

This dependency map is the recommended implementation order and service dependency baseline.

---

# 20. Configuration & Environment Variables

## 20.1 Configuration Categories Mentioned / Implied by Architecture

**[REQUIRED / ARCHITECTURE]**

The system may require configuration for:

- AI/NLP APIs.
- Cloud storage.
- Payment gateway.
- Email/SMS services.
- Analytics services.
- Databases.
- Authentication.
- Docker/deployment.

## 20.2 Secrets

The document does not provide actual API keys, secret values, database credentials, or environment variable names.

Use placeholders only.

Example:

```text
OPENAI_API_KEY=<YOUR_API_KEY>
DATABASE_URL=<YOUR_DATABASE_URL>
CLOUD_STORAGE_CONFIG=<YOUR_CONFIG>
PAYMENT_GATEWAY_CONFIG=<YOUR_CONFIG>
EMAIL_SMS_CONFIG=<YOUR_CONFIG>
```

These example variable names are **[DEFAULT]** and are not project requirements.

## 20.3 Ports / URLs / Model Paths

Use the project default defined in Section 49.

---

# 21. Installation & Setup

## 21.1 Prerequisites

Use a current stable Python 3.12 environment, Node.js 22 LTS, Docker Desktop, Git, and PostgreSQL/MongoDB/Redis services. Pin all application dependencies in lock files or version-constrained manifests.

**Known technology categories:**

- Python.
- FastAPI.
- JavaScript.
- React.js.
- Databases/services listed in the architecture.
- Docker.
- Git/GitHub.
- Postman.

## 21.2 Runtime Versions

Python 3.12, Node.js 22 LTS, latest compatible stable database/service images, and pinned package versions.

## 21.3 Dependency Installation Commands

Use `pip install -r backend/requirements.txt` for backend dependencies and `npm ci` for frontend dependencies.

## 21.4 Database Setup Commands

Use Docker Compose for local databases and run versioned migrations automatically during development.

## 21.5 Model Setup Commands

Provide reproducible scripts under `scripts/models/` for downloading, training, evaluating, and registering models.

## 21.6 API Setup Commands

Run FastAPI with Uvicorn in development and behind a production ASGI server in deployment.

## 21.7 Running the Project

Use Docker Compose for the default local environment; provide a one-command startup path in `README.md`.

## 21.8 Deployment Commands

Use Docker images plus CI/CD through GitHub Actions; target AWS by default while keeping cloud-specific adapters replaceable.

---

# 22. Testing Requirements

## 22.1 Explicit Testing Requirements

**[REQUIRED]**

- API validation and testing.
- End-to-end workflow testing.
- Security testing.
- Performance optimization/testing.
- Testing and validations during Week 7–8.

## 22.2 Testing Areas

The architecture/project structure implies testing across:

- Authentication.
- Palm analysis.
- Tarot workflows.
- AI interpretation.
- Recommendations.
- Dashboards.
- Reporting.
- APIs.
- Deployment.

However, detailed test cases are not provided by the document.

## 22.3 Test Case Table

The document does not give explicit input/output test cases. Therefore, Use concrete, testable expected results and acceptance criteria for every requirement.

| Test ID | Scenario | Input | Expected Output | Priority | Reference |
|---|---|---|---|---|---|
| TC-001 | Authentication | Valid registration + login | JWT-authenticated session is created | P0 | Required |
| TC-002 | Palm workflow | Valid palm image | Palm features and interpretation are produced | P0 | Required |
| TC-003 | Tarot workflow | Deck + spread + card selection | Structured tarot reading is produced | P0 | Required |
| TC-004 | End-to-end workflow | Authenticated reading request | Reading completes through dashboard/history/report | P0 | Required |
| TC-005 | Export | Completed report | PDF and Excel files are generated successfully | P1 | Required |

These test rows summarize explicit project outcomes rather than inventing detailed assertions.

---

# 23. Error Handling

## 23.1 Explicitly Mentioned Error-Related Controls

The specification requires:

- Request validation.
- API validation and testing.
- Security testing.
- Authentication.
- Access control.
- Monitoring and logging.
- Alert management.

## 23.2 Specific Error Cases

Use the following standard error cases and behaviors:

- Invalid image format.
- Missing user fields.
- Authentication failure response.
- OAuth2 provider failure.
- AI API timeout.
- Model inference error.
- Database failure.
- Storage failure.
- Payment failure.
- Notification failure.
- Rate-limit response body.
- Retry policies.

**Status:** Use the project default defined in Section 49.

---

# 24. Security Requirements

## 24.1 Explicit Security Requirements

**[REQUIRED]**

- Secure authentication.
- JWT authentication.
- OAuth2 login.
- Role-based access control.
- Request validation.
- Security testing.
- Data encryption.
- Security monitoring.
- Access control.
- Automated backups.
- Disaster recovery.

## 24.2 Security Architecture

The architecture diagram includes a dedicated **Backup & Security** section:

- Automated Backups.
- Data Encryption.
- Security Monitoring.
- Access Control.
- Disaster Recovery.

## 24.3 Secrets Management

The project does not define a secrets manager or exact secret-storage method.

---

# 25. Deployment

## 25.1 Containerization

**[REQUIRED]** Docker containerization.

## 25.2 Cloud Deployment

**[REQUIRED]** Cloud deployment platforms such as:

- AWS.
- Azure.

The project presents AWS/Azure as deployment options rather than requiring both.

## 25.3 Production Requirements

**[REQUIRED]**

- Production deployment.
- Monitoring and logging.
- Stable performance and responsiveness.
- Docker deployment.
- Documentation.

## 25.4 Cloud Storage

Architecture diagram:

- AWS S3.
- Azure Blob.

These are alternatives shown in the architecture.

## 25.5 Monitoring

- Application monitoring.
- Performance monitoring.
- Log management.
- Alert management.

---

# 26. Performance Requirements

## 26.1 Metrics Explicitly Listed

**[REQUIRED]**

### Palm Analysis Metrics

- Palm feature detection accuracy.
- Palm classification accuracy.
- Palm interpretation consistency.

### Tarot Intelligence Metrics

- Card recognition accuracy.
- Interpretation relevance score.
- Reading completion rate.

### Recommendation Metrics

- Guidance relevance.
- User engagement rate.
- Recommendation effectiveness.

### Analytics Metrics

- Reading satisfaction score.
- User retention rate.
- Session engagement rate.

### System Performance Metrics

- API response time.
- Dashboard loading speed.
- Reading generation latency.
- Concurrent user handling capacity.



## 26.2 Quantitative Targets

The document provides qualitative quantitative-goal statements but does **not** specify numerical target thresholds for these metrics.

## 26.3 Example Quantitative Goals Section

**[REQUIRED]**

### Palm Analysis

Provide accurate palm feature extraction and interpretation generation.

### Tarot Intelligence

Generate engaging and context-aware tarot reading experiences.

### Personalized Guidance

Deliver relevant personality insights and growth recommendations.

### User Engagement

Increase reading completion and platform engagement through interactive experiences.

### Platform Performance

Support large-scale reading generation and analytics workflows while maintaining stable performance and responsiveness.



---

# 27. Expected Input → Processing → Output

## 27.1 Palm Reading Flow

**[SYSTEM FLOW]**

```text
INPUT
Palm Image
  ↓
VALIDATION
Image / Upload Validation
  ↓
PREPROCESSING
Palm Preprocessing
  ↓
FEATURE EXTRACTION
Palm Feature Extraction
  ↓
DETECTION / RECOGNITION
Palm Line Detection + Pattern Recognition
  ↓
PALM FEATURES
Life Line / Head Line / Heart Line / Fate Line /
Sun Line / Palm Shape / Finger Structure
  ↓
INTERPRETATION
Palm Interpretation Generation
  ↓
PERSONALIZATION
Personality + User Context
  ↓
GUIDANCE
Scoring + Recommendations
  ↓
OUTPUT
Reading / Insights / Report
```

Use the image validation and preprocessing defaults defined in Section 49.

## 27.2 Tarot Reading Flow

```text
INPUT
User Tarot Reading Request
  ↓
DECK SELECTION
  ↓
SHUFFLE SIMULATION
  ↓
SPREAD SELECTION
  ↓
CARD SELECTION
  ↓
CARD INTERPRETATION
  ↓
CONTEXT-AWARE INTERPRETATION
  ↓
PERSONALIZED INSIGHTS
  ↓
GUIDANCE SCORE
  ↓
RECOMMENDATIONS
  ↓
READING SYNTHESIS
  ↓
OUTPUT
Reading / Insights / Report
```

## 27.3 Combined Intelligence Flow

```text
Palm Intelligence + Tarot Intelligence
              ↓
       AI Interpretation
              ↓
      User Context / Profile
              ↓
      Personality Intelligence
              ↓
       Trend Analysis
              ↓
    Spiritual Guidance Scoring
              ↓
      Recommendation Engine
              ↓
        Reading Synthesis
              ↓
 Dashboard / Reports / Notifications
```

---

# 28. UI / User Workflow

## 28.1 Core User Journey

**[SYSTEM FLOW]**

```text
Open Platform
   ↓
Register / Login
   ↓
Authenticate
   ↓
Create / Customize Profile
   ↓
Choose Palm or Tarot Reading
   ├── Palm → Upload Image
   └── Tarot → Select Spread / Draw Cards
   ↓
Generate Interpretation
   ↓
View Personalized Insights
   ↓
View Recommendations
   ↓
Save Reading to History
   ↓
Open Dashboard / Report
   ↓
Export document / Excel
```

## 28.2 User Actions Explicitly Shown

**[REQUIRED]**

- Upload palm image.
- Select tarot spread.
- Draw cards.
- Get readings.
- View history.
- Track history.
- Get recommendations.
- Export reports.

---

# 29. Reports

## 29.1 Report Categories

**[REQUIRED]**

- Palmistry report.
- Tarot report.
- Personality report.
- Spiritual guidance report.
- Insight trend report.

## 29.2 Report Formats

- document.
- Excel.

## 29.3 Scheduled Reports

The architecture diagram lists **Scheduled Reports** under the Report Service.

The document does not provide the schedule configuration, timing rules, recipient rules, or exact scheduling implementation.

---

# 30. Notifications and Engagement

## 30.1 Required Notification Types

- Daily guidance notifications.
- Reading reminders.
- Insight updates.
- Spiritual growth alerts.
- Platform announcements.

## 30.2 Architecture Integration

The architecture diagram contains a Notification Service with:

- Reading Reminders.
- Daily Guidance.
- Progress Alerts.
- Push Notifications.

It also identifies Email/SMS integration through:

- SendGrid.
- Twilio.

Use the notification channel defaults in Section 49.

---

# 31. External Service Integration

## 31.1 Cloud Storage

**Options shown:**

- AWS S3.
- Azure Blob.

**Purpose:** Storage of cloud-hosted files/media.

## 31.2 AI / NLP

**Options/tools shown:**

- OpenAI.
- Hugging Face.
- LangChain.

## 31.3 Image Processing

**Tools shown:**

- OpenCV.
- YOLO.

## 31.4 Spiritual & Tarot Knowledge Base

The architecture includes a spiritual and tarot knowledge base.

Use the following implementation defaults:

- Exact format.
- Dataset specification.
- Database schema.
- Governance process.
- Update process.

## 31.5 Payment Gateway

Options shown:

- Stripe.
- Razorpay.

Payment-related tables are also represented in PostgreSQL.

Use INR as the default currency, Razorpay checkout, webhook verification, and configuration-driven pricing; do not hard-code pricing.

## 31.6 Email / SMS

Options shown:

- SendGrid.
- Twilio.

## 31.7 Analytics

The architecture lists:

- Google Analytics.
- Other analytics services (“etc.”).

Use the analytics event and KPI definitions established during implementation and record them in `docs/analytics.md`.

---

# 32. Knowledge & Semantic Intelligence

## 32.1 Vector Database

**[document Requirement / Architecture]**

FAISS / Chroma for:

- Embeddings.
- Insight embeddings.
- Semantic search.

## 32.2 Knowledge Graph

**Neo4j** for:

- Symbol relations.
- Card meanings.
- Palm patterns.
- Interactions.

## 32.3 Search

**Elasticsearch** for:

- Reading search.
- User search.
- Tarot search.
- Trend search.

## 32.4 Embeddings

Sentence Transformers is listed in the technology stack.

Use `sentence-transformers/all-MiniLM-L6-v2` as the default embedding model.

---

# 33. Monitoring, Logging, Backup & Security

## 33.1 Monitoring

- Application monitoring.
- Performance monitoring.

## 33.2 Logging

- Log management.
- Logging at API Gateway.
- Logs in MongoDB architecture section.

## 33.3 Alerting

- Alert management.

## 33.4 Backup

- Automated backups.

## 33.5 Data Protection

- Data encryption.

## 33.6 Security

- Security monitoring.
- Access control.

## 33.7 Recovery

- Disaster recovery.

---

# 34. Deliverables

## 34.1 Required Deliverables

Based on explicit outcomes/tasks in the document:

- Fully implemented frontend.
- Fully implemented backend.
- Authentication and role-based access.
- User profile management.
- Palm analysis engine.
- Tarot reading engine.
- AI interpretation engine.
- Personality intelligence workflows.
- Life trend analysis.
- Recommendation system.
- Personalized dashboards.
- Analytics.
- Reports and exports.
- Notifications/engagement system.
- End-to-end reading workflow.
- Docker containerization.
- Production deployment.
- Monitoring and logging.
- Documentation.
- User guides.
- Final presentation.

## 34.2 Project Artifacts Explicitly Referenced by Technology/Implementation

The project references:

- Application code.
- Datasets/reference datasets.
- Models.
- Reports.
- Dashboards.
- Documentation.
- User guides.
- Deployment artifacts.

Use the repository structure defined in Section 15.

## 34.3 Optional Deliverables

No separate optional deliverables are required beyond the listed deliverables.

---

# 35. Definition of Done

The following checklist is based only on requirements/outcomes stated in the document.

- [ ] Project initialization completed.
- [ ] Frontend and backend initialized.
- [ ] Authentication implemented.
- [ ] JWT authentication implemented.
- [ ] OAuth2 login implemented.
- [ ] Role-based access control implemented.
- [ ] User profile management functional.
- [ ] Palmistry reference datasets integrated.
- [ ] Tarot reference datasets integrated.
- [ ] Palm analysis engine operational.
- [ ] Palm feature extraction operational.
- [ ] Tarot reading engine functional.
- [ ] Supported tarot spreads implemented.
- [ ] Reading generation workflow completed.
- [ ] AI interpretation engine operational.
- [ ] Personality intelligence workflows implemented.
- [ ] Life trend analysis implemented.
- [ ] Recommendation system functional.
- [ ] Spiritual guidance scoring implemented.
- [ ] Personalized dashboards completed.
- [ ] Analytics modules implemented.
- [ ] Notification and engagement system implemented.
- [ ] Reports generated.
- [ ] PDF export implemented.
- [ ] Excel export implemented.
- [ ] Frontend/backend integration completed.
- [ ] API validation/testing completed.
- [ ] End-to-end workflow testing completed.
- [ ] Security testing completed.
- [ ] Performance optimization completed.
- [ ] Docker containerization completed.
- [ ] Production deployment completed.
- [ ] Monitoring and logging configured.
- [ ] Documentation completed.
- [ ] User guides prepared.
- [ ] Final presentation prepared.
- [ ] End-to-end palmistry and tarot workflow demonstrable.

---

# 36. Constraints and Important Rules

## 36.1 Technology Constraints

**[REQUIRED]**

The project technology stack names:

- Python.
- FastAPI.
- JavaScript.
- React.js.
- PostgreSQL.
- MongoDB.
- OpenCV.
- YOLO.
- MediaPipe.
- TensorFlow.
- PyTorch.
- LangChain.
- Hugging Face Transformers.
- OpenAI APIs.
- Sentence Transformers.
- Pillow.
- Albumentations.
- Docker.
- AWS / Azure.
- Tailwind CSS.
- Chart.js.
- Plotly.
- Git/GitHub.
- Docker Compose.
- GitHub Actions.
- Postman.

## 36.2 Architecture Constraints

The architecture is organized around:

- API Gateway.
- Microservices.
- AI/ML intelligence engine.
- Multiple data stores.
- External service integrations.
- Monitoring/logging.
- Backup/security.

## 36.3 Explicit Alternatives

Where alternatives are given:

- AWS / Azure.
- AWS S3 / Azure Blob.
- FAISS / Chroma.
- Stripe / Razorpay.
- SendGrid / Twilio.

Do not present both alternatives as mandatory implementations unless the project owner explicitly decides to use both.

## 36.4 Security Constraints

- JWT authentication.
- OAuth2.
- Role-based access.
- Data encryption.
- Security monitoring.
- Access control.
- Automated backups.
- Disaster recovery.

## 36.5 Performance Constraints

The platform is expected to support large-scale reading generation and analytics workflows while maintaining stable performance and responsiveness.

The document does not provide numerical thresholds.

---

# 37. Resolved Implementation Decisions

The following decisions are already resolved by the defaults in Section 49. The coding agent should use them directly and should not block implementation by asking for these details.

## 37.1 API Contract
Use FastAPI REST endpoints under `/api/v1`, Pydantic schemas, JSON payloads, consistent error responses, request IDs, pagination, and the authentication conventions in Section 49.

## 37.2 Database Schema
Design PostgreSQL tables, MongoDB collections, indexes, constraints, and relationships around the entities listed in Sections 10 and 12. Use UUID identifiers, UTC timestamps, migrations, and repository/service boundaries.

## 37.3 Dataset Selection
Select license-compatible palmistry, hand-landmark, and tarot datasets. Record dataset name, version, license, URL, classes, annotations, checksums, and split information in `data/README.md`.

## 37.4 Model Selection
Use transfer-learning CNNs for palm line/feature models, a vision classifier for tarot cards, OpenAI as the default interpretation model provider, Sentence Transformers for embeddings, a personality intelligence pipeline, and a trend prediction/synthesis pipeline. Keep every model replaceable through adapters/configuration.

## 37.5 AI Prompting and Output
Use versioned structured prompts and structured JSON outputs validated by Pydantic schemas. Store model ID, prompt version, timestamps, and relevant input context metadata with generated interpretations.

## 37.6 Scoring
Normalize component scores to 0–100 and apply the fixed weighted formula in Sections 7 and 8. Use the score labels defined in Section 49.

## 37.7 Spiritual Knowledge Base
Use a structured knowledge base containing tarot meanings, spread meanings, palm feature meanings, symbol relationships, interpretation guidance, and recommendation mappings. Use retrieval before generation.

## 37.8 Image Handling
Use JPG, JPEG, PNG, and WEBP up to 10 MB per image. Validate file type/signature, normalize images before inference, and retain an audit-safe original.

## 37.9 Mobile Strategy
Implement responsive web/PWA access first. Keep APIs and frontend architecture suitable for later native Android/iOS clients without rewriting core business logic.

## 37.10 Payment Strategy
Keep payment integration behind an adapter. Default provider is Razorpay; Stripe is the interchangeable alternative. Do not invent pricing or paid features.

## 37.11 Notification Strategy
Default channels are in-app and email. SendGrid is the default email provider; Twilio is the SMS adapter. Respect per-user notification preferences.

## 37.12 Cloud Strategy
Default production cloud is AWS. Default object storage is S3. Keep Azure/Blob Storage adapters available.

## 37.13 Vector Database
Default vector database is Chroma. Keep a vector-store interface so FAISS can be substituted.

## 37.14 External Providers
- AI: OpenAI by default; Hugging Face for compatible local/open alternatives.
- Payments: Razorpay by default; Stripe adapter.
- Email: SendGrid by default; Twilio for SMS.
- Storage: AWS S3 by default; Azure Blob adapter.

## 37.15 Performance
Use the initial engineering targets in Section 49.17, benchmark them under realistic workloads, and record measured results rather than claiming unmeasured performance.

# 38. Evaluation Criteria

## Milestone 1 — Week 2

**[REQUIRED]**

- Project initialization completed.
- Authentication implemented.
- User profile management functional.
- Palmistry and tarot datasets integrated.

## Milestone 2 — Week 4

**[REQUIRED]**

- Palm analysis engine operational.
- Tarot reading workflows functional.
- Reading generation system implemented.

## Milestone 3 — Week 6

**[REQUIRED]**

- AI interpretation engine operational.
- Recommendation system functional.
- Personalized guidance workflows completed.

## Milestone 4 — Week 8

**[REQUIRED]**

- Fully deployed frontend and backend.
- Dashboards and reporting systems operational.
- End-to-end palmistry and tarot intelligence workflow demonstrated.

---

# 39. AI Agent Development Rules

This section defines the specification-of-truth behavior for an AI coding/development agent working from this document.

## 40.1 Specification Authority

1. The uploaded document is the primary specification of truth.
2. Do not remove mandatory requirements.
3. Do not replace specified technologies without a strong implementation reason and explicit project decision.
4. Do not invent requirements.
5. Clearly distinguish mandatory requirements from implementation decisions.
6. If something is ambiguous, identify the ambiguity instead of silently guessing.
7. Preserve compatibility between modules.
8. Follow task dependencies.
9. Do not implement optional/alternative items as mandatory without a project decision.
10. Prefer simple, maintainable implementations unless the document requires complexity.
11. Maintain the project's stated architecture as closely as practical.
12. Before major architectural changes, verify whether the document already specifies an approach.
13. Keep track of completed and remaining requirements.
14. Never claim a feature is implemented unless it actually exists.
15. When a requirement cannot be implemented exactly, explain the limitation and propose the closest compatible alternative.

## 40.2 Requirement Labeling

Use these labels in planning and implementation documents:

- **[REQUIRED]** — directly stated in specification.
- **[SYSTEM FLOW]** — recommended end-to-end flow connecting multiple requirements.
- **[DEFAULT]** — implementation decision to use unless explicitly overridden.
- **[DECISION]** — a project-level implementation decision recorded by the agent.

## 40.3 Technical Accuracy

Preserve:

- Exact technology names.
- Exact model names/categories.
- Exact library names.
- Numerical values.
- Formula weights.
- Database technology names.
- External provider names.
- Terminology.
- Architecture relationships.
- Explicit constraints.

---

# 40. Final Master Requirements Table

> **Priority rule:** The project uses practical implementation priorities. P0 items are essential to a working product; P1 items are required capabilities that follow the core flow; P2 items are enhancement/scale items.

| ID | Requirement | Type | Priority | Status |
|---|---|---|---|---|---|
| FR-001 | User registration and login | Functional | P1 | Pending |
| FR-002 | JWT authentication | Security | P1 | Pending |
| FR-003 | OAuth2 login | Security | P1 | Pending |
| FR-004 | Role-based access control | Security | P1 | Pending |
| FR-005 | User profile management | Functional | P1 | Pending |
| FR-006 | Palm image upload | Functional / AI | P1 | Pending |
| FR-007 | Palm preprocessing | AI/ML | P1 | Pending |
| FR-008 | Palm feature extraction | AI/ML | P1 | Pending |
| FR-009 | Palm line detection | AI/ML | P1 | Pending |
| FR-010 | Palm pattern recognition | AI/ML | P1 | Pending |
| FR-011 | Palm shape analysis | AI/ML | P1 | Pending |
| FR-012 | Finger structure analysis | AI/ML | P1 | Pending |
| FR-013 | Tarot deck selection | Functional | P1 | Pending |
| FR-014 | Card shuffling simulation | Functional | P1 | Pending |
| FR-015 | Card selection workflow | Functional | P1 | Pending |
| FR-016 | Tarot spread generation | Functional | P1 | Pending |
| FR-017 | Single-card spread | Functional | P1 | Pending |
| FR-018 | Three-card spread | Functional | P1 | Pending |
| FR-019 | Relationship spread | Functional | P1 | Pending |
| FR-020 | Career spread | Functional | P1 | Pending |
| FR-021 | Celtic Cross spread | Functional | P1 | Pending |
| FR-022 | Life Path spread | Functional | P1 | Pending |
| FR-023 | Palm interpretation generation | AI/ML | P1 | Pending |
| FR-024 | Tarot interpretation generation | AI/ML | P1 | Pending |
| FR-025 | Context-aware insight generation | AI/ML | P1 | Pending |
| FR-026 | Personalized guidance creation | AI/ML | P1 | Pending |
| FR-027 | Reading synthesis | AI/ML | P1 | Pending |
| FR-028 | Personality profiling | AI/ML | P1 | Pending |
| FR-029 | Strength analysis | AI/ML | P1 | Pending |
| FR-030 | Weakness analysis | AI/ML | P1 | Pending |
| FR-031 | Behavioral insights | AI/ML | P1 | Pending |
| FR-032 | Personal development recommendations | AI/ML | P1 | Pending |
| FR-033 | Life path analysis | AI/ML | P1 | Pending |
| FR-034 | Opportunity identification | AI/ML | P1 | Pending |
| FR-035 | Challenge forecasting | AI/ML | P1 | Pending |
| FR-036 | Trend monitoring | AI/ML | P1 | Pending |
| FR-037 | Growth potential assessment | AI/ML | P1 | Pending |
| FR-038 | Personality alignment scoring | AI/ML | P1 | Pending |
| FR-039 | Reading confidence scoring | AI/ML | P1 | Pending |
| FR-040 | Guidance relevance scoring | AI/ML | P1 | Pending |
| FR-041 | Self-development scoring | AI/ML | P1 | Pending |
| FR-042 | Weighted overall insight score | AI/ML | P1 | Pending |
| FR-043 | Personal growth recommendations | AI/ML | P1 | Pending |
| FR-044 | Relationship guidance | AI/ML | P1 | Pending |
| FR-045 | Career suggestions | AI/ML | P1 | Pending |
| FR-046 | Goal alignment recommendations | AI/ML | P1 | Pending |
| FR-047 | Spiritual development insights | AI/ML | P1 | Pending |
| FR-048 | User dashboard | UI | P1 | Pending |
| FR-049 | Tarot Reader dashboard | UI | P1 | Pending |
| FR-050 | Spiritual Consultant dashboard | UI | P1 | Pending |
| FR-051 | Admin dashboard | UI | P1 | Pending |
| FR-052 | Daily guidance notifications | Functional | P1 | Pending |
| FR-053 | Reading reminders | Functional | P1 | Pending |
| FR-054 | Insight updates | Functional | P1 | Pending |
| FR-055 | Spiritual growth alerts | Functional | P1 | Pending |
| FR-056 | Platform announcements | Functional | P1 | Pending |
| FR-057 | Palmistry reports | Reporting | P1 | Pending |
| FR-058 | Tarot reports | Reporting | P1 | Pending |
| FR-059 | Personality reports | Reporting | P1 | Pending |
| FR-060 | Spiritual guidance reports | Reporting | P1 | Pending |
| FR-061 | Insight trend reports | Reporting | P1 | Pending |
| FR-062 | PDF export | Reporting | P1 | Pending |
| FR-063 | Excel export | Reporting | P1 | Pending |
| FR-064 | Frontend/backend integration | Technical | P1 | Pending |
| FR-065 | API validation/testing | API | P1 | Pending |
| FR-066 | End-to-end workflow testing | Technical | P1 | Pending |
| FR-067 | Security testing | Security | P1 | Pending |
| FR-068 | Performance optimization | Performance | P1 | Pending |
| FR-069 | Docker containerization | Deployment | P1 | Pending |
| FR-070 | Production deployment | Deployment | P1 | Pending |
| FR-071 | Monitoring and logging setup | Technical | P1 | Pending |
| FR-072 | Documentation and user guides | Documentation | P1 | Pending |

---

# 41. Reference Technical Inventory

For implementation reference, the following exact technology names are preserved from the document.

## Programming / Backend

- Python.
- FastAPI.

## Frontend

- JavaScript.
- React.js.
- Next.js.
- Tailwind CSS.

## Databases / Storage

- PostgreSQL.
- MongoDB.
- Redis.
- Elasticsearch.
- FAISS.
- Chroma.
- Neo4j.
- InfluxDB.
- AWS S3.
- Azure Blob.

## AI / ML / CV

- OpenCV.
- YOLO.
- MediaPipe.
- TensorFlow.
- PyTorch.
- Sentence Transformers.

## NLP / LLM / AI APIs

- LangChain.
- Hugging Face Transformers.
- OpenAI APIs.

## Reporting / Visualization

- Chart.js.
- Plotly.

## Cloud / Deployment / DevOps

- Docker.
- Docker Compose.
- AWS.
- Azure.
- GitHub Actions.

## Development / Testing

- VS Code.
- Git.
- GitHub.
- Postman.

## External Services

- Stripe.
- Razorpay.
- SendGrid.
- Twilio.
- Google Analytics.

---

# 42. Reference Dataset Inventory

| Dataset | Purpose |
|---|---|
| Palmistry Image Dataset | Palm line detection, palm feature extraction, palm classification |
| Hand Landmark Dataset | Hand segmentation, palm structure analysis, finger pattern detection |
| Tarot Card Image Dataset | Tarot card recognition, card classification, card interpretation support |

No specific dataset URLs or named public datasets are provided in the document.

---

# 43. Reference Palm Feature Inventory

The document explicitly identifies these features:

1. Life Line.
2. Head Line.
3. Heart Line.
4. Fate Line.
5. Sun Line.
6. Palm Shape.
7. Finger Structure.

---

# 44. Reference Tarot Spread Inventory

1. Single Card Reading.
2. Three Card Reading.
3. Relationship Spread.
4. Career Spread.
5. Celtic Cross Spread.
6. Life Path Spread.

---

# 45. Reference Insight Category Inventory

1. Personality.
2. Relationships.
3. Career.
4. Finance.
5. Health & Wellness.
6. Personal Growth.
7. Life Opportunities.

---

# 46. Reference Performance Metric Inventory

## Palm Analysis

- Palm feature detection accuracy.
- Palm classification accuracy.
- Palm interpretation consistency.

## Tarot Intelligence

- Card recognition accuracy.
- Interpretation relevance score.
- Reading completion rate.

## Recommendations

- Guidance relevance.
- User engagement rate.
- Recommendation effectiveness.

## Analytics

- Reading satisfaction score.
- User retention rate.
- Session engagement rate.

## System Performance

- API response time.
- Dashboard loading speed.
- Reading generation latency.
- Concurrent user handling capacity.

---

# 49. Implementation Decisions and Defaults

This section resolves open implementation choices so the coding agent can proceed without unnecessary clarification. These defaults may be changed through an explicit engineering decision recorded in `docs/decisions/`.

## 49.1 Frontend
- Next.js with React.js and JavaScript.
- Tailwind CSS for styling.
- Chart.js for standard dashboard charts.
- Plotly for advanced analytical visualizations.
- Responsive web application/PWA is the initial mobile strategy.

## 49.2 Backend
- FastAPI with Python 3.12.
- REST API prefix `/api/v1`.
- Pydantic for validation.
- SQLAlchemy + Alembic for PostgreSQL.
- MongoDB access through a repository/service layer.
- Redis for cache/session/temporary state.
- Celery + Redis for long-running background jobs.

## 49.3 Authentication and RBAC
- JWT access tokens with short expiry and rotating refresh tokens.
- OAuth2 provider default: Google.
- Password hashing: Argon2id.
- User: own profile, readings, reports, notifications, recommendations.
- Tarot Reader: assigned-user reading access, session tracking, reading analytics, report management.
- Spiritual Consultant: trend analysis, consultation insights, guidance effectiveness.
- Administrator: user management, platform analytics, configuration, system reports, audit logs.
- Enforce permissions in the backend; frontend checks are supplementary only.

## 49.4 Media
- Accepted image types: JPG, JPEG, PNG, WEBP.
- Maximum single upload: 10 MB.
- Validate MIME type and file signature.
- Preserve the original upload and create a normalized processing copy.

## 49.5 Palm Computer Vision
- Preprocess with orientation correction, resize, RGB conversion, denoising, contrast normalization, segmentation, and normalization.
- MediaPipe for landmarks; OpenCV for image operations.
- YOLO where region/object detection is needed.
- PyTorch transfer-learning CNN by default for learned palm-line/feature models.
- Required outputs: Life Line, Head Line, Heart Line, Fate Line, Sun Line, Palm Shape, Finger Structure.
- Persist model version and confidence for every inference result.

## 49.6 Tarot
- Default deck: Rider-Waite-Smith.
- Data-driven deck definitions so additional decks can be added.
- Production shuffle: cryptographically secure Fisher-Yates.
- Test mode supports deterministic seeds.
- Required spreads: Single Card, Three Card, Relationship, Career, Celtic Cross, Life Path.
- Every spread definition contains card positions, labels, meanings, and interpretation order.

## 49.7 AI / LLM
- Default primary provider: OpenAI API.
- LangChain for orchestration where useful.
- Hugging Face Transformers for local/open alternatives when appropriate.
- Sentence Transformers for embeddings.
- Keep provider/model names configurable.
- Validate every LLM response against a structured schema before persistence.
- Store model identifier, prompt version, and timestamp with generated interpretations.

## 49.8 Knowledge / Retrieval
- Default vector database: Chroma.
- Neo4j for symbolic relationships.
- Elasticsearch for search.
- Knowledge domains: tarot meanings, spread meanings, palm feature meanings, symbol relations, interpretation guidance, recommendation mappings.
- Retrieval precedes generation for grounded interpretation.

## 49.9 Insight Scoring
Normalize each component score to 0–100 before applying the fixed weights:

```text
Overall Insight Score =
  0.30 × Palm Analysis Confidence
+ 0.25 × Tarot Interpretation Relevance
+ 0.20 × Personality Alignment
+ 0.15 × User Context Relevance
+ 0.10 × Reading Consistency
```

Labels: 0–39 Low, 40–69 Moderate, 70–84 High, 85–100 Very High. Never present the score as objective certainty.

## 49.10 Data Architecture
- PostgreSQL is the transactional system of record.
- MongoDB stores flexible palm/tarot/insight/notification/log documents.
- Redis stores sessions, cache, and temporary state.
- Elasticsearch stores search indexes.
- Chroma stores embeddings and semantic retrieval data.
- Neo4j stores symbolic relationships.
- InfluxDB stores time-series engagement, trend, and performance data.
- Use UUIDs and UTC timestamps.
- Use database migrations from the beginning.

## 49.11 Storage and Cloud
- Default cloud: AWS.
- Default object storage: S3.
- Keep an interface allowing Azure Blob substitution.

## 49.12 Payments
- Default provider: Razorpay.
- Keep Stripe behind the same payment adapter.
- Do not invent pricing, subscriptions, or paid features that are not part of the approved business flow.

## 49.13 Notifications
- Default channels: in-app + email.
- Default email provider: SendGrid.
- Twilio remains the provider adapter for SMS.
- User preferences control notification opt-in/out.
- Store scheduling data in UTC and render in user-local time.

## 49.14 API Conventions
- REST + JSON.
- OpenAPI generated by FastAPI.
- Versioned endpoints under `/api/v1`.
- Error payload includes `code`, `message`, `request_id`, and optional field errors.
- General rate limit: 60 requests/minute/user; use stricter limits for expensive AI endpoints.
- Use cursor pagination for high-volume feeds and page/page_size for standard dashboards.

## 49.15 Testing
- Backend: pytest.
- Frontend: Vitest + React Testing Library.
- End-to-end: Playwright.
- API contract/manual validation: Postman.
- Every functional requirement must have at least one automated acceptance test.

## 49.16 Deployment
- Docker Compose for local development.
- GitHub Actions for CI/CD.
- AWS as default production cloud.
- Separate development/staging/production configuration.
- Health checks, structured logging, monitoring, alerts, backups, and disaster recovery are mandatory.

## 49.17 Performance Targets
- Typical API response: under 500 ms excluding async AI/model jobs.
- Dashboard initial load: under 2.5 s on a normal broadband connection.
- Palm inference target: under 10 s for supported images on the optimized deployment path.
- Long-running AI/report operations are asynchronous with job progress.
- API workers remain horizontally scalable.

## 49.18 Error Handling
- 400/422 for invalid request data as appropriate.
- 401 authentication failure.
- 403 authorization failure.
- 404 missing respecification.
- 415 unsupported media type.
- 429 rate limit.
- 502/503 for controlled external dependency failures.
- Retry transient provider failures with bounded exponential backoff.
- Never blindly retry non-idempotent operations.
- Every request gets a traceable request_id.

## 49.19 Safety of Generated Interpretations
- Treat palmistry and tarot as spiritual/interpretive experiences.
- Health outputs are non-diagnostic and should advise professional care for real health concerns.
- Financial outputs are not guaranteed investment advice.
- Trend/future outputs describe reflective possibilities rather than guaranteed events.
- Avoid manipulative, fear-based, or absolute claims.

# 50. Final Agent Operating Context

An AI coding/development agent should understand the project as follows:

```text
PROJECT:
Palmistry & Tarot Intelligence Platform

CORE PURPOSE:
AI-powered palm + tarot analysis that produces personalized spiritual
insights, guidance, personality intelligence, trend analysis,
recommendations, dashboards, analytics, and reports.

CLIENTS / USERS:
User
Tarot Reader
Spiritual Consultant
Administrator

CORE FLOWS:
Authentication
→ Profile
→ Palm Analysis and/or Tarot Reading
→ AI Interpretation
→ Personality Intelligence
→ Trend Analysis
→ Guidance Scoring
→ Recommendations
→ Reading Synthesis
→ Dashboard / Reports / Notifications

CORE BACKEND:
FastAPI + service-oriented / microservices architecture

CORE FRONTEND:
JavaScript + React.js
Additional listed UI stack: Next.js, Tailwind CSS, Chart.js, Plotly

CORE AI/ML:
CNN palm line detection
Palm feature recognition
Tarot classification
LLM/NLP interpretation
Insight generation
Recommendation engine
Personality profiling
Trend prediction

CORE DATA:
PostgreSQL
MongoDB
Redis
Elasticsearch
FAISS / Chroma
Media Storage
Neo4j
InfluxDB

EXTERNAL SERVICES:
AWS / Azure
OpenAI / Hugging Face / LangChain
Stripe / Razorpay
SendGrid / Twilio
Google Analytics, etc.

DEPLOYMENT:
Docker
AWS / Azure

REQUIRED FINAL STATE:
A deployed, integrated, tested, monitored platform with
working palmistry and tarot workflows, AI interpretation,
personalized guidance, dashboards, reports, exports,
documentation, and a demonstrable end-to-end workflow.
```

---

# 51. Final Quality-Control Rules

Before considering implementation complete, the development agent should verify:

## Completeness

- [ ] Entire project scope has been addressed.
- [ ] All listed modules have an implementation or documented reason for incomplete status.
- [ ] All supported tarot spreads are present.
- [ ] All listed palm features are present.
- [ ] All listed insight categories are represented.
- [ ] Dashboards for all four roles exist.
- [ ] Reporting and export requirements exist.
- [ ] Notifications are represented.
- [ ] Scoring model uses the document's stated weights.
- [ ] Required datasets/reference data have been integrated or their absence is explicitly documented.
- [ ] Deployment and monitoring are addressed.

## Accuracy

- [ ] Exact technology names are preserved.
- [ ] Alternatives are not silently collapsed into mandatory selections.
- [ ] No project requirement has been silently removed.
- [ ] No unsupported numerical thresholds have been invented.
- [ ] Unknown API/schema/model details must use Section 49 defaults and be documented when a later engineering decision changes them.
- [ ] Major implementation decisions are documented in `docs/decisions/`.

## AI Usability

- [ ] The agent can identify required modules.
- [ ] The agent can identify major dependencies.
- [ ] The agent can identify required-vs-default decisions.
- [ ] The agent can identify information gaps before implementation.
- [ ] The agent can track milestones and tasks.
- [ ] The agent can trace major requirements back to project sections.

---

# 52. Final Agent Execution Checklist

Before each task:
- [ ] Read the relevant specification section.
- [ ] Inspect the current repository implementation.
- [ ] Verify dependencies and interfaces.
- [ ] Update `AGENT_PROGRESS.md` with the planned change.

After each task:
- [ ] Implement the complete working slice.
- [ ] Add or update automated tests.
- [ ] Run lint, type checks, and builds.
- [ ] Run relevant integration tests.
- [ ] Verify existing features still work.
- [ ] Update `AGENT_PROGRESS.md`.

Before each milestone is complete:
- [ ] All milestone requirements are implemented.
- [ ] End-to-end workflow is demonstrable.
- [ ] Security and validation checks pass.
- [ ] Performance has been measured.
- [ ] Documentation reflects the actual implementation.
- [ ] Known limitations are recorded.

FINAL DEFINITION OF DONE:
The platform is complete only when authentication, role-based dashboards, palm analysis, tarot reading, AI interpretation, personality intelligence, trend analysis, scoring, recommendations, notifications, analytics, reports, exports, testing, Docker deployment, monitoring, security, documentation, and end-to-end workflows are implemented and demonstrably working together.
