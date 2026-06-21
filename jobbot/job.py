"""Common job representation shared by every source."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field


@dataclass
class Job:
    title: str
    company: str
    url: str
    source: str
    location: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""

    @property
    def uid(self) -> str:
        """Stable id for dedup, based on (title, company) not URL.

        Studios post the same role once per location with distinct URLs; keying on
        title+company collapses those into a single alert. Distinct titles (e.g.
        "...- Paper.io 2" vs "...- Growth") stay separate. Pruning lets a long-gone
        role re-alert later if reposted.
        """
        norm = " ".join(f"{self.title} {self.company}".lower().split())
        return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:16]
