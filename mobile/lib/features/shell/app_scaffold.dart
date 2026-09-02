import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session.dart';
import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../cashier/cashier_page.dart';
import '../floor/floor_page.dart';
import '../home/home_page.dart';
import '../kds/kds_page.dart';
import '../order/order_dtos.dart';

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
        body: Stack(
          children: [AppBackground(), Center(child: CircularProgressIndicator())],
        ),
      );
    }

    final s = context.s;
    final tabs = _tabsForRole(session.session.role, s);
    final safeIndex = _index.clamp(0, tabs.length - 1);

    return Scaffold(
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(child: tabs[safeIndex].page),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: safeIndex,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: [
          for (final t in tabs)
            NavigationDestination(icon: Icon(t.icon), label: t.label),
        ],
      ),
    );
  }

  List<_TabDef> _tabsForRole(Role role, Strings s) {
    final home = _TabDef(Icons.home_outlined, s.navHome, const HomePage());
    final more = _TabDef(Icons.grid_view_outlined, s.navMore, _Placeholder(s.navMore));
    final floor = _TabDef(Icons.tab_outlined, s.navFloor, const FloorPage());
    switch (role) {
      case Role.waiter:
        return [
          home,
          floor,
          _TabDef(Icons.point_of_sale_outlined, s.navCashier, _Placeholder(s.navCashier)),
          more,
        ];
      case Role.kitchen:
      case Role.bar:
        final station = role == Role.bar ? Station.bar : Station.kitchen;
        return [
          home,
          _TabDef(
            role == Role.bar ? Icons.local_bar_outlined : Icons.restaurant_outlined,
            role == Role.bar ? s.kdsBar : s.kdsKitchen,
            KdsPage(station: station),
          ),
          more,
        ];
      case Role.cashier:
        return [
          home,
          floor,
          _TabDef(Icons.point_of_sale_outlined, s.cashierTitle, const CashierPage()),
          more,
        ];
      case Role.owner:
      case Role.manager:
        return [
          home,
          floor,
          _TabDef(Icons.insights_outlined, s.navFinance, _Placeholder(s.navFinance)),
          more,
        ];
    }
  }
}

class _TabDef {
  const _TabDef(this.icon, this.label, this.page);
  final IconData icon;
  final String label;
  final Widget page;
}

class _Placeholder extends StatelessWidget {
  const _Placeholder(this.title);
  final String title;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: GlassPanel(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(title, style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              Text('${s.comingSoon} · F1'),
            ],
          ),
        ),
      ),
    );
  }
}
