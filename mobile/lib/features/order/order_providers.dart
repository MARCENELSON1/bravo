import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../api/api_client.dart';
import '../../api/api_error.dart';
import '../../data/offline/order_op.dart';
import '../../data/offline/sync_providers.dart';
import '../../data/offline/sync_queue.dart';
import '../../theme/theme_controller.dart';
import '../floor/floor_providers.dart';
import 'capture_logic.dart';
import 'order_dtos.dart';
import 'order_optimistic.dart';
import 'order_repository.dart';
import 'product_dtos.dart';
import 'product_repository.dart';
import 'product_usage.dart';

final productRepositoryProvider = Provider<ProductRepository>(
  (ref) => ProductRepository(ref.read(apiDioProvider)),
);

final productsProvider = FutureProvider.autoDispose<List<Product>>(
  (ref) => ref.read(productRepositoryProvider).products(),
);

final productUsageProvider = Provider<ProductUsage>(
  (ref) => ProductUsage(ref.read(sharedPreferencesProvider)),
);

/// Controlador de una comanda: captura optimista con UUID de cliente + reconcilia
/// con la orden autoritativa que devuelve cada endpoint (OrderResponse). Serializa
/// las mutaciones para evitar carreras entre taps rápidos.
class OrderController extends AutoDisposeFamilyAsyncNotifier<Order, String> {
  Future<void> _lock = Future<void>.value();

  @override
  Future<Order> build(String arg) => ref.read(orderRepositoryProvider).get(arg);

  OrderRepository get _repo => ref.read(orderRepositoryProvider);
  SyncQueue get _queue => ref.read(syncQueueProvider);
  Order get _current => state.value!;

  Future<void> _serialized(Future<void> Function() action) {
    final completer = Completer<void>();
    _lock = _lock.then((_) async {
      try {
        await action();
        completer.complete();
      } catch (e, st) {
        completer.completeError(e, st);
      }
    });
    return completer.future;
  }

  /// `optionIds` = modificadores elegidos. Se manda SIEMPRE la lista (aunque
  /// vacía): así el server valida los grupos obligatorios contra la carta.
  Future<void> addProduct(
    Product p,
    int qty, {
    String? note,
    List<String> optionIds = const [],
  }) async {
    final itemId = const Uuid().v4();
    state = AsyncData(
      applyAdd(
        _current,
        p,
        qty,
        itemId,
        note: note,
        options: snapshotOptions(p, optionIds),
      ),
    );
    await ref.read(productUsageProvider).bump(p.id);
    await _serialized(() async {
      try {
        state = AsyncData(
          await _repo.addItem(
            arg,
            id: itemId,
            productId: p.id,
            quantity: qty,
            note: note,
            optionIds: optionIds,
          ),
        );
      } on ApiError catch (e) {
        if (e.code == 'network_error') {
          await _queue.enqueue(
            OrderOp.addItem(
              orderId: arg,
              itemId: itemId,
              productId: p.id,
              quantity: qty,
              note: note,
              optionIds: optionIds,
            ),
          );
          // se mantiene el estado optimista; se drena al reconectar
        } else {
          state = AsyncData(await _repo.get(arg));
          rethrow;
        }
      }
    });
  }

  Future<void> setQty(String itemId, int qty) async {
    if (qty < 1) return;
    state = AsyncData(applyQty(_current, itemId, qty));
    await _serialized(() async {
      try {
        state = AsyncData(await _repo.setQuantity(arg, itemId, qty));
      } on ApiError catch (e) {
        if (e.code == 'network_error') {
          await _queue.enqueue(
            OrderOp.setQty(orderId: arg, itemId: itemId, quantity: qty),
          );
        } else {
          state = AsyncData(await _repo.get(arg));
          rethrow;
        }
      }
    });
  }

  Future<void> setNote(String itemId, String? note) async {
    state = AsyncData(applyNote(_current, itemId, note));
    await _serialized(() async {
      try {
        state = AsyncData(await _repo.setNote(arg, itemId, note));
      } on ApiError catch (e) {
        if (e.code == 'network_error') {
          await _queue.enqueue(
            OrderOp.setNote(orderId: arg, itemId: itemId, note: note),
          );
        } else {
          state = AsyncData(await _repo.get(arg));
          rethrow;
        }
      }
    });
  }

  Future<void> removeItem(String itemId) async {
    state = AsyncData(applyRemove(_current, itemId));
    await _serialized(() async {
      try {
        state = AsyncData(await _repo.removeItem(arg, itemId));
      } on ApiError catch (e) {
        if (e.code == 'network_error') {
          await _queue.enqueue(
            OrderOp.removeItem(orderId: arg, itemId: itemId),
          );
        } else {
          state = AsyncData(await _repo.get(arg));
          rethrow;
        }
      }
    });
  }

  Future<void> send() => _serialized(() async {
    try {
      state = AsyncData(await _repo.send(arg));
    } on ApiError catch (e) {
      if (e.code == 'network_error') {
        await _queue.enqueue(OrderOp.send(orderId: arg));
      } else {
        rethrow;
      }
    }
  });

  /// Marca la comanda como servida (READY → SERVED). Sin cola offline: servir es
  /// un gesto en mano, con la mesa delante — si no hay red, se avisa y se reintenta.
  Future<void> served() => _serialized(() async {
    state = AsyncData(await _repo.markServed(arg));
  });

  // Cursos: gestos en mano con la mesa delante → sin cola offline (como
  // `served`): si no hay red se avisa y se reintenta.
  Future<void> fireNext() => _serialized(() async {
    state = AsyncData(await _repo.fireNext(arg));
  });

  Future<void> fireAll() => _serialized(() async {
    state = AsyncData(await _repo.fireAll(arg));
  });

  Future<void> serveCourse(Course course) => _serialized(() async {
    state = AsyncData(await _repo.advanceCourse(arg, course, 'served'));
  });

  Future<void> setCourse(String itemId, Course course) => _serialized(() async {
    state = AsyncData(await _repo.setCourse(arg, itemId, course));
  });

  Future<void> transfer(String tableId) => _serialized(() async {
    try {
      state = AsyncData(await _repo.transfer(arg, tableId));
    } on ApiError catch (e) {
      if (e.code == 'network_error') {
        await _queue.enqueue(OrderOp.transfer(orderId: arg, tableId: tableId));
      } else {
        rethrow;
      }
    }
  });

  Future<void> merge(String sourceOrderId) => _serialized(() async {
    try {
      state = AsyncData(await _repo.merge(arg, sourceOrderId));
    } on ApiError catch (e) {
      if (e.code == 'network_error') {
        await _queue.enqueue(
          OrderOp.merge(orderId: arg, sourceOrderId: sourceOrderId),
        );
      } else {
        rethrow;
      }
    }
  });
}

final orderControllerProvider = AsyncNotifierProvider.autoDispose
    .family<OrderController, Order, String>(OrderController.new);
