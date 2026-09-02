import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import 'supplier_repository.dart';

/// Proveedores (Fase 6): lista + alta/edición.
class ProveedoresPage extends ConsumerStatefulWidget {
  const ProveedoresPage({super.key});

  @override
  ConsumerState<ProveedoresPage> createState() => _ProveedoresPageState();
}

class _ProveedoresPageState extends ConsumerState<ProveedoresPage> {
  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(suppliersProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.proveedoresTitle),
        backgroundColor: Colors.transparent,
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _form(s, null),
        child: const Icon(Icons.add),
      ),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => ErrorView(
                error: e,
                onRetry: () => ref.invalidate(suppliersProvider),
              ),
              data: (list) {
                Future<void> refresh() async =>
                    ref.invalidate(suppliersProvider);
                if (list.isEmpty) {
                  return RefreshIndicator(
                    onRefresh: refresh,
                    child: ListView(
                      physics: const AlwaysScrollableScrollPhysics(),
                      children: [
                        SizedBox(
                            height: 280,
                            child: EmptyView(message: s.proveedoresEmpty)),
                      ],
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: refresh,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    children: [
                      GlassPanel(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Material(
                          type: MaterialType.transparency,
                          child: Column(
                            children: [
                              for (var i = 0; i < list.length; i++) ...[
                                if (i > 0) const Divider(height: 1),
                                _tile(s, list[i]),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _tile(Strings s, Supplier sup) {
    final sub = [
      if (sup.contact != null && sup.contact!.isNotEmpty) sup.contact!,
      if (sup.phone != null && sup.phone!.isNotEmpty) sup.phone!,
    ].join(' · ');
    return ListTile(
      title: Text(sup.name),
      subtitle: sub.isEmpty ? null : Text(sub),
      trailing: sup.active
          ? null
          : Icon(Icons.block, size: 18, color: Theme.of(context).colorScheme.error),
      onTap: () => _form(s, sup),
    );
  }

  Future<void> _form(Strings s, Supplier? existing) async {
    final name = TextEditingController(text: existing?.name ?? '');
    final contact = TextEditingController(text: existing?.contact ?? '');
    final phone = TextEditingController(text: existing?.phone ?? '');
    final notes = TextEditingController(text: existing?.notes ?? '');
    var active = existing?.active ?? true;

    final saved = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialog) => Padding(
          padding: EdgeInsets.only(
            left: 16,
            right: 16,
            top: 16,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 16,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(existing == null ? s.provNew : existing.name,
                  style: Theme.of(ctx).textTheme.titleMedium),
              const SizedBox(height: 12),
              TextField(
                controller: name,
                decoration: InputDecoration(labelText: s.provName),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: contact,
                decoration: InputDecoration(labelText: s.provContact),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: phone,
                keyboardType: TextInputType.phone,
                decoration: InputDecoration(labelText: s.provPhone),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: notes,
                decoration: InputDecoration(labelText: s.provNotes),
              ),
              if (existing != null)
                SwitchListTile(
                  contentPadding: EdgeInsets.zero,
                  value: active,
                  onChanged: (v) => setDialog(() => active = v),
                  title: Text(s.provActive),
                ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: () => Navigator.of(ctx).pop(true),
                child: Text(MaterialLocalizations.of(ctx).okButtonLabel),
              ),
            ],
          ),
        ),
      ),
    );

    if (saved != true) return;
    final nm = name.text.trim();
    if (nm.isEmpty) return;
    try {
      final repo = ref.read(supplierRepositoryProvider);
      if (existing == null) {
        await repo.create(
            name: nm, contact: _n(contact), phone: _n(phone), notes: _n(notes));
      } else {
        await repo.update(existing.id,
            name: nm,
            contact: _n(contact),
            phone: _n(phone),
            notes: _n(notes),
            active: active);
      }
      ref.invalidate(suppliersProvider);
    } on ApiError catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }

  String? _n(TextEditingController c) {
    final t = c.text.trim();
    return t.isEmpty ? null : t;
  }
}
