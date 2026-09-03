import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session.dart';
import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import '../billing/suscripcion_page.dart';
import '../crm/clientes_page.dart';
import '../expenses/gastos_page.dart';
import '../floor/mesas_qr_page.dart';
import '../inventory/insumos_page.dart';
import '../inventory/proveedores_page.dart';
import '../platform/platform_page.dart';
import '../platform/platform_repository.dart';
import '../invoices/comprobantes_page.dart';
import '../products/productos_page.dart';
import '../reports/analytics_page.dart';
import '../reports/reportes_page.dart';
import '../reservations/reservas_page.dart';
import '../timeclock/staff_page.dart';
import '../settings/ajustes_page.dart';
import '../settings/printer_page.dart';
import '../timeclock/fichaje_page.dart';
import '../tips/tips_page.dart';

/// Hub de la tab "Más": calca las capacidades del rol (guards `RequireRole` del
/// web). Cada rol ve solo lo que puede tocar y que no está ya en su barra de
/// abajo. Fichaje, Impresora y Ajustes son para todos.
class MorePage extends ConsumerWidget {
  const MorePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final sessionState = ref.watch(sessionProvider);
    final role = sessionState is SessionAuthenticated
        ? sessionState.session.role
        : null;
    final isAdmin = role == Role.owner || role == Role.manager;
    final isOwner = role == Role.owner;
    final isCashier = role == Role.cashier;
    final isPlatformAdmin =
        ref.watch(platformAccessProvider).valueOrNull ?? false;

    final items = <(IconData, String, Widget)>[
      // Cajero: Reservas + Clientes (no están en su barra de abajo).
      if (isCashier) ...[
        (Icons.event_available_outlined, s.reservasTitle, const ReservasPage()),
        (Icons.people_alt_outlined, s.clientesTitle, const ClientesPage()),
      ],
      // Todos:
      (Icons.schedule_outlined, s.fichajeTitle, const FichajePage()),
      (Icons.print_outlined, s.printerTitle, const PrinterPage()),
      // Hub de gestión (OWNER/MANAGER):
      if (isAdmin) ...[
        (Icons.volunteer_activism_outlined, s.tipsTitle, const TipsPage()),
        (Icons.badge_outlined, s.staffTitle, const StaffPage()),
        (Icons.inventory_2_outlined, s.productosTitle, const ProductosPage()),
        (Icons.egg_alt_outlined, s.insumosTitle, const InsumosPage()),
        (Icons.local_shipping_outlined, s.proveedoresTitle,
            const ProveedoresPage()),
        (Icons.shopping_cart_outlined, s.gastosTitle, const GastosPage()),
        (Icons.receipt_long_outlined, s.comprobantesTitle,
            const ComprobantesPage()),
        (Icons.bar_chart_outlined, s.reportesTitle, const ReportesPage()),
        (Icons.query_stats_outlined, s.analyticsTitle, const AnalyticsPage()),
        (Icons.people_alt_outlined, s.clientesTitle, const ClientesPage()),
        (Icons.event_available_outlined, s.reservasTitle, const ReservasPage()),
        (Icons.qr_code_2_outlined, s.mesasQrTitle, const MesasQrPage()),
      ],
      // Ajustes: para todos (Apariencia/perfil son universales).
      (Icons.settings_outlined, s.ajustesTitle, const AjustesPage()),
      if (isOwner)
        (Icons.card_membership_outlined, s.billingTitle,
            const SuscripcionPage()),
      if (isPlatformAdmin)
        (Icons.workspace_premium_outlined, s.platformTitle,
            const PlatformPage()),
    ];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassPanel(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Material(
            type: MaterialType.transparency,
            child: Column(
              children: [
                for (var i = 0; i < items.length; i++) ...[
                  if (i > 0) const Divider(height: 1),
                  _tile(context, items[i].$1, items[i].$2, items[i].$3),
                ],
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _tile(BuildContext context, IconData icon, String title, Widget page) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => Navigator.of(context)
          .push(MaterialPageRoute(builder: (_) => page)),
    );
  }
}
