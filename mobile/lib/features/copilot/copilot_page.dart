import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import 'copilot_repository.dart';

class _Message {
  const _Message({required this.isUser, required this.text, this.answer});
  final bool isUser;
  final String text;
  final CopilotAnswer? answer;
}

/// Copiloto (Fase 5): consulta en lenguaje natural sobre el negocio
/// (POST /copilot/ask → respuesta + tabla).
class CopilotPage extends ConsumerStatefulWidget {
  const CopilotPage({super.key});

  @override
  ConsumerState<CopilotPage> createState() => _CopilotPageState();
}

class _CopilotPageState extends ConsumerState<CopilotPage> {
  final _input = TextEditingController();
  final _messages = <_Message>[];
  bool _loading = false;

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final q = _input.text.trim();
    if (q.isEmpty || _loading) return;
    setState(() {
      _messages.add(_Message(isUser: true, text: q));
      _loading = true;
      _input.clear();
    });
    try {
      final answer = await ref.read(copilotRepositoryProvider).ask(q);
      setState(() =>
          _messages.add(_Message(isUser: false, text: answer.answer, answer: answer)));
    } on ApiError catch (e) {
      setState(() => _messages.add(_Message(isUser: false, text: e.message)));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(title: Text(s.copilotTitle), backgroundColor: Colors.transparent),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: Column(
              children: [
                Expanded(
                  child: _messages.isEmpty
                      ? Center(
                          child: Padding(
                            padding: const EdgeInsets.all(24),
                            child: Text(s.copilotEmpty,
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                    color:
                                        Theme.of(context).colorScheme.onSurfaceVariant)),
                          ),
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _messages.length,
                          itemBuilder: (context, i) => _bubble(_messages[i]),
                        ),
                ),
                if (_loading) const LinearProgressIndicator(),
                _composer(s),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _composer(Strings s) {
    return Padding(
      padding: EdgeInsets.only(
        left: 12,
        right: 12,
        top: 8,
        bottom: MediaQuery.of(context).viewInsets.bottom + 12,
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _input,
              textInputAction: TextInputAction.send,
              onSubmitted: (_) => _send(),
              decoration: InputDecoration(hintText: s.copilotHint),
            ),
          ),
          const SizedBox(width: 8),
          IconButton.filled(
            onPressed: _loading ? null : _send,
            icon: const Icon(Icons.send),
          ),
        ],
      ),
    );
  }

  Widget _bubble(_Message m) {
    final scheme = Theme.of(context).colorScheme;
    if (m.isUser) {
      return Align(
        alignment: Alignment.centerRight,
        child: Container(
          margin: const EdgeInsets.only(bottom: 10, left: 40),
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: scheme.primary,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Text(m.text, style: TextStyle(color: scheme.onPrimary)),
        ),
      );
    }
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10, right: 40),
        child: GlassPanel(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(m.text),
              if (m.answer != null && m.answer!.rows.isNotEmpty) ...[
                const SizedBox(height: 8),
                _table(m.answer!),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _table(CopilotAnswer a) {
    final rows = a.rows.take(10).toList();
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        columnSpacing: 16,
        headingRowHeight: 32,
        dataRowMinHeight: 28,
        dataRowMaxHeight: 36,
        columns: [for (final c in a.columns) DataColumn(label: Text(c))],
        rows: [
          for (final r in rows)
            DataRow(cells: [for (final cell in r) DataCell(Text('$cell'))]),
        ],
      ),
    );
  }
}
