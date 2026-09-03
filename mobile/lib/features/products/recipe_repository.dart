import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';

/// Una línea de receta (backend `RecipeItemSchema`): un insumo o una preparación
/// con su cantidad.
class RecipeItem {
  const RecipeItem({required this.qty, this.ingredientId, this.preparationId});

  final int qty;
  final String? ingredientId;
  final String? preparationId;

  bool get isPreparation => preparationId != null;

  Map<String, dynamic> toJson() => {
        'ingredient_id': ?ingredientId,
        'preparation_id': ?preparationId,
        'qty': qty,
      };

  factory RecipeItem.fromJson(Map<String, dynamic> j) => RecipeItem(
        qty: (j['qty'] as int?) ?? 0,
        ingredientId: j['ingredient_id'] as String?,
        preparationId: j['preparation_id'] as String?,
      );
}

/// Receta de un producto (backend `RecipeResponse`).
class Recipe {
  const Recipe({
    required this.productId,
    required this.hasRecipe,
    required this.items,
  });

  final String productId;
  final bool hasRecipe;
  final List<RecipeItem> items;

  factory Recipe.fromJson(Map<String, dynamic> j) => Recipe(
        productId: j['product_id'] as String,
        hasRecipe: (j['has_recipe'] as bool?) ?? false,
        items: ((j['items'] as List?) ?? const [])
            .map((e) => RecipeItem.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList(),
      );
}

class RecipeRepository {
  RecipeRepository(this._dio);

  final Dio _dio;

  Future<Recipe> get(String productId) async {
    try {
      final res = await _dio.get<dynamic>('/products/$productId/recipe');
      return Recipe.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }

  Future<Recipe> set(String productId, List<RecipeItem> items) async {
    try {
      final res = await _dio.put<dynamic>(
        '/products/$productId/recipe',
        data: {'items': items.map((i) => i.toJson()).toList()},
      );
      return Recipe.fromJson(Map<String, dynamic>.from(res.data as Map));
    } catch (e) {
      throw toApiError(e);
    }
  }
}

final recipeRepositoryProvider = Provider<RecipeRepository>(
  (ref) => RecipeRepository(ref.read(apiDioProvider)),
);

final recipeProvider =
    FutureProvider.autoDispose.family<Recipe, String>(
  (ref, productId) => ref.read(recipeRepositoryProvider).get(productId),
);
