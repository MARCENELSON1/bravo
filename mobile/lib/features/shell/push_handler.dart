import 'dart:async';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session_notifier.dart';
import '../../data/push/push_service.dart';
import '../order/comanda_lista_sheet.dart';

/// Montaje global del push (Fase 4): registra el token del device al haber sesión
/// y, cuando el mozo toca una notificación ("Mesa lista" / "te asignaron"), abre el
/// modal de la comanda —esté como esté la app (background o cerrada)—. Complementa
/// al SSE (`ReadyAlert`), que cubre la app en primer plano. Defensivo: sin Firebase
/// configurado no hace nada.
class PushHandler extends ConsumerStatefulWidget {
  const PushHandler({super.key, required this.child});
  final Widget child;

  @override
  ConsumerState<PushHandler> createState() => _PushHandlerState();
}

class _PushHandlerState extends ConsumerState<PushHandler> {
  StreamSubscription<RemoteMessage>? _sub;

  @override
  void initState() {
    super.initState();
    _setup();
  }

  Future<void> _setup() async {
    // AppScaffold solo se monta con sesión → registramos el token del device.
    if (ref.read(sessionProvider) is SessionAuthenticated) {
      await ref.read(pushServiceProvider).start();
    }
    try {
      // Tap con la app en background.
      _sub = FirebaseMessaging.onMessageOpenedApp.listen(_onTap);
      // Tap que abrió la app desde cero (estaba terminada).
      final initial = await FirebaseMessaging.instance.getInitialMessage();
      if (initial != null) _onTap(initial);
    } catch (_) {
      // firebase_messaging no disponible → sin deep-link, la app sigue.
    }
  }

  void _onTap(RemoteMessage message) {
    if (!mounted) return;
    final target = pushTarget(message.data);
    if (target == null) return;
    ComandaListaSheet.show(
      context,
      orderId: target.orderId,
      tableNumber: target.tableNumber,
    );
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
