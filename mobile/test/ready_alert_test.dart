import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/data/realtime/realtime_service.dart';
import 'package:wellnod_mobile/features/shell/ready_alert.dart';

void main() {
  const me = 'w1';

  RealtimeEvent ev(String name, Map<String, dynamic> data) =>
      RealtimeEvent(name, data);

  test('order.ready del mozo → devuelve orderId + mesa', () {
    final r = readyOrderFor(
      ev('order.ready',
          {'order_id': 'o1', 'table_number': '7', 'waiter_id': 'w1'}),
      me,
    );
    expect(r, isNotNull);
    expect(r!.orderId, 'o1');
    expect(r.tableNumber, 7);
  });

  test('order.ready de OTRO mozo → null', () {
    final r = readyOrderFor(
      ev('order.ready',
          {'order_id': 'o1', 'table_number': '7', 'waiter_id': 'w2'}),
      me,
    );
    expect(r, isNull);
  });

  test('otro evento (floor.changed) → null', () {
    expect(readyOrderFor(ev('floor.changed', {'table_id': 't1'}), me), isNull);
  });

  test('sin order_id → null', () {
    final r = readyOrderFor(
      ev('order.ready', {'waiter_id': 'w1', 'table_number': '7'}),
      me,
    );
    expect(r, isNull);
  });

  test('table_number vacío → mesa null pero devuelve el pedido', () {
    final r = readyOrderFor(
      ev('order.ready',
          {'order_id': 'o1', 'table_number': '', 'waiter_id': 'w1'}),
      me,
    );
    expect(r, isNotNull);
    expect(r!.tableNumber, isNull);
    expect(r.orderId, 'o1');
  });
}
