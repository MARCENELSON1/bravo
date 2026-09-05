import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/features/order/capture_logic.dart';
import 'package:wellnod_mobile/features/order/order_dtos.dart';
import 'package:wellnod_mobile/features/order/product_dtos.dart';

Product _p(String id, String name, {String? category, String station = 'KITCHEN'}) =>
    Product(
      id: id,
      name: name,
      priceAmount: 1000,
      currency: 'ARS',
      station: station,
      active: true,
      category: category,
    );

OrderItem _it(String productId, int qty, ItemStatus status) => OrderItem(
      id: 'i-$productId-$qty-${status.name}',
      productId: productId,
      name: productId,
      unitPriceAmount: 1000,
      quantity: qty,
      status: status,
      station: Station.kitchen,
    );

Order _order(List<OrderItem> items) => Order(
      id: 'o1',
      tableId: 't1',
      status: 'OPEN',
      currency: 'ARS',
      items: items,
      totalAmount: 0,
    );

void main() {
  final carta = [
    _p('mila', 'Milanesa napolitana', category: 'Principales'),
    _p('bife', 'Bife de chorizo', category: 'Principales'),
    _p('prov', 'Provoleta', category: 'Entradas'),
    _p('malbec', 'Copa de Malbec', category: 'Bebidas', station: 'BAR'),
    _p('flan', 'Flan mixto', category: 'Postres'),
    _p('cafe', 'Café', category: 'Bebidas', station: 'BAR'),
  ];

  group('normalizeText', () {
    test('minúsculas y sin tildes', () {
      expect(normalizeText('  Café Ñandú  '), 'cafe nandu');
    });
  });

  group('categoriesOf', () {
    test('distintas, en orden de aparición, sin nulls', () {
      final withNull = [...carta, _p('x', 'Sin categoría')];
      expect(categoriesOf(withNull),
          ['Principales', 'Entradas', 'Bebidas', 'Postres']);
    });
  });

  group('filterProducts', () {
    test('por categoría', () {
      final r = filterProducts(carta, category: 'Bebidas');
      expect(r.map((p) => p.id), ['malbec', 'cafe']);
    });

    test('sin categoría ni búsqueda → toda la carta', () {
      expect(filterProducts(carta).length, carta.length);
    });

    test('"mila" encuentra Milanesa (apodo por prefijo)', () {
      expect(filterProducts(carta, query: 'mila').map((p) => p.id), ['mila']);
    });

    test('"napo" encuentra napolitana (contains)', () {
      expect(filterProducts(carta, query: 'napo').map((p) => p.id), ['mila']);
    });

    test('la búsqueda ignora tildes y la pestaña elegida', () {
      // "cafe" sin tilde encuentra "Café", aunque la categoría sea otra.
      final r = filterProducts(carta, category: 'Postres', query: 'cafe');
      expect(r.map((p) => p.id), ['cafe']);
    });

    test('la búsqueda también matchea la categoría', () {
      final r = filterProducts(carta, query: 'postre');
      expect(r.map((p) => p.id), ['flan']);
    });
  });

  group('pendingQtyOf', () {
    test('suma solo lo PENDING de ese producto', () {
      final o = _order([
        _it('mila', 2, ItemStatus.pending),
        _it('mila', 1, ItemStatus.pending),
        _it('mila', 5, ItemStatus.sent), // ya marchado: no cuenta
        _it('bife', 1, ItemStatus.pending),
      ]);
      expect(pendingQtyOf(o, 'mila'), 3);
      expect(pendingQtyOf(o, 'bife'), 1);
      expect(pendingQtyOf(o, 'flan'), 0);
    });
  });
}
