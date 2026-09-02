import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:wellnod_mobile/data/offline/order_op.dart';
import 'package:wellnod_mobile/data/offline/sync_queue.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('OrderOp round-trips por JSON', () {
    final op = OrderOp.addItem(
      orderId: 'o1',
      itemId: 'i1',
      productId: 'p1',
      quantity: 2,
      note: 'sin sal',
    );
    final back = OrderOp.fromJson(op.toJson());
    expect(back.type, OrderOpType.addItem);
    expect(back.orderId, 'o1');
    expect(back.itemId, 'i1');
    expect(back.productId, 'p1');
    expect(back.quantity, 2);
    expect(back.note, 'sin sal');
  });

  test('enqueue persiste FIFO y actualiza el contador; replaceAll reemplaza',
      () async {
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    final q = SyncQueue(prefs);
    expect(q.count.value, 0);

    await q.enqueue(
        OrderOp.addItem(orderId: 'o1', itemId: 'i1', productId: 'p1', quantity: 1));
    await q.enqueue(OrderOp.send(orderId: 'o1'));
    expect(q.all().length, 2);
    expect(q.count.value, 2);
    expect(q.all().first.type, OrderOpType.addItem); // FIFO

    // sobrevive a reinstanciar con las mismas prefs (persistencia)
    final q2 = SyncQueue(prefs);
    expect(q2.all().length, 2);

    await q2.replaceAll([q2.all().last]);
    expect(q2.all().single.type, OrderOpType.send);
    expect(q2.count.value, 1);
  });
}
