"""Deterministic narrator: fixed Spanish copy per insight code, filled with the
insight's own numbers. The default — no LLM, no hallucination, fully testable."""

from __future__ import annotations

from app.domain.advisor.insights import Insight
from app.domain.advisor.ports import InsightNarrator, NarratedInsight


def _money(amount: int) -> str:
    """Minor units → '$12.345' (ARS-style thousands; advice omits centavos)."""
    sign = "-" if amount < 0 else ""
    whole = abs(amount) // 100
    return f"{sign}${whole:,.0f}".replace(",", ".")


def _pct(bps: int) -> str:
    return f"{bps / 100:.0f}%"


class TemplateNarrator(InsightNarrator):
    async def narrate(self, insight: Insight) -> NarratedInsight:
        title, body, action = self._copy(insight)
        return NarratedInsight(
            code=insight.code,
            severity=insight.severity.value,
            bucket=insight.bucket.value,
            title=title,
            body=body,
            action=action,
        )

    @staticmethod
    def _copy(insight: Insight) -> tuple[str, str, str]:
        d = insight.data
        code = insight.code
        if code == "losing_money":
            return (
                "Estás perdiendo plata",
                f"Tu margen neto del período es {_money(d['net_margin'])} "
                f"sobre ventas de {_money(d['sales'])}.",
                "Revisá food cost, sueldos y gastos fijos: algo no cierra.",
            )
        if code == "below_break_even":
            return (
                "No llegás al punto de equilibrio",
                f"Vendiste {_money(d['sales'])} pero necesitás {_money(d['break_even'])} "
                "para cubrir tus costos.",
                "Empujá ventas o bajá costos fijos para llegar al equilibrio.",
            )
        if code == "high_food_cost":
            return (
                "Food cost alto",
                f"Tu food cost fue {_pct(d['food_cost_ratio_bps'])} "
                f"(objetivo {_pct(d['target_bps'])}).",
                "Revisá recetas, porciones o precios de los platos.",
            )
        if code == "high_prime_cost":
            return (
                "Prime cost alto",
                f"Comida + personal suman {_pct(d['prime_cost_ratio_bps'])} de las ventas.",
                "Por arriba de 65% aprieta: mirá compras y turnos.",
            )
        if code == "high_no_show":
            return (
                "Muchos no-shows",
                f"Tu tasa de no-show fue {_pct(d['no_show_rate_bps'])}.",
                "Pedí confirmación o seña en las reservas de mayor demanda.",
            )
        if code == "high_waste":
            return (
                "Mermas altas",
                f"Tiraste {_money(d['waste_amount'])} en mermas "
                f"({_pct(d['waste_ratio_bps'])} del food cost).",
                "Revisá compras, vencimientos y porcionado.",
            )
        if code == "configure_costs":
            return (
                "Configurá tus costos",
                "Cargá tus sueldos y costos fijos del mes.",
                "Así desbloqueás margen neto, prime cost y punto de equilibrio.",
            )
        if code == "healthy_food_cost":
            return (
                "Food cost en orden",
                f"Tu food cost fue {_pct(d['food_cost_ratio_bps'])}, "
                f"dentro del objetivo ({_pct(d['target_bps'])}).",
                "Seguí así; es la palanca de margen más importante.",
            )
        if code == "margin_improved":
            return (
                "Mejoró tu margen",
                f"Tu margen neto subió a {_money(d['net_margin'])} "
                f"(antes {_money(d['previous_net_margin'])}).",
                "Lo que estás haciendo funciona — sostenelo.",
            )
        return (insight.code, "", "")
