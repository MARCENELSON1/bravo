import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Mesa (backend `TableResponse`) para la gestión de QR.
class TableItem {
  const TableItem({
    required this.id,
    required this.number,
    required this.active,
    this.name,
  });
  final String id;
  final int number;
  final bool active;
  final String? name;
  factory TableItem.fromJson(Map<String, dynamic> j) => TableItem(
        id: j['id'] as String,
        number: (j['number'] as int?) ?? 0,
        active: (j['active'] as bool?) ?? true,
        name: j['name'] as String?,
      );
}

/// Config del autopedido (backend `SelfOrderSettingsResponse`).
class SelfOrderSettings {
  const SelfOrderSettings({
    required this.enabled,
    required this.requiresConfirmation,
    this.prepayRequired = false,
    this.mode = 'READ_ONLY',
  });
  final bool enabled;
  final bool requiresConfirmation;
  final bool prepayRequired;
  // Fase 3: READ_ONLY | SALON | SELF_SERVICE (deriva de los flags).
  final String mode;
  factory SelfOrderSettings.fromJson(Map<String, dynamic> j) =>
      SelfOrderSettings(
        enabled: (j['enabled'] as bool?) ?? false,
        requiresConfirmation: (j['requires_confirmation'] as bool?) ?? true,
        prepayRequired: (j['prepay_required'] as bool?) ?? false,
        mode: (j['mode'] as String?) ?? 'READ_ONLY',
      );
  SelfOrderSettings copyWith({
    bool? enabled,
    bool? requiresConfirmation,
    bool? prepayRequired,
    String? mode,
  }) =>
      SelfOrderSettings(
        enabled: enabled ?? this.enabled,
        requiresConfirmation: requiresConfirmation ?? this.requiresConfirmation,
        prepayRequired: prepayRequired ?? this.prepayRequired,
        mode: mode ?? this.mode,
      );
}

/// Config del pago en mesa (backend `SelfPaySettingsResponse`).
class SelfPaySettings {
  const SelfPaySettings({required this.enabled, required this.tipsEnabled});
  final bool enabled;
  final bool tipsEnabled;
  factory SelfPaySettings.fromJson(Map<String, dynamic> j) => SelfPaySettings(
        enabled: (j['enabled'] as bool?) ?? false,
        tipsEnabled: (j['tips_enabled'] as bool?) ?? true,
      );
  SelfPaySettings copyWith({bool? enabled, bool? tipsEnabled}) =>
      SelfPaySettings(
        enabled: enabled ?? this.enabled,
        tipsEnabled: tipsEnabled ?? this.tipsEnabled,
      );
}

class TableQrRepository {
  TableQrRepository(this._dio);
  final Dio _dio;

  Future<List<TableItem>> tables() async {
    try {
      final res = await _dio.get<dynamic>('/tables');
      return ((res.data as List?) ?? const [])
          .map((e) => TableItem.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<String> qrUrl(String tableId) async {
    try {
      final res = await _dio.get<dynamic>('/tables/$tableId/qr');
      final map = Map<String, dynamic>.from(res.data as Map);
      return (map['url'] as String?) ?? '';
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<SelfOrderSettings> selfOrder() async {
    try {
      final res = await _dio.get<dynamic>('/self-order/settings');
      return SelfOrderSettings.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<SelfOrderSettings> updateSelfOrder(SelfOrderSettings v) async {
    try {
      final res = await _dio.put<dynamic>('/self-order/settings', data: {
        'enabled': v.enabled,
        'requires_confirmation': v.requiresConfirmation,
      });
      return SelfOrderSettings.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Fase 3: fija el modo de la Carta QR (READ_ONLY | SALON | SELF_SERVICE); el
  /// backend deriva los flags. Autoservicio necesita además el pago en mesa.
  Future<SelfOrderSettings> updateSelfOrderMode(String mode) async {
    try {
      final res =
          await _dio.put<dynamic>('/self-order/settings', data: {'mode': mode});
      return SelfOrderSettings.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<SelfPaySettings> selfPay() async {
    try {
      final res = await _dio.get<dynamic>('/self-pay/settings');
      return SelfPaySettings.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<SelfPaySettings> updateSelfPay(SelfPaySettings v) async {
    try {
      final res = await _dio.put<dynamic>('/self-pay/settings',
          data: {'enabled': v.enabled, 'tips_enabled': v.tipsEnabled});
      return SelfPaySettings.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final tableQrRepositoryProvider = Provider<TableQrRepository>(
  (ref) => TableQrRepository(ref.read(apiDioProvider)),
);

final tablesProvider = FutureProvider.autoDispose<List<TableItem>>(
  (ref) => ref.read(tableQrRepositoryProvider).tables(),
);

final tableQrUrlProvider =
    FutureProvider.autoDispose.family<String, String>(
  (ref, tableId) => ref.read(tableQrRepositoryProvider).qrUrl(tableId),
);

final selfOrderSettingsProvider = FutureProvider.autoDispose<SelfOrderSettings>(
  (ref) => ref.read(tableQrRepositoryProvider).selfOrder(),
);

final selfPaySettingsProvider = FutureProvider.autoDispose<SelfPaySettings>(
  (ref) => ref.read(tableQrRepositoryProvider).selfPay(),
);
