import 'package:esc_pos_utils_plus/esc_pos_utils_plus.dart';

import '../../features/order/order_dtos.dart';

/// Arma el ticket de comanda de cocina en bytes ESC/POS. Port de
/// `frontend/src/lib/ticket.ts`: agrupa por estación (COCINA/BARRA), imprime
/// `qty× nombre`, los modificadores y la nota, y corta el papel. Suma los
/// `selected_options` (que la web hoy no imprime).
Future<List<int>> buildKitchenTicket(
  Order order, {
  String? tableLabel,
  PaperSize paper = PaperSize.mm58,
}) async {
  final profile = await CapabilityProfile.load();
  final g = Generator(paper, profile);
  var bytes = <int>[];

  bytes += g.text(
    'COMANDA',
    styles: const PosStyles(
      bold: true,
      align: PosAlign.center,
      height: PosTextSize.size2,
      width: PosTextSize.size2,
    ),
  );
  if (tableLabel != null) {
    bytes += g.text(tableLabel, styles: const PosStyles(align: PosAlign.center));
  }
  bytes += g.hr();

  final byStation = <Station, List<OrderItem>>{};
  for (final item in order.liveItems) {
    byStation.putIfAbsent(item.station, () => []).add(item);
  }

  for (final entry in byStation.entries) {
    bytes += g.text(
      entry.key == Station.bar ? 'BARRA' : 'COCINA',
      styles: const PosStyles(bold: true, underline: true),
    );
    for (final item in entry.value) {
      bytes += g.text(
        '${item.quantity}x ${item.name}',
        styles: const PosStyles(bold: true),
      );
      if (item.selectedOptions.isNotEmpty) {
        bytes += g.text('  ${item.selectedOptions.map((o) => o.name).join(', ')}');
      }
      if (item.note != null && item.note!.isNotEmpty) {
        bytes += g.text('  > ${item.note}');
      }
    }
    bytes += g.hr();
  }

  bytes += g.feed(1);
  bytes += g.cut();
  return bytes;
}

/// Ticket de prueba para verificar el emparejamiento de la impresora.
Future<List<int>> buildTestTicket({PaperSize paper = PaperSize.mm58}) async {
  final profile = await CapabilityProfile.load();
  final g = Generator(paper, profile);
  var bytes = <int>[];
  bytes += g.text(
    'WELLNOD',
    styles: const PosStyles(
      bold: true,
      align: PosAlign.center,
      height: PosTextSize.size2,
      width: PosTextSize.size2,
    ),
  );
  bytes += g.text('Prueba de impresora', styles: const PosStyles(align: PosAlign.center));
  bytes += g.hr();
  bytes += g.feed(1);
  bytes += g.cut();
  return bytes;
}
