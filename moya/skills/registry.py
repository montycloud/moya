"""
SkillRegistry — versioned catalog for discovering and retrieving Skills.

Supports multiple versions of the same skill name.  Agents may pin to a
specific version or request the latest.  Registering the same name+version
twice with different content raises ``SkillVersionConflictError``.

Usage::

    registry = SkillRegistry()
    registry.register(web_search_v1)
    registry.register(web_search_v2)

    latest = registry.get("web_search")                   # newest version
    pinned = registry.get("web_search", version="1.0.0")  # exact version

    # Full dep tree for "summarise_search" (which depends on "web_search")
    ordered = registry.resolve_dependencies("summarise_search")
    # → [web_search, summarise_search]  (dependencies first)
"""

from typing import Dict, List, Optional

from moya.skills.skill import Skill


class SkillVersionConflictError(Exception):
    """Raised when the same name+version is registered with different content."""


class SkillNotFoundError(Exception):
    """Raised when a required skill or dependency cannot be found."""


def _parse_version(v: str):
    """Return a tuple for semantic-version ordering."""
    try:
        parts = [int(x) for x in v.strip().split(".")]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts)
    except ValueError:
        return (0, 0, 0)


class SkillRegistry:
    """
    Versioned catalog of available Skills.

    Internal storage: ``{name: {version_str: Skill}}``.
    The *latest* version is the one with the highest semantic version number.
    """

    def __init__(self) -> None:
        # name → {version → Skill}
        self._skills: Dict[str, Dict[str, Skill]] = {}

    # ── Registration ──────────────────────────────────────────────────────────

    def register(self, skill: Skill, overwrite: bool = False) -> None:
        """
        Add *skill* to the catalog.

        Args:
            skill:     The Skill to register.
            overwrite: When ``True``, silently replace an existing same-version
                       entry.  When ``False`` (default), raise
                       ``SkillVersionConflictError`` if the same name+version
                       already exists with different content.

        Raises:
            SkillVersionConflictError: if ``overwrite=False`` and the same
                name+version is already registered.
        """
        versions = self._skills.setdefault(skill.name, {})
        existing = versions.get(skill.version)
        if existing is not None and not overwrite:
            if existing is not skill:
                raise SkillVersionConflictError(
                    f"Skill '{skill.name}' version '{skill.version}' is already "
                    "registered. Use overwrite=True to replace it or bump the version."
                )
        versions[skill.version] = skill

    # ── Retrieval ─────────────────────────────────────────────────────────────

    def get(self, name: str, version: Optional[str] = None) -> Optional[Skill]:
        """
        Return a skill by name and optional version.

        Args:
            name:    Skill name.
            version: Exact version string.  If omitted, returns the latest.

        Returns:
            The matching Skill, or ``None`` if not found.
        """
        versions = self._skills.get(name)
        if not versions:
            return None
        if version is not None:
            return versions.get(version)
        # latest = highest semantic version
        latest_key = max(versions, key=_parse_version)
        return versions[latest_key]

    def list_versions(self, name: str) -> List[str]:
        """Return all registered version strings for *name*, sorted newest-first."""
        versions = self._skills.get(name, {})
        return sorted(versions.keys(), key=_parse_version, reverse=True)

    def list_skills(self) -> List[Skill]:
        """Return the latest version of every registered skill."""
        result = []
        for name in self._skills:
            skill = self.get(name)
            if skill:
                result.append(skill)
        return result

    def find_by_tag(self, tag: str) -> List[Skill]:
        """Return latest versions of skills that include the given tag."""
        return [s for s in self.list_skills() if tag in s.tags]

    def find_by_name_fragment(self, fragment: str) -> List[Skill]:
        """Return skills whose name or description contains *fragment* (case-insensitive)."""
        frag = fragment.lower()
        return [
            s for s in self.list_skills()
            if frag in s.name.lower() or frag in s.description.lower()
        ]

    # ── Dependency resolution ─────────────────────────────────────────────────

    def resolve_dependencies(
        self,
        skill_name: str,
        version: Optional[str] = None,
    ) -> List[Skill]:
        """
        Return an ordered list of all skills needed to attach *skill_name*,
        including transitive dependencies.  Dependencies always come before
        the skills that depend on them (topological order).

        Args:
            skill_name: Root skill to resolve.
            version:    Pin to a specific version; ``None`` uses latest.

        Returns:
            Ordered list of Skills (deps first, then the root skill).

        Raises:
            SkillNotFoundError: if *skill_name* or any dependency is missing.
            ValueError:         if a circular dependency is detected.
        """
        root = self.get(skill_name, version)
        if root is None:
            raise SkillNotFoundError(
                f"Skill '{skill_name}'"
                + (f" version '{version}'" if version else "")
                + " is not registered."
            )
        ordered: List[Skill] = []
        seen: set = set()

        def _visit(skill: Skill, chain: List[str]) -> None:
            if skill.name in chain:
                cycle = " → ".join(chain + [skill.name])
                raise ValueError(f"Circular skill dependency detected: {cycle}")
            if skill.name in seen:
                return
            for dep_name in skill.dependencies:
                dep = self.get(dep_name)
                if dep is None:
                    raise SkillNotFoundError(
                        f"Skill '{skill.name}' depends on '{dep_name}' "
                        "which is not registered."
                    )
                _visit(dep, chain + [skill.name])
            seen.add(skill.name)
            ordered.append(skill)

        _visit(root, [])
        return ordered
