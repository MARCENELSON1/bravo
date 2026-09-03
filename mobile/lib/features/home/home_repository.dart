import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';
import '../finance/finance_range.dart';
import '../reports/reports_repository.dart';

/// Resumen del dashboard (backend `DashboardSummaryResponse`).
class DashboardSummary {
  const DashboardSummary({
    required this.currency,
    required this.sales,
    required this.expenses,
    required this.net,
    required this.activeOrders,
    required this.paidOrders,
    required this.avgTicket,
    required this.collectedNet,
    required this.feesTotal,
    required this.paymentCount,
  });

  final String currency;
  final int sales;
  final int expenses;
  final int net;
  final int activeOrders;
  final int paidOrders;
  final int avgTicket;
  final int collectedNet;
  final int feesTotal;
  final int paymentCount;

  factory DashboardSummary.fromJson(Map<String, dynamic> j) => DashboardSummary(
        currency: j['currency'] as String,
        sales: (j['sales'] as int?) ?? 0,
        expenses: (j['expenses'] as int?) ?? 0,
        net: (j['net'] as int?) ?? 0,
        activeOrders: (j['active_orders'] as int?) ?? 0,
        paidOrders: (j['paid_orders'] as int?) ?? 0,
        avgTicket: (j['avg_ticket'] as int?) ?? 0,
        collectedNet: (j['collected_net'] as int?) ?? 0,
        feesTotal: (j['fees_total'] as int?) ?? 0,
        paymentCount: (j['payment_count'] as int?) ?? 0,
      );
}

/// Ventana "hoy" (desde el comienzo del día local, en UTC).
String _startOfTodayIso() {
  final now = DateTime.now();
  return DateTime(now.year, now.month, now.day).toUtc().toIso8601String();
}

/// Ventana de los últimos 7 días (incluye hoy).
RangeWindow _last7DaysWindow() {
  final now = DateTime.now();
  final from = DateTime(now.year, now.month, now.day)
      .subtract(const Duration(days: 6));
  return RangeWindow(
      from.toUtc().toIso8601String(), now.toUtc().toIso8601String());
}

class HomeRepository {
  HomeRepository(this._dio);

  final Dio _dio;

  Future<DashboardSummary> dashboard({String? from}) async {
    try {
      final res = await _dio.get<dynamic>('/reports/dashboard',
          queryParameters: from == null ? null : {'from': from});
      return DashboardSummary.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final homeRepositoryProvider = Provider<HomeRepository>(
  (ref) => HomeRepository(ref.read(apiDioProvider)),
);

/// Resumen del día (Home). El Home es "hoy" → acota a `from = comienzo del día`.
final dashboardProvider = FutureProvider.autoDispose<DashboardSummary>(
  (ref) => ref.read(homeRepositoryProvider).dashboard(from: _startOfTodayIso()),
);

/// Serie de facturación de los últimos 7 días (para el chart + hoy vs ayer).
final revenue7dProvider = FutureProvider.autoDispose<List<RevenueDailyPoint>>(
  (ref) => ref.read(reportsRepositoryProvider).revenueDaily(_last7DaysWindow()),
);
