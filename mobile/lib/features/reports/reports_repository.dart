import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

class RevenueSummary {
  const RevenueSummary({
    required this.currency,
    required this.salesAmount,
    required this.collectedAmount,
    required this.expenseAmount,
    required this.grossMarginAmount,
    required this.ordersCount,
    required this.averageTicketAmount,
  });

  final String currency;
  final int salesAmount;
  final int collectedAmount;
  final int expenseAmount;
  final int grossMarginAmount;
  final int ordersCount;
  final int averageTicketAmount;

  factory RevenueSummary.fromJson(Map<String, dynamic> j) => RevenueSummary(
        currency: j['currency'] as String,
        salesAmount: (j['sales_amount'] as int?) ?? 0,
        collectedAmount: (j['collected_amount'] as int?) ?? 0,
        expenseAmount: (j['expense_amount'] as int?) ?? 0,
        grossMarginAmount: (j['gross_margin_amount'] as int?) ?? 0,
        ordersCount: (j['orders_count'] as int?) ?? 0,
        averageTicketAmount: (j['average_ticket_amount'] as int?) ?? 0,
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
        productName: j['product_name'] as String,
        unitsSold: (j['units_sold'] as int?) ?? 0,
        salesAmount: (j['sales_amount'] as int?) ?? 0,
        marginAmount: (j['margin_amount'] as int?) ?? 0,
        currency: j['currency'] as String,
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
        method: j['method'] as String,
        direction: j['direction'] as String,
        amount: (j['amount'] as int?) ?? 0,
        count: (j['count'] as int?) ?? 0,
      );
}

class ReportsRepository {
  ReportsRepository(this._dio);

  final Dio _dio;

  Future<RevenueSummary> revenue() async {
    try {
      final res = await _dio.get<dynamic>('/analytics/revenue');
      return RevenueSummary.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<List<ProductPerf>> products() async {
    try {
      final res = await _dio.get<dynamic>('/analytics/products',
          queryParameters: {'limit': 10});
      return (res.data as List)
          .map((e) => ProductPerf.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<List<PaymentMixRow>> paymentMix() async {
    try {
      final res = await _dio.get<dynamic>('/analytics/payment-mix');
      return (res.data as List)
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

final revenueProvider = FutureProvider.autoDispose<RevenueSummary>(
  (ref) => ref.read(reportsRepositoryProvider).revenue(),
);

final productPerfProvider = FutureProvider.autoDispose<List<ProductPerf>>(
  (ref) => ref.read(reportsRepositoryProvider).products(),
);

final paymentMixProvider = FutureProvider.autoDispose<List<PaymentMixRow>>(
  (ref) => ref.read(reportsRepositoryProvider).paymentMix(),
);
