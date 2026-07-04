"""
Trip Planning Pipeline for the MOYA Trip Planner demo.

Exercises every MOYA flow primitive:
  LoopStep     — destination overview refined until "OVERVIEW COMPLETE"
  ParallelStep — itinerary + budget generated concurrently
  BranchStep   — packing list branches on trip style
  FunctionStep — save intermediate results & final synthesis

Pipeline structure::

    Step 1  LoopStep(AgentStep(destination_expert))
               Repeats up to 3 times until output contains "OVERVIEW COMPLETE"
    Step 2  FunctionStep  — saves destination overview to ctx.metadata
    Step 3  ParallelStep
               ├── AgentStep(itinerary_builder)
               └── AgentStep(budget_advisor)
    Step 4  FunctionStep  — saves parallel outputs to ctx.metadata
    Step 5  BranchStep    — routes on ctx.metadata["style"]
               ├── "cultural"    → AgentStep(packing_advisor)
               ├── "adventure"   → AgentStep(packing_advisor)
               └── "relaxation"  → AgentStep(packing_advisor)
    Step 6  FunctionStep  — saves packing list to ctx.metadata
    Step 7  FunctionStep  — delegates final synthesis to coordinator

Entry point::

    result = run_pipeline(trip_request)

where ``trip_request`` is a dict with keys:
    city, country, days, month, budget_usd, style, passport
"""

from moya.flows.pipeline import FlowContext, Pipeline
from moya.flows.steps import (
    AgentStep,
    BranchStep,
    FunctionStep,
    LoopStep,
    ParallelStep,
)


def build_pipeline(agent_registry, delegation_manager):
    """
    Build and return the trip-planning Pipeline.

    Args:
        agent_registry:     The AgentRegistry from agents.build_registry().
        delegation_manager: The DelegationManager from agents.build_registry().

    Returns:
        A configured Pipeline instance.
    """
    dest_expert = agent_registry.get_agent("destination_expert")
    itinerary = agent_registry.get_agent("itinerary_builder")
    budget = agent_registry.get_agent("budget_advisor")
    packing = agent_registry.get_agent("packing_advisor")

    # ------------------------------------------------------------------
    # Step 1 — destination overview (loop until quality gate passes)
    # ------------------------------------------------------------------
    destination_step = LoopStep(
        step=AgentStep(dest_expert, name="destination_expert"),
        until=lambda ctx: "OVERVIEW COMPLETE" in ctx.output,
        max_iterations=3,
        name="destination_loop",
    )

    # ------------------------------------------------------------------
    # Step 2 — save overview to metadata
    # ------------------------------------------------------------------
    def save_overview(ctx: FlowContext) -> FlowContext:
        ctx.metadata["destination_overview"] = ctx.output
        return ctx

    # ------------------------------------------------------------------
    # Step 3 — itinerary + budget in parallel
    # ------------------------------------------------------------------
    def _itinerary_prompt(ctx: FlowContext) -> FlowContext:
        meta = ctx.metadata
        ctx.output = (
            f"Create a detailed {meta['days']}-day itinerary for a "
            f"{meta['style']} trip to {meta['city']}, {meta['country']} "
            f"in {meta['month']}. Include morning, afternoon, and evening "
            f"activities for each day. Total budget: ${meta['budget_usd']} USD."
        )
        return ctx

    def _budget_prompt(ctx: FlowContext) -> FlowContext:
        meta = ctx.metadata
        ctx.output = (
            f"Use the trip cost tool to estimate the budget for a "
            f"{meta['days']}-day {meta['style']} trip to {meta['city']} "
            f"for a traveller with a US passport. Budget cap: ${meta['budget_usd']} USD. "
            f"Then provide money-saving tips."
        )
        return ctx

    itinerary_branch = Pipeline(steps=[
        FunctionStep(_itinerary_prompt, name="itinerary_prompt"),
        AgentStep(itinerary, name="itinerary_builder"),
    ])

    budget_branch = Pipeline(steps=[
        FunctionStep(_budget_prompt, name="budget_prompt"),
        AgentStep(budget, name="budget_advisor"),
    ])

    parallel_step = ParallelStep(
        steps=[
            FunctionStep(lambda ctx: itinerary_branch.run_ctx(ctx), name="itinerary_branch"),
            FunctionStep(lambda ctx: budget_branch.run_ctx(ctx), name="budget_branch"),
        ],
        name="itinerary_and_budget",
        merge=lambda outputs: "\n\n---PARALLEL_SEPARATOR---\n\n".join(outputs),
    )

    # ------------------------------------------------------------------
    # Step 4 — split parallel output and save to metadata
    # ------------------------------------------------------------------
    def save_parallel(ctx: FlowContext) -> FlowContext:
        parts = ctx.output.split("\n\n---PARALLEL_SEPARATOR---\n\n", 1)
        ctx.metadata["itinerary"] = parts[0] if len(parts) > 0 else ctx.output
        ctx.metadata["budget"] = parts[1] if len(parts) > 1 else ""
        return ctx

    # ------------------------------------------------------------------
    # Step 5 — packing list branch
    # ------------------------------------------------------------------
    def _packing_prompt(style: str):
        def _set(ctx: FlowContext) -> FlowContext:
            meta = ctx.metadata
            ctx.output = (
                f"Create a {style}-focused packing list for a {meta['days']}-day trip "
                f"to {meta['city']}, {meta['country']} in {meta['month']}. "
                f"Tailor recommendations to {style} activities."
            )
            return ctx
        return _set

    packing_branch_steps = {
        style: Pipeline(steps=[
            FunctionStep(_packing_prompt(style), name=f"packing_prompt_{style}"),
            AgentStep(packing, name="packing_advisor"),
        ])
        for style in ("cultural", "adventure", "relaxation")
    }

    packing_step = BranchStep(
        condition=lambda ctx: ctx.metadata.get("style", "cultural"),
        branches={
            style: FunctionStep(
                lambda ctx, s=style: packing_branch_steps[s].run_ctx(ctx),
                name=f"packing_{style}",
            )
            for style in ("cultural", "adventure", "relaxation")
        },
        name="packing_branch",
    )

    # ------------------------------------------------------------------
    # Step 6 — save packing list
    # ------------------------------------------------------------------
    def save_packing(ctx: FlowContext) -> FlowContext:
        ctx.metadata["packing_list"] = ctx.output
        return ctx

    # ------------------------------------------------------------------
    # Step 7 — coordinator synthesises everything
    # ------------------------------------------------------------------
    def synthesise(ctx: FlowContext) -> FlowContext:
        meta = ctx.metadata
        synthesis_task = (
            f"Assemble a complete, polished travel plan for a "
            f"{meta['days']}-day {meta['style']} trip to {meta['city']}, "
            f"{meta['country']} in {meta['month']} with a ${meta['budget_usd']} budget.\n\n"
            f"Use the following sections exactly:\n\n"
            f"=== DESTINATION OVERVIEW ===\n{meta.get('destination_overview', '')}\n\n"
            f"=== DAY-BY-DAY ITINERARY ===\n{meta.get('itinerary', '')}\n\n"
            f"=== BUDGET BREAKDOWN ===\n{meta.get('budget', '')}\n\n"
            f"=== PACKING LIST ===\n{meta.get('packing_list', '')}\n\n"
            f"=== TRAVEL TIPS ===\n"
            f"Include visa requirements for a {meta.get('passport', 'US')} passport holder, "
            f"safety notes, and eco-friendly travel suggestions.\n\n"
            f"Present this as one cohesive, well-formatted travel document."
        )
        ctx.output = delegation_manager.delegate(
            task=synthesis_task,
            agent_name="coordinator",
            thread_id=ctx.thread_id,
        )
        return ctx

    # ------------------------------------------------------------------
    # Assemble the pipeline
    # ------------------------------------------------------------------
    pipeline = Pipeline(
        steps=[
            destination_step,
            FunctionStep(save_overview, name="save_overview"),
            parallel_step,
            FunctionStep(save_parallel, name="save_parallel_outputs"),
            packing_step,
            FunctionStep(save_packing, name="save_packing"),
            FunctionStep(synthesise, name="synthesis"),
        ]
    )
    return pipeline


def run_pipeline(trip_request: dict, agent_registry=None, delegation_manager=None) -> str:
    """
    Run the trip-planning pipeline for a given trip request.

    Args:
        trip_request: Dict with keys: city, country, days, month,
                      budget_usd, style, passport.
        agent_registry:     Pre-built AgentRegistry (built externally to avoid
                            re-launching the MCP server on every call).
        delegation_manager: Pre-built DelegationManager.

    Returns:
        The assembled travel plan as a string.
    """
    if agent_registry is None or delegation_manager is None:
        from trip_planner.agents import build_registry
        agent_registry, _, _, delegation_manager, _ = build_registry()

    pipeline = build_pipeline(agent_registry, delegation_manager)

    initial_message = (
        f"I want to plan a {trip_request['days']}-day trip to "
        f"{trip_request['city']}, {trip_request['country']} in "
        f"{trip_request['month']}. My budget is ${trip_request['budget_usd']} USD "
        f"and I prefer {trip_request['style']} experiences. "
        f"I have a {trip_request['passport']} passport."
    )

    return pipeline.run(
        thread_id="trip_planning",
        message=initial_message,
        **trip_request,
    )
