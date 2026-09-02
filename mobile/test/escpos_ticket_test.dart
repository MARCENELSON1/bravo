import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/data/printing/escpos_ticket.dart';
import 'package:wellnod_mobile/features/order/order_dtos.dart';

Order _order() => Order(
      id: 'o1',
      tableId: 't1',
      status: 'SENT',
      currency: 'ARS',
      totalAmount: 0,
      items: [
        OrderItem(
          id: 'i1',
          productId: 'p1',
          name: 'Pizza',
          unitPriceAmount: 0,
          quantity: 2,
          status: ItemStatus.sent,
          station: Station.kitchen,
          selectedOptions: const [
            SelectedOption(optionId: 'x', name: 'Con panceta', priceDelta: 0),
          ],
        ),
        OrderItem(
          id: 'i2',
          productId: 'p2',
          name: 'Cerveza',
          unitPriceAmount: 0,
          quantity: 1,
          status: ItemStatus.sent,
          station: Station.bar,
        ),
      ],
    );

bool _contains(List<int> haystack, List<int> needle) {
  for (var i = 0; i + needle.length <= haystack.length; i++) {
    var ok = true;
    for (var j = 0; j < needle.length; j++) {
      if (haystack[i + j] != needle[j]) {
        ok = false;
        break;
      }
    }
    if (ok) return true;
  }
  return false;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('el ticket incluye nombres, agrupa por estación y suma modificadores',
      () async {
    final bytes = await buildKitchenTicket(_order(), tableLabel: 'Mesa 5');
    expect(bytes, isNotEmpty);
    expect(_contains(bytes, 'Pizza'.codeUnits), isTrue);
    expect(_contains(bytes, 'Cerveza'.codeUnits), isTrue);
    expect(_contains(bytes, 'COCINA'.codeUnits), isTrue);
    expect(_contains(bytes, 'BARRA'.codeUnits), isTrue);
    expect(_contains(bytes, 'Con panceta'.codeUnits), isTrue);
  });
}
