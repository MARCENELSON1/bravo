import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Un plan de Wellnod (backend `PlanResponse`).
class BillingPlan {
  const BillingPlan({
    required this.id,
    required this.tier,
    required this.amount,
    required this.currency,
    required this.interval,
    required this.features,
  });
  final String id;
  final String tier;
  final int amount;
  final String currency;
  final String interval; // MONTH | YEAR
  final List<String> features;
  factory BillingPlan.fromJson(Map<String, dynamic> j) => BillingPlan(
        id: j['id'] as String,
        tier: (j['tier'] as String?) ?? '',
        amount: (j['amount'] as int?) ?? 0,
        currency: (j['currency'] as String?) ?? 'ARS',
        interval: (j['interval'] as String?) ?? 'MONTH',
        features: ((j['features'] as List?) ?? const [])
            .map((e) => e.toString())
            .toList(),
      );
}

/// Suscripción actual (backend `SubscriptionResponse`).
class Subscription {
  const Subscription({
    required this.status,
    required this.grantsAccess,
    this.currentPeriodEnd,
  });
  final String status;
  final bool grantsAccess;
  final String? currentPeriodEnd;
  factory Subscription.fromJson(Map<String, dynamic> j) => Subscription(
        status: (j['status'] as String?) ?? '',
        grantsAccess: (j['grants_access'] as bool?) ?? false,
        currentPeriodEnd: j['current_period_end'] as String?,
      );
}

class BillingRepository {
  BillingRepository(this._dio);
  final Dio _dio;

  Future<List<BillingPlan>> plans(String region) async {
    try {
      final res = await _dio.get<dynamic>('/billing/plans',
          queryParameters: {'region': region});
      return ((res.data as List?) ?? const [])
          .map((e) => BillingPlan.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Subscription?> subscription() async {
    try {
      final res = await _dio.get<dynamic>('/billing/subscription');
      if (res.data == null) return null;
      return Subscription.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<String> checkout(String planId) async {
    try {
      final res = await _dio
          .post<dynamic>('/billing/checkout', data: {'plan_id': planId});
      final map = Map<String, dynamic>.from(res.data as Map);
      return (map['url'] as String?) ?? '';
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> cancel() async {
    try {
      await _dio.delete<dynamic>('/billing/subscription');
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final billingRepositoryProvider = Provider<BillingRepository>(
  (ref) => BillingRepository(ref.read(apiDioProvider)),
);

final subscriptionProvider = FutureProvider.autoDispose<Subscription?>(
  (ref) => ref.read(billingRepositoryProvider).subscription(),
);

final billingPlansProvider =
    FutureProvider.autoDispose.family<List<BillingPlan>, String>(
  (ref, region) => ref.read(billingRepositoryProvider).plans(region),
);
