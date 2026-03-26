import streamlit as st
from datetime import date

# ---------------------------------------------------------------------------
# Page config — must be first Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Meazure Sales Intelligence",
    page_icon="🔍",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Minimal style tweaks — keep it clean, no heavy CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* Slightly tighten the default max width */
        .block-container { max-width: 820px; padding-top: 2rem; }

        /* Section header styling */
        .section-title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #1A2E44;
            margin-bottom: 0.25rem;
        }

        /* Cost note */
        .cost-note {
            font-size: 0.78rem;
            color: #888888;
            margin-top: 1.5rem;
            text-align: right;
        }

        /* Bullet list items */
        .intel-list li {
            margin-bottom: 0.3rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("Meazure Sales Intelligence")
st.caption("Pre-call research for sales reps")
st.divider()

# ---------------------------------------------------------------------------
# Input form
# ---------------------------------------------------------------------------
with st.form("research_form"):
    company_url = st.text_input(
        "Company Website URL",
        placeholder="https://www.example.com",
        help="The company's main website. Used as the starting point for research.",
    )
    contact_name = st.text_input(
        "Contact Name (First Last) — optional",
        placeholder="Jane Smith",
        help="Full name of the person you're meeting with. Leave blank for company-only research.",
    )
    linkedin_url = st.text_input(
        "LinkedIn Profile URL (optional)",
        placeholder="https://www.linkedin.com/in/janesmith",
        help="Helps disambiguate the contact when the name is common.",
    )
    submitted = st.form_submit_button("Research", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# On submit — run research
# ---------------------------------------------------------------------------
if submitted:
    # Validate required fields
    if not company_url.strip():
        st.error("Please enter a company website URL.")
        st.stop()

    # Run with progress feedback
    result = None
    usage = None

    status_placeholder = st.empty()
    with st.spinner(""):
        status_placeholder.info("Researching company...")
        try:
            from agent import run_research
            # Update status mid-way (approximate — real progress is inside the agent)
            status_placeholder.info("Searching for contact and industry news...")
            result, usage = run_research(
                company_url=company_url.strip(),
                contact_name=contact_name.strip() if contact_name.strip() else None,
                linkedin_url=linkedin_url.strip() if linkedin_url.strip() else None,
            )
            status_placeholder.info("Generating insights...")
        except Exception as exc:
            status_placeholder.empty()
            st.error(f"Research failed: {exc}")
            st.stop()

    status_placeholder.empty()

    if result is None:
        st.error("No results returned. Please try again.")
        st.stop()

    # Check for parse error
    parse_error = result.get("_parse_error", False)
    if parse_error:
        st.warning(
            "The AI response could not be parsed as JSON. Showing raw output below. "
            "Try running again — this occasionally happens with complex responses."
        )
        st.text_area("Raw AI Output", result.get("_raw_text", ""), height=300)

    # -----------------------------------------------------------------------
    # Helper renderers
    # -----------------------------------------------------------------------
    def _val(v, fallback="Not available"):
        if v is None:
            return fallback
        v = str(v).strip()
        return v if v else fallback

    def _bullet_md(items):
        if not items:
            return "_None found._"
        return "\n".join(f"- {item}" for item in items if item and str(item).strip())

    # -----------------------------------------------------------------------
    # Section 1: Contact Intel
    # -----------------------------------------------------------------------
    with st.expander("Contact Intel", expanded=True):
        contact = result.get("contact", {})

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Name**")
            st.write(_val(contact.get("name")))
        with col2:
            st.markdown("**Title**")
            st.write(_val(contact.get("title")))

        st.markdown("**Responsibilities**")
        st.write(_val(contact.get("responsibilities")))

        st.markdown("**Professional Interests**")
        st.write(_val(contact.get("interests")))

        st.markdown("**Recent Activity**")
        st.write(_val(contact.get("recent_activity")))

        additional = contact.get("suggested_additional_contacts", [])
        if additional:
            st.markdown("**Suggested Additional Contacts**")
            for ac in additional:
                name = _val(ac.get("name"), "Unknown")
                title = _val(ac.get("likely_title"), "")
                why = _val(ac.get("why_relevant"), "")
                label = f"**{name}**"
                if title:
                    label += f" — {title}"
                st.markdown(f"- {label}")
                if why:
                    st.markdown(f"  *{why}*")

    # -----------------------------------------------------------------------
    # Section 2: Company Intel
    # -----------------------------------------------------------------------
    with st.expander("Company Intel", expanded=True):
        company = result.get("company", {})

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Company Name**")
            st.write(_val(company.get("name")))
        with col2:
            st.markdown("**Industry**")
            st.write(_val(company.get("industry")))

        website = _val(company.get("website"), "")
        if website and website != "Not available":
            st.markdown("**Website**")
            st.markdown(f"[{website}]({website})")

        st.markdown("**Description**")
        st.write(_val(company.get("description")))

        st.markdown("**Goals & Growth Areas**")
        st.write(_val(company.get("goals_and_growth_areas")))

        st.markdown("**Challenges**")
        st.write(_val(company.get("challenges")))

        st.markdown("**Stay-in-Touch Trigger**")
        st.write(_val(company.get("stay_in_touch")))

        news = company.get("recent_news", [])
        if news:
            st.markdown("**Recent News**")
            st.markdown(_bullet_md(news))

    # -----------------------------------------------------------------------
    # Section 3: Conversation Starters
    # -----------------------------------------------------------------------
    with st.expander("Conversation Starters", expanded=True):
        conv = result.get("conversation_starters", {})

        st.markdown("**Anticipated Pain Points**")
        pain_points = conv.get("anticipated_pain_points", [])
        if pain_points:
            st.markdown(_bullet_md(pain_points))
        else:
            st.write("_None identified._")

        st.markdown("**Suggested Questions for the Call**")
        questions = conv.get("suggested_questions", [])
        if questions:
            for i, q in enumerate(questions, 1):
                st.markdown(f"{i}. {q}")
        else:
            st.write("_None generated._")

    # -----------------------------------------------------------------------
    # Section 4: Meazure Opportunity Map
    # -----------------------------------------------------------------------
    with st.expander("Meazure Opportunity Map", expanded=True):
        opp_map = result.get("opportunity_map", [])

        if opp_map:
            for entry in opp_map:
                service = _val(entry.get("meazure_service"), "Unnamed Service")
                relevance = _val(entry.get("relevance"), "")
                talking = _val(entry.get("talking_point"), "")

                st.markdown(f"##### {service}")
                if relevance and relevance != "Not available":
                    st.markdown(f"**Why relevant:** {relevance}")
                if talking and talking != "Not available":
                    st.markdown(f"**Talking point:** _{talking}_")
                st.divider()
        else:
            st.write("_No opportunity mapping data available._")

    # -----------------------------------------------------------------------
    # PDF Export
    # -----------------------------------------------------------------------
    st.markdown("---")
    try:
        from pdf_export import generate_pdf
        pdf_bytes = generate_pdf(result, company_url.strip(), contact_name.strip())

        company_name_slug = (
            result.get("company", {}).get("name", "prospect")
            .lower()
            .replace(" ", "_")
            .replace("/", "")
        )
        contact_slug = contact_name.strip().lower().replace(" ", "_")
        filename = f"meazure_intel_{contact_slug}_{company_name_slug}_{date.today().isoformat()}.pdf"

        st.download_button(
            label="Export to PDF",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            use_container_width=False,
        )
    except Exception as e:
        st.warning(f"PDF generation failed: {e}")

    # -----------------------------------------------------------------------
    # Cost display
    # -----------------------------------------------------------------------
    if usage:
        cost_str = f"${usage['estimated_cost_usd']:.4f}"
        tokens_str = f"{usage['input_tokens']:,} in / {usage['output_tokens']:,} out"
        st.markdown(
            f"<div class='cost-note'>Estimated run cost: {cost_str} &nbsp;|&nbsp; Tokens: {tokens_str}</div>",
            unsafe_allow_html=True,
        )
