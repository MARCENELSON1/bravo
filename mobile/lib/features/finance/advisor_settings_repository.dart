import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Config del asesor/finanzas (backend `AdvisorSettingsResponse`). Los `*_bps`
/// son puntos básicos (10000 = 100%); los `*_amount`/cost son unidades menores.
class AdvisorSettings {
  const AdvisorSettings({
    required this.monthlyLaborCost,
    required this.monthlyOtherFixedCosts,
    required this.targetFoodCostBps,
    required this.seats,
    required this.dailyOpenMinutes,
    required this.monthlyInflationBps,
    required this.defaultVatBps,
    required this.currency,
    required this.configured,
  });

  final int monthlyLaborCost;
  final int monthlyOtherFixedCosts;
  final int targetFoodCostBps;
  final int seats;
  final int dailyOpenMinutes;
  final int monthlyInflationBps;
  final int defaultVatBps;
  final String currency;
  final bool configured;

  factory AdvisorSettings.fromJson(Map<String, dynamic> j) => AdvisorSettings(
        monthlyLaborCost: (j['monthly_labor_cost'] as int?) ?? 0,
        monthlyOtherFixedCosts: (j['monthly_other_fixed_costs'] as int?) ?? 0,
        targetFoodCostBps: (j['target_food_cost_bps'] as int?) ?? 0,
        seats: (j['seats'] as int?) ?? 0,
        dailyOpenMinutes: (j['daily_open_minutes'] as int?) ?? 0,
        monthlyInflationBps: (j['monthly_inflation_bps'] as int?) ?? 0,
        defaultVatBps: (j['default_vat_bps'] as int?) ?? 0,
        currency: (j['currency'] as String?) ?? 'ARS',
        configured: (j['configured'] as bool?) ?? false,
      );
}

class AdvisorSettingsRepository {
  AdvisorSettingsRepository(this._dio);

  final Dio _dio;

  Future<AdvisorSettings> get() async {
    try {
      final res = await _dio.get<dynamic>('/advisor/settings');
      return AdvisorSettings.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> update({
    required int monthlyLaborCost,
    required int monthlyOtherFixedCosts,
    required int targetFoodCostBps,
    required int seats,
    required int dailyOpenMinutes,
    required int monthlyInflationBps,
    required int defaultVatBps,
  }) async {
    try {
      await _dio.put<dynamic>('/advisor/settings', data: {
        'monthly_labor_cost': monthlyLaborCost,
        'monthly_other_fixed_costs': monthlyOtherFixedCosts,
        'target_food_cost_bps': targetFoodCostBps,
        'seats': seats,
        'daily_open_minutes': dailyOpenMinutes,
        'monthly_inflation_bps': monthlyInflationBps,
        'default_vat_bps': defaultVatBps,
      });
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final advisorSettingsRepositoryProvider = Provider<AdvisorSettingsRepository>(
  (ref) => AdvisorSettingsRepository(ref.read(apiDioProvider)),
);

final advisorSettingsProvider = FutureProvider.autoDispose<AdvisorSettings>(
  (ref) => ref.read(advisorSettingsRepositoryProvider).get(),
);
