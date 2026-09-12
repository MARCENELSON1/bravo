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

/// Ajustes — **listado de secciones**, no una tira de pestañas.
///
/// Espejo de la estructura que el web adoptó en `72d8698`: trece pestañas no
/// entraban en ninguna pantalla y había que arrastrar de costado para descubrir
/// que existían Equipo o Integraciones. Un teléfono es peor todavía para eso.
/// Ahora es una entrada por sección y la salida es siempre un paso.
///
/// La diferencia con el web es la mecánica, no la estructura: allá el listado y
/// la sección se cruzan con un deslizamiento propio; acá se empuja una pantalla,
/// que es el gesto que el sistema ya trae —con su deslizamiento desde el borde
/// para volver— y que nadie tiene que aprender.
///
/// Una sección entra al listado solo si tiene contenido real: ver
/// [SettingRow.isReal] y el porqué en `settings_sections.dart`.

class AjustesPage extends ConsumerWidget {
  const AjustesPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final en = Localizations.localeOf(context).languageCode == 'en';
    final st = ref.watch(sessionProvider);
    final session = st is SessionAuthenticated ? st.session : null;
    final isAdmin = session?.role.isAdmin ?? false;

    final tabs = visibleSettingsTabs(isAdmin: isAdmin);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.ajustesTitle),
        backgroundColor: Colors.transparent,
      ),
      body: SafeArea(
        top: false,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            GlassPanel(
              padding: const EdgeInsets.symmetric(vertical: 4),
              child: Material(
                type: MaterialType.transparency,
                child: Column(
                  children: [
                    for (final t in tabs)
                      _SectionEntry(tab: t, en: en, isAdmin: isAdmin),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// Una entrada del listado. Sin línea divisoria, igual que el web: el alto de la
/// fila y el espacio alcanzan para separarlas.
class _SectionEntry extends StatelessWidget {
  const _SectionEntry({
    required this.tab,
    required this.en,
    required this.isAdmin,
  });

  final SettingsTab tab;
  final bool en;
  final bool isAdmin;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ListTile(
      title: Text(tab.title(en)),
      trailing: Icon(Icons.chevron_right, color: scheme.onSurfaceVariant),
      onTap: () => Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => _SectionPage(tab: tab, isAdmin: isAdmin),
        ),
      ),
    );
  }
}

/// Una sección, en su propia pantalla. El título es el de la sección y el único
/// control de salida es el de volver — "de una sección al listado, del listado
/// afuera", como en el web.
class _SectionPage extends ConsumerWidget {
  const _SectionPage({required this.tab, required this.isAdmin});

  final SettingsTab tab;
  final bool isAdmin;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final en = Localizations.localeOf(context).languageCode == 'en';
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(tab.title(en)),
        backgroundColor: Colors.transparent,
      ),
      body: SafeArea(
        top: false,
        child: _SectionBody(tab: tab, isAdmin: isAdmin),
      ),
    );
  }
}

class _SectionBody extends ConsumerWidget {
  const _SectionBody({required this.tab, required this.isAdmin});

  final SettingsTab tab;
  final bool isAdmin;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final en = Localizations.localeOf(context).languageCode == 'en';
    final st = ref.watch(sessionProvider);
    final session = st is SessionAuthenticated ? st.session : null;
    final rows = visibleRows(tab);

    // Las secciones funcionales son OWNER/MANAGER: a un operativo le darían 403,
    // así que su sección directamente no aparece en el listado.
    final section = switch (tab.id) {
      'apariencia' => _Appearance(),
      'caja' when isAdmin => const CajaSettingsSection(),
      'salones' when isAdmin => const SalonesSettingsSection(),
      'negocio' when isAdmin => const NegocioSettingsSection(),
      'equipo' when isAdmin => const EquipoSettingsSection(),
      'integraciones' when isAdmin => const IntegracionesSettingsSection(),
      _ => null,
    };

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (section != null) ...[section, const SizedBox(height: 16)],
        if (rows.isNotEmpty)
          GlassPanel(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Material(
              type: MaterialType.transparency,
              child: Column(
                children: [
                  for (final r in rows)
                    _Row(row: r, en: en, session: session, s: s),
                ],
              ),
            ),
          ),
      ],
    );
  }
}

class _Appearance extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final mode = ref.watch(themeModeProvider);
    final reduceMotion = ref.watch(reduceMotionProvider);
    // El `Material` va adentro del panel a propósito: `GlassPanel` pinta un
    // fondo, y `ListTile` dibuja su realce sobre el `Material` más cercano —
    // si ese Material queda por encima del fondo, el toque no se ve.
    return GlassPanel(
      child: Material(
        type: MaterialType.transparency,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(s.theme, style: Theme.of(context).textTheme.titleSmall),
            const SizedBox(height: 8),
            SegmentedButton<ThemeMode>(
              segments: [
                ButtonSegment(
                  value: ThemeMode.light,
                  label: Text(s.themeLight),
                ),
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
      ),
    );
  }
}

/// Una fila: nombre a la izquierda, valor a la derecha. Sin línea divisoria y
/// sin botón "Editar" — el web lo sacó porque estaba deshabilitado en todas y
/// prometía una acción que no existía; acá el filtro de [SettingRow.isReal] ya
/// dejó afuera esas filas, así que la que queda o muestra un dato cierto o abre
/// una pantalla, y en ese caso la fila ENTERA es lo que se toca.
class _Row extends StatelessWidget {
  const _Row({
    required this.row,
    required this.en,
    required this.session,
    required this.s,
  });

  final SettingRow row;
  final bool en;
  final Session? session;
  final Strings s;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final value = _dyn(row.dyn, session) ?? row.value(en);
    final opens = row.open != null;

    return ListTile(
      leading: row.dyn == 'avatar'
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
        row.label(en),
        style: row.danger ? TextStyle(color: scheme.error) : null,
      ),
      subtitle: row.desc(en) == null ? null : Text(row.desc(en)!),
      trailing: value != null
          ? Text(value, style: TextStyle(color: scheme.onSurfaceVariant))
          : opens
          ? Icon(
              Icons.chevron_right,
              color: row.danger ? scheme.error : scheme.onSurfaceVariant,
            )
          : null,
      onTap: opens
          ? () =>
                Navigator.of(context)
                    .push(MaterialPageRoute(builder: (_) => row.open!()))
          : null,
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
