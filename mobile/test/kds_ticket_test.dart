import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/features/kds/kds_ticket.dart';
import 'package:wellnod_mobile/features/order/order_dtos.dart';

OrderItem _item({
  required String id,
  required ItemStatus status,
  DateTime? sentAt,
  String name = 'X',
}) =>
    OrderItem(
      id: id,
      productId: 'p',
      name: name,
      unitPriceAmount: 0,
      quantity: 1,
      status: status,
      station: Station.kitchen,
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
  test('kdsTickets filtra SENT/PREPARING y ordena más viejo primero', () {
    final now = DateTime(2026, 1, 1, 12, 0);
    final orders = [
      _order('o1', [
        _item(id: 'a', status: ItemStatus.pending), // excluido (pending)
        _item(
            id: 'b',
            status: ItemStatus.sent,
            sentAt: now.subtract(const Duration(minutes: 3)),
            name: 'Nuevo'),
        _item(id: 'c', status: ItemStatus.served, sentAt: now), // excluido
      ]),
      _order('o2', [
        _item(
            id: 'd',
            status: ItemStatus.preparing,
            sentAt: now.subtract(const Duration(minutes: 12)),
            name: 'Viejo'),
      ]),
    ];

    final tickets = kdsTickets(orders, now: now);

    expect(tickets.length, 2);
    expect(tickets.first.item.name, 'Viejo'); // más viejo primero
    expect(tickets.first.minutes, 12);
    expect(tickets.first.isLate, isTrue);
    expect(tickets.last.item.name, 'Nuevo');
    expect(tickets.last.isLate, isFalse);
  });
}
