import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'order_op.dart';

/// Cola FIFO de operaciones pendientes, persistida en shared_preferences.
/// El orden de la lista ES el orden de reintento. `count` es un `ValueNotifier`
/// que alimenta el indicador de sync.
class SyncQueue {
  SyncQueue(this._prefs) {
    count.value = all().length;
  }

  final SharedPreferences _prefs;
  static const _key = 'wellnod:sync_queue';

  final ValueNotifier<int> count = ValueNotifier<int>(0);

  List<OrderOp> all() {
    final raw = _prefs.getString(_key);
    if (raw == null) return [];
    try {
      return (jsonDecode(raw) as List)
          .map((e) => OrderOp.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> enqueue(OrderOp op) async {
    final ops = all()..add(op);
    await _save(ops);
  }

  Future<void> replaceAll(List<OrderOp> ops) => _save(ops);

  Future<void> _save(List<OrderOp> ops) async {
    await _prefs.setString(
      _key,
      jsonEncode(ops.map((o) => o.toJson()).toList()),
    );
    count.value = ops.length;
  }
}
