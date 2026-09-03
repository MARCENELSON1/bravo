/// Veredicto del día (Home Nivel 1), portado de `daily-verdict.ts`. Función pura.
/// `net` = ganancia neta del día (unidades menores). `pctVsYesterday` = variación
/// de la facturación de hoy vs ayer (null si no hay dato de ayer).
enum VerdictTone { good, ok, bad }

enum VerdictVs { more, less }

class DailyVerdict {
  const DailyVerdict({required this.tone, this.vs, this.pct});
  final VerdictTone tone;
  final VerdictVs? vs;
  final int? pct;
}

DailyVerdict dailyVerdict(int net, double? pctVsYesterday) {
  final pct = pctVsYesterday?.abs().round();
  final vs = pctVsYesterday == null
      ? null
      : (pctVsYesterday >= 0 ? VerdictVs.more : VerdictVs.less);
  final tone = net < 0
      ? VerdictTone.bad
      : (pctVsYesterday != null && pctVsYesterday < 0
          ? VerdictTone.ok
          : VerdictTone.good);
  return DailyVerdict(tone: tone, vs: vs, pct: pct);
}
