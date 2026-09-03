/// Selector temporal de Finanzas (paridad con `finance-range.ts` del web):
/// Hoy / Esta semana / Este mes / Trimestre → ventana {from,to} ISO.
enum FinanceRange { today, week, month, quarter }

class RangeWindow {
  const RangeWindow(this.from, this.to);
  final String from; // ISO
  final String to; // ISO
}

DateTime _startOfDay(DateTime d) => DateTime(d.year, d.month, d.day);

// Lunes como primer día (rioplatense).
DateTime _startOfWeek(DateTime d) {
  final day = _startOfDay(d);
  final weekday = (day.weekday + 6) % 7; // 0 = lunes
  return day.subtract(Duration(days: weekday));
}

DateTime _startOfQuarter(DateTime d) =>
    DateTime(d.year, (d.month - 1) ~/ 3 * 3 + 1, 1);

RangeWindow rangeWindow(FinanceRange range, [DateTime? nowArg]) {
  final now = nowArg ?? DateTime.now();
  final from = switch (range) {
    FinanceRange.today => _startOfDay(now),
    FinanceRange.week => _startOfWeek(now),
    FinanceRange.quarter => _startOfQuarter(now),
    FinanceRange.month => DateTime(now.year, now.month, 1),
  };
  return RangeWindow(from.toUtc().toIso8601String(), now.toUtc().toIso8601String());
}
