import 'order_dtos.dart';
import 'product_dtos.dart';

/// Lógica pura de la grilla de captura (sin widgets, testeable).

const _diacritics = {
  'á': 'a',
  'é': 'e',
  'í': 'i',
  'ó': 'o',
  'ú': 'u',
  'ü': 'u',
  'à': 'a',
  'è': 'e',
  'ì': 'i',
  'ò': 'o',
  'ù': 'u',
  'ñ': 'n',
  'ç': 'c',
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

/// Categorías distintas, en el orden en que aparecen en la carta. Se unifican
/// sin distinguir mayúsculas ni tildes ("CAFÉ" y "Café" son una sola pestaña;
/// gana el nombre que aparece primero).
List<String> categoriesOf(List<Product> products) {
  final seen = <String>{};
  final out = <String>[];
  for (final p in products) {
    final c = p.category;
    if (c != null && c.isNotEmpty && seen.add(normalizeText(c))) out.add(c);
  }
  return out;
}

bool sameCategory(String? a, String? b) =>
    a != null && b != null && normalizeText(a) == normalizeText(b);

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
        .where(
          (p) =>
              normalizeText(p.name).contains(q) ||
              (p.category != null && normalizeText(p.category!).contains(q)),
        )
        .toList();
  }
  if (category == null) return products;
  return products.where((p) => sameCategory(p.category, category)).toList();
}

/// Cantidad de ese producto todavía PENDING en la comanda (lo que se está
/// armando ahora): alimenta el badge de la grilla. Lo ya marchado no cuenta.
int pendingQtyOf(Order order, String productId) => order.items
    .where((i) => i.status.isPending && i.productId == productId)
    .fold(0, (a, i) => a + i.quantity);

/// Suma de `priceDelta` de las opciones elegidas (para el precio optimista;
/// el server pliega el mismo delta en `unit_price`).
int optionsDelta(Product p, List<String> optionIds) {
  final chosen = optionIds.toSet();
  var delta = 0;
  for (final g in p.modifierGroups) {
    for (final o in g.options) {
      if (chosen.contains(o.id)) delta += o.priceDelta;
    }
  }
  return delta;
}

/// Regla min/max de cada grupo (espeja `select_options` del backend): un grupo
/// obligatorio sin elegir, o más opciones que `maxSelect`, invalidan.
bool selectionValid(Product p, List<String> optionIds) {
  final chosen = optionIds.toSet();
  for (final g in p.modifierGroups) {
    final n = g.options.where((o) => chosen.contains(o.id)).length;
    if (n < g.minSelect || n > g.maxSelect) return false;
  }
  return true;
}

/// Snapshot (nombre + delta) de las opciones elegidas, para pintar la línea
/// optimista igual que la va a devolver el server.
List<SelectedOption> snapshotOptions(Product p, List<String> optionIds) {
  final chosen = optionIds.toSet();
  return [
    for (final g in p.modifierGroups)
      for (final o in g.options)
        if (chosen.contains(o.id))
          SelectedOption(
            optionId: o.id,
            name: o.name,
            priceDelta: o.priceDelta,
          ),
  ];
}

/// Línea PENDING de la comanda a la que hay que SUMARLE en vez de crear otra:
/// mismo producto, misma nota y los mismos modificadores. Tocar dos veces un
/// producto tiene que dar "2× Milanesa", no dos renglones de 1.
OrderItem? mergeableLine(
  Order order,
  Product product, {
  String? note,
  List<String> optionIds = const [],
}) {
  final wanted = optionIds.toSet();
  for (final it in order.items) {
    if (!it.status.isPending) continue;
    if (it.productId != product.id) continue;
    if ((it.note ?? '') != (note ?? '')) continue;
    final has = it.selectedOptions.map((o) => o.optionId).toSet();
    if (has.length != wanted.length || !has.containsAll(wanted)) continue;
    return it;
  }
  return null;
}

/// Última línea PENDING de ese producto (la que se descuenta al tocar "−" en
/// la grilla). null = no hay nada que quitar.
OrderItem? lastPendingLine(Order order, String productId) {
  OrderItem? found;
  for (final it in order.items) {
    if (it.status.isPending && it.productId == productId) found = it;
  }
  return found;
}
