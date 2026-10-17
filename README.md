# KEYSTONE — Evidence-First AI Company Brain

**Hackathon:** Graph Hacks: Context for AI Agents  
**Track:** Company Brain  
**Technology:** Python, Streamlit, FalkorDB, Cypher

## 1. Problem

Company knowledge is often scattered across project plans, decisions, updates, and risk records. Traditional keyword search can find text but may fail to reveal how information connects across a business.

This makes it difficult to trace conflicting information, understand project impact, and identify the evidence behind a decision.

## 2. Solution

KEYSTONE is a graph-powered company intelligence prototype. It stores business knowledge and relationships in FalkorDB and uses Cypher queries to retrieve connected evidence.

KEYSTONE can:

- Search claims and their source documents.
- Identify potential conflicting launch-date claims in the demo dataset.
- Retrieve project ownership and recorded risks.
- Connect claims to decisions they support.
- Trace a potential conflict to the affected project, owner, and risk.
- Answer predefined questions about projects using graph data.

KEYSTONE is an evidence-retrieval prototype, not an autonomous decision-maker. Its question routing and recommendations are rule-based.

## 3. Why FalkorDB?

The relationships between knowledge items are central to KEYSTONE. FalkorDB stores entities and their connections as a property graph and allows the application to traverse those relationships using Cypher.

Examples of graph paths include:

- Document → CONTAINS → Claim → SUPPORTS → Decision
- Document → ABOUT → Project → HAS_RISK → Risk
- Person → OWNS → Project
- Claim → CONFLICTS_WITH → Claim

This helps KEYSTONE retrieve connected evidence rather than treating each piece of information in isolation.

## 4. Architecture

1. **User interface:** Streamlit presents search, company intelligence, Q&A, and impact analysis.
2. **Application logic:** Python routes questions to predefined query patterns.
3. **Graph database:** FalkorDB stores documents, claims, projects, people, decisions, risks, and relationships.
4. **Graph queries:** Cypher retrieves evidence and follows relationships.
5. **Impact analysis:** The application connects a potential conflict to the affected project, owner, and risk.

## 5. Graph Data Model

### Nodes

| Node | Properties |
|---|---|
| Document | id, title |
| Claim | id, text |
| Decision | id, text |
| Project | id, name, status |
| Person | id, name, role |
| Risk | id, title, severity |

### Relationships

| Relationship | Meaning |
|---|---|
| Document -[CONTAINS]-> Claim | A document contains a claim |
| Claim -[SUPPORTS]-> Decision | A claim supports a recorded decision |
| Claim -[CONFLICTS_WITH]-> Claim | Two claims are flagged as conflicting |
| Document -[ABOUT]-> Project | A document concerns a project |
| Person -[OWNS]-> Project | A person owns a project |
| Project -[HAS_RISK]-> Risk | A risk is associated with a project |

## 6. Demo Scenario

The synthetic Product Launch Plan contains two claims:

- The product launch is planned for December 2026.
- The product launch is planned for January 2027.

KEYSTONE retrieves the claims and traces their connections to the Product Launch project, its owner, and its recorded high-severity risk.

The prototype recommends verifying the authoritative date before finalizing campaign timing.

A second synthetic project, Customer Onboarding, demonstrates project-specific ownership and decision retrieval. It also demonstrates that KEYSTONE can report when no linked risk is recorded.

All example names and business records are synthetic demo data.

## 7. Example Cypher Query: Multi-Hop Impact Analysis

The following query traverses multiple graph relationships to connect a source document and conflicting claims to a project, its owner, and a recorded risk.

```cypher
MATCH (d:Document)-[:CONTAINS]->(c1:Claim)-[:CONFLICTS_WITH]->(c2:Claim),
      (d)-[:ABOUT]->(p:Project),
      (person:Person)-[:OWNS]->(p),
      (p)-[:HAS_RISK]->(risk:Risk)
RETURN d.title AS document,
       c1.text AS first_claim,
       c2.text AS conflicting_claim,
       p.name AS project,
       p.status AS project_status,
       person.name AS owner,
       risk.title AS risk,
       risk.severity AS severity;
```

### Example result

| Field | Expected demo value |
|---|---|
| document | Product Launch Plan |
| first_claim | The product launch is planned for December 2026. |
| conflicting_claim | The product launch is planned for January 2027. |
| project | Product Launch |
| project_status | At Risk |
| owner | Maya Chen |
| risk | Conflicting launch dates |
| severity | High |

**Why it matters:** This query follows connected graph relationships to show the potential business impact of conflicting evidence. The disagreement does not prove that either date is incorrect. A human should verify the authoritative date.

## 8. Run Locally

### Requirements

- Python 3.11 or newer
- A reachable FalkorDB instance
- Git, if cloning the repository

### Setup

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Create a `.env` file using `.env.example` as a template. Fill in your own FalkorDB connection settings.

Start the application:

```powershell
python -m streamlit run app.py
```

Open the local URL displayed in the terminal.

## 9. Configuration and Security

The application requires FalkorDB connection settings for the host, port, username, password, and graph name.

- Never commit `.env`, passwords, API keys, or other credentials.
- Use synthetic, public, or explicitly authorized data.
- Verify secure TLS configuration before deploying or transmitting credentials over an untrusted network.
- Apply appropriate database access permissions.

## 10. Limitations

- Question understanding uses keyword-based routing and predefined query patterns.
- The current potential-conflict detector uses a narrow launch-month rule; it is not a general contradiction detector.
- The prototype does not currently use an LLM to generate answers.
- Results depend on the information and relationships stored in FalkorDB.
- Missing graph relationships do not prove that a risk or decision does not exist elsewhere.
- The demo dataset is small and synthetic; broader validation is needed for real-world use.

## 11. AI Assistance

Disclose AI coding or writing assistance used in developing the project, as required by the hackathon rules. The project authors are responsible for testing the code and understanding how the system works.

## 12. License

Add an appropriate open-source license before publishing the repository if you intend to license the project for reuse. Do not claim a license until you have added its license file.
