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
import '../finance/advisor_page.dart';
import '../finance/finanzas_page.dart';
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

/// Hub de la tab "Más": accesos a Fichaje, Propinas (admin/cajero) e Impresora.
class MorePage extends ConsumerWidget {
  const MorePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final sessionState = ref.watch(sessionProvider);
    final role = sessionState is SessionAuthenticated
        ? sessionState.session.role
        : null;
    final isAdmin = role == Role.owner || role == Role.manager || role == Role.cashier;
    final isOwner = role == Role.owner;
    // El panel de plataforma se muestra solo a super-admins (flag del backend).
    final isPlatformAdmin =
        ref.watch(platformAccessProvider).valueOrNull ?? false;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        GlassPanel(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Material(
            type: MaterialType.transparency,
            child: Column(
              children: [
                _tile(context, Icons.schedule_outlined, s.fichajeTitle,
                    const FichajePage()),
                if (isAdmin) ...[
                  const Divider(height: 1),
                  _tile(context, Icons.volunteer_activism_outlined, s.tipsTitle,
                      const TipsPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.badge_outlined, s.staffTitle,
                      const StaffPage()),
                ],
                const Divider(height: 1),
                _tile(context, Icons.print_outlined, s.printerTitle,
                    const PrinterPage()),
                if (isAdmin) ...[
                  const Divider(height: 1),
                  _tile(context, Icons.inventory_2_outlined, s.productosTitle,
                      const ProductosPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.egg_alt_outlined, s.insumosTitle,
                      const InsumosPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.local_shipping_outlined,
                      s.proveedoresTitle, const ProveedoresPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.account_balance_wallet_outlined,
                      s.finanzasTitle, const FinanzasPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.auto_awesome_outlined, s.advisorTitle,
                      const AdvisorPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.shopping_cart_outlined, s.gastosTitle,
                      const GastosPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.receipt_long_outlined,
                      s.comprobantesTitle, const ComprobantesPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.bar_chart_outlined, s.reportesTitle,
                      const ReportesPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.query_stats_outlined, s.analyticsTitle,
                      const AnalyticsPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.people_alt_outlined, s.clientesTitle,
                      const ClientesPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.event_available_outlined,
                      s.reservasTitle, const ReservasPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.qr_code_2_outlined, s.mesasQrTitle,
                      const MesasQrPage()),
                  const Divider(height: 1),
                  _tile(context, Icons.settings_outlined, s.ajustesTitle,
                      const AjustesPage()),
                ],
                if (isOwner) ...[
                  const Divider(height: 1),
                  _tile(context, Icons.card_membership_outlined,
                      s.billingTitle, const SuscripcionPage()),
                ],
                if (isPlatformAdmin) ...[
                  const Divider(height: 1),
                  _tile(context, Icons.workspace_premium_outlined,
                      s.platformTitle, const PlatformPage()),
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
