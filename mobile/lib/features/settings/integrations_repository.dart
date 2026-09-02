import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Estado de la conexión con Mercado Pago (backend `MpConnectionResponse`).
class MpConnection {
  const MpConnection({
    required this.connected,
    this.nickname,
    this.externalAccountId,
    this.liveMode = false,
  });

  final bool connected;
  final String? nickname;
  final String? externalAccountId;
  final bool liveMode;

  factory MpConnection.fromJson(Map<String, dynamic> j) => MpConnection(
        connected: (j['connected'] as bool?) ?? false,
        nickname: j['nickname'] as String?,
        externalAccountId: j['external_account_id'] as String?,
        liveMode: (j['live_mode'] as bool?) ?? false,
      );
}

class IntegrationsRepository {
  IntegrationsRepository(this._dio);
  final Dio _dio;

  Future<MpConnection> getMercadoPago() async {
    try {
      final res = await _dio.get<dynamic>('/integrations/mercadopago');
      return MpConnection.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<String> connectUrl() async {
    try {
      final res = await _dio.get<dynamic>('/integrations/mercadopago/connect');
      final map = Map<String, dynamic>.from(res.data as Map);
      return (map['url'] as String?) ?? '';
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<void> disconnectMercadoPago() async {
    try {
      await _dio.delete<dynamic>('/integrations/mercadopago');
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final integrationsRepositoryProvider = Provider<IntegrationsRepository>(
  (ref) => IntegrationsRepository(ref.read(apiDioProvider)),
);

final mercadoPagoConnectionProvider =
    FutureProvider.autoDispose<MpConnection>(
  (ref) => ref.read(integrationsRepositoryProvider).getMercadoPago(),
);
