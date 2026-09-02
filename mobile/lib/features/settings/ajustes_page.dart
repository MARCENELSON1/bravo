import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session.dart';
import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../../theme/theme_controller.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import 'settings_sections.dart';

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
    return DefaultTabController(
      length: settingsTabs.length,
      child: Scaffold(
        backgroundColor: Colors.transparent,
        appBar: AppBar(
          title: Text(s.ajustesTitle),
          backgroundColor: Colors.transparent,
          bottom: TabBar(
            isScrollable: true,
            tabAlignment: TabAlignment.start,
            tabs: [for (final t in settingsTabs) Tab(text: t.title(en))],
          ),
        ),
        body: Stack(
          children: [
            const AppBackground(),
            SafeArea(
              top: false,
              child: TabBarView(
                children: [for (final t in settingsTabs) _TabView(tab: t)],
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
    final session =
        sessionState is SessionAuthenticated ? sessionState.session : null;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (tab.id == 'apariencia') ...[
          _appearance(context, ref, s),
          const SizedBox(height: 16),
        ],
        GlassPanel(
          padding: const EdgeInsets.symmetric(vertical: 4),
          child: Material(
            type: MaterialType.transparency,
            child: Column(
              children: [
                for (var i = 0; i < tab.rows.length; i++) ...[
                  if (i > 0) const Divider(height: 1),
                  _row(context, s, en, tab.rows[i], session),
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
              ButtonSegment(value: ThemeMode.system, label: Text(s.themeSystem)),
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
      trailing = Text(value,
          style: TextStyle(color: scheme.onSurfaceVariant));
    } else if (r.action != null) {
      trailing = TextButton(
        onPressed: () => ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.editSoon))),
        style: TextButton.styleFrom(
          foregroundColor:
              r.danger ? scheme.error : scheme.onSurfaceVariant,
        ),
        child: Text(settingsActionLabel(r.action!, en)),
      );
    }

    return ListTile(
      leading: r.dyn == 'avatar'
          ? CircleAvatar(
              backgroundColor: scheme.primary,
              child: Text(_initials(session),
                  style: TextStyle(
                      color: scheme.onPrimary, fontWeight: FontWeight.w600)),
            )
          : null,
      title: Text(r.label(en),
          style: r.danger ? TextStyle(color: scheme.error) : null),
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
    final parts = base.split(RegExp(r'[ @.]')).where((p) => p.isNotEmpty).toList();
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts.first.substring(0, 1).toUpperCase();
    return (parts[0].substring(0, 1) + parts[1].substring(0, 1)).toUpperCase();
  }
}
