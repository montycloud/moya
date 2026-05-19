"""
moya.flows — declarative multi-step agent pipelines.

Quick start::

    from moya.flows import Pipeline, AgentStep, ParallelStep

    pipeline = Pipeline([
        AgentStep(researcher),
        ParallelStep([AgentStep(analyst_a), AgentStep(analyst_b)]),
        AgentStep(writer),
    ])

    result = pipeline.run(thread_id="t1", message="Explain quantum computing")
"""

from moya.flows.pipeline import FlowContext, Pipeline
from moya.flows.steps import AgentStep, BranchStep, FunctionStep, LoopStep, ParallelStep

__all__ = [
    "FlowContext",
    "Pipeline",
    "AgentStep",
    "FunctionStep",
    "ParallelStep",
    "BranchStep",
    "LoopStep",
]
