import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/auth/dtos.dart';
import 'package:wellnod_mobile/auth/session.dart';

void main() {
  test('Role.fromApi mapea todos los roles, incluido BAR', () {
    expect(Role.fromApi('OWNER'), Role.owner);
    expect(Role.fromApi('MANAGER'), Role.manager);
    expect(Role.fromApi('WAITER'), Role.waiter);
    expect(Role.fromApi('KITCHEN'), Role.kitchen);
    expect(Role.fromApi('BAR'), Role.bar);
    expect(Role.fromApi('CASHIER'), Role.cashier);
    expect(Role.fromApi('desconocido'), Role.waiter); // fallback seguro
  });

  test('displayName usa el nombre o la parte local del email', () {
    final withName = Session.fromMe(const MeResponse(
      tenantId: 't',
      userId: 'u',
      role: 'OWNER',
      email: 'a@b.com',
      tenantName: 'Resto',
      name: 'Marce',
    ));
    expect(withName.displayName, 'Marce');

    final noName = Session.fromMe(const MeResponse(
      tenantId: 't',
      userId: 'u',
      role: 'WAITER',
      email: 'juan@resto.com',
      tenantName: 'Resto',
    ));
    expect(noName.displayName, 'juan');
  });
}
