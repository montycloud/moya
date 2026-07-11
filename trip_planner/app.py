"""
Streamlit UI for the MOYA Trip Planner demo.

Three tabs:
  Plan Trip       — Run the full pipeline and display the travel plan.
  Ask Questions   — Chat with the coordinator agent via LLM-driven delegation.
  Framework View  — Explore the MOYA registry: agents, skills, tools.

Usage::

    streamlit run trip_planner/app.py

Prerequisites:
    export OPENAI_API_KEY=sk-...
    pip install openai mcp streamlit
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MOYA Trip Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Cached resource — builds registries once per session
# The cache key includes the api_key so a new key triggers a fresh build.
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner="Starting MCP server and initialising agents...")
def get_registries(api_key: str):
    os.environ["OPENAI_API_KEY"] = api_key
    from trip_planner.agents import build_registry
    return build_registry()


# ---------------------------------------------------------------------------
# Main layout
# ---------------------------------------------------------------------------
st.title("✈️ MOYA Trip Planner")
st.caption(
    "A full-stack demo of the MOYA multi-agent framework — "
    "pipelines, MCP tools, skills, delegation, and registry discovery."
)

# ---------------------------------------------------------------------------
# Sidebar — trip configuration form
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Trip Configuration")

    # API key — prefer env var, fall back to sidebar input
    _env_key = os.environ.get("OPENAI_API_KEY", "")
    if _env_key:
        openai_api_key = _env_key
        st.success("OpenAI API key loaded from environment.", icon="🔑")
    else:
        openai_api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            help="Paste your key here if OPENAI_API_KEY is not set in the environment.",
        )
        if not openai_api_key:
            st.warning("Enter your OpenAI API key to continue.")

    st.divider()

    city = st.text_input("Destination City", value="Tokyo")
    country = st.text_input("Country", value="Japan")
    month = st.selectbox(
        "Travel Month",
        ["January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"],
        index=9,
    )
    days = st.slider("Number of Days", min_value=3, max_value=21, value=7)
    budget = st.number_input("Total Budget (USD)", min_value=500, max_value=50000,
                              value=4000, step=500)
    style = st.selectbox("Trip Style", ["cultural", "adventure", "relaxation"], index=0)
    passport = st.selectbox("Passport Country", ["US", "UK", "Australia", "Canada",
                                                   "Germany", "France", "Other"], index=0)

    st.divider()
    st.caption("Powered by MOYA · OpenAI · MCP")

trip_request = {
    "city": city,
    "country": country,
    "days": days,
    "month": month.lower(),
    "budget_usd": budget,
    "style": style,
    "passport": passport,
}

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_plan, tab_chat, tab_framework = st.tabs(["Plan Trip", "Ask Questions", "Framework View"])

# ===========================================================================
# Tab 1 — Plan Trip
# ===========================================================================
with tab_plan:
    st.subheader("Generate Your Travel Plan")
    st.write(
        f"Click **Plan My Trip** to generate a complete {days}-day travel plan for "
        f"{city.title()}, {country.title()} in {month}."
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        plan_button = st.button("Plan My Trip", type="primary", use_container_width=True)

    if plan_button and not openai_api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif plan_button:
        agent_registry, skill_registry, tool_registry, delegation_manager, _ = get_registries(openai_api_key)

        progress_placeholder = st.empty()
        result_placeholder = st.empty()

        steps_status = {
            "Researching destination...": False,
            "Building itinerary & budget (parallel)...": False,
            "Creating packing list...": False,
            "Synthesising final plan...": False,
        }

        progress_bar = st.progress(0)
        status_container = st.empty()

        with st.spinner("Running trip planning pipeline..."):
            from trip_planner.pipeline import build_pipeline

            pipeline = build_pipeline(agent_registry, delegation_manager)

            initial_message = (
                f"I want to plan a {trip_request['days']}-day trip to "
                f"{trip_request['city']}, {trip_request['country']} in "
                f"{trip_request['month']}. My budget is ${trip_request['budget_usd']} USD "
                f"and I prefer {trip_request['style']} experiences. "
                f"I have a {trip_request['passport']} passport."
            )

            result = pipeline.run(
                thread_id="streamlit_plan",
                message=initial_message,
                **trip_request,
            )

        progress_bar.progress(100)
        status_container.success("Travel plan complete!")

        st.divider()
        st.subheader(f"Your {days}-Day {style.title()} Trip to {city.title()}")

        # Display plan in expandable sections
        sections = [
            ("DESTINATION OVERVIEW", "destination_overview"),
            ("DAY-BY-DAY ITINERARY", "itinerary"),
            ("BUDGET BREAKDOWN", "budget"),
            ("PACKING LIST", "packing_list"),
            ("TRAVEL TIPS", "travel_tips"),
        ]

        # Try to parse sections from result
        result_text = result
        st.markdown(result_text)

    elif "last_plan" in st.session_state:
        st.markdown(st.session_state["last_plan"])

# ===========================================================================
# Tab 2 — Ask Questions (LLM-driven delegation)
# ===========================================================================
with tab_chat:
    st.subheader("Ask the Trip Coordinator")
    st.write(
        "Ask follow-up questions about your trip. The coordinator agent will "
        "delegate to specialist agents as needed."
    )

    # Initialise chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display existing messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Suggested questions
    if not st.session_state.chat_history:
        st.write("**Try these questions:**")
        suggestions = [
            f"What should I be careful about regarding safety in {city}?",
            f"Can you suggest eco-friendly options for my {city} trip?",
            f"Give me a revised budget if I want to add a day trip nearby.",
        ]
        for suggestion in suggestions:
            if st.button(suggestion, key=f"suggest_{suggestion[:20]}"):
                st.session_state.pending_question = suggestion
                st.rerun()

    # Handle pending suggestion
    if "pending_question" in st.session_state:
        user_input = st.session_state.pop("pending_question")
    else:
        user_input = st.chat_input("Ask about your trip...")

    if user_input and not openai_api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
    elif user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Coordinator is delegating to specialists..."):
                agent_registry, _, _, _, _ = get_registries(openai_api_key)
                coordinator = agent_registry.get_agent("coordinator")
                response = coordinator.handle_message(user_input, thread_id="streamlit_chat")
            st.markdown(response)

        st.session_state.chat_history.append({"role": "assistant", "content": response})

    if st.session_state.chat_history:
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

# ===========================================================================
# Tab 3 — Framework View (registry discovery, no LLM calls)
# ===========================================================================
with tab_framework:
    st.subheader("MOYA Framework View")
    st.write("Explore the live MOYA registries — no LLM calls required.")

    if not openai_api_key:
        st.info("Enter your OpenAI API key in the sidebar to load the registries.")
        st.stop()

    agent_registry, skill_registry, tool_registry, _, _ = get_registries(openai_api_key)

    # ---- Agents table ----
    st.markdown("#### Registered Agents")
    agent_infos = agent_registry.list_agents()
    if agent_infos:
        rows = []
        for info in agent_infos:
            rows.append({
                "Name": info.name,
                "Skills": ", ".join(info.skills) if info.skills else "—",
                "Tags": ", ".join(info.tags) if info.tags else "—",
                "Description": info.description[:80] + "..." if len(info.description) > 80 else info.description,
            })
        st.dataframe(rows, use_container_width=True)
    else:
        st.info("No agents registered.")

    # ---- Skill discovery ----
    col_skills, col_tags = st.columns(2)

    with col_skills:
        st.markdown("#### All Skills")
        for skill in skill_registry.list_skills():
            with st.expander(f"{skill.name} v{skill.version}"):
                st.write(f"**Description:** {skill.description}")
                st.write(f"**Tags:** {', '.join(skill.tags)}")
                has_tools = skill.tools_factory is not None
                st.write(f"**Has tools:** {'Yes' if has_tools else 'No (prompt-only)'}")
                if skill.prompt_snippet:
                    st.code(skill.prompt_snippet, language="markdown")

    with col_tags:
        st.markdown("#### Discovery Queries")

        st.write("**Agents with `travel_safety` skill:**")
        safety_agents = agent_registry.find_agents_with_skill("travel_safety")
        for a in safety_agents:
            st.write(f"  • {a.agent_name}")

        st.write("**Agents tagged `specialist`:**")
        specialists = agent_registry.find_agents_by_tag("specialist")
        for a in specialists:
            st.write(f"  • {a.agent_name}")

        st.write("**Eco-related skills:**")
        eco_skills = skill_registry.find_by_tag("eco")
        for s in eco_skills:
            st.write(f"  • {s.name}")

    # ---- Tool catalog ----
    st.markdown("#### Tool Catalog (MCP + Local)")
    catalog = tool_registry.get_catalog()
    if catalog:
        tool_rows = []
        for t in catalog:
            params = list(t["parameters"].keys())
            tool_rows.append({
                "Tool Name": t["name"],
                "Parameters": ", ".join(params) if params else "—",
                "Description": (t.get("description") or "")[:80],
            })
        st.dataframe(tool_rows, use_container_width=True)
    else:
        st.info("No tools in registry.")

    # ---- MCP info ----
    st.markdown("#### MCP Server")
    mcp_tools = [t for t in catalog if t["name"].startswith("trip_tools__")]
    st.success(
        f"MCP subprocess running — {len(mcp_tools)} tool(s) discovered via stdio transport: "
        + ", ".join(t["name"] for t in mcp_tools)
    )
