import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Un diagnóstico/alerta financiera (backend `FinanceDiagnosticResponse`).
class FinanceDiagnostic {
  const FinanceDiagnostic({
    required this.severity,
    required this.title,
    required this.body,
    this.action,
  });

  final String severity; // info | warn | critical ...
  final String title;
  final String body;
  final String? action;

  factory FinanceDiagnostic.fromJson(Map<String, dynamic> j) => FinanceDiagnostic(
        severity: (j['severity'] as String?) ?? 'info',
        title: (j['title'] as String?) ?? '',
        body: (j['body'] as String?) ?? '',
        action: j['action'] as String?,
      );
}

/// Panorama financiero (backend `FinanceOverviewResponse`). Slice de consulta:
/// solo campos de plata inequívocos + el resumen + las alertas (los KPIs crudos
/// mezclan montos y ratios, así que no se muestran para no engañar).
class FinanceOverview {
  const FinanceOverview({
    required this.currency,
    required this.collectedNetAmount,
    required this.commissionsAmount,
    required this.configured,
    this.summary,
    this.diagnostics = const [],
  });

  final String currency;
  final int collectedNetAmount;
  final int commissionsAmount;
  final bool configured;
  final String? summary;
  final List<FinanceDiagnostic> diagnostics;

  factory FinanceOverview.fromJson(Map<String, dynamic> j) => FinanceOverview(
        currency: j['currency'] as String,
        collectedNetAmount: (j['collected_net_amount'] as int?) ?? 0,
        commissionsAmount: (j['commissions_amount'] as int?) ?? 0,
        configured: (j['configured'] as bool?) ?? false,
        summary: j['summary'] as String?,
        diagnostics: ((j['diagnostics'] as List?) ?? const [])
            .map((e) => FinanceDiagnostic.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

class FinanceRepository {
  FinanceRepository(this._dio);

  final Dio _dio;

  Future<FinanceOverview> overview() async {
    try {
      final res = await _dio.get<dynamic>('/finance/overview');
      return FinanceOverview.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final financeRepositoryProvider = Provider<FinanceRepository>(
  (ref) => FinanceRepository(ref.read(apiDioProvider)),
);

final financeOverviewProvider = FutureProvider.autoDispose<FinanceOverview>(
  (ref) => ref.read(financeRepositoryProvider).overview(),
);
