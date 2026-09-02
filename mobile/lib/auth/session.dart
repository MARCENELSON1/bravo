import 'dtos.dart';

/// Roles del backend (`domain/user/value_objects.py`, incluye BAR).
enum Role {
  owner,
  manager,
  waiter,
  kitchen,
  bar,
  cashier;

  static Role fromApi(String value) {
    switch (value) {
      case 'OWNER':
        return Role.owner;
      case 'MANAGER':
        return Role.manager;
      case 'WAITER':
        return Role.waiter;
      case 'KITCHEN':
        return Role.kitchen;
      case 'BAR':
        return Role.bar;
      case 'CASHIER':
        return Role.cashier;
      default:
        return Role.waiter;
    }
  }

  String get api => switch (this) {
        Role.owner => 'OWNER',
        Role.manager => 'MANAGER',
        Role.waiter => 'WAITER',
        Role.kitchen => 'KITCHEN',
        Role.bar => 'BAR',
        Role.cashier => 'CASHIER',
      };

  bool get isAdmin => this == Role.owner || this == Role.manager;
}

/// Sesión hidratada (espeja `frontend/src/auth/session.ts`).
class Session {
  const Session({
    required this.userId,
    required this.tenantId,
    required this.email,
    required this.tenantName,
    required this.role,
    this.name,
  });

  final String userId;
  final String tenantId;
  final String email;
  final String tenantName;
  final Role role;
  final String? name;

  /// Nombre para saludar: el nombre real o, si no hay, la parte local del email.
  String get displayName =>
      (name != null && name!.trim().isNotEmpty) ? name!.trim() : email.split('@').first;

  factory Session.fromMe(MeResponse me) => Session(
        userId: me.userId,
        tenantId: me.tenantId,
        email: me.email,
        tenantName: me.tenantName,
        role: Role.fromApi(me.role),
        name: me.name,
      );
}
