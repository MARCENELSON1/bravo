import 'package:dio/dio.dart';

import '../../api/dio_errors.dart';
import 'product_dtos.dart';

class ProductRepository {
  ProductRepository(this._dio);

  final Dio _dio;

  /// Catálogo + grupos de modificadores de todos los productos, en paralelo y
  /// unidos acá: la grilla de captura los necesita al instante al tocar.
  Future<List<Product>> products() async {
    try {
      final results = await Future.wait([
        _dio.get<dynamic>('/products'),
        _dio.get<dynamic>('/products/modifiers'),
      ]);
      final groupsByProduct = <String, List<ModifierGroup>>{
        for (final e in (results[1].data as List? ?? const []))
          (e as Map)['product_id']
              as String: ((e['groups'] as List?) ?? const [])
              .map(
                (g) =>
                    ModifierGroup.fromJson(Map<String, dynamic>.from(g as Map)),
              )
              .toList(),
      };
      return (results[0].data as List).map((e) {
        final p = Product.fromJson(Map<String, dynamic>.from(e as Map));
        final groups = groupsByProduct[p.id];
        return groups == null ? p : p.withModifierGroups(groups);
      }).toList();
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Marca un producto disponible/no-disponible hoy ("86").
  Future<void> setAvailability(String productId, bool availableToday) async {
    try {
      await _dio.put<dynamic>(
        '/products/$productId/availability',
        data: {'available_today': availableToday},
      );
    } catch (e) {
      throw toApiError(e);
    }
  }

  /// Cambia el precio del producto (`price_amount` en unidades menores).
  Future<void> updatePrice(String productId, int priceAmount) async {
    try {
      await _dio.put<dynamic>(
        '/products/$productId/price',
        data: {'price_amount': priceAmount},
      );
    } catch (e) {
      throw toApiError(e);
    }
  }
}
