import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/features/order/order_dtos.dart';
import 'package:wellnod_mobile/features/order/order_optimistic.dart';
import 'package:wellnod_mobile/features/order/product_dtos.dart';

Order _order({List<OrderItem> items = const [], int total = 0}) => Order(
      id: 'o1',
      tableId: 't1',
      status: 'OPEN',
      currency: 'ARS',
      items: items,
      totalAmount: total,
    );

Product _prod({int price = 100000}) => Product(
      id: 'p1',
      name: 'Pizza',
      priceAmount: price,
      currency: 'ARS',
      station: 'KITCHEN',
      active: true,
    );

OrderItem _item({
  String id = 'i1',
  int price = 100000,
  int qty = 1,
  ItemStatus status = ItemStatus.pending,
}) =>
    OrderItem(
      id: id,
      productId: 'p1',
      name: 'Pizza',
      unitPriceAmount: price,
      quantity: qty,
      status: status,
      station: Station.kitchen,
    );

void main() {
  test('applyAdd agrega el ítem con el UUID y suma al total', () {
    final o = applyAdd(_order(), _prod(price: 120000), 2, 'i1');
    expect(o.items.single.id, 'i1');
    expect(o.items.single.status, ItemStatus.pending);
    expect(o.totalAmount, 240000);
  });

  test('applyQty ajusta cantidad y total en un ítem PENDING', () {
    final o = _order(items: [_item(qty: 1)], total: 100000);
    final r = applyQty(o, 'i1', 3);
    expect(r.items.single.quantity, 3);
    expect(r.totalAmount, 300000);
  });

  test('applyQty no toca ítems ya marchados', () {
    final o = _order(items: [_item(qty: 1, status: ItemStatus.sent)], total: 100000);
    final r = applyQty(o, 'i1', 5);
    expect(r.items.single.quantity, 1);
    expect(r.totalAmount, 100000);
  });

  test('applyRemove saca el ítem y descuenta del total', () {
    final o = _order(items: [_item(qty: 2)], total: 200000);
    final r = applyRemove(o, 'i1');
    expect(r.items, isEmpty);
    expect(r.totalAmount, 0);
  });
}
