import 'package:flutter_test/flutter_test.dart';
import 'package:wellnod_mobile/features/floor/floor_dtos.dart';
import 'package:wellnod_mobile/features/floor/floor_view.dart';

FloorSession _session(
  SessionState state, {
  DateTime? since,
  int? pax,
  String? waiter,
}) =>
    FloorSession(
      id: 's1',
      state: state,
      stateSince: since,
      pax: pax,
      waiterName: waiter,
    );

FloorTable _table({FloorSession? session}) => FloorTable(
      id: 't1',
      number: 5,
      status: session == null ? 'FREE' : 'OCCUPIED',
      session: session,
      capacity: 4,
    );

void main() {
  test('mesa libre → free, sin atención', () {
    final v = floorView(_table());
    expect(v.status, FloorStatus.free);
    expect(v.attention, false);
  });

  test('TO_SERVE → atención + pax de la sesión', () {
    final v = floorView(_table(session: _session(SessionState.toServe, pax: 3)));
    expect(v.status, FloorStatus.toServe);
    expect(v.attention, true);
    expect(v.pax, 3);
  });

  test('TO_CHARGE también pide atención', () {
    final v = floorView(_table(session: _session(SessionState.toCharge)));
    expect(v.attention, true);
  });

  test('SERVED no pide atención', () {
    final v = floorView(_table(session: _session(SessionState.served)));
    expect(v.status, FloorStatus.served);
    expect(v.attention, false);
  });

  test('minutos derivados de state_since', () {
    final now = DateTime(2026, 1, 1, 12, 0);
    final v = floorView(
      _table(
          session: _session(SessionState.open,
              since: now.subtract(const Duration(minutes: 7)))),
      now: now,
    );
    expect(v.minutes, 7);
  });

  test('pax cae a capacity si la sesión no lo trae', () {
    final v = floorView(_table(session: _session(SessionState.open)));
    expect(v.pax, 4);
  });
}
