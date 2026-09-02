import 'package:print_bluetooth_thermal/print_bluetooth_thermal.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Impresora térmica ESC/POS por Bluetooth. Best-effort: si no hay impresora
/// guardada o falla, devuelve false sin romper el flujo (la comanda igual quedó
/// registrada / encolada). En el simulador (sin BT) el scan devuelve vacío.
class PrinterService {
  PrinterService(this._prefs);

  final SharedPreferences _prefs;
  static const _macKey = 'wellnod:printer_mac';
  static const _nameKey = 'wellnod:printer_name';

  String? get savedMac => _prefs.getString(_macKey);
  String? get savedName => _prefs.getString(_nameKey);

  Future<void> save(String mac, String name) async {
    await _prefs.setString(_macKey, mac);
    await _prefs.setString(_nameKey, name);
  }

  Future<void> clear() async {
    await _prefs.remove(_macKey);
    await _prefs.remove(_nameKey);
  }

  Future<bool> bluetoothEnabled() async {
    try {
      return await PrintBluetoothThermal.bluetoothEnabled;
    } catch (_) {
      return false;
    }
  }

  Future<List<BluetoothInfo>> paired() async {
    try {
      return await PrintBluetoothThermal.pairedBluetooths;
    } catch (_) {
      return [];
    }
  }

  /// Imprime bytes en la impresora guardada. Devuelve false si no hay impresora
  /// o si falla (no lanza).
  Future<bool> printBytes(List<int> bytes) async {
    final mac = savedMac;
    if (mac == null) return false;
    try {
      final connected = await PrintBluetoothThermal.connectionStatus;
      if (!connected) {
        final ok = await PrintBluetoothThermal.connect(macPrinterAddress: mac);
        if (!ok) return false;
      }
      return await PrintBluetoothThermal.writeBytes(bytes);
    } catch (_) {
      return false;
    }
  }
}
