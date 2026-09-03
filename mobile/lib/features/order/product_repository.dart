import 'package:dio/dio.dart';

import '../../api/dio_errors.dart';
import 'product_dtos.dart';

class ProductRepository {
  ProductRepository(this._dio);

  final Dio _dio;

  Future<List<Product>> products() async {
    try {
      final res = await _dio.get<dynamic>('/products');
      return (res.data as List)
          .map((e) => Product.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
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
