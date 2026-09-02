import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:print_bluetooth_thermal/print_bluetooth_thermal.dart';

import '../../data/printing/escpos_ticket.dart';
import '../../data/printing/printer_providers.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';

/// Settings de la impresora ESC/POS: elegir una impresora vinculada por Bluetooth
/// y probarla. La impresión de la comanda se dispara al marchar.
class PrinterPage extends ConsumerStatefulWidget {
  const PrinterPage({super.key});

  @override
  ConsumerState<PrinterPage> createState() => _PrinterPageState();
}

class _PrinterPageState extends ConsumerState<PrinterPage> {
  List<BluetoothInfo> _devices = [];
  bool _loading = false;
  bool _btOff = false;

  @override
  void initState() {
    super.initState();
    _scan();
  }

  Future<void> _scan() async {
    setState(() => _loading = true);
    final service = ref.read(printerServiceProvider);
    final on = await service.bluetoothEnabled();
    final list = on ? await service.paired() : <BluetoothInfo>[];
    if (!mounted) return;
    setState(() {
      _btOff = !on;
      _devices = list;
      _loading = false;
    });
  }

  Future<void> _select(BluetoothInfo device) async {
    await ref.read(printerServiceProvider).save(device.macAdress, device.name);
    if (!mounted) return;
    setState(() {});
    _toast(context.s.printerSaved);
  }

  Future<void> _test() async {
    final s = context.s;
    final service = ref.read(printerServiceProvider);
    if (service.savedMac == null) {
      _toast(s.printerNoPrinter);
      return;
    }
    final ok = await service.printBytes(await buildTestTicket());
    _toast(ok ? s.printerTestSent : s.printerNoPrinter);
  }

  void _toast(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final service = ref.watch(printerServiceProvider);
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.printerTitle),
        backgroundColor: Colors.transparent,
        actions: [
          IconButton(
            onPressed: _loading ? null : _scan,
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                GlassPanel(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(s.printerCurrent, style: theme.textTheme.titleSmall),
                      const SizedBox(height: 4),
                      Text(service.savedName ?? s.printerNone),
                      const SizedBox(height: 12),
                      OutlinedButton.icon(
                        onPressed: _test,
                        icon: const Icon(Icons.print_outlined),
                        label: Text(s.printerTest),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                Text(s.printerPaired, style: theme.textTheme.titleSmall),
                const SizedBox(height: 8),
                if (_loading)
                  const Center(
                    child: Padding(
                      padding: EdgeInsets.all(24),
                      child: CircularProgressIndicator(),
                    ),
                  )
                else if (_btOff)
                  GlassPanel(child: Text(s.printerBtOff))
                else if (_devices.isEmpty)
                  GlassPanel(child: Text(s.printerNoDevices))
                else
                  GlassPanel(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Material(
                      type: MaterialType.transparency,
                      child: Column(
                        children: [
                          for (final d in _devices)
                            ListTile(
                              leading: const Icon(Icons.print_outlined),
                              title: Text(d.name),
                              subtitle: Text(d.macAdress),
                              trailing: service.savedMac == d.macAdress
                                  ? const Icon(Icons.check_circle)
                                  : null,
                              onTap: () => _select(d),
                            ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
