from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.models.student import Student
from src.models.program import Program
from src.engines.rule_engine import RuleEngine, ScoredProgram
from src.engines.llm_engine import LLMEngine, LLMResult, LLMRecommendation
from src.utils.uncertainty import UncertaintyAnalyzer, UncertaintyReport


@dataclass
class HybridRecommendation:
    program: Program
    final_score: float
    rule_score: float
    llm_score: float
    rule_eligible: bool
    justification: str
    confidence: float
    sources: list[str] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)


@dataclass
class HybridResult:
    recommendations: list[HybridRecommendation]
    uncertainty: UncertaintyReport
    rule_result: list[ScoredProgram]
    llm_result: LLMResult
    overall_confidence: float = 0.0
    contradictions_detected: list[str] = field(default_factory=list)


class HybridEngine:
    """
    Intégrateur hybride combinant le moteur symbolique et le LLM.
    Fusionne les scores, détecte les désaccords et produit une conclusion unifiée.
    """

    def __init__(
        self,
        alpha: float = 0.5,
        beta: float = 0.5,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.alpha = alpha  # Poids du moteur symbolique
        self.beta = beta    # Poids du LLM
        self.rule_engine = RuleEngine()
        self.llm_engine = LLMEngine(api_key=api_key, model=model)
        self.uncertainty_analyzer = UncertaintyAnalyzer()

    def recommend(self, student: Student, programs: list[Program], top_n: int = 3) -> HybridResult:
        uncertainty = self.uncertainty_analyzer.analyze(student)

        # Approche 1 : Moteur symbolique
        rule_results = self.rule_engine.evaluate(student, programs)

        # Approche 2 : LLM
        llm_result = self.llm_engine.recommend(student, programs)

        # Fusion
        recommendations = self._merge_results(rule_results, llm_result, programs)

        # Application du modificateur d'incertitude
        for rec in recommendations:
            rec.confidence = max(0.0, min(1.0, rec.confidence + uncertainty.confidence_modifier))

        recommendations.sort(key=lambda x: x.final_score, reverse=True)
        recommendations = recommendations[:top_n]

        # Calcul de la confiance globale
        if recommendations:
            overall_confidence = sum(r.confidence for r in recommendations) / len(recommendations)
        else:
            overall_confidence = 0.0

        return HybridResult(
            recommendations=recommendations,
            uncertainty=uncertainty,
            rule_result=rule_results,
            llm_result=llm_result,
            overall_confidence=round(overall_confidence, 3),
            contradictions_detected=uncertainty.contradictions,
        )

    def _merge_results(
        self,
        rule_results: list[ScoredProgram],
        llm_result: LLMResult,
        programs: list[Program],
    ) -> list[HybridRecommendation]:
        rule_map = {sp.program.id: sp for sp in rule_results}
        llm_map = {r.program_id: r for r in llm_result.recommendations}
        all_program_ids = set(rule_map.keys()) | set(llm_map.keys())
        program_map = {p.id: p for p in programs}

        merged = []
        for pid in all_program_ids:
            program = program_map.get(pid)
            if not program:
                continue

            rule_sp = rule_map.get(pid)
            llm_rec = llm_map.get(pid)

            rule_score = (rule_sp.score / 100.0) if rule_sp else 0.0
            rule_eligible = rule_sp.eligible if rule_sp else False
            llm_score = llm_rec.confidence if llm_rec else 0.0

            # Score final pondéré
            if rule_sp and not rule_sp.eligible:
                # Le moteur symbolique a rejeté → pénalité forte
                final_score = rule_score * 0.3 + llm_score * 0.2
                sources = ["rule_engine (rejected)"]
                if llm_rec:
                    sources.append("llm_engine")
            else:
                final_score = self.alpha * rule_score + self.beta * llm_score
                sources = []
                if rule_sp:
                    sources.append("rule_engine")
                if llm_rec:
                    sources.append("llm_engine")

            # Justification combinée
            justification_parts = []
            disagreements = []

            if rule_sp and rule_sp.reasons:
                justification_parts.append("Règles: " + "; ".join(rule_sp.reasons[:3]))
            if llm_rec and llm_rec.justification:
                justification_parts.append("Analyse LLM: " + llm_rec.justification[:200])

            # Détection de désaccords
            if rule_sp and llm_rec:
                if rule_sp.eligible and llm_rec.confidence < 0.3:
                    disagreements.append("Moteur rules: éligible / LLM: faible confiance")
                if not rule_sp.eligible and llm_rec.confidence > 0.7:
                    disagreements.append("Moteur rules: non éligible / LLM: haute confiance")

                rule_in_top = rule_sp.score >= 60
                llm_in_top = llm_rec.confidence >= 0.6
                if rule_in_top != llm_in_top:
                    disagreements.append(
                        f"Différence de classement: rules={rule_sp.score:.0f}, llm={llm_rec.confidence:.2f}"
                    )

            confidence = final_score
            if disagreements:
                confidence *= 0.85
                justification_parts.append(f"⚠ Désaccords entre moteurs: {'; '.join(disagreements)}")

            merged.append(HybridRecommendation(
                program=program,
                final_score=round(final_score, 4),
                rule_score=round(rule_score, 4),
                llm_score=round(llm_score, 4),
                rule_eligible=rule_eligible,
                justification=" ".join(justification_parts),
                confidence=round(min(1.0, confidence), 3),
                sources=sources,
                disagreements=disagreements,
            ))

        return merged
