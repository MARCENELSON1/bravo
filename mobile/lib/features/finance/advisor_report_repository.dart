import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';
import 'finance_range.dart';

/// KPIs del Asesor (backend `AdvisorKpisResponse`). Montos en unidades menores;
/// ratios en bps.
class AdvisorKpis {
  const AdvisorKpis({
    required this.currency,
    required this.salesAmount,
    required this.grossMarginAmount,
    required this.netMarginAmount,
    required this.foodCostRatioBps,
    required this.laborCostRatioBps,
    required this.primeCostRatioBps,
    required this.breakEvenAmount,
    required this.ordersCount,
    required this.averageTicketAmount,
    required this.noShowRateBps,
    required this.configured,
  });

  final String currency;
  final int salesAmount;
  final int grossMarginAmount;
  final int netMarginAmount;
  final int foodCostRatioBps;
  final int laborCostRatioBps;
  final int primeCostRatioBps;
  final int breakEvenAmount;
  final int ordersCount;
  final int averageTicketAmount;
  final int noShowRateBps;
  final bool configured;

  factory AdvisorKpis.fromJson(Map<String, dynamic> j) => AdvisorKpis(
        currency: (j['currency'] as String?) ?? 'ARS',
        salesAmount: (j['sales_amount'] as int?) ?? 0,
        grossMarginAmount: (j['gross_margin_amount'] as int?) ?? 0,
        netMarginAmount: (j['net_margin_amount'] as int?) ?? 0,
        foodCostRatioBps: (j['food_cost_ratio_bps'] as int?) ?? 0,
        laborCostRatioBps: (j['labor_cost_ratio_bps'] as int?) ?? 0,
        primeCostRatioBps: (j['prime_cost_ratio_bps'] as int?) ?? 0,
        breakEvenAmount: (j['break_even_amount'] as int?) ?? 0,
        ordersCount: (j['orders_count'] as int?) ?? 0,
        averageTicketAmount: (j['average_ticket_amount'] as int?) ?? 0,
        noShowRateBps: (j['no_show_rate_bps'] as int?) ?? 0,
        configured: (j['configured'] as bool?) ?? false,
      );
}

/// Un insight narrado (backend `NarratedInsightResponse`).
class AdvisorInsight {
  const AdvisorInsight({
    required this.code,
    required this.severity,
    required this.bucket,
    required this.title,
    required this.body,
    required this.action,
  });
  final String code;
  final String severity; // info | warn | critical ...
  final String bucket;
  final String title;
  final String body;
  final String action;
  factory AdvisorInsight.fromJson(Map<String, dynamic> j) => AdvisorInsight(
        code: (j['code'] as String?) ?? '',
        severity: (j['severity'] as String?) ?? 'info',
        bucket: (j['bucket'] as String?) ?? '',
        title: (j['title'] as String?) ?? '',
        body: (j['body'] as String?) ?? '',
        action: (j['action'] as String?) ?? '',
      );
}

class AdvisorReport {
  const AdvisorReport({
    required this.kpis,
    required this.insights,
    required this.llmEnabled,
    this.summary,
  });
  final AdvisorKpis kpis;
  final List<AdvisorInsight> insights;
  final bool llmEnabled;
  final String? summary;
  factory AdvisorReport.fromJson(Map<String, dynamic> j) => AdvisorReport(
        kpis: AdvisorKpis.fromJson(Map<String, dynamic>.from(j['kpis'] as Map)),
        insights: ((j['insights'] as List?) ?? const [])
            .map((e) => AdvisorInsight.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
        llmEnabled: (j['llm_enabled'] as bool?) ?? false,
        summary: j['summary'] as String?,
      );
}

class AdvisorReportRepository {
  AdvisorReportRepository(this._dio);
  final Dio _dio;

  Future<AdvisorReport> report(RangeWindow w) async {
    try {
      final res = await _dio.get<dynamic>('/advisor/report',
          queryParameters: {'from': w.from, 'to': w.to});
      return AdvisorReport.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final advisorReportRepositoryProvider = Provider<AdvisorReportRepository>(
  (ref) => AdvisorReportRepository(ref.read(apiDioProvider)),
);

final advisorReportProvider =
    FutureProvider.autoDispose.family<AdvisorReport, FinanceRange>(
  (ref, range) => ref.read(advisorReportRepositoryProvider).report(rangeWindow(range)),
);
