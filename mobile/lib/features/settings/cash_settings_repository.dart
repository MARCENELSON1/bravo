import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Política de caja (backend `CashSettingsResponse`): exigir caja abierta para
/// cobrar + arqueo ciego. OFF por default. Editable por OWNER/MANAGER.
class CashSettings {
  const CashSettings({
    required this.requireOpenCashSession,
    required this.blindCashCount,
  });

  final bool requireOpenCashSession;
  final bool blindCashCount;

  factory CashSettings.fromJson(Map<String, dynamic> j) => CashSettings(
        requireOpenCashSession: (j['require_open_cash_session'] as bool?) ?? false,
        blindCashCount: (j['blind_cash_count'] as bool?) ?? false,
      );

  CashSettings copyWith({bool? requireOpenCashSession, bool? blindCashCount}) =>
      CashSettings(
        requireOpenCashSession:
            requireOpenCashSession ?? this.requireOpenCashSession,
        blindCashCount: blindCashCount ?? this.blindCashCount,
      );
}

/// Comisión de pasarela por medio de pago (backend `FeeRateItem`). `feeBps` en
/// puntos básicos: 100 bps = 1%.
class FeeRate {
  const FeeRate({required this.method, required this.feeBps});
  final String method;
  final int feeBps;
  factory FeeRate.fromJson(Map<String, dynamic> j) => FeeRate(
        method: j['method'] as String,
        feeBps: (j['fee_bps'] as int?) ?? 0,
      );
  Map<String, dynamic> toJson() => {'method': method, 'fee_bps': feeBps};
}

class CashSettingsRepository {
  CashSettingsRepository(this._dio);
  final Dio _dio;

  Future<CashSettings> getSettings() async {
    try {
      final res = await _dio.get<dynamic>('/cashier/settings');
      return CashSettings.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<CashSettings> updateSettings(CashSettings s) async {
    try {
      final res = await _dio.put<dynamic>('/cashier/settings', data: {
        'require_open_cash_session': s.requireOpenCashSession,
        'blind_cash_count': s.blindCashCount,
      });
      return CashSettings.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<List<FeeRate>> getFeeRates() async {
    try {
      final res = await _dio.get<dynamic>('/payments/fee-rates');
      final map = Map<String, dynamic>.from(res.data as Map);
      final rates = (map['rates'] as List<dynamic>? ?? []);
      return rates
          .map((r) => FeeRate.fromJson(Map<String, dynamic>.from(r as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> updateFeeRates(List<FeeRate> rates) async {
    try {
      await _dio.put<dynamic>('/payments/fee-rates',
          data: {'rates': [for (final r in rates) r.toJson()]});
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final cashSettingsRepositoryProvider = Provider<CashSettingsRepository>(
  (ref) => CashSettingsRepository(ref.read(apiDioProvider)),
);

final cashSettingsProvider = FutureProvider.autoDispose<CashSettings>(
  (ref) => ref.read(cashSettingsRepositoryProvider).getSettings(),
);

final feeRatesProvider = FutureProvider.autoDispose<List<FeeRate>>(
  (ref) => ref.read(cashSettingsRepositoryProvider).getFeeRates(),
);
