import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Datos fiscales del local (backend `FiscalSettingsResponse`). `country`,
/// `currency`, `tax_regime`, `tax_engine` son de solo lectura (los define el
/// spine de país); la dirección es editable.
class FiscalSettings {
  const FiscalSettings({
    required this.country,
    required this.currency,
    required this.taxRegime,
    required this.taxEngine,
    this.street,
    this.city,
    this.state,
    this.zip,
  });

  final String country;
  final String currency;
  final String taxRegime;
  final String taxEngine;
  final String? street;
  final String? city;
  final String? state;
  final String? zip;

  factory FiscalSettings.fromJson(Map<String, dynamic> j) => FiscalSettings(
        country: (j['country'] as String?) ?? '',
        currency: (j['currency'] as String?) ?? '',
        taxRegime: (j['tax_regime'] as String?) ?? '',
        taxEngine: (j['tax_engine'] as String?) ?? '',
        street: j['street'] as String?,
        city: j['city'] as String?,
        state: j['state'] as String?,
        zip: j['zip'] as String?,
      );
}

class FiscalRepository {
  FiscalRepository(this._dio);
  final Dio _dio;

  Future<FiscalSettings> get() async {
    try {
      final res = await _dio.get<dynamic>('/tenants/fiscal-settings');
      return FiscalSettings.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<FiscalSettings> updateAddress({
    String? street,
    String? city,
    String? state,
    String? zip,
  }) async {
    try {
      final res = await _dio.put<dynamic>('/tenants/fiscal-address', data: {
        'street': street,
        'city': city,
        'state': state,
        'zip': zip,
      });
      return FiscalSettings.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final fiscalRepositoryProvider = Provider<FiscalRepository>(
  (ref) => FiscalRepository(ref.read(apiDioProvider)),
);

final fiscalSettingsProvider = FutureProvider.autoDispose<FiscalSettings>(
  (ref) => ref.read(fiscalRepositoryProvider).get(),
);
