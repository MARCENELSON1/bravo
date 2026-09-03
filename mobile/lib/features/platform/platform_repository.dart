import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Feature del catálogo (backend `FeatureResponse`).
class PlatformFeature {
  const PlatformFeature({required this.key, required this.label});
  final String key;
  final String label;
  factory PlatformFeature.fromJson(Map<String, dynamic> j) => PlatformFeature(
        key: (j['key'] as String?) ?? '',
        label: (j['label'] as String?) ?? '',
      );
}

/// Plan del catálogo global (backend `PlatformPlanResponse`).
class PlatformPlan {
  const PlatformPlan({
    required this.id,
    required this.tier,
    required this.region,
    required this.amount,
    required this.currency,
    required this.interval,
    required this.features,
    required this.active,
  });
  final String id;
  final String tier;
  final String region;
  final int amount;
  final String currency;
  final String interval;
  final List<String> features;
  final bool active;
  factory PlatformPlan.fromJson(Map<String, dynamic> j) => PlatformPlan(
        id: (j['id'] as String?) ?? '',
        tier: (j['tier'] as String?) ?? '',
        region: (j['region'] as String?) ?? '',
        amount: (j['amount'] as int?) ?? 0,
        currency: (j['currency'] as String?) ?? 'USD',
        interval: (j['interval'] as String?) ?? 'MONTH',
        features: ((j['features'] as List?) ?? const [])
            .map((e) => e.toString())
            .toList(),
        active: (j['active'] as bool?) ?? true,
      );
}

class PlatformRepository {
  PlatformRepository(this._dio);
  final Dio _dio;

  Future<bool> access() async {
    try {
      final res = await _dio.get<dynamic>('/platform/access');
      final map = Map<String, dynamic>.from(res.data as Map);
      return (map['platform_admin'] as bool?) ?? false;
    } catch (_) {
      return false; // 403/no-admin → sin acceso
    }
  }

  Future<List<PlatformFeature>> features() async {
    try {
      final res = await _dio.get<dynamic>('/platform/features');
      return ((res.data as List?) ?? const [])
          .map((e) => PlatformFeature.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<List<PlatformPlan>> plans() async {
    try {
      final res = await _dio.get<dynamic>('/platform/plans');
      return ((res.data as List?) ?? const [])
          .map((e) => PlatformPlan.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> savePlan({
    String? id,
    required String tier,
    required String region,
    required int amount,
    required String currency,
    required String interval,
    required List<String> features,
    required bool active,
  }) async {
    try {
      await _dio.post<dynamic>('/platform/plans', data: {
        'id': id,
        'tier': tier,
        'region': region,
        'amount': amount,
        'currency': currency,
        'interval': interval,
        'features': features,
        'active': active,
      });
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> deletePlan(String id) async {
    try {
      await _dio.delete<dynamic>('/platform/plans/$id');
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final platformRepositoryProvider = Provider<PlatformRepository>(
  (ref) => PlatformRepository(ref.read(apiDioProvider)),
);

final platformAccessProvider = FutureProvider.autoDispose<bool>(
  (ref) => ref.read(platformRepositoryProvider).access(),
);

final platformFeaturesProvider =
    FutureProvider.autoDispose<List<PlatformFeature>>(
  (ref) => ref.read(platformRepositoryProvider).features(),
);

final platformPlansProvider = FutureProvider.autoDispose<List<PlatformPlan>>(
  (ref) => ref.read(platformRepositoryProvider).plans(),
);
