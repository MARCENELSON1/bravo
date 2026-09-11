import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_client.dart';
import '../../api/dio_errors.dart';
import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';

/// Alcance del borrado: si esta persona es el último dueño, se va el local
/// entero y no solo su acceso. Lo decide el backend, no la app.
class DeletionScope {
  const DeletionScope({required this.deletesBusiness, required this.tenantName});
  final bool deletesBusiness;
  final String tenantName;

  factory DeletionScope.fromJson(Map<String, dynamic> j) => DeletionScope(
        deletesBusiness: (j['deletes_business'] as bool?) ?? false,
        tenantName: (j['tenant_name'] as String?) ?? '',
      );
}

final deletionScopeProvider = FutureProvider.autoDispose<DeletionScope>((ref) async {
  final dio = ref.watch(apiDioProvider);
  try {
    final res = await dio.get<dynamic>('/me/deletion-scope');
    return DeletionScope.fromJson(res.data as Map<String, dynamic>);
  } on DioException catch (e) {
    throw toApiError(e);
  }
});

/// Borrar la propia cuenta (App Store 5.1.1(v)).
///
/// Dos cuidados de diseño, los dos deliberados:
///
/// 1. **La advertencia la escribe el backend, no la pantalla.** Si el que borra
///    es el último dueño se va el local con todo su historial; si es un empleado,
///    solo su acceso. Adivinarlo en el cliente sería mentirle a alguien.
/// 2. **Se pide la contraseña y escribir el nombre del local.** Es irreversible y
///    no hay papelera: la fricción es la función.
class DeleteAccountPage extends ConsumerStatefulWidget {
  const DeleteAccountPage({super.key});

  @override
  ConsumerState<DeleteAccountPage> createState() => _DeleteAccountPageState();
}

class _DeleteAccountPageState extends ConsumerState<DeleteAccountPage> {
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _password.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _delete(DeletionScope scope) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(apiDioProvider).delete<dynamic>(
            '/me',
            data: {'password': _password.text},
          );
      if (!mounted) return;
      // La sesión ya no existe del otro lado; cerrarla acá evita quedar con un
      // token que solo produce errores.
      await ref.read(sessionProvider.notifier).logout();
    } on DioException catch (e) {
      if (!mounted) return;
      setState(() => _error = toApiError(e).message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final async = ref.watch(deletionScopeProvider);

    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Text(s.deleteAccountTitle),
        backgroundColor: Colors.transparent,
      ),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: async.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text(s.deleteAccountScopeError)),
              data: (scope) {
                final needsName = scope.deletesBusiness;
                final ready = _password.text.length >= 8 &&
                    (!needsName || _confirm.text.trim() == scope.tenantName.trim());
                return ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    GlassPanel(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Semantics(
                            header: true,
                            child: Text(
                              needsName
                                  ? s.deleteAccountBusinessTitle(scope.tenantName)
                                  : s.deleteAccountUserTitle,
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                    fontWeight: FontWeight.w700,
                                    color: scheme.error,
                                  ),
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            needsName
                                ? s.deleteAccountBusinessBody
                                : s.deleteAccountUserBody,
                            style: TextStyle(color: scheme.onSurfaceVariant),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _password,
                      obscureText: true,
                      autofillHints: const [AutofillHints.password],
                      decoration: InputDecoration(
                        labelText: s.deleteAccountPasswordLabel,
                        helperText: s.deleteAccountPasswordHelp,
                      ),
                      onChanged: (_) => setState(() {}),
                    ),
                    if (needsName) ...[
                      const SizedBox(height: 12),
                      TextField(
                        controller: _confirm,
                        decoration: InputDecoration(
                          labelText: s.deleteAccountConfirmLabel(scope.tenantName),
                        ),
                        onChanged: (_) => setState(() {}),
                      ),
                    ],
                    if (_error != null) ...[
                      const SizedBox(height: 12),
                      Text(_error!, style: TextStyle(color: scheme.error)),
                    ],
                    const SizedBox(height: 20),
                    FilledButton(
                      onPressed: _busy || !ready ? null : () => _delete(scope),
                      style: FilledButton.styleFrom(
                        backgroundColor: scheme.error,
                        foregroundColor: scheme.onError,
                        minimumSize: const Size.fromHeight(52),
                      ),
                      child: _busy
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : Text(s.deleteAccountConfirmAction),
                    ),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
