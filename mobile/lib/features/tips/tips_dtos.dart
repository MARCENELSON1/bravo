/// Fila del reporte de propinas por mozo (backend `TipsReportRowResponse`).
class TipRow {
  const TipRow({
    required this.waiterId,
    required this.waiterName,
    required this.earned,
    required this.paid,
    required this.pending,
  });

  final String waiterId;
  final String waiterName;
  final int earned;
  final int paid;
  final int pending;

  factory TipRow.fromJson(Map<String, dynamic> j) => TipRow(
        waiterId: j['waiter_id'] as String,
        waiterName: j['waiter_name'] as String,
        earned: (j['earned'] as int?) ?? 0,
        paid: (j['paid'] as int?) ?? 0,
        pending: (j['pending'] as int?) ?? 0,
      );
}

/// Reporte de propinas (backend `TipsReportResponse`).
class TipsReport {
  const TipsReport({
    required this.currency,
    required this.rows,
    required this.earnedTotal,
    required this.paidTotal,
    required this.pendingTotal,
  });

  final String currency;
  final List<TipRow> rows;
  final int earnedTotal;
  final int paidTotal;
  final int pendingTotal;

  factory TipsReport.fromJson(Map<String, dynamic> j) => TipsReport(
        currency: j['currency'] as String,
        earnedTotal: (j['earned_total'] as int?) ?? 0,
        paidTotal: (j['paid_total'] as int?) ?? 0,
        pendingTotal: (j['pending_total'] as int?) ?? 0,
        rows: ((j['rows'] as List?) ?? const [])
            .map((e) => TipRow.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}
