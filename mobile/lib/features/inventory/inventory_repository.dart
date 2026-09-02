import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Insumo (backend `IngredientResponse`).
class Ingredient {
  const Ingredient({
    required this.id,
    required this.name,
    required this.unit,
    required this.stockQty,
    required this.minQty,
    required this.unitCostAmount,
    required this.currency,
    required this.isBelowMin,
    required this.active,
  });

  final String id;
  final String name;
  final String unit;
  final int stockQty;
  final int minQty;
  final int unitCostAmount;
  final String currency;
  final bool isBelowMin;
  final bool active;

  factory Ingredient.fromJson(Map<String, dynamic> j) => Ingredient(
        id: j['id'] as String,
        name: j['name'] as String,
        unit: j['unit'] as String,
        stockQty: (j['stock_qty'] as int?) ?? 0,
        minQty: (j['min_qty'] as int?) ?? 0,
        unitCostAmount: (j['unit_cost_amount'] as int?) ?? 0,
        currency: j['currency'] as String,
        isBelowMin: (j['is_below_min'] as bool?) ?? false,
        active: (j['active'] as bool?) ?? true,
      );
}

class InventoryRepository {
  InventoryRepository(this._dio);

  final Dio _dio;

  Future<List<Ingredient>> ingredients() async {
    try {
      final res = await _dio.get<dynamic>('/inventory/ingredients');
      return (res.data as List)
          .map((e) => Ingredient.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Registra una compra: suma `qty` al stock con su costo unitario.
  Future<void> purchase(
    String ingredientId, {
    required int qty,
    required int unitCostAmount,
  }) async {
    try {
      await _dio.post<dynamic>(
        '/inventory/ingredients/$ingredientId/purchase',
        data: {'qty': qty, 'unit_cost_amount': unitCostAmount},
      );
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Registra una merma: descuenta `qty` del stock.
  Future<void> waste(String ingredientId, {required int qty, String? note}) async {
    try {
      await _dio.post<dynamic>(
        '/inventory/ingredients/$ingredientId/waste',
        data: {'qty': qty, 'note': ?note},
      );
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final inventoryRepositoryProvider = Provider<InventoryRepository>(
  (ref) => InventoryRepository(ref.read(apiDioProvider)),
);

final ingredientsProvider = FutureProvider.autoDispose<List<Ingredient>>(
  (ref) => ref.read(inventoryRepositoryProvider).ingredients(),
);
