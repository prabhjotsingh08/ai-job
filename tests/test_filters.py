"""AI-Engineer filter logic: role-in-title + topic-in-body, seniority + YOE exclusion."""
from jobbot.config import Config
from jobbot.filters import _exceeds_years, is_remote, matches
from jobbot.job import Job


def _cfg(**over):
    data = {
        "keywords": ["ai engineer", "machine learning engineer", "ml engineer",
                     "llm engineer", "ai developer"],
        "topics": ["rag", "llm", "llms", "ai agent", "ai agents", "agentic", "agent", "agents"],
        "exclude": ["senior", "sr", "staff", "principal", "lead", "head of",
                    "manager", "director", "vp"],
        "max_years": 5,
    }
    data.update(over)
    return Config(data)


def _job(title, desc="", source="RemoteOK"):
    return Job(title=title, company="x", url="u", source=source, description=desc)


def test_role_in_title_plus_topic_in_body_matches():
    assert matches(_job("AI Engineer", "You will build RAG pipelines."), _cfg())


def test_topic_in_title_matches():
    assert matches(_job("LLM Engineer", "great team"), _cfg())  # 'llm' topic in title


def test_role_without_topic_dropped():
    assert not matches(_job("AI Engineer", "general backend work"), _cfg())


def test_non_role_title_dropped():
    assert not matches(_job("Data Analyst", "we use LLM and RAG"), _cfg())


def test_senior_title_excluded():
    assert not matches(_job("Senior AI Engineer", "RAG, LLMs"), _cfg())
    assert not matches(_job("AI Engineer - Lead", "agentic AI"), _cfg())


def test_high_experience_excluded():
    assert not matches(_job("AI Engineer", "Require 7+ years of experience. RAG."), _cfg())


def test_junior_experience_kept():
    assert matches(_job("AI Engineer", "2-4 years experience with LLMs and agents."), _cfg())
    assert matches(_job("AI Developer", "Fresher friendly. Build agentic AI."), _cfg())


def test_exceeds_years_unit():
    assert _exceeds_years("minimum 8 years required", 5)
    assert _exceeds_years("7-10 years", 5)
    assert _exceeds_years("6+ years", 5)
    assert not _exceeds_years("5+ years", 5)
    assert not _exceeds_years("2 years", 5)
    assert not _exceeds_years("1-6 years", 5)   # lower bound 1 -> junior-friendly
    assert not _exceeds_years("no experience mentioned", 5)


def test_is_remote_remote_only_source():
    assert is_remote(_job("AI Engineer", source="Remotive"))


def test_is_remote_needs_term_for_generic_source():
    # Adzuna (body-match) with 'remote' in description passes; without, fails.
    assert is_remote(Job(title="AI Engineer", company="x", url="", source="Adzuna",
                         location="London", description="Fully remote role."))
    assert not is_remote(Job(title="AI Engineer", company="x", url="", source="Adzuna",
                            location="London", description="Onsite only."))
