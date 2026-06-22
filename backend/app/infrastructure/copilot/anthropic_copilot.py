"""LLM copilot adapter: Claude turns a question into SQL, and turns result rows
into a Spanish answer. The answer is grounded — a guardrail rejects any number
not present in the result rows (falls back to a deterministic count)."""

from __future__ import annotations

import re

from app.domain.copilot.ports import CopilotLLM, QueryResult
from app.infrastructure.llm.client import LlmClient

_SQL_SYSTEM = (
    "Sos un generador de SQL para PostgreSQL de un sistema de gastronomía. Dada "
    "una pregunta en español, devolvés UNA sola consulta SELECT de solo lectura "
    "usando EXCLUSIVAMENTE estas tablas y columnas:\n{schema}\n"
    "Reglas: solo SELECT; sin punto y coma; NO uses SELECT * (nombrá las columnas); "
    "NO filtres por tenant_id (el sistema lo hace solo); los montos están en unidades "
    "menores (centavos). Devolvé SOLO el SQL, sin explicación ni markdown."
)
_ANSWER_SYSTEM = (
    "Respondé la pregunta del dueño en español rioplatense, en una o dos frases, "
    "usando SOLO los datos de la tabla de resultados. No inventes ni calcules "
    "números que no estén en los datos. Si no hay filas, decí que no hay datos."
)


def _strip_fences(text: str) -> str:
    out = text.strip()
    out = re.sub(r"^```(?:sql)?", "", out).strip()
    out = re.sub(r"```$", "", out).strip()
    return out


def _numbers(s: str) -> set[str]:
    # Drop thousands separators between digits so "$300.000" ~ "300000".
    s = re.sub(r"(?<=\d)[.,\s](?=\d)", "", s)
    return set(re.findall(r"\d+", s))


def _render(result: QueryResult) -> str:
    lines = [" | ".join(result.columns)]
    lines += [" | ".join(str(v) for v in row) for row in result.rows[:50]]
    return "\n".join(lines)


def _fallback(result: QueryResult) -> str:
    n = len(result.rows)
    if n == 0:
        return "No encontré datos para esa pregunta."
    return f"Encontré {n} resultado{'s' if n != 1 else ''}. Mirá la tabla de abajo."


class AnthropicCopilotLLM(CopilotLLM):
    def __init__(self, llm: LlmClient) -> None:
        self._llm = llm

    async def to_sql(self, question: str, schema_doc: str) -> str:
        system = _SQL_SYSTEM.format(schema=schema_doc)
        raw = await self._llm.complete(system=system, user=question, max_tokens=400)
        return _strip_fences(raw)

    async def answer(self, question: str, result: QueryResult) -> str:
        if not result.rows:
            return _fallback(result)  # no data → deterministic, don't trust the LLM
        rendered = _render(result)
        user = f"Pregunta: {question}\n\nResultados:\n{rendered}"
        try:
            text = (
                await self._llm.complete(system=_ANSWER_SYSTEM, user=user, max_tokens=300)
            ).strip()
        except Exception:
            return _fallback(result)
        # Guardrail: no number that isn't in the result rows.
        if not text or (_numbers(text) - _numbers(rendered)):
            return _fallback(result)
        return text
