import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/features/floor/floor_dtos.dart';
import 'package:wellnod_mobile/features/floor/floor_ops.dart';
import 'package:wellnod_mobile/features/order/order_dtos.dart';

final _now = DateTime(2026, 9, 5, 21, 0);

FloorSession _session(SessionState state,
        {int minutesAgo = 0, String? waiter}) =>
    FloorSession(
      id: 's',
      state: state,
      stateSince: _now.subtract(Duration(minutes: minutesAgo)),
      waiterId: waiter,
    );

Order _order(int total) => Order(
      id: 'o',
      tableId: 't',
      status: 'SENT',
      currency: 'ARS',
      items: const [],
      totalAmount: total,
    );

FloorTable _t(String id, int number,
        {FloorSession? session, Order? order}) =>
    FloorTable(
      id: id,
      number: number,
      status: (session != null || order != null) ? 'OCCUPIED' : 'FREE',
      session: session,
      activeOrder: order,
    );

void main() {
  group('sortByUrgency', () {
    test('atención primero, la que más espera arriba; el resto en su orden', () {
      final tables = [
        _t('a', 1, session: _session(SessionState.open)),
        _t('b', 2, session: _session(SessionState.toServe, minutesAgo: 5)),
        _t('c', 3, session: _session(SessionState.inKitchen)),
        _t('d', 4, session: _session(SessionState.toServe, minutesAgo: 18)),
        _t('e', 5, session: _session(SessionState.toCharge, minutesAgo: 9)),
        _t('f', 6),
      ];
      final r = sortByUrgency(tables, now: _now).map((t) => t.id).toList();
      expect(r, ['d', 'e', 'b', 'a', 'c', 'f']);
    });
  });

  group('summarizeFloor', () {
    test('cuenta mías, para servir, a cobrar y suma mis mesas', () {
      final tables = [
        _t('a', 1,
            session: _session(SessionState.toServe, waiter: 'me'),
            order: _order(10000)),
        _t('b', 2,
            session: _session(SessionState.open, waiter: 'me'),
            order: _order(5000)),
        _t('c', 3,
            session: _session(SessionState.toServe, waiter: 'other'),
            order: _order(7000)),
        _t('d', 4, session: _session(SessionState.toCharge, waiter: 'other')),
        _t('e', 5),
      ];
      final s = summarizeFloor(tables, 'me', now: _now);
      expect(s.mine, 2);
      expect(s.toServe, 2); // en todo el piso: el que ve, sirve
      expect(s.toCharge, 1);
      expect(s.mineTotal, 15000);
    });

    test('sin usuario no hay "mías"', () {
      final s = summarizeFloor(
          [_t('a', 1, session: _session(SessionState.open, waiter: 'x'))], null);
      expect(s.mine, 0);
      expect(s.mineTotal, 0);
    });
  });

  group('newlyAttention', () {
    test('solo las que PASARON a atención respecto del snapshot anterior', () {
      final before = [
        _t('a', 1, session: _session(SessionState.toServe)), // ya pedía
        _t('b', 2, session: _session(SessionState.inKitchen)),
        _t('c', 3, session: _session(SessionState.open)),
      ];
      final snap = attentionSnapshot(before, now: _now);
      final after = [
        _t('a', 1, session: _session(SessionState.toServe)), // sigue: no pulsa
        _t('b', 2, session: _session(SessionState.toServe)), // nueva: pulsa
        _t('c', 3, session: _session(SessionState.open)),
        _t('z', 9, session: _session(SessionState.toCharge)), // apareció: pulsa
      ];
      expect(newlyAttention(snap, after, now: _now), {'b', 'z'});
    });
  });
}
