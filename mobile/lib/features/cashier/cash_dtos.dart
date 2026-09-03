/// Sesión de caja abierta (backend `CashSessionResponse`).
class CashSession {
  const CashSession({
    required this.id,
    required this.status,
    required this.currency,
    required this.openingFloatAmount,
    this.openedAt,
  });

  final String id;
  final String status; // OPEN | CLOSED
  final String currency;
  final int openingFloatAmount;
  final DateTime? openedAt;

  bool get isOpen => status == 'OPEN';

  factory CashSession.fromJson(Map<String, dynamic> j) => CashSession(
        id: j['id'] as String,
        status: j['status'] as String,
        currency: j['currency'] as String,
        openingFloatAmount: j['opening_float_amount'] as int,
        openedAt: _date(j['opened_at']),
      );
}

/// Línea del arqueo por método (backend `CashReportLineResponse`).
class CashReportLine {
  const CashReportLine({
    required this.method,
    required this.expected,
    required this.tips,
    this.counted,
    this.difference,
  });

  final String method;
  final int expected;
  final int tips;
  final int? counted;
  final int? difference;

  factory CashReportLine.fromJson(Map<String, dynamic> j) => CashReportLine(
        method: j['method'] as String,
        expected: (j['expected'] as int?) ?? 0,
        tips: (j['tips'] as int?) ?? 0,
        counted: j['counted'] as int?,
        difference: j['difference'] as int?,
      );
}

/// Reporte de cierre / arqueo Z (backend `CashReportResponse`).
class CashReport {
  const CashReport({
    required this.currency,
    required this.openingFloat,
    required this.expectedTotal,
    required this.tipsTotal,
    required this.lines,
    this.countedTotal,
    this.differenceTotal,
  });

  final String currency;
  final int openingFloat;
  final int expectedTotal;
  final int tipsTotal;
  final List<CashReportLine> lines;
  final int? countedTotal;
  final int? differenceTotal;

  factory CashReport.fromJson(Map<String, dynamic> j) => CashReport(
        currency: j['currency'] as String,
        openingFloat: (j['opening_float'] as int?) ?? 0,
        expectedTotal: (j['expected_total'] as int?) ?? 0,
        tipsTotal: (j['tips_total'] as int?) ?? 0,
        countedTotal: j['counted_total'] as int?,
        differenceTotal: j['difference_total'] as int?,
        lines: ((j['lines'] as List?) ?? const [])
            .map((e) => CashReportLine.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

DateTime? _date(Object? v) => v is String ? DateTime.tryParse(v)?.toLocal() : null;
