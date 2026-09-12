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
          // El cuerpo llega hasta el pie de la pantalla y la barra flota encima.
          // Es lo que le da al vidrio algo que difuminar —la lista que le pasa
          // por debajo— y a cambio obliga a que cada pantalla deje aire al final
          // para que su último ítem pueda subir: eso es `navBarInset`.
          extendBody: true,
          body: Stack(
            children: [
              // IndexedStack mantiene vivas todas las tabs → conservan scroll,
              // formularios y conexiones en vivo al cambiar de una a otra.
              SafeArea(
                // Abajo no: ahí el `Scaffold` publica el alto de la barra y las
                // pantallas lo consumen ellas. Recortarlo acá lo escondería.
                bottom: false,
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

/// La barra de navegación como una pastilla de vidrio que flota.
///
/// Antes iba pegada de borde a borde y con las esquinas en punto: ocupaba el
/// pie de la pantalla como un zócalo, que es justo lo contrario de lo que hacen
/// los paneles de arriba. Ahora se despega de los tres bordes, alineada con el
/// margen de las tarjetas, y lleva su borde de un pelo y su desenfoque para que
/// se lea como una más de la familia y no como parte del teléfono. El gris es
/// el de las superficies de la app, no el velo fino de las tarjetas: la barra
/// tiene texto chico encima y tiene que sostenerlo.
///
/// Lo que difumina es el fondo escénico que pinta `AppBackground`: el degradado,
/// el grano y las manchas que se mueven despacio. El grano es lo que más se
/// nota, porque es lo único de alta frecuencia ahí abajo.
class _GlassNavBar extends StatelessWidget {
  const _GlassNavBar({required this.child});

  final Widget child;

  /// Casi una cápsula. La barra mide 78 de alto, así que 32 la redondea hasta
  /// el límite de lo que todavía se lee como un rectángulo blando y no como un
  /// óvalo, que a lo ancho de la pantalla quedaría raro.
  static const double _radius = 32;

  /// El mismo margen que usa el contenido de las pantallas, para que la barra
  /// caiga en la misma columna que las tarjetas que tiene encima.
  static const double _sideMargin = 16;

  /// Cuánto del velo tapa al desenfoque.
  ///
  /// Bastante: la barra es del gris de las superficies, no un vidrio fino como
  /// el de las tarjetas. Lleva texto de 13 encima y no puede depender de qué
  /// mancha del fondo le toque pasar por detrás. Lo que pasa —ese 18%— alcanza
  /// para que la lista que corre por abajo se adivine desenfocada y la barra
  /// cambie sola, sin que nada se lea a través.
  static const double _fill = 0.82;

  @override
  Widget build(BuildContext context) {
    final dark = Theme.of(context).brightness == Brightness.dark;
    final scheme = Theme.of(context).colorScheme;
    final mq = MediaQuery.of(context);
    final radius = BorderRadius.circular(_radius);
    // La barra de inicio del iPhone reserva 34 abajo. La pastilla no los
    // necesita adentro —no hay nada que proteger ahí— pero sí hay que dejar
    // aire debajo de ella: la mitad alcanza para que no se toquen, y en un
    // teléfono sin barra de inicio el mínimo sigue siendo un margen normal.
    final bottomMargin = math.max(mq.padding.bottom / 2, 12.0);

    return Padding(
      padding: EdgeInsets.only(
        left: _sideMargin,
        right: _sideMargin,
        bottom: bottomMargin,
      ),
      child: DecoratedBox(
        // La sombra va afuera del recorte: adentro quedaría tapada por el
        // propio panel y la pastilla no se despegaría de nada.
        decoration: BoxDecoration(
          borderRadius: radius,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: dark ? 0.34 : 0.10),
              blurRadius: 28,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: ClipRRect(
          borderRadius: radius,
          child: BackdropFilter(
            // Más que el de `GlassPanel` (18): esta superficie es ancha y baja,
            // y con menos desenfoque se le ven las vetas del grano en diagonal.
            filter: ImageFilter.blur(sigmaX: 24, sigmaY: 24),
            child: DecoratedBox(
              decoration: BoxDecoration(
                color: scheme.surface.withValues(alpha: _fill),
                borderRadius: radius,
                border: Border.all(
                  color: dark
                      ? Colors.white.withValues(alpha: 0.12)
                      : Colors.black.withValues(alpha: 0.08),
                ),
              ),
              child: MediaQuery(
                // El área segura la resuelve el margen de afuera; adentro sería
                // un colchón de 34 dentro de una pastilla de 64.
                data: mq.copyWith(padding: mq.padding.copyWith(bottom: 0)),
                child: child,
              ),
            ),
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
