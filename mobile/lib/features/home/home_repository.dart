import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

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
  });

  final String currency;
  final int sales;
  final int expenses;
  final int net;
  final int activeOrders;
  final int paidOrders;
  final int avgTicket;
  final int collectedNet;

  factory DashboardSummary.fromJson(Map<String, dynamic> j) => DashboardSummary(
        currency: j['currency'] as String,
        sales: (j['sales'] as int?) ?? 0,
        expenses: (j['expenses'] as int?) ?? 0,
        net: (j['net'] as int?) ?? 0,
        activeOrders: (j['active_orders'] as int?) ?? 0,
        paidOrders: (j['paid_orders'] as int?) ?? 0,
        avgTicket: (j['avg_ticket'] as int?) ?? 0,
        collectedNet: (j['collected_net'] as int?) ?? 0,
      );
}

class HomeRepository {
  HomeRepository(this._dio);

  final Dio _dio;

  Future<DashboardSummary> dashboard() async {
    try {
      final res = await _dio.get<dynamic>('/reports/dashboard');
      return DashboardSummary.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final homeRepositoryProvider = Provider<HomeRepository>(
  (ref) => HomeRepository(ref.read(apiDioProvider)),
);

final dashboardProvider = FutureProvider.autoDispose<DashboardSummary>(
  (ref) => ref.read(homeRepositoryProvider).dashboard(),
);
