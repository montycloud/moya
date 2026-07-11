"""
Pipeline example — multi-step agent workflows with MOYA Flows.

This example builds a simple research-and-write pipeline:
  1. A researcher agent gathers information on a topic.
  2. Two analyst agents work in parallel to find pros and cons.
  3. A writer agent synthesises the analyses into a final article.

It also demonstrates BranchStep (route based on content) and
LoopStep (refine until a condition is met).

Requires: OPENAI_API_KEY environment variable.
"""

import os

from moya.agents.openai_agent import OpenAIAgent, OpenAIAgentConfig
from moya.flows import AgentStep, BranchStep, FunctionStep, LoopStep, ParallelStep, Pipeline


# ---------------------------------------------------------------------------
# Helper: create a lightweight OpenAI agent
# ---------------------------------------------------------------------------

def make_agent(name: str, description: str, system_prompt: str) -> OpenAIAgent:
    config = OpenAIAgentConfig(
        agent_name=name,
        description=description,
        agent_type="OpenAIAgent",
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o-mini",
        system_prompt=system_prompt,
    )
    return OpenAIAgent(config)


# ---------------------------------------------------------------------------
# Example 1: Sequential pipeline
# ---------------------------------------------------------------------------

def example_sequential():
    print("\n" + "=" * 60)
    print("Example 1: Sequential pipeline")
    print("=" * 60)

    researcher = make_agent(
        "researcher",
        "Researches a topic and provides key facts.",
        "You are a research assistant. Summarise the key facts about the given topic in 3–5 bullet points.",
    )
    writer = make_agent(
        "writer",
        "Writes a short article from bullet points.",
        "You are a writer. Turn the given bullet points into a concise, engaging paragraph.",
    )

    pipeline = Pipeline(
        steps=[AgentStep(researcher), AgentStep(writer)],
        name="research_and_write",
    )

    result = pipeline.run(thread_id="demo-1", message="Renewable energy")
    print(result)


# ---------------------------------------------------------------------------
# Example 2: Parallel fan-out
# ---------------------------------------------------------------------------

def example_parallel():
    print("\n" + "=" * 60)
    print("Example 2: Parallel fan-out")
    print("=" * 60)

    pros_agent = make_agent(
        "pros_analyst",
        "Lists the advantages of a topic.",
        "You are an analyst. List 3 advantages of the given subject. Be concise.",
    )
    cons_agent = make_agent(
        "cons_analyst",
        "Lists the disadvantages of a topic.",
        "You are an analyst. List 3 disadvantages of the given subject. Be concise.",
    )
    synthesiser = make_agent(
        "synthesiser",
        "Synthesises pros and cons into a balanced conclusion.",
        "You are an editor. Given a list of pros and cons, write one balanced concluding paragraph.",
    )

    pipeline = Pipeline(
        steps=[
            ParallelStep(
                steps=[AgentStep(pros_agent, name="pros"), AgentStep(cons_agent, name="cons")],
                merge=lambda outputs: "PROS:\n" + outputs[0] + "\n\nCONS:\n" + outputs[1],
            ),
            AgentStep(synthesiser),
        ],
        name="balanced_analysis",
    )

    result = pipeline.run(thread_id="demo-2", message="Remote work")
    print(result)


# ---------------------------------------------------------------------------
# Example 3: BranchStep — route by topic
# ---------------------------------------------------------------------------

def example_branch():
    print("\n" + "=" * 60)
    print("Example 3: BranchStep routing")
    print("=" * 60)

    tech_agent = make_agent(
        "tech_expert",
        "Explains technical topics.",
        "You are a technology expert. Answer the question clearly and concisely.",
    )
    general_agent = make_agent(
        "general_expert",
        "Answers general knowledge questions.",
        "You are a knowledgeable assistant. Answer the question clearly and concisely.",
    )

    def detect_topic(ctx):
        keywords = ["python", "code", "algorithm", "software", "hardware", "api"]
        if any(kw in ctx.output.lower() for kw in keywords):
            return "tech"
        return "general"

    pipeline = Pipeline(
        steps=[
            BranchStep(
                condition=detect_topic,
                branches={
                    "tech": AgentStep(tech_agent),
                    "general": AgentStep(general_agent),
                },
            )
        ],
        name="topic_router",
    )

    for question in ["What is a Python generator?", "Who painted the Mona Lisa?"]:
        print(f"\nQ: {question}")
        result = pipeline.run(thread_id="demo-3", message=question)
        print(f"A: {result}")


# ---------------------------------------------------------------------------
# Example 4: LoopStep — iterative refinement
# ---------------------------------------------------------------------------

def example_loop():
    print("\n" + "=" * 60)
    print("Example 4: LoopStep — iterative refinement")
    print("=" * 60)

    refiner = make_agent(
        "refiner",
        "Refines text until it is under 50 words.",
        (
            "You are an editor. If the input text is longer than 50 words, "
            "shorten it while keeping the key message. "
            "If it is already 50 words or fewer, reply with the text unchanged "
            "followed by the word DONE on a new line."
        ),
    )

    pipeline = Pipeline(
        steps=[
            LoopStep(
                step=AgentStep(refiner),
                until=lambda ctx: "DONE" in ctx.output,
                max_iterations=5,
            ),
            # Strip the DONE marker before returning
            FunctionStep(lambda ctx: setattr(ctx, "output", ctx.output.replace("DONE", "").strip()) or ctx),
        ],
        name="shrink_to_50",
    )

    long_text = (
        "Artificial intelligence is rapidly transforming every industry on the planet, "
        "from healthcare and finance to education and transportation, creating unprecedented "
        "opportunities for innovation while also raising important ethical questions that "
        "society must carefully consider and address before these powerful systems become "
        "even more deeply embedded in our daily lives."
    )

    result = pipeline.run(thread_id="demo-4", message=long_text)
    print(result)


# ---------------------------------------------------------------------------
# Example 5: Nested pipelines
# ---------------------------------------------------------------------------

def example_nested():
    print("\n" + "=" * 60)
    print("Example 5: Nested pipelines")
    print("=" * 60)

    summariser = make_agent(
        "summariser", "Summarises text.", "Summarise the following in one sentence."
    )
    translator = make_agent(
        "translator",
        "Translates to Spanish.",
        "Translate the following text to Spanish. Return only the translation.",
    )
    formatter = make_agent(
        "formatter",
        "Formats text as a tweet.",
        "Rewrite the following as a tweet (under 280 characters, no hashtags).",
    )

    # Inner pipeline: summarise then translate
    inner = Pipeline([AgentStep(summariser), AgentStep(translator)], name="summarise_and_translate")

    # Outer pipeline: inner pipeline then format as tweet
    # Nested pipeline used as a step via run_ctx
    outer = Pipeline(
        steps=[
            FunctionStep(lambda ctx: inner.run_ctx(ctx)),
            AgentStep(formatter),
        ],
        name="translate_and_tweet",
    )

    text = (
        "The James Webb Space Telescope has provided astronomers with the deepest "
        "infrared images of the universe ever captured, revealing galaxies that formed "
        "less than a billion years after the Big Bang."
    )

    result = outer.run(thread_id="demo-5", message=text)
    print(result)


# ---------------------------------------------------------------------------
# Run all examples
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    example_sequential()
    example_parallel()
    example_branch()
    example_loop()
    example_nested()
