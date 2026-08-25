import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.engines.hybrid import HybridEngine
from src.engines.rule_engine import RuleEngine
from src.engines.llm_engine import LLMEngine
from src.knowledge.loader import load_programs, load_students
from src.models.student import Student, Skill, SkillLevel, Constraint


@pytest.fixture
def programs():
    return load_programs()


@pytest.fixture
def students():
    return load_students()


@pytest.fixture
def hybrid_engine():
    return HybridEngine(alpha=0.5, beta=0.5)


class TestHybridEngine:
    def test_returns_hybrid_result(self, hybrid_engine, programs, students):
        student = students[0]
        result = hybrid_engine.recommend(student, programs)
        assert result.recommendations is not None
        assert result.uncertainty is not None
        assert result.rule_result is not None
        assert result.llm_result is not None

    def test_top_n_limit(self, hybrid_engine, programs, students):
        student = students[0]
        result = hybrid_engine.recommend(student, programs, top_n=2)
        assert len(result.recommendations) <= 2

    def test_scores_between_0_and_1(self, hybrid_engine, programs, students):
        student = students[0]
        result = hybrid_engine.recommend(student, programs)
        for rec in result.recommendations:
            assert 0 <= rec.final_score <= 1
            assert 0 <= rec.confidence <= 1

    def test_empty_student_gets_low_confidence(self, hybrid_engine, programs):
        student = Student(
            id="EMPTY", name="Vide", current_level="",
            skills=[], interests=[], constraints=Constraint(),
        )
        result = hybrid_engine.recommend(student, programs)
        assert result.overall_confidence < 0.5


class TestAllStudents:
    @pytest.mark.parametrize("student_idx", list(range(10)))
    def test_all_sample_students(self, hybrid_engine, programs, students, student_idx):
        if student_idx >= len(students):
            pytest.skip("Not enough sample students")
        student = students[student_idx]
        result = hybrid_engine.recommend(student, programs)
        assert len(result.recommendations) >= 0
        assert result.overall_confidence >= 0


class TestEdgeCases:
    def test_no_budget(self, hybrid_engine, programs):
        student = Student(
            id="E1", name="No Budget", current_level="bac",
            skills=[], interests=["informatique"],
            constraints=Constraint(max_budget=None),
        )
        result = hybrid_engine.recommend(student, programs)
        assert result.recommendations is not None

    def test_zero_budget(self, hybrid_engine, programs):
        student = Student(
            id="E2", name="Zero Budget", current_level="bac",
            skills=[], interests=["informatique"],
            constraints=Constraint(max_budget=0),
        )
        result = hybrid_engine.recommend(student, programs)
        assert result.recommendations is not None

    def test_very_short_duration(self, hybrid_engine, programs):
        student = Student(
            id="E3", name="Short", current_level="bac+3",
            skills=[], interests=["informatique"],
            constraints=Constraint(max_duration_months=1),
        )
        result = hybrid_engine.recommend(student, programs)
        assert result.recommendations is not None

    def test_contradictory_profile(self, hybrid_engine, programs):
        student = Student(
            id="E4", name="Contradictory", current_level="bac+5",
            skills=[
                Skill(domain="informatique", level=SkillLevel.EXPERT, grade=5),
            ],
            interests=["informatique", "arts", "philosophie"],
            constraints=Constraint(max_budget=30000),
            free_text="Je ne sais pas ce que je veux.",
        )
        result = hybrid_engine.recommend(student, programs)
        assert len(result.contradictions_detected) > 0 or result.uncertainty.warnings
