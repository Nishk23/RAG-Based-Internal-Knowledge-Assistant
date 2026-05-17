from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SampleEvalCase:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str


def get_sample_eval_cases() -> list[SampleEvalCase]:
    return [
        SampleEvalCase(
            question="What does the SLA policy say about incident updates?",
            answer="The policy requires updates every 30 minutes during a Sev-1 incident.",
            contexts=[
                "For Sev-1 incidents, status updates must be posted every 30 minutes.",
                "Escalation to on-call manager occurs after 15 minutes.",
            ],
            ground_truth="Sev-1 incidents require status updates every 30 minutes.",
        )
    ]
