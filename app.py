
import os
import streamlit as st
from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

def config_value(key, default=None):
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return os.getenv(key, default)

st.set_page_config(
    page_title="KEYSTONE | Company Brain",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 KEYSTONE")
st.subheader("Evidence-First AI Company Brain")
st.caption(
    "Find claims, trace decisions, and inspect the evidence "
    "connecting company knowledge."
)

@st.cache_resource
def get_graph():
    db = FalkorDB(
        host=config_value("FALKORDB_HOST"),
        port=int(config_value("FALKORDB_PORT", "57993")),
        username=config_value("FALKORDB_USERNAME"),
        password=config_value("FALKORDB_PASSWORD"),
        ssl=False,
        socket_connect_timeout=5,
        socket_timeout=10,
    )
    return db.select_graph(config_value("FALKORDB_GRAPH", "keystone"))
try:
    graph = get_graph()
    graph.query("RETURN 1 AS ready")
    st.success("Connected to FalkorDB Cloud")
except Exception as exc:
    st.error("Could not connect to FalkorDB. Check your connection settings.")
    st.caption(f"Technical detail: {type(exc).__name__}: {exc}")
    st.stop()

st.divider()

search_term = st.text_input(
    "Search company knowledge",
    placeholder="Try: launch, December 2026, campaign...",
)

if st.button("Search knowledge", type="primary"):
    
    query = """
    MATCH (d:Document)-[r1:CONTAINS]->(c:Claim)
    OPTIONAL MATCH (c)-[r2:SUPPORTS]->(dec:Decision)
    WITH d, c, dec, type(r1) AS document_link,
         type(r2) AS decision_link,
         toLower(
             coalesce(d.title, '') + ' ' +
             coalesce(c.text, '') + ' ' +
             coalesce(dec.text, '')
         ) AS searchable
    WHERE searchable CONTAINS toLower($term)
    RETURN d.id AS document_id,
           d.title AS document,
           c.id AS claim_id,
           c.text AS claim,
           dec.id AS decision_id,
           dec.text AS decision,
           document_link,
           decision_link
    LIMIT 50
    """

    
    try:
        result = graph.query(query, {"term": search_term.strip()})
        rows = result.result_set

        if not search_term.strip():
            st.info("Enter a search term first.")

        elif not rows:
            st.warning("No matching evidence found in the graph.")

        else:
            st.subheader(f"Evidence found: {len(rows)}")

            for row in rows:
                (
                    document_id, document,
                    claim_id, claim,
                    decision_id, decision,
                    document_link, decision_link
                ) = row

                with st.container(border=True):
                    st.markdown(f"**Document:** {document or 'Untitled'}")
                    st.markdown(f"**Claim:** {claim or 'No claim text'}")
                    st.markdown(f"**Decision:** {decision or 'No linked decision'}")

                    st.markdown("**Evidence path:**")
                    st.write(
                        f"Document -[{document_link}]-> Claim"
                    )

                    if decision:
                        st.write(
                            f"Claim -[{decision_link}]-> Decision"
                        )

                    with st.expander("Inspect evidence IDs"):
                        st.write("Document ID:", document_id)
                        st.write("Claim ID:", claim_id)
                        st.write("Decision ID:", decision_id)

    except Exception as exc:
        st.error(f"Search failed: {type(exc).__name__}: {exc}")


st.caption(
    "KEYSTONE retrieves connected evidence from FalkorDB. "
    "It does not invent an answer when no matching evidence is found."
)

st.divider()
st.subheader("⚠️ Potential Conflicts")
st.caption(
    "Flags claims about the same topic that may disagree. "
    "Review the underlying evidence before treating a conflict as confirmed."
)

try:
    conflict_query = """
    MATCH (d:Document)-[:CONTAINS]->(c1:Claim)
    MATCH (d)-[:CONTAINS]->(c2:Claim)
    WHERE c1.id < c2.id
      AND toLower(c1.text) CONTAINS 'launch'
      AND toLower(c2.text) CONTAINS 'launch'
      AND (
          (toLower(c1.text) CONTAINS 'december'
           AND toLower(c2.text) CONTAINS 'january')
          OR
          (toLower(c1.text) CONTAINS 'january'
           AND toLower(c2.text) CONTAINS 'december')
      )
    RETURN d.title AS document,
           c1.id AS claim1_id,
           c1.text AS claim1,
           c2.id AS claim2_id,
           c2.text AS claim2
    """

    conflicts = graph.query(conflict_query).result_set

    if conflicts:
        for conflict in conflicts:
            doc, id1, text1, id2, text2 = conflict

            with st.container(border=True):
                st.warning("Potential disagreement detected")
                st.write("**Document:**", doc)
                st.write(f"**Claim 1 ({id1}):** {text1}")
                
                st.write(f"**Claim 2 ({id2}):** {text2}")

                st.info(
                    "These claims mention different launch months. "
                    "Check the source and dates before deciding which is correct."
                )
    else:
        st.success("No matching potential conflicts found.")

except Exception as exc:
    st.error(f"Conflict check failed: {type(exc).__name__}: {exc}")
    

st.divider()
st.subheader("Knowledge graph overview")

try:
    overview_query = """
    MATCH (n)
    UNWIND labels(n) AS label
    RETURN label, count(n) AS total
    ORDER BY label
    """

    overview_rows = graph.query(overview_query).result_set

    metrics = {
        str(row[0]): int(row[1])
        for row in overview_rows
    }

    metric_labels = [
        ("Documents", "Document"),
        ("Claims", "Claim"),
        ("Decisions", "Decision"),
        ("Projects", "Project"),
        ("People", "Person"),
        ("Risks", "Risk"),
    ]

    cols = st.columns(3)

    for index, (display_name, node_label) in enumerate(metric_labels):
        with cols[index % 3]:
            st.metric(
                display_name,
                metrics.get(node_label, 0)
            )

except Exception as exc:
    st.warning(
        f"Graph overview is temporarily unavailable: "
        f"{type(exc).__name__}"
    )

st.divider()
st.subheader("🧠 Company Intelligence")
st.caption(
    "Answer project questions using connected graph evidence."
)

try:
    intelligence_query = """
    MATCH (p:Project)
    OPTIONAL MATCH (owner:Person)-[:OWNS]->(p)
    OPTIONAL MATCH (p)-[:HAS_RISK]->(risk:Risk)
    RETURN p.id AS project_id,
           p.name AS project_name,
           p.status AS project_status,
           owner.name AS owner_name,
           owner.role AS owner_role,
           risk.title AS risk_title,
           risk.severity AS risk_severity
    """

    intelligence_rows = graph.query(
        intelligence_query
    ).result_set

    if intelligence_rows:
        for row in intelligence_rows:
            (
                project_id,
                project_name,
                project_status,
                owner_name,
                owner_role,
                risk_title,
                risk_severity,
            ) = row

            with st.container(border=True):
                st.markdown(
                    f"### {project_name or project_id}"
                )

                st.write(
                    "**Project status:**",
                    project_status or "Not specified",
                )
                st.write(
                    "**Owner:**",
                    owner_name or "Not recorded",
                )
                st.write(
                    "**Role:**",
                    owner_role or "Not recorded",
                )
                st.write(
                    "**Associated risk:**",
                    risk_title or "No linked risk found",
                )
                st.write(
                    "**Risk severity:**",
                    risk_severity or "Not specified",
                )

                st.caption(
                    "Evidence source: Project, OWNS, and HAS_RISK "
                    "relationships stored in FalkorDB."
                )
    else:
        st.info("No projects found in the knowledge graph.")

except Exception as exc:
    st.error(
        f"Company Intelligence failed: "
        f"{type(exc).__name__}: {exc}"
    )

st.divider()

st.divider()
st.subheader("💬 Ask KEYSTONE")
st.caption(
    "Ask a company question. KEYSTONE identifies the project "
    "and retrieves supporting evidence from FalkorDB."
)

question = st.text_input(
    "Your question",
    placeholder="Who owns Customer Onboarding?",
    key="keystone_question",
)

if st.button("Ask Company Brain", type="primary"):
    q = question.strip().lower()

    if not q:
        st.info("Please enter a question first.")

    else:
        try:
            # Find project names already stored in FalkorDB.
            project_rows = graph.query("""
                MATCH (p:Project)
                RETURN p.name
            """).result_set

            project_names = [
                str(row[0]) for row in project_rows if row[0]
            ]

            # Recognize a project by its full name or a distinctive word.
            matched_project = None

            for name in project_names:
                name_lower = name.lower()
                words = [
                    word for word in name_lower.split()
                    if len(word) > 3
                ]

                if name_lower in q or any(
                    word in q for word in words
                ):
                    matched_project = name
                    break

            project_param = {"project_name": matched_project}
            rows = []

            # 1. Project ownership
            if any(word in q for word in [
                "owner", "owns", "ownership", "responsible",
                "who manages", "who is managing",
                "who leads", "who is leading"
            ]):
                rows = graph.query("""
                    MATCH (person:Person)-[:OWNS]->(p:Project)
                    WHERE $project_name IS NULL
                       OR toLower(p.name) = toLower($project_name)
                    RETURN p.name, person.name, person.role
                    ORDER BY p.name
                """, project_param).result_set

                if rows:
                    st.markdown("### Project ownership")

                    for project, person, role in rows:
                        st.write(f"**Project:** {project or 'Unknown'}")
                        st.write(f"**Owner:** {person or 'Not recorded'}")
                        st.write(f"**Role:** {role or 'Not recorded'}")
                        st.caption(
                            "Evidence path: Person -[OWNS]-> Project"
                        )
                else:
                    st.info(
                        "No ownership relationship is recorded "
                        "for the requested project."
                    )

            # 2. Project risks
            elif any(word in q for word in [
                "risk", "risks", "danger", "severity", "at risk"
            ]):
                if matched_project:
                    rows = graph.query("""
                        MATCH (p:Project)
                        WHERE toLower(p.name) = toLower($project_name)
                        OPTIONAL MATCH (p)-[:HAS_RISK]->(risk:Risk)
                        RETURN p.name, p.status,
                               risk.title, risk.severity
                    """, project_param).result_set
                else:
                    rows = graph.query("""
                        MATCH (p:Project)-[:HAS_RISK]->(risk:Risk)
                        RETURN p.name, p.status,
                               risk.title, risk.severity
                        ORDER BY p.name
                    """).result_set

                if rows:
                    st.markdown("### Project risk evidence")

                    for project, status, title, severity in rows:
                        st.write(f"**Project:** {project or 'Unknown'}")
                        st.write(
                            f"**Status:** {status or 'Not recorded'}"
                        )

                        if title:
                            st.write(f"**Recorded risk:** {title}")
                            st.write(
                                f"**Severity:** {severity or 'Not recorded'}"
                            )
                            st.caption(
                                "Evidence path: Project -[HAS_RISK]-> Risk"
                            )
                        else:
                            st.info(
                                f"No linked risk is recorded for {project}."
                            )
                else:
                    st.info(
                        "No linked project risks were found in the graph."
                    )

            # 3. Decisions linked to claims and projects
            elif any(word in q for word in [
                "decision", "decisions", "campaign", "prepare"
            ]):
                if matched_project:
                    rows = graph.query("""
                        MATCH (doc:Document)-[:ABOUT]->(p:Project)
                        MATCH (doc)-[:CONTAINS]->(c:Claim)
                              -[:SUPPORTS]->(d:Decision)
                        WHERE toLower(p.name) = toLower($project_name)
                        RETURN p.name, doc.title, c.text, d.text
                    """, project_param).result_set
                else:
                    rows = graph.query("""
                        MATCH (c:Claim)-[:SUPPORTS]->(d:Decision)
                        RETURN null, null, c.text, d.text
                    """).result_set

                if rows:
                    st.markdown("### Decision evidence")

                    for project, document, claim, decision in rows:
                        if project:
                            st.write(f"**Project:** {project}")
                        if document:
                            st.write(f"**Source document:** {document}")

                        st.write(
                            f"**Supporting claim:** {claim or 'Not recorded'}"
                        )
                        st.write(
                            f"**Decision:** {decision or 'Not recorded'}"
                        )
                        st.caption(
                            "Evidence path: Document → Claim → Decision"
                        )
                else:
                    st.info(
                        "No linked decision evidence was found "
                        "for the requested project."
                    )

            # 4. Launch-date claims and potential conflicts
            elif any(word in q for word in [
                "launch", "date", "month", "conflict",
                "conflicting", "disagree", "disagreement"
            ]):
                rows = graph.query("""
                    MATCH (d:Document)-[:CONTAINS]->(c:Claim)
                    WHERE toLower(coalesce(c.text, '')) CONTAINS 'launch'
                    RETURN d.title, c.id, c.text
                    ORDER BY c.id
                """).result_set

                if rows:
                    st.markdown("### Launch-date evidence")

                    for document, claim_id, claim in rows:
                        st.write(f"**Source document:** {document}")
                        st.write(f"**Claim ID:** {claim_id}")
                        st.write(f"**Evidence:** {claim}")

                    st.warning(
                        "Review the source claims before deciding "
                        "which launch date is authoritative."
                    )
                else:
                    st.info("No launch-related claims were found.")

            else:
                st.info(
                    "Try asking about ownership, risks, decisions, "
                    "or launch dates. Include a project name or a "
                    "distinctive word such as 'onboarding' or 'launch'."
                )

        except Exception as exc:
            st.error(
                f"Question failed: {type(exc).__name__}: {exc}"
            )


st.write(
    "Trace a disagreement through the knowledge graph "
    "to the affected project, owner, and risk."
)

if st.button("Trace Launch-Date Impact"):
    impact_query = """
    MATCH (d:Document)-[:CONTAINS]->(c1:Claim)
          -[:CONFLICTS_WITH]->(c2:Claim)
    MATCH (d)-[:ABOUT]->(p:Project)
    OPTIONAL MATCH (person:Person)-[:OWNS]->(p)
    OPTIONAL MATCH (p)-[:HAS_RISK]->(risk:Risk)
    RETURN d.title AS document,
           c1.text AS claim_one,
           c2.text AS claim_two,
           p.name AS project,
           p.status AS status,
           person.name AS owner,
           risk.title AS risk,
           risk.severity AS severity
    """

    try:
        impact_rows = graph.query(impact_query).result_set

        if not impact_rows:
            st.warning(
                "No complete impact path found. "
                "Check that the document, project, conflict, "
                "owner, and risk relationships exist."
            )

        for row in impact_rows:
            (
                document, claim_one, claim_two,
                project, status, owner, risk, severity
            ) = row

            with st.container(border=True):
                st.markdown("### Potential business impact")

                st.write("**Source document:**", document)
                st.write("**First claim:**", claim_one)
                st.write("**Conflicting claim:**", claim_two)

                st.divider()

                st.write("**Affected project:**", project)
                st.write("**Project status:**", status or "Not recorded")
                st.write("**Project owner:**", owner or "Not recorded")
                st.write("**Recorded risk:**", risk or "Not recorded")
                st.write(
                    "**Risk severity:**",
                    severity or "Not recorded"
                )

                st.info(
                    "Recommended follow-up: ask the project owner "
                    "to verify the authoritative launch date before "
                    "finalizing campaign timing."
                )

                st.caption(
                    "Graph path: Document → Claim → Conflicting Claim; "
                    "Document → Project → Owner / Risk."
                )

    except Exception as exc:
        st.error(
            f"Impact analysis failed: {type(exc).__name__}: {exc}"
        )

