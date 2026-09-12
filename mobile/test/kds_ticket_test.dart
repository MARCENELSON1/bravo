import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/features/kds/kds_ticket.dart';
import 'package:wellnod_mobile/features/order/order_dtos.dart';

OrderItem _item({
  required String id,
  required ItemStatus status,
  DateTime? sentAt,
  String name = 'X',
  Course course = Course.main,
}) => OrderItem(
  id: id,
  productId: 'p',
  name: name,
  unitPriceAmount: 0,
  quantity: 1,
  status: status,
  station: Station.kitchen,
  course: course,
  sentAt: sentAt,
);

Order _order(String id, List<OrderItem> items) => Order(
  id: id,
  tableId: 't',
  status: 'SENT',
  currency: 'ARS',
  totalAmount: 0,
  items: items,
);

void main() {
  final now = DateTime(2026, 1, 1, 12, 0);

  test('un ticket por (comanda, curso); al fuego primero, más viejo arriba', () {
    final orders = [
      _order('o1', [
        _item(id: 'a', status: ItemStatus.pending), // excluido (sin marchar)
        _item(
          id: 'b',
          status: ItemStatus.sent,
          sentAt: now.subtract(const Duration(minutes: 3)),
          name: 'Provoleta',
          course: Course.starter,
        ),
        _item(
          id: 'b2',
          status: ItemStatus.sent,
          sentAt: now.subtract(const Duration(minutes: 3)),
          name: 'Rabas',
          course: Course.starter,
        ),
        _item(
          id: 'h',
          status: ItemStatus.held,
          name: 'Bife',
          course: Course.main,
        ), // en espera: se ve, va al final
        _item(id: 'c', status: ItemStatus.served, sentAt: now), // excluido
      ]),
      _order('o2', [
        _item(
          id: 'd',
          status: ItemStatus.preparing,
          sentAt: now.subtract(const Duration(minutes: 12)),
          name: 'Milanesa',
        ),
      ]),
    ];

    final tickets = kdsTickets(orders, now: now);

    expect(tickets.length, 3);
    // más viejo primero
    expect(tickets[0].items.single.name, 'Milanesa');
    expect(tickets[0].minutes, 12);
    expect(tickets[0].isLate, isTrue);
    expect(tickets[0].canFinish, isTrue); // todo preparando → "Listo"
    // la entrada de o1 agrupa sus 2 platos en un solo ticket
    expect(tickets[1].course, Course.starter);
    expect(tickets[1].items.map((i) => i.name), ['Provoleta', 'Rabas']);
    expect(tickets[1].canStart, isTrue); // hay SENT → "Empezar"
    // el principal en espera va último y no apura
    expect(tickets[2].held, isTrue);
    expect(tickets[2].isLate, isFalse);
    expect(tickets[2].canFinish, isFalse);
  });

  test('mezcla SENT + PREPARING en un curso → todavía "Empezar"', () {
    final t = kdsTickets([
      _order('o', [
        _item(id: 'a', status: ItemStatus.preparing, sentAt: now),
        _item(id: 'b', status: ItemStatus.sent, sentAt: now),
      ]),
    ], now: now).single;
    expect(t.canStart, isTrue);
    expect(t.canFinish, isFalse);
  });
}
