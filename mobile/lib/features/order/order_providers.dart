import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../api/api_client.dart';
import '../../theme/theme_controller.dart';
import '../floor/floor_providers.dart';
import 'order_dtos.dart';
import 'order_optimistic.dart';
import 'order_repository.dart';
import 'product_dtos.dart';
import 'product_repository.dart';
import 'product_usage.dart';

final productRepositoryProvider = Provider<ProductRepository>(
  (ref) => ProductRepository(ref.read(apiDioProvider)),
);

final productsProvider = FutureProvider<List<Product>>(
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

  Future<void> addProduct(Product p, int qty) async {
    final itemId = const Uuid().v4();
    state = AsyncData(applyAdd(_current, p, qty, itemId));
    await ref.read(productUsageProvider).bump(p.id);
    await _serialized(() async {
      try {
        state = AsyncData(
          await _repo.addItem(arg, id: itemId, productId: p.id, quantity: qty),
        );
      } catch (e) {
        state = AsyncData(await _repo.get(arg));
        rethrow;
      }
    });
  }

  Future<void> setQty(String itemId, int qty) async {
    if (qty < 1) return;
    state = AsyncData(applyQty(_current, itemId, qty));
    await _serialized(() async {
      try {
        state = AsyncData(await _repo.setQuantity(arg, itemId, qty));
      } catch (e) {
        state = AsyncData(await _repo.get(arg));
        rethrow;
      }
    });
  }

  Future<void> removeItem(String itemId) async {
    state = AsyncData(applyRemove(_current, itemId));
    await _serialized(() async {
      try {
        state = AsyncData(await _repo.removeItem(arg, itemId));
      } catch (e) {
        state = AsyncData(await _repo.get(arg));
        rethrow;
      }
    });
  }

  Future<void> send() => _serialized(() async {
        state = AsyncData(await _repo.send(arg));
      });

  Future<void> transfer(String tableId) => _serialized(() async {
        state = AsyncData(await _repo.transfer(arg, tableId));
      });

  Future<void> merge(String sourceOrderId) => _serialized(() async {
        state = AsyncData(await _repo.merge(arg, sourceOrderId));
      });
}

final orderControllerProvider =
    AsyncNotifierProvider.autoDispose.family<OrderController, Order, String>(
  OrderController.new,
);
