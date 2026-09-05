import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';

import '../../api/api_error.dart';
import '../../features/order/order_repository.dart';
import 'order_op.dart';
import 'sync_queue.dart';

/// Drena la cola de contingencia contra los endpoints idempotentes. Se dispara
/// al recuperar conectividad (connectivity_plus) y en el arranque. Procesa FIFO:
/// las ops que entran quedan drenadas; ante un error de red se corta y se
/// conservan las restantes; un error de negocio (4xx) descarta la op (no se
/// puede aplicar) para no trabar la cola.
class SyncService {
  SyncService({
    required this.queue,
    required this.repo,
    required this.onDrained,
  });

  final SyncQueue queue;
  final OrderRepository repo;
  final void Function() onDrained;

  final Connectivity _connectivity = Connectivity();
  StreamSubscription<List<ConnectivityResult>>? _sub;
  bool _draining = false;

  void start() {
    _sub = _connectivity.onConnectivityChanged.listen((results) {
      if (results.any((r) => r != ConnectivityResult.none)) {
        drain();
      }
    });
    drain(); // intento inicial
  }

  void dispose() {
    _sub?.cancel();
  }

  Future<void> drain() async {
    if (_draining) return;
    _draining = true;
    try {
      final ops = queue.all();
      if (ops.isEmpty) return;

      final remaining = <OrderOp>[];
      var stopped = false;
      for (final op in ops) {
        if (stopped) {
          remaining.add(op);
          continue;
        }
        try {
          await _execute(op);
        } on ApiError catch (e) {
          if (e.code == 'network_error') {
            stopped = true; // sigue sin red → conservar y reintentar luego
            remaining.add(op);
          }
          // error de negocio → descartar la op (no re-encolar)
        }
      }
      await queue.replaceAll(remaining);
      if (remaining.length != ops.length) onDrained();
    } finally {
      _draining = false;
    }
  }

  Future<void> _execute(OrderOp op) async {
    switch (op.type) {
      case OrderOpType.addItem:
        await repo.addItem(op.orderId,
            id: op.itemId!,
            productId: op.productId!,
            quantity: op.quantity!,
            note: op.note);
      case OrderOpType.setQty:
        await repo.setQuantity(op.orderId, op.itemId!, op.quantity!);
      case OrderOpType.setNote:
        await repo.setNote(op.orderId, op.itemId!, op.note);
      case OrderOpType.removeItem:
        await repo.removeItem(op.orderId, op.itemId!);
      case OrderOpType.send:
        await repo.send(op.orderId);
      case OrderOpType.transfer:
        await repo.transfer(op.orderId, op.tableId!);
      case OrderOpType.merge:
        await repo.merge(op.orderId, op.sourceOrderId!);
    }
  }
}
