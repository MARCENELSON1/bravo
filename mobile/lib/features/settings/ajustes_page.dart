import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session.dart';
import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../../theme/theme_controller.dart';
import '../../ui/glass_panel.dart';
import 'caja_settings_section.dart';
import 'equipo_settings_section.dart';
import 'integraciones_settings_section.dart';
import 'negocio_settings_section.dart';
import 'salones_settings_section.dart';
import 'settings_sections.dart';

/// Filas placeholder que se ocultan porque la sección ya las renderiza como
/// controles reales (para no mostrarlas dos veces).
/// Tabs que renderizan un widget real (no filas) — deben sobrevivir el filtro
/// aunque todas sus filas sean de relleno. Espejo de los `if (tab.id == ...)` del
/// build; si se agrega una sección allá, va acá.
const _tabsWithSection = <String>{
  'apariencia',
  'caja',
  'salones',
  'negocio',
  'equipo',
  'integraciones',
};

bool _hasSection(String id, bool isAdmin) =>
    id == 'apariencia' || (isAdmin && _tabsWithSection.contains(id));

const _functionalRows = <String, Set<String>>{
  'caja': {'Apertura de caja obligatoria', 'Arqueo ciego'},
  'salones': {'Sectores'},
  'negocio': {'Dirección'},
  'integraciones': {'Mercado Pago'},
};

/// Ajustes (Fase 6) — portado 1:1 de la config del web: 13 tabs. Apariencia es
/// funcional (tema + reducir movimiento); las demás secciones se irán volviendo
/// reales por tanda (caja, salones, integraciones, equipo, negocio, IA). El
/// resto de las filas son "Próximamente", igual que en la web.
class AjustesPage extends ConsumerWidget {
  const AjustesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final en = Localizations.localeOf(context).languageCode == 'en';
    // Una tab entra si tiene una sección real o al menos una fila real. Sin esto,
    // filtrar las filas de relleno dejaba tabs vacías — que se ven tan rotas como
    // el "Próximamente" que vinimos a sacar. Se enciende sola cuando su contenido
    // se vuelve real, así que no hay una lista que mantener a mano.
    final st = ref.watch(sessionProvider);
    final isAdmin = (st is SessionAuthenticated
        ? st.session.role.isAdmin
        : false);
    final tabs = [
      for (final t in settingsTabs)
        if (_hasSection(t.id, isAdmin) || t.rows.any((r) => r.isReal)) t,
    ];
    return DefaultTabController(
      length: tabs.length,
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: Text(s.ajustesTitle),
          backgroundColor: Colors.transparent,
          bottom: TabBar(
            isScrollable: true,
            tabAlignment: TabAlignment.start,
            tabs: [for (final t in tabs) Tab(text: t.title(en))],
          ),
        ),
        body: Stack(
          children: [
            SafeArea(
              top: false,
              child: TabBarView(
                children: [for (final t in tabs) _TabView(tab: t)],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _TabView extends ConsumerWidget {
  const _TabView({required this.tab});
  final SettingsTab tab;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final en = Localizations.localeOf(context).languageCode == 'en';
    final sessionState = ref.watch(sessionProvider);
    final session = sessionState is SessionAuthenticated
        ? sessionState.session
        : null;
    // Las secciones funcionales (caja/salones/negocio/equipo/integraciones) son
    // OWNER/MANAGER — a los operativos les daría 403. Para ellos la tab no
    // aparece: antes quedaba visible y vacía.
    final isAdmin = session?.role.isAdmin ?? false;

    // Solo sobrevive la fila que lee estado real o abre algo que existe. Antes se
    // renderizaban las 83 y las que no tenían backend mostraban "Próximamente" o
    // un valor inventado; `hidden` tapaba apenas 5. Ver `settings_sections.dart`.
    final hidden = isAdmin
        ? (_functionalRows[tab.id] ?? const <String>{})
        : const <String>{};
    final rows = [
      for (final r in tab.rows)
        if (r.isReal && !hidden.contains(r.es)) r,
    ];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (tab.id == 'apariencia') ...[
          _appearance(context, ref, s),
          const SizedBox(height: 16),
        ],
        if (tab.id == 'caja' && isAdmin) ...[
          const CajaSettingsSection(),
          const SizedBox(height: 16),
        ],
        if (tab.id == 'salones' && isAdmin) ...[
          const SalonesSettingsSection(),
          const SizedBox(height: 16),
        ],
        if (tab.id == 'negocio' && isAdmin) ...[
          const NegocioSettingsSection(),
          const SizedBox(height: 16),
        ],
        if (tab.id == 'equipo' && isAdmin) ...[
          const EquipoSettingsSection(),
          const SizedBox(height: 16),
        ],
        if (tab.id == 'integraciones' && isAdmin) ...[
          const IntegracionesSettingsSection(),
          const SizedBox(height: 16),
        ],
        if (rows.isNotEmpty)
          GlassPanel(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Material(
              type: MaterialType.transparency,
              child: Column(
                children: [
                  for (var i = 0; i < rows.length; i++) ...[
                    if (i > 0) const Divider(height: 1),
                    _row(context, s, en, rows[i], session),
                  ],
                ],
              ),
            ),
          ),
      ],
    );
  }

  Widget _appearance(BuildContext context, WidgetRef ref, Strings s) {
    final mode = ref.watch(themeModeProvider);
    final reduceMotion = ref.watch(reduceMotionProvider);
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.theme, style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 8),
          SegmentedButton<ThemeMode>(
            segments: [
              ButtonSegment(value: ThemeMode.light, label: Text(s.themeLight)),
              ButtonSegment(value: ThemeMode.dark, label: Text(s.themeDark)),
              ButtonSegment(
                value: ThemeMode.system,
                label: Text(s.themeSystem),
              ),
            ],
            selected: {mode},
            onSelectionChanged: (sel) =>
                ref.read(themeModeProvider.notifier).set(sel.first),
          ),
          const Divider(height: 24),
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: reduceMotion,
            onChanged: (v) => ref.read(reduceMotionProvider.notifier).set(v),
            title: Text(s.reduceMotion),
            subtitle: Text(s.reduceMotionDesc),
          ),
        ],
      ),
    );
  }

  Widget _row(
    BuildContext context,
    Strings s,
    bool en,
    SettingRow r,
    Session? session,
  ) {
    final scheme = Theme.of(context).colorScheme;
    final value = _dyn(r.dyn, session) ?? r.value(en);

    Widget? trailing;
    if (r.toggle) {
      trailing = const Switch(value: false, onChanged: null); // deshabilitado
    } else if (value != null) {
      trailing = Text(value, style: TextStyle(color: scheme.onSurfaceVariant));
    } else if (r.open != null) {
      trailing = TextButton(
        onPressed: () =>
            Navigator.of(context)
                .push(MaterialPageRoute(builder: (_) => r.open!())),
        style: TextButton.styleFrom(
          foregroundColor: r.danger ? scheme.error : scheme.primary,
        ),
        child: Text(settingsActionLabel(r.action ?? 'view', en)),
      );
    }

    return ListTile(
      leading: r.dyn == 'avatar'
          ? CircleAvatar(
              backgroundColor: scheme.primary,
              child: Text(
                _initials(session),
                style: TextStyle(
                  color: scheme.onPrimary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            )
          : null,
      title: Text(
        r.label(en),
        style: r.danger ? TextStyle(color: scheme.error) : null,
      ),
      subtitle: r.desc(en) == null ? null : Text(r.desc(en)!),
      trailing: trailing,
    );
  }

  String? _dyn(String? dyn, Session? session) {
    if (session == null || dyn == null) return null;
    return switch (dyn) {
      'name' => session.displayName,
      'email' => session.email,
      'tenant' => session.tenantName,
      _ => null,
    };
  }

  String _initials(Session? session) {
    final base = session?.name?.trim().isNotEmpty == true
        ? session!.name!.trim()
        : (session?.email ?? '?');
    final parts = base
        .split(RegExp(r'[ @.]'))
        .where((p) => p.isNotEmpty)
        .toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return (parts[0].substring(0, 1) + parts[1].substring(0, 1)).toUpperCase();
  }
}
