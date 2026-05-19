"""
SkillClassifier — routes messages to agents by required skill.

When the caller knows (or can infer) that a task requires a specific skill,
this classifier filters ``available_agents`` to those possessing the skill and
either returns the sole match immediately or uses a fallback LLM classifier to
disambiguate among multiple capable agents.

Usage::

    from moya.classifiers.skill_classifier import SkillClassifier

    # Route to whichever agent has the "web_search" skill
    classifier = SkillClassifier(required_skill="web_search",
                                  default_agent="general_agent")
    orchestrator = MultiAgentOrchestrator(registry, classifier)

    # Dynamic: infer required skill from the message
    classifier = SkillClassifier(skill_extractor=my_extractor,
                                  default_agent="general_agent")
"""

from typing import Callable, List, Optional

from moya.agents.agent_info import AgentInfo
from moya.classifiers.classifier import Classifier


class SkillClassifier(Classifier):
    """
    Classifier that selects agents by skill capability.

    Resolution order:
    1. Determine required skill from ``required_skill`` or ``skill_extractor``.
    2. Filter ``available_agents`` to those whose ``skills`` list contains it.
    3. If exactly one candidate → return it immediately.
    4. If multiple candidates → delegate to ``fallback_classifier`` (if set),
       passing only the filtered candidates.
    5. If no candidates → fall back to ``default_agent``.
    6. If no skill could be determined → fall back to ``default_agent``.
    """

    def __init__(
        self,
        required_skill: Optional[str] = None,
        skill_extractor: Optional[Callable[[str], Optional[str]]] = None,
        fallback_classifier: Optional[Classifier] = None,
        default_agent: Optional[str] = None,
    ) -> None:
        """
        Args:
            required_skill:     Static skill name to route by.  Takes priority
                                over ``skill_extractor``.
            skill_extractor:    ``(message: str) -> Optional[str]`` — called when
                                ``required_skill`` is not set. Returns a skill name
                                or ``None`` to skip skill-based routing.
            fallback_classifier: Used to break ties when multiple agents share the
                                 required skill.  Receives only the matching subset.
            default_agent:      Returned when no skill match is found.
        """
        if required_skill is None and skill_extractor is None:
            raise ValueError(
                "SkillClassifier requires either 'required_skill' or 'skill_extractor'."
            )
        self._required_skill = required_skill
        self._skill_extractor = skill_extractor
        self._fallback = fallback_classifier
        self._default = default_agent

    def classify(
        self,
        message: str,
        thread_id: Optional[str] = None,
        available_agents: Optional[List[AgentInfo]] = None,
    ) -> Optional[str]:
        if not available_agents:
            return self._default

        skill = self._required_skill
        if skill is None and self._skill_extractor:
            skill = self._skill_extractor(message)

        if not skill:
            return self._default

        candidates = [a for a in available_agents if skill in (a.skills or [])]

        if not candidates:
            return self._default

        if len(candidates) == 1:
            return candidates[0].name

        # Multiple candidates — try fallback classifier with the narrowed list
        if self._fallback:
            return self._fallback.classify(
                message=message,
                thread_id=thread_id,
                available_agents=candidates,
            )

        # No fallback — return the first candidate alphabetically for determinism
        return sorted(candidates, key=lambda a: a.name)[0].name
