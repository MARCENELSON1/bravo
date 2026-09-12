import 'dart:math' as math;
import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session.dart';
import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../cashier/cashier_page.dart';
import '../crm/clientes_page.dart';
import '../finance/advisor_page.dart';
import '../finance/finanzas_page.dart';
import '../floor/floor_page.dart';
import '../home/home_page.dart';
import '../kds/kds_page.dart';
import '../order/order_dtos.dart';
import '../reservations/reservas_page.dart';
import '../tips/tips_page.dart';
import 'more_page.dart';
import 'push_handler.dart';
import 'ready_alert.dart';

/// Shell con bottom nav por rol (espeja `role-landing.tsx` + la navegación del
/// front). En F0, todas las tabs menos "Inicio" son placeholders (llegan en F1).
class AppScaffold extends ConsumerStatefulWidget {
  const AppScaffold({super.key});

  @override
  ConsumerState<AppScaffold> createState() => _AppScaffoldState();
}

class _AppScaffoldState extends ConsumerState<AppScaffold> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    if (session is! SessionAuthenticated) {
      return const Scaffold(
        body: Stack(children: [Center(child: CircularProgressIndicator())]),
      );
    }

    final s = context.s;
    final tabs = _tabsForRole(session.session.role, s);
    final safeIndex = _index.clamp(0, tabs.length - 1);

    // PushHandler: registra el token de push + abre el modal al tocar una
    // notificación (app cerrada). ReadyAlert: aviso en vivo (SSE) con la app
    // abierta. Ambos montados una sola vez, solo con sesión autenticada.
    return PushHandler(
      child: ReadyAlert(
        child: Scaffold(
          // Transparente: el fondo escénico lo pinta el `builder` de MaterialApp,
          // una vez para toda la app. Un Scaffold opaco acá lo taparía.
          backgroundColor: Colors.transparent,
          body: Stack(
            children: [
              // IndexedStack mantiene vivas todas las tabs → conservan scroll,
              // formularios y conexiones en vivo al cambiar de una a otra.
              SafeArea(
                child: IndexedStack(
                  index: safeIndex,
                  children: [for (final t in tabs) t.page],
                ),
              ),
            ],
          ),
          bottomNavigationBar: _GlassNavBar(
            child: NavigationBar(
              // El material lo pinta `_GlassNavBar`; la barra va transparente
              // para no taparlo con su propio fondo.
              backgroundColor: Colors.transparent,
              surfaceTintColor: Colors.transparent,
              shadowColor: Colors.transparent,
              selectedIndex: safeIndex,
              onDestinationSelected: (i) => setState(() => _index = i),
              destinations: [
                for (final t in tabs)
                  NavigationDestination(icon: Icon(t.icon), label: t.label),
              ],
            ),
          ),
        ),
      ),
    );
  }

  List<_TabDef> _tabsForRole(Role role, Strings s) {
    final home = _TabDef(Icons.home_outlined, s.navHome, const HomePage());
    final more = _TabDef(Icons.grid_view_outlined, s.navMore, const MorePage());
    final floor = _TabDef(Icons.tab_outlined, s.navFloor, const FloorPage());
    // La barra calca las capacidades de cada rol (guards `RequireRole` del web).
    // Los roles operativos NO tienen "Inicio" (el dashboard es de OWNER/MANAGER):
    // arrancan directo en su pantalla de trabajo.
    switch (role) {
      case Role.waiter:
        return [
          floor,
          _TabDef(
            Icons.event_available_outlined,
            s.reservasTitle,
            const ReservasPage(),
          ),
          _TabDef(
            Icons.people_alt_outlined,
            s.clientesTitle,
            const ClientesPage(),
          ),
          more,
        ];
      case Role.kitchen:
      case Role.bar:
        final station = role == Role.bar ? Station.bar : Station.kitchen;
        return [
          _TabDef(
            role == Role.bar
                ? Icons.local_bar_outlined
                : Icons.restaurant_outlined,
            role == Role.bar ? s.kdsBar : s.kdsKitchen,
            KdsPage(station: station),
          ),
          more,
        ];
      case Role.cashier:
        return [
          floor,
          _TabDef(
            Icons.point_of_sale_outlined,
            s.cashierTitle,
            const CashierPage(),
          ),
          _TabDef(
            Icons.volunteer_activism_outlined,
            s.tipsTitle,
            const TipsPage(),
          ),
          more,
        ];
      case Role.owner:
      case Role.manager:
        return [
          home,
          floor,
          _TabDef(Icons.insights_outlined, s.navFinance, const FinanzasPage()),
          _TabDef(
            Icons.auto_awesome_outlined,
            s.advisorTitle,
            const AdvisorPage(),
          ),
          more,
        ];
    }
  }
}

/// La barra de navegación como vidrio esmerilado **opaco**.
///
/// Difumina lo que queda atrás —el fondo escénico que pinta `AppBackground`: el
/// degradado, el grano y las manchas que se mueven despacio— y lo cubre con un
/// tinte denso. Denso a propósito: no es una barra a través de la cual se ve,
/// es una superficie sólida que respira con lo que tiene detrás. El grano es lo
/// que más se nota, porque es lo único de alta frecuencia ahí abajo: el
/// desenfoque lo alisa y deja una banda más limpia que el resto de la pantalla.
///
/// El `NavigationBar` se reserva el área segura de abajo por su cuenta, así que
/// el tinte llega hasta el borde inferior del teléfono sin cortarse.
class _GlassNavBar extends StatelessWidget {
  const _GlassNavBar({required this.child});

  final Widget child;

  /// Cuánto del fondo pasa. Por encima de esto la barra deja de leerse como una
  /// superficie; por debajo, el desenfoque no se nota y es un rectángulo de
  /// color. El sistema llama a esto un material "grueso".
  static const double _fill = 0.82;

  /// Cuánto aire dejar bajo los textos, en un teléfono con barra de inicio.
  ///
  /// El sistema reserva 34 ahí, pensados para que nada quede debajo del dedo
  /// que desliza para salir de la app. Nuestro contenido más bajo son los
  /// textos, que no se tocan —lo que se toca es la fila entera, bien más
  /// arriba—, así que con 22 la barra de inicio sigue teniendo su lugar y la
  /// barra deja de tener un tercio de sí misma en blanco.
  static const double _bottomInset = 22;

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final scheme = Theme.of(context).colorScheme;
    final mq = MediaQuery.of(context);
    return ClipRect(
      child: BackdropFilter(
        // Más que el de `GlassPanel` (18): esta superficie es ancha y baja, y
        // con menos desenfoque se le ven las vetas del grano en diagonal.
        filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
        child: DecoratedBox(
          decoration: BoxDecoration(
            color: scheme.surface.withValues(alpha: _fill),
            border: Border(
              top: BorderSide(
                color: dark
                    ? Colors.white.withValues(alpha: 0.10)
                    : Colors.black.withValues(alpha: 0.08),
              ),
            ),
          ),
          child: MediaQuery(
            // En un teléfono sin barra de inicio el inset ya es 0 o casi: el
            // mínimo se respeta, no se inventa aire donde no hacía falta.
            data: mq.copyWith(
              padding: mq.padding.copyWith(
                bottom: math.min(mq.padding.bottom, _bottomInset),
              ),
            ),
            child: child,
          ),
        ),
      ),
    );
  }
}

class _TabDef {
  const _TabDef(this.icon, this.label, this.page);
  final IconData icon;
  final String label;
  final Widget page;
}
