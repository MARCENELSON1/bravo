import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../auth/session.dart';
import '../../l10n/strings.dart';
import '../../ui/glass_panel.dart';
import 'team_repository.dart';

/// Ajustes › Equipo — paridad con el InviteUserForm del web: invitar por email
/// con un rol. Roles asignables: todos menos OWNER.
class EquipoSettingsSection extends ConsumerStatefulWidget {
  const EquipoSettingsSection({super.key});
  @override
  ConsumerState<EquipoSettingsSection> createState() =>
      _EquipoSettingsSectionState();
}

class _EquipoSettingsSectionState extends ConsumerState<EquipoSettingsSection> {
  final _email = TextEditingController();
  Role _role = Role.waiter;
  bool _sending = false;

  static const _assignable = [
    Role.manager,
    Role.waiter,
    Role.kitchen,
    Role.bar,
    Role.cashier,
  ];

  @override
  void dispose() {
    _email.dispose();
    super.dispose();
  }

  bool _validEmail(String v) =>
      RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(v);

  Future<void> _send() async {
    final s = context.s;
    final email = _email.text.trim();
    if (!_validEmail(email)) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(s.inviteEmailInvalid)));
      return;
    }
    setState(() => _sending = true);
    try {
      final msg = await ref.read(teamRepositoryProvider).invite(email, _role.api);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text(msg.isNotEmpty ? msg : s.inviteSent)));
        _email.clear();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.inviteError)));
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.inviteTitle, style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 4),
          Text(s.inviteDesc,
              style: TextStyle(
                  color: Theme.of(context).colorScheme.onSurfaceVariant,
                  fontSize: 13)),
          const SizedBox(height: 12),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            autofillHints: const [AutofillHints.email],
            decoration: InputDecoration(labelText: s.inviteEmail),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<Role>(
            initialValue: _role,
            decoration: InputDecoration(labelText: s.inviteRole),
            items: [
              for (final r in _assignable)
                DropdownMenuItem(value: r, child: Text(s.role(r))),
            ],
            onChanged: (r) => setState(() => _role = r ?? _role),
          ),
          const SizedBox(height: 12),
          Align(
            alignment: Alignment.centerLeft,
            child: FilledButton.icon(
              onPressed: _sending ? null : _send,
              icon: const Icon(Icons.send_outlined),
              label: Text(s.inviteSend),
            ),
          ),
        ],
      ),
    );
  }
}
