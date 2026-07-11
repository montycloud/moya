"""
Skill attachment helpers.

``attach_skills()`` is the single place where skills are applied to an agent:
  1. Resolve transitive dependencies (if a SkillRegistry is provided).
  2. Deduplicate (skip already-attached skills by name).
  3. Append each skill's prompt snippet to ``agent.system_prompt``.
  4. Register each skill's tools via ``agent.tool_registry``.

Usage::

    from moya.skills.attachment import attach_skills

    # Simple — no dep resolution
    attach_skills(agent, [web_search_skill])

    # With dep resolution
    attach_skills(agent, [compound_skill], registry=skill_registry)
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from moya.agents.agent import Agent
    from moya.skills.skill import Skill
    from moya.skills.registry import SkillRegistry


def attach_skills(
    agent: "Agent",
    skills: "List[Skill]",
    registry: "Optional[SkillRegistry]" = None,
) -> "List[Skill]":
    """
    Attach *skills* to *agent*, resolving dependencies when *registry* is given.

    Args:
        agent:    The agent to attach skills to.
        skills:   Skills to attach (may have transitive deps in the registry).
        registry: Optional SkillRegistry for dependency lookup and resolution.

    Returns:
        The ordered list of all attached skills (deps first, then requested).
        Skills the agent already has (by name) are skipped silently.
    """
    already = {s.name for s in getattr(agent, "skills", [])}
    to_attach = _resolve_all(skills, registry, already)

    for skill in to_attach:
        if skill.prompt_snippet:
            agent.system_prompt += f"\n\n{skill.prompt_snippet}"
        if skill.tools_factory and agent.tool_registry:
            for tool in skill.tools_factory():
                agent.tool_registry.register_tool(tool)
        agent.skills.append(skill)
        already.add(skill.name)

    return to_attach


def _resolve_all(
    skills: "List[Skill]",
    registry: "Optional[SkillRegistry]",
    already_attached: set,
) -> "List[Skill]":
    """Return ordered list of skills to attach (deps first), deduped."""
    if registry is None:
        return [s for s in skills if s.name not in already_attached]

    ordered: List = []
    seen = set(already_attached)

    def _visit(skill, chain):
        if skill.name in chain:
            cycle = " → ".join(chain + [skill.name])
            raise ValueError(f"Circular skill dependency: {cycle}")
        if skill.name in seen:
            return
        for dep_name in skill.dependencies:
            dep = registry.get(dep_name)
            if dep is None:
                from moya.skills.registry import SkillNotFoundError
                raise SkillNotFoundError(
                    f"Skill '{skill.name}' depends on '{dep_name}' "
                    "which is not registered."
                )
            _visit(dep, chain + [skill.name])
        if skill.name not in seen:
            seen.add(skill.name)
            ordered.append(skill)

    for skill in skills:
        _visit(skill, [])

    return ordered
