import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import 'product_dtos.dart';

/// Ranking de productos por uso (espeja `frontend/src/lib/product-usage.ts`):
/// los más pedidos aparecen primero en la grilla. Se guarda en shared_preferences.
class ProductUsage {
  ProductUsage(this._prefs);

  final SharedPreferences _prefs;
  static const _key = 'wellnod:product_usage';

  Map<String, int> _load() {
    final raw = _prefs.getString(_key);
    if (raw == null) return {};
    try {
      final map = jsonDecode(raw) as Map;
      return map.map((k, v) => MapEntry(k as String, (v as num).toInt()));
    } catch (_) {
      return {};
    }
  }

  Future<void> bump(String productId) async {
    final map = _load();
    map[productId] = (map[productId] ?? 0) + 1;
    await _prefs.setString(_key, jsonEncode(map));
  }

  /// Orden estable: primero por uso desc, manteniendo el orden original ante empate.
  List<Product> rank(List<Product> products) {
    final usage = _load();
    final indexed = products.asMap().entries.toList();
    indexed.sort((a, b) {
      final byUse = (usage[b.value.id] ?? 0).compareTo(usage[a.value.id] ?? 0);
      return byUse != 0 ? byUse : a.key.compareTo(b.key);
    });
    return indexed.map((e) => e.value).toList();
  }
}
