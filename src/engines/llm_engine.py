from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from src.models.student import Student
from src.models.program import Program
from src.utils.uncertainty import UncertaintyAnalyzer, UncertaintyReport


@dataclass
class LLMRecommendation:
    program_id: str
    program_name: str
    confidence: float
    justification: str
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)


@dataclass
class LLMResult:
    recommendations: list[LLMRecommendation]
    reasoning: str
    uncertainty: UncertaintyReport | None = None
    raw_response: str = ""
    latency_ms: float = 0.0
    used_fallback: bool = False


SYSTEM_PROMPT = """Tu es un conseiller orientation expert. Tu aides les étudiants à trouver la formation idéale.

RÈGLES STRICTES:
1. Tu dois te baser UNIQUEMENT sur les formations du catalogue fourni
2. Tu dois toujours justifier tes recommandations avec des arguments concrets
3. Si le profil est incomplet, tu dois poser des questions de clarification
4. Si les prérequis ne sont pas satisfaits, signale-le explicitement
5. Donne un score de confiance (0-1) pour chaque recommandation
6. Identifie les risques et les points faibles du profil

FORMAT DE SORTIE (JSON strict):
{
  "recommendations": [
    {
      "program_id": "PX",
      "confidence": 0.85,
      "justification": "...",
      "pros": ["...", "..."],
      "cons": ["...", "..."],
      "questions": ["..."]
    }
  ],
  "reasoning": " raisonnement global...",
  "clarification_needed": ["question 1", "question 2"]
}

IMPORTANT: Réponds UNIQUEMENT en JSON valide, pas de texte avant ou après."""


def _build_prompt(student: Student, programs: list[Program], uncertainty: UncertaintyReport) -> str:
    student_ctx = student.to_context_string()
    programs_ctx = "\n\n".join(p.to_context_string() for p in programs)
    uncertainty_ctx = ""
    if uncertainty.missing_info:
        uncertainty_ctx += f"\nInformations manquantes: {', '.join(uncertainty.missing_info)}"
    if uncertainty.contradictions:
        uncertainty_ctx += f"\nContradictions détectées: {', '.join(uncertainty.contradictions)}"
    if uncertainty.warnings:
        uncertainty_ctx += f"\nAlertes: {', '.join(uncertainty.warnings)}"

    return f"""PROFIL ÉTUDIANT:
{student_ctx}

{uncertainty_ctx}

CATALOGUE DE FORMATIONS DISPONIBLES:
{programs_ctx}

Analyse le profil, identifie les forces et faiblesses, puis recommande les 2-3 meilleures formations avec justification détaillée. Si le profil est incomplet, inclus des questions de clarification."""


class LLMEngine:
    """
    Moteur LLM guidé par règles pour la recommandation.
    Supporte OpenAI, Ollama (local/gratuit), ou fallback déterministe.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        try:
            from dotenv import load_dotenv
            from pathlib import Path
            env_path = Path(__file__).resolve().parent.parent.parent / "config" / ".env"
            load_dotenv(env_path)
        except ImportError:
            pass
        self.provider = os.getenv("LLM_PROVIDER", "fallback")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.uncertainty_analyzer = UncertaintyAnalyzer()

    def recommend(self, student: Student, programs: list[Program]) -> LLMResult:
        uncertainty = self.uncertainty_analyzer.analyze(student)
        filtered = self._pre_filter(student, programs)

        if self.provider == "ollama":
            return self._call_ollama(student, filtered, uncertainty)
        elif self.provider == "openai":
            if not self.api_key or self.api_key == "sk-votre-cle-api-ici":
                return self._fallback_reasoning(student, filtered, uncertainty)
            return self._call_openai(student, filtered, uncertainty)
        else:
            return self._fallback_reasoning(student, filtered, uncertainty)

    def _pre_filter(self, student: Student, programs: list[Program]) -> list[Program]:
        """Pré-filtrage simple pour réduire le contexte envoyé au LLM."""
        candidates = []
        for p in programs:
            if student.constraints.max_budget is not None and p.cost > student.constraints.max_budget * 1.5:
                continue
            if student.constraints.max_duration_months and p.duration_months > student.constraints.max_duration_months * 2:
                continue
            candidates.append(p)
        return candidates if candidates else programs[:5]

    def _call_openai(self, student: Student, programs: list[Program], uncertainty: UncertaintyReport) -> LLMResult:
        try:
            from openai import OpenAI
        except ImportError:
            return self._fallback_reasoning(student, programs, uncertainty)

        client = OpenAI(api_key=self.api_key)
        user_msg = _build_prompt(student, programs, uncertainty)

        start = time.time()
        try:
            response = client.chat.completions.create(
                model=self.openai_model,
                temperature=self.temperature,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                max_tokens=2000,
            )
            latency = (time.time() - start) * 1000
            raw = response.choices[0].message.content.strip()
            parsed = self._parse_response(raw)
            parsed.uncertainty = uncertainty
            parsed.latency_ms = latency
            parsed.raw_response = raw
            return parsed
        except Exception:
            return self._fallback_reasoning(student, programs, uncertainty)

    def _call_ollama(self, student: Student, programs: list[Program], uncertainty: UncertaintyReport) -> LLMResult:
        try:
            import ollama as ollama_lib
        except ImportError:
            return self._fallback_reasoning(student, programs, uncertainty)

        user_msg = _build_prompt(student, programs, uncertainty)
        start = time.time()
        try:
            response = ollama_lib.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                options={"temperature": self.temperature},
            )
            latency = (time.time() - start) * 1000
            raw = response["message"]["content"].strip()
            parsed = self._parse_response(raw)
            parsed.uncertainty = uncertainty
            parsed.latency_ms = latency
            parsed.raw_response = raw
            return parsed
        except Exception as e:
            return self._fallback_reasoning(student, programs, uncertainty)

    def _parse_response(self, raw: str) -> LLMResult:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            return LLMResult(
                recommendations=[],
                reasoning=f"Réponse LLM non parsable: {raw[:200]}",
                raw_response=raw,
                used_fallback=True,
            )

        recs = []
        for r in data.get("recommendations", []):
            recs.append(LLMRecommendation(
                program_id=r.get("program_id", ""),
                program_name=r.get("program_name", r.get("program_id", "")),
                confidence=float(r.get("confidence", 0.5)),
                justification=r.get("justification", ""),
                pros=r.get("pros", []),
                cons=r.get("cons", []),
                questions=r.get("questions", []),
            ))

        return LLMResult(
            recommendations=recs,
            reasoning=data.get("reasoning", ""),
            raw_response=raw,
        )

    def _fallback_reasoning(self, student: Student, programs: list[Program], uncertainty: UncertaintyReport) -> LLMResult:
        """
        Raisonnement déterministe quand le LLM n'est pas disponible.
        Simule un raisonnement de type 'LLM' basé sur des règles simples.
        """
        recs = []
        student_domains = {sk.domain.lower() for sk in student.skills}
        student_interests_lower = {i.lower() for i in student.interests}
        student_all = student_domains | student_interests_lower

        for p in programs:
            confidence = 0.5
            pros = []
            cons = []
            questions = []

            program_domain = p.domain.value.lower()
            program_domain_flat = program_domain.replace("_", " ")
            has_domain_match = (
                program_domain in student_domains
                or program_domain_flat in student_domains
                or any(
                    interest in program_domain_flat or program_domain_flat in interest
                    or interest.replace(" ", "_") in program_domain
                    for interest in student_interests_lower
                )
                or any(
                    sa in program_domain_flat or program_domain_flat in sa
                    or any(w in sa for w in program_domain_flat.split() if len(w) > 3)
                    for sa in student_all
                )
            )

            if has_domain_match:
                confidence += 0.2
            else:
                confidence -= 0.3
                cons.append(f"Aucun lien avec vos compétences (domaine: {p.domain.value})")

            if student.interests:
                interest_match = sum(
                    1 for i in student.interests
                    if i.lower() in f"{p.domain.value} {p.name} {' '.join(p.skills_taught)}".lower()
                )
                if interest_match > 0:
                    confidence += interest_match * 0.1
                    pros.append("Correspond à vos intérêts")

            prereq_met = all(
                student.has_skill(pr.domain, _level_from_str(pr.min_level))
                for pr in p.prerequisites if pr.required
            )
            if prereq_met:
                pros.append("Prérequis satisfaits")
                confidence += 0.05
            else:
                cons.append("Certains prérequis ne sont pas satisfaits")
                confidence -= 0.1
                questions.append("Avez-vous des certificats ou expériences non listées ?")

            if student.constraints.max_budget and p.cost <= student.constraints.max_budget:
                pros.append(f"Dans le budget ({p.cost}€)")
                confidence += 0.05
            elif student.constraints.max_budget:
                cons.append(f"Coût ({p.cost}€) élevé")

            if student.constraints.preferred_location and p.location.lower() == student.constraints.preferred_location.lower():
                pros.append(f"À {p.location}")
                confidence += 0.05

            confidence = max(0.0, min(1.0, confidence))
            justification = f"Formation {p.name} en {p.domain.value}. "
            if pros:
                justification += "Points forts: " + "; ".join(pros) + ". "
            if cons:
                justification += "Points faibles: " + "; ".join(cons) + ". "

            recs.append(LLMRecommendation(
                program_id=p.id,
                program_name=p.name,
                confidence=round(confidence, 2),
                justification=justification,
                pros=pros,
                cons=cons,
                questions=questions,
            ))

        recs.sort(key=lambda x: x.confidence, reverse=True)

        reasoning = "Raisonnement hors-ligne (LLM non disponible). "
        if uncertainty.missing_info:
            reasoning += f"Profil incomplet: {', '.join(uncertainty.missing_info[:3])}. "
        reasoning += f"{len(recs)} formations analysées."

        return LLMResult(
            recommendations=recs,
            reasoning=reasoning,
            uncertainty=uncertainty,
            used_fallback=True,
        )


def _level_from_str(level: str) -> "SkillLevel":
    from src.models.student import SkillLevel
    mapping = {
        "none": SkillLevel.NONE,
        "beginner": SkillLevel.BEGINNER,
        "intermediate": SkillLevel.INTERMEDIATE,
        "advanced": SkillLevel.ADVANCED,
        "expert": SkillLevel.EXPERT,
    }
    return mapping.get(level, SkillLevel.NONE)
