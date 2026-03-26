import os
import json
import re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

def _get_api_key():
    """Read API key from st.secrets (Streamlit Cloud) or .env (local)."""
    try:
        import streamlit as st
        return st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    except Exception:
        return os.environ.get("ANTHROPIC_API_KEY")

MEAZURE_PORTFOLIO = """
Meazure Learning offers the following products and services:

SERVICES:
- Test Program Consultation: Strategic guidance for exam program development
- Test Development & Psychometrics: Expert creation and validation of assessments
- Item Writing & Analysis: Professional creation and evaluation of test questions
- Advanced Remote Exam Security: Protecting assessment integrity during online testing
- Test Administration & Delivery: End-to-end management of exam logistics
- Scoring, Marking & Standard Setting: Professional evaluation and benchmarking
- Data Forensics: Analysis to detect irregularities and ensure assessment validity
- Robust Reporting: Comprehensive analytics and insights
- Remote Exam Proctoring (ProctorU): Monitored online testing with human oversight
- Test Center Proctoring: In-person supervised exam administration

TECHNOLOGY PLATFORMS:
- Meazure Exam Platform: Integrated testing delivery
- Guardian Secure Browser: Lockdown browser for exam security
- PASS: Exam delivery system
- ADE: Item authoring and exam development
- Connect: Candidate management system
- Itematic: Automated item generation using AI
- RedPen: Constructed response marking automation
"""

SYSTEM_PROMPT = f"""You are a senior sales intelligence analyst for Meazure Learning, a leading provider of assessment, exam delivery, and proctoring solutions.

Your task is to research a prospect and produce a structured intelligence report for a sales rep preparing for a call.

MEAZURE LEARNING PORTFOLIO (do not search for this — use as-is):
{MEAZURE_PORTFOLIO}

RESEARCH INSTRUCTIONS:
You have access to a web search tool. Use it to gather information in this order:
1. Search the company website URL provided to understand what the company does, its products/services, and mission.
2. Search for recent company news: funding rounds, leadership changes, press releases, partnerships, expansions (last 6-12 months). Use query like: "<company name> news 2024 2025"
3. Search for the individual contact by combining their full name with the company name, e.g. "<First Last> <Company Name>". Do NOT search by name alone — many people share names. If a LinkedIn URL is provided, reference it as context.
4. Search for industry trends relevant to the company's domain, e.g. "<industry> assessment trends 2025" or "<industry> certification trends".
5. Use all gathered information to reason about how Meazure Learning's portfolio maps to this prospect's needs.

OUTPUT FORMAT:
Return ONLY a valid JSON object. No markdown, no code fences, no explanatory text — just raw JSON.

The JSON must follow this exact schema:
{{
  "contact": {{
    "name": "full name of the contact",
    "title": "their job title if found, else empty string",
    "responsibilities": "brief description of their likely role and responsibilities based on title and company context",
    "interests": "professional interests, areas of focus, or topics they engage with publicly",
    "recent_activity": "any recent posts, articles, speaking engagements, or public activity",
    "suggested_additional_contacts": [
      {{
        "name": "name if found, else a role description like 'VP of Certification'",
        "likely_title": "their title or likely title",
        "why_relevant": "why a Meazure sales rep should also speak with this person"
      }}
    ]
  }},
  "company": {{
    "name": "company name",
    "website": "company website URL",
    "description": "2-3 sentence summary of what the company does",
    "industry": "primary industry or sector",
    "recent_news": ["bullet string 1", "bullet string 2"],
    "goals_and_growth_areas": "what the company appears to be prioritizing or growing toward",
    "challenges": "likely operational, compliance, or competitive challenges the company faces",
    "stay_in_touch": "a reason or trigger to follow up with this company in the future (e.g. upcoming conference, renewal cycle, regulatory change)"
  }},
  "conversation_starters": {{
    "anticipated_pain_points": [
      "pain point 1 relevant to assessments, credentialing, exams, or workforce",
      "pain point 2",
      "pain point 3"
    ],
    "suggested_questions": [
      "open-ended question for the sales call 1",
      "open-ended question 2",
      "open-ended question 3"
    ]
  }},
  "opportunity_map": [
    {{
      "meazure_service": "exact name of Meazure service or product",
      "relevance": "why this is relevant to this specific prospect",
      "talking_point": "a concrete, tailored talking point the sales rep can use"
    }}
  ]
}}

Be specific and factual. If you cannot find information for a field, use an empty string or empty array rather than making things up. The opportunity_map should include 3-5 services that are genuinely relevant to this prospect — do not list all services indiscriminately.
"""


def run_research(company_url: str, contact_name: str = None, linkedin_url: str = None) -> tuple[dict, dict]:
    """
    Run sales intelligence research for a given company and contact.

    Returns:
        (result_dict, usage_dict) where usage_dict contains token counts and estimated cost.
    """
    client = Anthropic(api_key=_get_api_key())

    # Build the user message
    user_parts = [f"Company Website URL: {company_url}"]
    if contact_name and contact_name.strip():
        user_parts.append(f"Contact Name: {contact_name.strip()}")
    else:
        user_parts.append("Contact Name: Not provided — skip individual contact research and focus on company research only.")
    if linkedin_url and linkedin_url.strip():
        user_parts.append(f"LinkedIn Profile URL (for reference): {linkedin_url.strip()}")

    user_message = "\n".join(user_parts) + "\n\nPlease research this prospect and return the JSON intelligence report."

    tools = [
        {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 10,
        }
    ]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=tools,
        messages=[
            {"role": "user", "content": user_message}
        ],
    )

    # Extract text content from the response
    raw_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            raw_text += block.text

    # Parse JSON robustly — try multiple strategies
    raw_text = raw_text.strip()

    def extract_json(text):
        # Strategy 1: direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: strip markdown code fences then parse
        cleaned = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Strategy 3: find the first { and last } and extract the JSON block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return None

    parsed = extract_json(raw_text)
    if parsed is not None:
        result = parsed
    else:
        result = {
            "_parse_error": True,
            "_raw_text": raw_text,
            "contact": {"name": contact_name or "", "title": "", "responsibilities": "", "interests": "", "recent_activity": "", "suggested_additional_contacts": []},
            "company": {"name": "", "website": company_url, "description": "", "industry": "", "recent_news": [], "goals_and_growth_areas": "", "challenges": "", "stay_in_touch": ""},
            "conversation_starters": {"anticipated_pain_points": [], "suggested_questions": []},
            "opportunity_map": [],
        }

    # Calculate usage and cost
    input_tokens = response.usage.input_tokens if response.usage else 0
    output_tokens = response.usage.output_tokens if response.usage else 0

    input_cost = (input_tokens / 1_000_000) * 0.80
    output_cost = (output_tokens / 1_000_000) * 4.00
    search_cost = 0.08  # 8 searches avg at $10/1000

    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": round(input_cost + output_cost + search_cost, 4),
    }

    return result, usage
