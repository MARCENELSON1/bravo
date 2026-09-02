import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import 'sectors_repository.dart';

/// Ajustes › Salones y mesas — paridad con el SectorsManager del web: listar,
/// crear, renombrar y borrar sectores.
class SalonesSettingsSection extends ConsumerWidget {
  const SalonesSettingsSection({super.key});

  Future<void> _editDialog(BuildContext context, WidgetRef ref,
      {Sector? sector}) async {
    final s = context.s;
    final controller = TextEditingController(text: sector?.name ?? '');
    final name = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(sector == null ? s.sectorAdd : s.sectorName),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: InputDecoration(labelText: s.sectorName),
          onSubmitted: (v) => Navigator.pop(ctx, v.trim()),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: Text(s.cancel)),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, controller.text.trim()),
            child: Text(s.setSave),
          ),
        ],
      ),
    );
    if (name == null || name.isEmpty) return;
    try {
      final repo = ref.read(sectorsRepositoryProvider);
      if (sector == null) {
        await repo.create(name);
      } else {
        await repo.update(sector.id, name, color: sector.color,
            sortOrder: sector.sortOrder);
      }
      ref.invalidate(sectorsProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.sectorSaved)));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.sectorSaveError)));
      }
    }
  }

  Future<void> _delete(
      BuildContext context, WidgetRef ref, Sector sector) async {
    final s = context.s;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(s.sectorDeleteConfirm(sector.name)),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false), child: Text(s.cancel)),
          FilledButton(
            style: FilledButton.styleFrom(
                backgroundColor: Theme.of(ctx).colorScheme.error),
            onPressed: () => Navigator.pop(ctx, true),
            child: Text(s.setDelete),
          ),
        ],
      ),
    );
    if (ok != true) return;
    try {
      await ref.read(sectorsRepositoryProvider).delete(sector.id);
      ref.invalidate(sectorsProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.sectorDeleted)));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.sectorSaveError)));
      }
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final async = ref.watch(sectorsProvider);
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.sectorsTitle, style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 4),
          Text(s.sectorsDesc,
              style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  fontSize: 13)),
          const SizedBox(height: 8),
          async.when(
            loading: () => const Padding(
              padding: EdgeInsets.all(8),
              child: Center(child: CircularProgressIndicator()),
            ),
            error: (e, _) =>
                Text(e is ApiError ? e.message : s.sectorSaveError),
            data: (sectors) => Column(
              children: [
                if (sectors.isEmpty)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: Text(s.sectorsEmpty,
                        style: TextStyle(
                            color:
                                Theme.of(context).colorScheme.onSurfaceVariant)),
                  ),
                for (final sector in sectors)
                  Material(
                    type: MaterialType.transparency,
                    child: ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: _colorDot(sector.color, context),
                      title: Text(sector.name),
                      trailing: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          IconButton(
                            icon: const Icon(Icons.edit_outlined),
                            tooltip: s.setEdit,
                            onPressed: () =>
                                _editDialog(context, ref, sector: sector),
                          ),
                          IconButton(
                            icon: const Icon(Icons.delete_outline),
                            tooltip: s.setDelete,
                            color: Theme.of(context).colorScheme.error,
                            onPressed: () => _delete(context, ref, sector),
                          ),
                        ],
                      ),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton.icon(
              onPressed: () => _editDialog(context, ref),
              icon: const Icon(Icons.add),
              label: Text(s.sectorAdd),
            ),
          ),
        ],
      ),
    );
  }

  Widget _colorDot(String? color, BuildContext context) {
    final c = _parseColor(color) ?? Theme.of(context).colorScheme.primary;
    return Container(
      width: 14,
      height: 14,
      decoration: BoxDecoration(color: c, shape: BoxShape.circle),
    );
  }

  Color? _parseColor(String? hex) {
    if (hex == null) return null;
    var h = hex.replaceFirst('#', '');
    if (h.length == 6) h = 'FF$h';
    final v = int.tryParse(h, radix: 16);
    return v == null ? null : Color(v);
  }
}
