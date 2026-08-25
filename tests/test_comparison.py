import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import json
import pytest
from src.engines.hybrid import HybridEngine
from src.engines.rule_engine import RuleEngine
from src.engines.llm_engine import LLMEngine
from src.utils.uncertainty import UncertaintyAnalyzer
from src.knowledge.loader import load_programs, load_students


@pytest.fixture
def programs():
    return load_programs()


@pytest.fixture
def students():
    return load_students()


class TestComparison10Cases:
    """
    Comparaison des 2 approches sur 10 cas de test dont 3 cas limites.
    Mesure: exactitude (éligibilité cohérente), temps, cohérence inter-moteurs.
    """

    EXPECTED_ELIGIBLE = {
        "S01": ["P01", "P09"],
        "S02": ["P12"],
        "S03": ["P10", "P08"],
        "S04": [],
        "S05": ["P10", "P08", "P04"],
        "S06": [],
        "S07": ["P09", "P02"],
        "S08": ["P08", "P04"],
        "S09": ["P10", "P08"],
        "S10": ["P08"],
    }

    def test_rule_engine_consistency(self, programs, students):
        engine = RuleEngine()
        results = {}
        for student in students:
            start = time.time()
            scored = engine.evaluate(student, programs)
            elapsed = time.time() - start
            eligible_ids = [sp.program.id for sp in scored if sp.eligible]
            results[student.id] = {
                "eligible": eligible_ids,
                "top3": [sp.program.id for sp in scored[:3]],
                "time_ms": elapsed * 1000,
            }

        for sid, res in results.items():
            assert res["time_ms"] < 100, f"Règles trop lent pour {sid}: {res['time_ms']:.0f}ms"
            expected = self.EXPECTED_ELIGIBLE.get(sid, [])
            if expected:
                overlap = set(expected) & set(res["eligible"])
                assert len(overlap) > 0, f"{sid}: aucune formation attendue trouvée éligible. Got: {res['eligible']}"

    def test_llm_engine_fallback(self, programs, students):
        engine = LLMEngine()
        for student in students:
            start = time.time()
            result = engine.recommend(student, programs)
            elapsed = time.time() - start
            assert result.used_fallback, "Fallback should be used without API key"
            assert elapsed < 5000, f"LLM fallback trop lent pour {student.id}: {elapsed*1000:.0f}ms"

    def test_hybrid_engine_full(self, programs, students):
        engine = HybridEngine()
        all_results = []
        for student in students:
            start = time.time()
            result = engine.recommend(student, programs)
            elapsed = (time.time() - start) * 1000
            all_results.append({
                "student": student.id,
                "recommendations": len(result.recommendations),
                "confidence": result.overall_confidence,
                "time_ms": elapsed,
                "contradictions": len(result.contradictions_detected),
            })

        for r in all_results:
            assert r["time_ms"] < 10000, f"Trop lent: {r['student']}"
            assert r["confidence"] >= 0

    def test_edge_case_empty_profile(self, programs):
        engine = HybridEngine()
        from src.models.student import Student, Constraint
        student = Student(
            id="EDGE_EMPTY", name="Profil Vide",
            current_level="", skills=[], interests=[],
            constraints=Constraint(), free_text=None,
        )
        result = engine.recommend(student, programs)
        u = result.uncertainty
        assert u.completeness < 0.1
        assert len(u.missing_info) > 0

    def test_edge_case_contradictions(self, programs):
        engine = HybridEngine()
        from src.models.student import Student, Skill, SkillLevel, Constraint
        student = Student(
            id="EDGE_CONTRA", name="Contradictoire",
            current_level="bac+5",
            skills=[
                Skill(domain="informatique", level=SkillLevel.EXPERT, grade=4),
            ],
            interests=["informatique", "droit", "cuisine"],
            constraints=Constraint(max_budget=0, max_duration_months=2),
            free_text="Je veux tout et rien à la fois.",
        )
        result = engine.recommend(student, programs)
        assert result.uncertainty.completeness < 1.0

    def test_edge_case_zero_budget(self, programs):
        engine = HybridEngine()
        from src.models.student import Student, Skill, SkillLevel, Constraint
        student = Student(
            id="EDGE_BUDGET", name="Budget Zéro",
            current_level="bac+3",
            skills=[Skill(domain="informatique", level=SkillLevel.BEGINNER)],
            interests=["informatique"],
            constraints=Constraint(max_budget=0, max_duration_months=24),
        )
        result = engine.recommend(student, programs)
        for rec in result.recommendations:
            assert rec.program.cost == 0 or not rec.rule_eligible

    def test_programs_count(self, programs):
        assert len(programs) >= 10

    def test_students_count(self, students):
        assert len(students) >= 10

    def test_comparison_report(self, programs, students):
        rule_engine = RuleEngine()
        llm_engine = LLMEngine()
        report = []
        for student in students:
            r_scored = rule_engine.evaluate(student, programs)
            l_result = llm_engine.recommend(student, programs)
            r_top3 = [sp.program.id for sp in r_scored[:3]]
            l_top3 = [r.program_id for r in l_result.recommendations[:3]]
            agreement = len(set(r_top3) & set(l_top3))
            report.append({
                "student": student.id,
                "rule_top3": r_top3,
                "llm_top3": l_top3,
                "agreement_count": agreement,
            })

        avg_agreement = sum(r["agreement_count"] for r in report) / len(report)
        assert avg_agreement >= 0.3, f"Accord moyen trop faible: {avg_agreement:.1f}/3"
