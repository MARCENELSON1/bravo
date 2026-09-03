import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';
import 'finance_range.dart';

/// KPI financiero (backend `FinanceKpiResponse`). `kind`: money | ratio |
/// turnover. `value`/`delta` en unidades menores (money) o bps (ratio) o
/// centésimas de vuelta (turnover). `status`: healthy | warn | alert | neutral.
class FinanceKpi {
  const FinanceKpi({
    required this.key,
    required this.kind,
    required this.value,
    required this.previous,
    required this.delta,
    required this.status,
    this.healthyLow,
    this.healthyHigh,
  });

  final String key;
  final String kind;
  final int value;
  final int previous;
  final int delta;
  final String status;
  final int? healthyLow;
  final int? healthyHigh;

  factory FinanceKpi.fromJson(Map<String, dynamic> j) => FinanceKpi(
        key: j['key'] as String,
        kind: (j['kind'] as String?) ?? 'money',
        value: (j['value'] as int?) ?? 0,
        previous: (j['previous'] as int?) ?? 0,
        delta: (j['delta'] as int?) ?? 0,
        status: (j['status'] as String?) ?? 'neutral',
        healthyLow: j['healthy_low'] as int?,
        healthyHigh: j['healthy_high'] as int?,
      );
}

/// Proyección de fin de mes (backend `FinanceProjectionResponse`).
class FinanceProjection {
  const FinanceProjection({
    required this.salesAmount,
    required this.netMarginAmount,
    required this.monthDays,
    required this.elapsedDays,
  });
  final int salesAmount;
  final int netMarginAmount;
  final int monthDays;
  final int elapsedDays;
  factory FinanceProjection.fromJson(Map<String, dynamic> j) => FinanceProjection(
        salesAmount: (j['sales_amount'] as int?) ?? 0,
        netMarginAmount: (j['net_margin_amount'] as int?) ?? 0,
        monthDays: (j['month_days'] as int?) ?? 0,
        elapsedDays: (j['elapsed_days'] as int?) ?? 0,
      );
}

/// Margen por producto (backend `ProductMarginResponse`).
class ProductMargin {
  const ProductMargin({
    required this.productId,
    required this.productName,
    required this.unitsSold,
    required this.salesAmount,
    required this.marginAmount,
  });
  final String productId;
  final String productName;
  final int unitsSold;
  final int salesAmount;
  final int marginAmount;
  factory ProductMargin.fromJson(Map<String, dynamic> j) => ProductMargin(
        productId: j['product_id'] as String,
        productName: (j['product_name'] as String?) ?? '',
        unitsSold: (j['units_sold'] as int?) ?? 0,
        salesAmount: (j['sales_amount'] as int?) ?? 0,
        marginAmount: (j['margin_amount'] as int?) ?? 0,
      );
}

/// Un diagnóstico/alerta financiera (backend `FinanceDiagnosticResponse`).
class FinanceDiagnostic {
  const FinanceDiagnostic({
    required this.severity,
    required this.bucket,
    required this.title,
    required this.body,
    this.action,
  });

  final String severity; // info | warn | critical ...
  final String bucket;
  final String title;
  final String body;
  final String? action;

  factory FinanceDiagnostic.fromJson(Map<String, dynamic> j) =>
      FinanceDiagnostic(
        severity: (j['severity'] as String?) ?? 'info',
        bucket: (j['bucket'] as String?) ?? '',
        title: (j['title'] as String?) ?? '',
        body: (j['body'] as String?) ?? '',
        action: j['action'] as String?,
      );
}

/// Panorama financiero completo (backend `FinanceOverviewResponse`), paridad
/// con la Pantalla Finanzas del web.
class FinanceOverview {
  const FinanceOverview({
    required this.currency,
    required this.periodDays,
    required this.configured,
    required this.collectedNetAmount,
    required this.commissionsAmount,
    this.summary,
    this.projection,
    this.kpis = const [],
    this.diagnostics = const [],
    this.productMargins = const [],
  });

  final String currency;
  final int periodDays;
  final bool configured;
  final int collectedNetAmount;
  final int commissionsAmount;
  final String? summary;
  final FinanceProjection? projection;
  final List<FinanceKpi> kpis;
  final List<FinanceDiagnostic> diagnostics;
  final List<ProductMargin> productMargins;

  FinanceKpi? kpi(String key) {
    for (final k in kpis) {
      if (k.key == key) return k;
    }
    return null;
  }

  factory FinanceOverview.fromJson(Map<String, dynamic> j) {
    List<T> list<T>(String key, T Function(Map<String, dynamic>) f) =>
        ((j[key] as List?) ?? const [])
            .map((e) => f(Map<String, dynamic>.from(e as Map)))
            .toList();
    return FinanceOverview(
      currency: j['currency'] as String,
      periodDays: (j['period_days'] as int?) ?? 0,
      configured: (j['configured'] as bool?) ?? false,
      collectedNetAmount: (j['collected_net_amount'] as int?) ?? 0,
      commissionsAmount: (j['commissions_amount'] as int?) ?? 0,
      summary: j['summary'] as String?,
      projection: j['projection'] == null
          ? null
          : FinanceProjection.fromJson(
              Map<String, dynamic>.from(j['projection'] as Map)),
      kpis: list('kpis', FinanceKpi.fromJson),
      diagnostics: list('diagnostics', FinanceDiagnostic.fromJson),
      productMargins: list('product_margins', ProductMargin.fromJson),
    );
  }
}

/// Fila del desglose de gastos por categoría (backend `ExpenseCategoryRowResponse`).
class ExpenseRow {
  const ExpenseRow({
    required this.category,
    required this.amount,
    required this.previous,
    required this.delta,
  });
  final String category;
  final int amount;
  final int previous;
  final int delta;
  factory ExpenseRow.fromJson(Map<String, dynamic> j) => ExpenseRow(
        category: (j['category'] as String?) ?? '',
        amount: (j['amount'] as int?) ?? 0,
        previous: (j['previous'] as int?) ?? 0,
        delta: (j['delta'] as int?) ?? 0,
      );
}

class ExpenseBreakdown {
  const ExpenseBreakdown(
      {required this.currency, required this.total, required this.rows});
  final String currency;
  final int total;
  final List<ExpenseRow> rows;
  factory ExpenseBreakdown.fromJson(Map<String, dynamic> j) => ExpenseBreakdown(
        currency: (j['currency'] as String?) ?? 'ARS',
        total: (j['total'] as int?) ?? 0,
        rows: ((j['rows'] as List?) ?? const [])
            .map((e) => ExpenseRow.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

/// Un movimiento (backend `MovementResponse`).
class Movement {
  const Movement({
    required this.occurredAt,
    required this.kind,
    required this.amount,
    required this.method,
    required this.currency,
    this.category,
    this.description,
  });
  final String occurredAt;
  final String kind; // inflow | expense ...
  final int amount;
  final String method;
  final String currency;
  final String? category;
  final String? description;
  factory Movement.fromJson(Map<String, dynamic> j) => Movement(
        occurredAt: (j['occurred_at'] as String?) ?? '',
        kind: (j['kind'] as String?) ?? '',
        amount: (j['amount'] as int?) ?? 0,
        method: (j['method'] as String?) ?? '',
        currency: (j['currency'] as String?) ?? 'ARS',
        category: j['category'] as String?,
        description: j['description'] as String?,
      );
}

class FinanceRepository {
  FinanceRepository(this._dio);
  final Dio _dio;

  Future<FinanceOverview> overview(RangeWindow w) async {
    try {
      final res = await _dio.get<dynamic>('/finance/overview',
          queryParameters: {'from': w.from, 'to': w.to});
      return FinanceOverview.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<ExpenseBreakdown> expenseBreakdown(RangeWindow w) async {
    try {
      final res = await _dio.get<dynamic>('/finance/expenses/breakdown',
          queryParameters: {'from': w.from, 'to': w.to});
      return ExpenseBreakdown.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<List<Movement>> movements(RangeWindow w, {int limit = 30}) async {
    try {
      final res = await _dio.get<dynamic>('/finance/movements',
          queryParameters: {'from': w.from, 'to': w.to, 'limit': limit});
      return ((res.data as List?) ?? const [])
          .map((e) => Movement.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final financeRepositoryProvider = Provider<FinanceRepository>(
  (ref) => FinanceRepository(ref.read(apiDioProvider)),
);

final financeOverviewProvider =
    FutureProvider.autoDispose.family<FinanceOverview, FinanceRange>(
  (ref, range) => ref.read(financeRepositoryProvider).overview(rangeWindow(range)),
);

final expenseBreakdownProvider =
    FutureProvider.autoDispose.family<ExpenseBreakdown, FinanceRange>(
  (ref, range) =>
      ref.read(financeRepositoryProvider).expenseBreakdown(rangeWindow(range)),
);

final movementsProvider =
    FutureProvider.autoDispose.family<List<Movement>, FinanceRange>(
  (ref, range) => ref.read(financeRepositoryProvider).movements(rangeWindow(range)),
);
