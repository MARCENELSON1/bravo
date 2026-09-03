import 'dart:io' show Platform;

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'device_repository.dart';

/// Objetivo del deep-link de un push (Fase 4): qué modal abrir cuando el mozo
/// toca la notificación. Función pura (testeable). Devuelve null si no aplica.
({String orderId, int? tableNumber})? pushTarget(Map<String, dynamic> data) {
  final kind = data['kind'];
  if (kind != 'order.ready' && kind != 'table.assigned') return null;
  final orderId = data['order_id'] as String?;
  if (orderId == null || orderId.isEmpty) return null;
  return (
    orderId: orderId,
    tableNumber: int.tryParse('${data['table_number'] ?? ''}'),
  );
}

/// Setup de push (Fase 4): pide permiso, obtiene el FCM token y lo registra en el
/// backend; re-registra ante refresh. Aislado y defensivo — un fallo de push nunca
/// rompe la app (sin Firebase configurado, queda inerte).
class PushService {
  PushService(this._ref);
  final Ref _ref;
  bool _started = false;

  Future<void> start() async {
    if (_started) return;
    _started = true;
    try {
      final messaging = FirebaseMessaging.instance;
      await messaging.requestPermission();
      final token = await messaging.getToken();
      if (token != null) await _register(token);
      messaging.onTokenRefresh.listen(_register);
    } catch (_) {
      // Sin Firebase configurado / permiso denegado → push inerte, la app sigue.
    }
  }

  Future<void> _register(String token) async {
    try {
      await _ref
          .read(deviceRepositoryProvider)
          .register(token, Platform.isIOS ? 'ios' : 'android');
    } catch (_) {
      // El registro puede fallar (offline); se reintenta en el próximo arranque.
    }
  }
}

final pushServiceProvider = Provider<PushService>((ref) => PushService(ref));
