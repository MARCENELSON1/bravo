import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/features/order/capture_logic.dart';
import 'package:wellnod_mobile/features/order/order_dtos.dart';
import 'package:wellnod_mobile/features/order/product_dtos.dart';

Product _p(String id, String name,
        {String? category,
        String station = 'KITCHEN',
        List<ModifierGroup> groups = const []}) =>
    Product(
      id: id,
      name: name,
      priceAmount: 1000,
      currency: 'ARS',
      station: station,
      active: true,
      category: category,
      modifierGroups: groups,
    );

const _punto = ModifierGroup(
  id: 'g-punto',
  name: 'Punto',
  minSelect: 1,
  maxSelect: 1,
  options: [
    ModifierOption(id: 'jugoso', name: 'Jugoso'),
    ModifierOption(id: 'apunto', name: 'A punto'),
  ],
);
const _extras = ModifierGroup(
  id: 'g-extras',
  name: 'Agregados',
  minSelect: 0,
  maxSelect: 2,
  options: [
    ModifierOption(id: 'panceta', name: '+Panceta', priceDelta: 1200),
    ModifierOption(id: 'queso', name: '+Queso', priceDelta: 800),
    ModifierOption(id: 'huevo', name: '+Huevo', priceDelta: 500),
  ],
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

  group('modificadores', () {
    final bife = _p('bife', 'Bife', groups: const [_punto, _extras]);
    final agua = _p('agua', 'Agua');

    test('needsChoice solo si hay grupo obligatorio', () {
      expect(bife.needsChoice, isTrue);
      expect(agua.needsChoice, isFalse);
    });

    test('selectionValid exige el obligatorio y respeta el máximo', () {
      expect(selectionValid(bife, []), isFalse); // falta el punto
      expect(selectionValid(bife, ['jugoso']), isTrue);
      expect(selectionValid(bife, ['jugoso', 'panceta', 'queso']), isTrue);
      expect(selectionValid(bife, ['jugoso', 'panceta', 'queso', 'huevo']),
          isFalse); // 3 > maxSelect 2
      expect(selectionValid(agua, []), isTrue); // sin grupos, siempre válido
    });

    test('optionsDelta suma solo lo elegido', () {
      expect(optionsDelta(bife, ['jugoso']), 0);
      expect(optionsDelta(bife, ['jugoso', 'panceta', 'huevo']), 1700);
    });

    test('snapshotOptions arma nombre + delta en orden de la carta', () {
      final snap = snapshotOptions(bife, ['queso', 'jugoso']);
      expect(snap.map((o) => o.name), ['Jugoso', '+Queso']);
      expect(snap.map((o) => o.priceDelta), [0, 800]);
    });
  });

  group('readyCourse (servir SIEMPRE por curso)', () {
    OrderItem it(String id, Course c, ItemStatus st) => OrderItem(
      id: id,
      productId: id,
      name: id,
      unitPriceAmount: 1000,
      quantity: 1,
      status: st,
      station: Station.kitchen,
      course: c,
    );
    Order ord(List<OrderItem> items) => Order(
      id: 'o',
      tableId: 't',
      status: 'SENT',
      currency: 'ARS',
      items: items,
      totalAmount: 0,
    );

    test('devuelve el curso más bajo que está listo', () {
      final o = ord([
        it('bife', Course.main, ItemStatus.ready),
        it('prov', Course.starter, ItemStatus.ready),
      ]);
      expect(o.readyCourse, Course.starter); // la entrada primero
    });

    test('ignora cursos en cocina o ya servidos', () {
      final o = ord([
        it('prov', Course.starter, ItemStatus.served),
        it('bife', Course.main, ItemStatus.sent),
      ]);
      expect(o.readyCourse, isNull);
    });

    test('un curso con un plato aún en cocina NO está listo', () {
      final o = ord([
        it('prov', Course.starter, ItemStatus.ready),
        it('rabas', Course.starter, ItemStatus.preparing),
      ]);
      expect(o.courseState(Course.starter), CourseState.inKitchen);
      expect(o.readyCourse, isNull);
    });

    test('regresión: entrada servida + bebida en cocina → nada para servir', () {
      // El caso que rompía: la pantalla vieja mostraba "Listo" y todo fallaba.
      final o = ord([
        it('burrata', Course.starter, ItemStatus.served),
        it('empanadas', Course.starter, ItemStatus.served),
        it('aperol', Course.immediate, ItemStatus.sent),
      ]);
      expect(o.readyCourse, isNull);
      expect(o.readyCount, 0);
    });
  });

  group('merge de líneas (tocar 2 veces = 2×, no 2 renglones)', () {
    final mila = _p('mila', 'Milanesa');
    OrderItem line(String id, String prod, int qty,
            {String? note, List<String> opts = const []}) =>
        OrderItem(
          id: id,
          productId: prod,
          name: prod,
          unitPriceAmount: 1000,
          quantity: qty,
          status: ItemStatus.pending,
          station: Station.kitchen,
          note: note,
          selectedOptions: [
            for (final o in opts)
              SelectedOption(optionId: o, name: o, priceDelta: 0),
          ],
        );
    Order ord(List<OrderItem> items) => Order(
      id: 'o',
      tableId: 't',
      status: 'OPEN',
      currency: 'ARS',
      items: items,
      totalAmount: 0,
    );

    test('encuentra la línea del mismo producto sin nota ni opciones', () {
      final o = ord([line('a', 'mila', 1)]);
      expect(mergeableLine(o, mila)?.id, 'a');
    });

    test('no mezcla si la nota difiere', () {
      final o = ord([line('a', 'mila', 1, note: 'sin sal')]);
      expect(mergeableLine(o, mila), isNull);
      expect(mergeableLine(o, mila, note: 'sin sal')?.id, 'a');
    });

    test('no mezcla si los modificadores difieren', () {
      final o = ord([line('a', 'mila', 1, opts: ['jugoso'])]);
      expect(mergeableLine(o, mila), isNull);
      expect(mergeableLine(o, mila, optionIds: ['jugoso'])?.id, 'a');
      expect(mergeableLine(o, mila, optionIds: ['cocido']), isNull);
    });

    test('no toca líneas ya marchadas', () {
      final marchada = OrderItem(
        id: 'x',
        productId: 'mila',
        name: 'Milanesa',
        unitPriceAmount: 1000,
        quantity: 1,
        status: ItemStatus.sent,
        station: Station.kitchen,
      );
      expect(mergeableLine(ord([marchada]), mila), isNull);
    });

    test('lastPendingLine devuelve la última pendiente del producto', () {
      final o = ord([line('a', 'mila', 1), line('b', 'mila', 2)]);
      expect(lastPendingLine(o, 'mila')?.id, 'b');
      expect(lastPendingLine(o, 'bife'), isNull);
    });
  });
}
