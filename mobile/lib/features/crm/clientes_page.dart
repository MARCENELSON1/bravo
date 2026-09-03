import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import 'customer_repository.dart';

/// Clientes / CRM (Fase 6): búsqueda, alta y edición.
class ClientesPage extends ConsumerStatefulWidget {
  const ClientesPage({super.key});

  @override
  ConsumerState<ClientesPage> createState() => _ClientesPageState();
}

class _ClientesPageState extends ConsumerState<ClientesPage> {
  final _search = TextEditingController();

  @override
  void initState() {
    super.initState();
    _search.addListener(() {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final async = ref.watch(customersProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(s.clientesTitle), backgroundColor: Colors.transparent),
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
                onRetry: () => ref.invalidate(customersProvider),
              ),
              data: (list) => _content(s, list),
            ),
          ),
        ],
      ),
    );
  }

  Widget _content(Strings s, List<Customer> list) {
    final q = _search.text.trim().toLowerCase();
    final filtered = q.isEmpty
        ? list
        : list
            .where((c) =>
                c.name.toLowerCase().contains(q) ||
                (c.phone?.contains(q) ?? false))
            .toList();
    return RefreshIndicator(
      onRefresh: () async => ref.invalidate(customersProvider),
      child: ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      children: [
        TextField(
          controller: _search,
          decoration: InputDecoration(
            hintText: s.clientesSearch,
            prefixIcon: const Icon(Icons.search),
          ),
        ),
        const SizedBox(height: 12),
        if (filtered.isEmpty)
          GlassPanel(child: Text(s.clientesEmpty))
        else
          GlassPanel(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Material(
              type: MaterialType.transparency,
              child: Column(
                children: [
                  for (var i = 0; i < filtered.length; i++) ...[
                    if (i > 0) const Divider(height: 1),
                    _tile(s, filtered[i]),
                  ],
                ],
              ),
            ),
          ),
      ],
      ),
    );
  }

  Widget _tile(Strings s, Customer c) {
    final sub = [
      if (c.phone != null && c.phone!.isNotEmpty) c.phone!,
      if (c.email != null && c.email!.isNotEmpty) c.email!,
    ].join(' · ');
    return ListTile(
      title: Text(c.name),
      subtitle: sub.isEmpty ? null : Text(sub),
      trailing: c.noContactar
          ? Icon(Icons.do_not_disturb_on_outlined,
              size: 18, color: Theme.of(context).colorScheme.error)
          : null,
      onTap: () => _form(s, c),
    );
  }

  Future<void> _form(Strings s, Customer? existing) async {
    final name = TextEditingController(text: existing?.name ?? '');
    final phone = TextEditingController(text: existing?.phone ?? '');
    final email = TextEditingController(text: existing?.email ?? '');
    final notes = TextEditingController(text: existing?.notes ?? '');
    var noContact = existing?.noContactar ?? false;

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
              Text(existing == null ? s.clienteNew : existing.name,
                  style: Theme.of(ctx).textTheme.titleMedium),
              const SizedBox(height: 12),
              TextField(
                controller: name,
                decoration: InputDecoration(labelText: s.provName),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: phone,
                keyboardType: TextInputType.phone,
                decoration: InputDecoration(labelText: s.provPhone),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: email,
                keyboardType: TextInputType.emailAddress,
                decoration: InputDecoration(labelText: s.clienteEmail),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: notes,
                decoration: InputDecoration(labelText: s.provNotes),
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                value: noContact,
                onChanged: (v) => setDialog(() => noContact = v),
                title: Text(s.clienteNoContact),
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
      final repo = ref.read(customerRepositoryProvider);
      if (existing == null) {
        await repo.create(
            name: nm,
            phone: _n(phone),
            email: _n(email),
            notes: _n(notes),
            noContactar: noContact);
      } else {
        await repo.update(existing.id,
            name: nm,
            phone: _n(phone),
            email: _n(email),
            notes: _n(notes),
            noContactar: noContact);
      }
      ref.invalidate(customersProvider);
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
