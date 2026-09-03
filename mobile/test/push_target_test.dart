import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/data/push/push_service.dart';

void main() {
  test('order.ready con order_id → target con mesa', () {
    final r = pushTarget(
        {'kind': 'order.ready', 'order_id': 'o1', 'table_number': '7'});
    expect(r, isNotNull);
    expect(r!.orderId, 'o1');
    expect(r.tableNumber, 7);
  });

  test('table.assigned también dispara el modal', () {
    final r = pushTarget(
        {'kind': 'table.assigned', 'order_id': 'o2', 'table_number': ''});
    expect(r!.orderId, 'o2');
    expect(r.tableNumber, isNull);
  });

  test('otro kind → null', () {
    expect(pushTarget({'kind': 'floor.changed', 'order_id': 'o1'}), isNull);
  });

  test('sin order_id → null', () {
    expect(pushTarget({'kind': 'order.ready'}), isNull);
  });
}
