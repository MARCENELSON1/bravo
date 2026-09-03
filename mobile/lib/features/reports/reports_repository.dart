import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';
import '../finance/finance_range.dart';

/// Resumen del período (backend `DashboardSummaryResponse`, `/reports/dashboard`).
class ReportSummary {
  const ReportSummary({
    required this.currency,
    required this.sales,
    required this.collectedNet,
    required this.expenses,
    required this.avgTicket,
    required this.paidOrders,
  });
  final String currency;
  final int sales;
  final int collectedNet;
  final int expenses;
  final int avgTicket;
  final int paidOrders;
  int get profit => collectedNet - expenses;
  factory ReportSummary.fromJson(Map<String, dynamic> j) => ReportSummary(
        currency: (j['currency'] as String?) ?? 'ARS',
        sales: (j['sales'] as int?) ?? 0,
        collectedNet: (j['collected_net'] as int?) ?? 0,
        expenses: (j['expenses'] as int?) ?? 0,
        avgTicket: (j['avg_ticket'] as int?) ?? 0,
        paidOrders: (j['paid_orders'] as int?) ?? 0,
      );
}

/// Un día de ventas (backend `RevenueDailyPointResponse`).
class RevenueDailyPoint {
  const RevenueDailyPoint(
      {required this.day, required this.salesAmount, required this.ordersCount});
  final String day;
  final int salesAmount;
  final int ordersCount;
  factory RevenueDailyPoint.fromJson(Map<String, dynamic> j) => RevenueDailyPoint(
        day: (j['day'] as String?) ?? '',
        salesAmount: (j['sales_amount'] as int?) ?? 0,
        ordersCount: (j['orders_count'] as int?) ?? 0,
      );
}

class ProductPerf {
  const ProductPerf({
    required this.productName,
    required this.unitsSold,
    required this.salesAmount,
    required this.marginAmount,
    required this.currency,
  });

  final String productName;
  final int unitsSold;
  final int salesAmount;
  final int marginAmount;
  final String currency;

  factory ProductPerf.fromJson(Map<String, dynamic> j) => ProductPerf(
        productName: (j['product_name'] as String?) ?? '',
        unitsSold: (j['units_sold'] as int?) ?? 0,
        salesAmount: (j['sales_amount'] as int?) ?? 0,
        marginAmount: (j['margin_amount'] as int?) ?? 0,
        currency: (j['currency'] as String?) ?? 'ARS',
      );
}

class PaymentMixRow {
  const PaymentMixRow({
    required this.method,
    required this.direction,
    required this.amount,
    required this.count,
  });

  final String method;
  final String direction;
  final int amount;
  final int count;

  factory PaymentMixRow.fromJson(Map<String, dynamic> j) => PaymentMixRow(
        method: (j['method'] as String?) ?? '',
        direction: (j['direction'] as String?) ?? '',
        amount: (j['amount'] as int?) ?? 0,
        count: (j['count'] as int?) ?? 0,
      );
}

class ReportsRepository {
  ReportsRepository(this._dio);
  final Dio _dio;

  Map<String, dynamic> _win(RangeWindow w) => {'from': w.from, 'to': w.to};

  Future<ReportSummary> summary(RangeWindow w) async {
    try {
      final res =
          await _dio.get<dynamic>('/reports/dashboard', queryParameters: _win(w));
      return ReportSummary.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<List<RevenueDailyPoint>> revenueDaily(RangeWindow w) async {
    try {
      final res = await _dio.get<dynamic>('/analytics/revenue/daily',
          queryParameters: _win(w));
      return ((res.data as List?) ?? const [])
          .map((e) => RevenueDailyPoint.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<List<ProductPerf>> products(RangeWindow w) async {
    try {
      final res = await _dio.get<dynamic>('/analytics/products',
          queryParameters: {..._win(w), 'limit': 10});
      return ((res.data as List?) ?? const [])
          .map((e) => ProductPerf.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<List<PaymentMixRow>> paymentMix(RangeWindow w) async {
    try {
      final res = await _dio.get<dynamic>('/analytics/payment-mix',
          queryParameters: _win(w));
      return ((res.data as List?) ?? const [])
          .map((e) => PaymentMixRow.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final reportsRepositoryProvider = Provider<ReportsRepository>(
  (ref) => ReportsRepository(ref.read(apiDioProvider)),
);

final reportSummaryProvider =
    FutureProvider.autoDispose.family<ReportSummary, FinanceRange>(
  (ref, range) => ref.read(reportsRepositoryProvider).summary(rangeWindow(range)),
);

final revenueDailyProvider =
    FutureProvider.autoDispose.family<List<RevenueDailyPoint>, FinanceRange>(
  (ref, range) =>
      ref.read(reportsRepositoryProvider).revenueDaily(rangeWindow(range)),
);

final productPerfProvider =
    FutureProvider.autoDispose.family<List<ProductPerf>, FinanceRange>(
  (ref, range) => ref.read(reportsRepositoryProvider).products(rangeWindow(range)),
);

final paymentMixProvider =
    FutureProvider.autoDispose.family<List<PaymentMixRow>, FinanceRange>(
  (ref, range) => ref.read(reportsRepositoryProvider).paymentMix(rangeWindow(range)),
);
