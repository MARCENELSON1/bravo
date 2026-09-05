import 'order_dtos.dart';
import 'product_dtos.dart';

/// Lógica pura de la grilla de captura (sin widgets, testeable).

const _diacritics = {
  'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u',
  'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
  'ñ': 'n', 'ç': 'c',
};

/// Minúsculas y sin tildes: "mila" encuentra "Milanesa" y "napo" a
/// "napolitana" aunque el mozo tipee sin acentos ni mayúsculas.
String normalizeText(String s) {
  final sb = StringBuffer();
  for (final r in s.toLowerCase().runes) {
    final ch = String.fromCharCode(r);
    sb.write(_diacritics[ch] ?? ch);
  }
  return sb.toString().trim();
}

/// Categorías distintas, en el orden en que aparecen en la carta.
List<String> categoriesOf(List<Product> products) {
  final seen = <String>{};
  final out = <String>[];
  for (final p in products) {
    final c = p.category;
    if (c != null && c.isNotEmpty && seen.add(c)) out.add(c);
  }
  return out;
}

/// Filtra por categoría (null = todas) o por búsqueda normalizada sobre nombre
/// y categoría. La búsqueda manda: si hay texto, busca en toda la carta e
/// ignora la pestaña elegida (el mozo que tipea quiere encontrar, no navegar).
List<Product> filterProducts(
  List<Product> products, {
  String? category,
  String query = '',
}) {
  final q = normalizeText(query);
  if (q.isNotEmpty) {
    return products
        .where((p) =>
            normalizeText(p.name).contains(q) ||
            (p.category != null && normalizeText(p.category!).contains(q)))
        .toList();
  }
  if (category == null) return products;
  return products.where((p) => p.category == category).toList();
}

/// Cantidad de ese producto todavía PENDING en la comanda (lo que se está
/// armando ahora): alimenta el badge de la grilla. Lo ya marchado no cuenta.
int pendingQtyOf(Order order, String productId) => order.items
    .where((i) => i.status.isPending && i.productId == productId)
    .fold(0, (a, i) => a + i.quantity);
