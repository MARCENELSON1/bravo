import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/session_notifier.dart';
import '../../l10n/strings.dart';
import '../../theme/colors.dart';
import '../../ui/glass_panel.dart';
import '../../util/money.dart';
import '../cashier/payment_dtos.dart';
import '../copilot/copilot_page.dart';
import '../expenses/gastos_page.dart';
import '../finance/finance_range.dart';
import '../finance/finance_repository.dart';
import '../reports/reports_repository.dart';
import 'daily_verdict.dart';
import 'home_repository.dart';

/// Home v2 (paridad con el Inicio del web, solo OWNER/MANAGER): jerarquía de 7
/// niveles — arrancás viendo la ganancia del día.
class HomePage extends ConsumerStatefulWidget {
  const HomePage({super.key});

  @override
  ConsumerState<HomePage> createState() => _HomePageState();
}

class _HomePageState extends ConsumerState<HomePage> {
  bool _taskDone = false;

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final sessionState = ref.watch(sessionProvider);
    if (sessionState is! SessionAuthenticated) {
      return const Center(child: CircularProgressIndicator());
    }
    final session = sessionState.session;
    final firstName =
        session.name?.trim().isNotEmpty == true ? session.name!.trim().split(' ').first : null;

    final summary = ref.watch(dashboardProvider);
    final daily = ref.watch(revenue7dProvider);
    final mix = ref.watch(paymentMixProvider(FinanceRange.today));
    final overview = ref.watch(financeOverviewProvider(FinanceRange.month));
    final movements = ref.watch(movementsProvider(FinanceRange.today));

    final d = summary.valueOrNull;
    final currency = d?.currency ?? 'ARS';
    final sales = d?.sales ?? 0;
    final expenses = d?.expenses ?? 0;
    final feesTotal = d?.feesTotal ?? 0;
    final net = (d?.collectedNet ?? sales) - expenses;
    final pct = _pctVsYesterday(daily.valueOrNull ?? const []);
    final verdict = dailyVerdict(net, pct);
    final marginPer100 = sales > 0 ? (net / sales * 100).round() : 0;
    final marginTentative = sales > 0 && expenses == 0;

    return Stack(
      children: [
        RefreshIndicator(
          onRefresh: () async {
            ref.invalidate(dashboardProvider);
            ref.invalidate(revenue7dProvider);
            ref.invalidate(paymentMixProvider(FinanceRange.today));
            ref.invalidate(financeOverviewProvider(FinanceRange.month));
            ref.invalidate(movementsProvider(FinanceRange.today));
          },
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
            children: [
              // Encabezado
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(s.dashGreeting(firstName),
                        style: Theme.of(context)
                            .textTheme
                            .headlineSmall
                            ?.copyWith(fontWeight: FontWeight.w800)),
                  ),
                  Text(s.dashTodayLabel(DateTime.now()),
                      style: TextStyle(
                          color: scheme.onSurfaceVariant, fontSize: 12)),
                ],
              ),
              const SizedBox(height: 16),

              // NIVEL 1 — Tu ganancia de hoy
              GlassPanel(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(s.dashProfitToday,
                        style: TextStyle(color: scheme.onSurfaceVariant)),
                    const SizedBox(height: 4),
                    Text(
                      summary.isLoading
                          ? '—'
                          : formatMoney(net, currency),
                      style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                            fontWeight: FontWeight.w800,
                            color: net < 0 ? scheme.error : scheme.onSurface,
                          ),
                    ),
                    const SizedBox(height: 6),
                    Text(s.dashVerdict(verdict.tone, verdict.vs, verdict.pct),
                        style: TextStyle(
                            color: _toneColor(verdict.tone, scheme),
                            fontWeight: FontWeight.w600)),
                    if (marginTentative)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(s.dashProfitTentative,
                            style: TextStyle(
                                color: WellnodPalette.warn, fontSize: 12)),
                      ),
                    if (feesTotal > 0)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(
                            s.dashFeesDeducted(formatMoney(feesTotal, currency)),
                            style: TextStyle(
                                color: scheme.onSurfaceVariant, fontSize: 12)),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: 12),

              // NIVEL 2 — Los 3 números
              Row(
                children: [
                  Expanded(
                    child: _numberCard(context, s.dashBilledToday,
                        formatMoney(sales, currency),
                        sub: s.dashPaymentsCount(d?.paymentCount ?? 0)),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _numberCard(context, s.dashSpentToday,
                        formatMoney(expenses, currency),
                        sub: s.dashExpensesRegistered),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              _numberCard(
                context,
                s.dashMarginToday,
                marginTentative ? '—' : (sales > 0 ? '$marginPer100%' : '—'),
                sub: marginTentative
                    ? s.dashLoadExpensesForMargin
                    : (sales > 0
                        ? s.dashMarginExplain(marginPer100)
                        : s.dashNoSalesYet),
                subWarn: marginTentative,
              ),
              const SizedBox(height: 12),

              // NIVEL 3 — Cobros de hoy por canal
              _channels(context, s, mix, currency),
              const SizedBox(height: 12),

              // NIVEL 4 — Alerta del día
              ..._alert(context, s, overview.valueOrNull),

              // NIVEL 5 — Progreso del mes
              _revenue7d(context, s, daily.valueOrNull, currency),
              const SizedBox(height: 12),
              _monthClose(context, s, overview.valueOrNull, currency),
              const SizedBox(height: 12),

              // NIVEL 6 — Últimos movimientos
              _movements(context, s, movements.valueOrNull, currency),

              // NIVEL 7 — Tu tarea para mañana
              ..._task(context, s, overview.valueOrNull),

              const SizedBox(height: 12),
              // Copiloto + cerrar sesión (theme/idioma viven en Ajustes)
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: () => Navigator.of(context).push(
                        MaterialPageRoute<void>(
                            builder: (_) => const CopilotPage()),
                      ),
                      icon: const Icon(Icons.auto_awesome, size: 18),
                      label: Text(s.askCopilot),
                    ),
                  ),
                  const SizedBox(width: 10),
                  TextButton.icon(
                    onPressed: () =>
                        ref.read(sessionProvider.notifier).logout(),
                    icon: const Icon(Icons.logout, size: 18),
                    label: Text(s.logout),
                  ),
                ],
              ),
            ],
          ),
        ),
        // FAB — registrar egreso
        Positioned(
          right: 16,
          bottom: 16,
          child: FloatingActionButton(
            heroTag: 'home-expense',
            tooltip: s.dashRegisterExpense,
            onPressed: () => Navigator.of(context).push(
              MaterialPageRoute<void>(builder: (_) => const GastosPage()),
            ),
            child: const Icon(Icons.add),
          ),
        ),
      ],
    );
  }

  Color _toneColor(VerdictTone tone, ColorScheme scheme) => switch (tone) {
        VerdictTone.good => scheme.primary,
        VerdictTone.ok => WellnodPalette.warn,
        VerdictTone.bad => scheme.error,
      };

  double? _pctVsYesterday(List<RevenueDailyPoint> pts) {
    final byDay = {for (final p in pts) p.day: p.salesAmount};
    String two(int n) => n.toString().padLeft(2, '0');
    String key(int off) {
      final now = DateTime.now();
      final c = DateTime(now.year, now.month, now.day)
          .subtract(Duration(days: off));
      return '${c.year}-${two(c.month)}-${two(c.day)}';
    }

    final today = byDay[key(0)] ?? 0;
    final yest = byDay[key(1)] ?? 0;
    if (yest <= 0) return null;
    return (today - yest) / yest * 100;
  }

  Widget _numberCard(BuildContext context, String label, String value,
      {String? sub, bool subWarn = false}) {
    final scheme = Theme.of(context).colorScheme;
    return GlassPanel(
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
          const SizedBox(height: 2),
          Align(
            alignment: Alignment.centerLeft,
            child: FittedBox(
              fit: BoxFit.scaleDown,
              child: Text(value,
                  maxLines: 1,
                  style: const TextStyle(
                      fontSize: 22, fontWeight: FontWeight.w800)),
            ),
          ),
          if (sub != null)
            Text(sub,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                    color: subWarn
                        ? WellnodPalette.warn
                        : scheme.onSurfaceVariant,
                    fontSize: 11)),
        ],
      ),
    );
  }

  Widget _channels(BuildContext context, Strings s,
      AsyncValue<List<PaymentMixRow>> mix, String currency) {
    final scheme = Theme.of(context).colorScheme;
    final rows = (mix.valueOrNull ?? const <PaymentMixRow>[])
        .where((r) => r.direction == 'INFLOW')
        .toList();
    final total = rows.fold<int>(0, (a, r) => a + r.amount);
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.dashChannelsTitle,
              style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 2),
          Text(s.dashChannelsSubtitle,
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 11)),
          const SizedBox(height: 12),
          if (rows.isEmpty)
            Text(mix.isLoading ? '…' : s.dashNoPaymentsToday,
                style: TextStyle(color: scheme.onSurfaceVariant))
          else
            for (final r in rows) ...[
              Row(
                children: [
                  Expanded(
                      child: Text(
                          s.methodLabel(PaymentMethod.fromApi(r.method)),
                          style: const TextStyle(fontWeight: FontWeight.w500))),
                  Text(
                    '${formatMoney(r.amount, currency)} · ${total > 0 ? (r.amount / total * 100).round() : 0}%',
                    style: TextStyle(
                        color: scheme.onSurfaceVariant, fontSize: 13),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: total > 0 ? r.amount / total : 0,
                  minHeight: 6,
                  backgroundColor: scheme.surfaceContainerHighest,
                ),
              ),
              const SizedBox(height: 12),
            ],
        ],
      ),
    );
  }

  List<Widget> _alert(
      BuildContext context, Strings s, FinanceOverview? overview) {
    final diags = overview?.diagnostics ?? const <FinanceDiagnostic>[];
    FinanceDiagnostic? top;
    for (final d in diags) {
      final sev = d.severity.toLowerCase();
      if (sev == 'alert' || sev == 'critical' || sev == 'warn' || sev == 'warning') {
        top = d;
        break;
      }
    }
    if (top == null) return const [];
    final scheme = Theme.of(context).colorScheme;
    final isWarn = top.severity.toLowerCase().startsWith('warn');
    final color = isWarn ? WellnodPalette.warn : scheme.error;
    return [
      GlassPanel(
        child: Container(
          decoration: BoxDecoration(
            border: Border(left: BorderSide(color: color, width: 2)),
          ),
          padding: const EdgeInsets.only(left: 10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(s.dashAttentionToday.toUpperCase(),
                  style: TextStyle(
                      color: color,
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.5)),
              const SizedBox(height: 4),
              Text(top.title,
                  style: const TextStyle(fontWeight: FontWeight.w600)),
              Text(top.body,
                  style: TextStyle(
                      color: scheme.onSurfaceVariant, fontSize: 13)),
            ],
          ),
        ),
      ),
      const SizedBox(height: 12),
    ];
  }

  Widget _revenue7d(BuildContext context, Strings s,
      List<RevenueDailyPoint>? points, String currency) {
    final scheme = Theme.of(context).colorScheme;
    final days = _last7Days(points ?? const []);
    final maxV = days.fold<int>(1, (m, d) => d.value > m ? d.value : m);
    final hasSales = days.any((d) => d.value > 0);
    final total = days.fold<int>(0, (a, d) => a + d.value);
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.dashRevenue7dTitle,
              style: Theme.of(context).textTheme.titleSmall),
          Text(s.dashTotalSuffix(formatMoney(total, currency)),
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
          const SizedBox(height: 12),
          if (!hasSales)
            SizedBox(
              height: 120,
              child: Center(
                  child: Text(s.dashNoSales7d,
                      style: TextStyle(color: scheme.onSurfaceVariant))),
            )
          else
            SizedBox(
              height: 140,
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  for (final d in days)
                    Expanded(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          Container(
                            height: (d.value / maxV) * 108 + 2,
                            margin: const EdgeInsets.symmetric(horizontal: 3),
                            decoration: BoxDecoration(
                              color: scheme.primary,
                              borderRadius: const BorderRadius.vertical(
                                  top: Radius.circular(4)),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(s.dashWeekdayShort(d.weekday),
                              style: TextStyle(
                                  color: scheme.onSurfaceVariant, fontSize: 10)),
                        ],
                      ),
                    ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _monthClose(BuildContext context, Strings s, FinanceOverview? overview,
      String currency) {
    final scheme = Theme.of(context).colorScheme;
    final p = overview?.projection;
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.dashMonthClose,
              style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 6),
          if (p != null) ...[
            Text.rich(TextSpan(children: [
              TextSpan(
                  text: '${s.dashOnTrackToClose} ',
                  style: TextStyle(color: scheme.onSurfaceVariant)),
              TextSpan(
                  text: formatMoney(p.salesAmount, currency),
                  style: const TextStyle(fontWeight: FontWeight.w700)),
            ])),
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: p.monthDays > 0 ? p.elapsedDays / p.monthDays : 0,
                minHeight: 6,
                backgroundColor: scheme.surfaceContainerHighest,
              ),
            ),
            const SizedBox(height: 6),
            Text(s.dashDayOfMonth(p.elapsedDays, p.monthDays),
                style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 12)),
          ] else
            Text(s.dashNotEnoughData,
                style: TextStyle(color: scheme.onSurfaceVariant)),
        ],
      ),
    );
  }

  Widget _movements(BuildContext context, Strings s,
      List<Movement>? movements, String currency) {
    final scheme = Theme.of(context).colorScheme;
    final list = (movements ?? const <Movement>[]).take(5).toList();
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(s.financeMovementsTitle,
              style: Theme.of(context).textTheme.titleSmall),
          const SizedBox(height: 6),
          if (list.isEmpty)
            Text(s.dashNoPaymentsToday,
                style: TextStyle(color: scheme.onSurfaceVariant))
          else
            for (final m in list)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: Row(
                  children: [
                    Icon(
                        m.kind == 'expense'
                            ? Icons.south_west
                            : Icons.north_east,
                        size: 14,
                        color:
                            m.kind == 'expense' ? scheme.error : scheme.primary),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(m.description ?? m.category ?? m.method,
                          maxLines: 1, overflow: TextOverflow.ellipsis),
                    ),
                    Text(
                      '${m.kind == 'expense' ? '−' : ''}${formatMoney(m.amount, m.currency)}',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),
        ],
      ),
    );
  }

  List<Widget> _task(BuildContext context, Strings s, FinanceOverview? overview) {
    if (_taskDone) return const [];
    final diags = overview?.diagnostics ?? const <FinanceDiagnostic>[];
    String? action;
    for (final d in diags) {
      final sev = d.severity.toLowerCase();
      final urgent = sev == 'alert' || sev == 'critical' || sev.startsWith('warn');
      if (urgent && d.action != null && d.action!.isNotEmpty) {
        action = d.action;
        break;
      }
    }
    if (action == null) return const [];
    final scheme = Theme.of(context).colorScheme;
    return [
      const SizedBox(height: 12),
      GlassPanel(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(s.dashTomorrowTaskTitle.toUpperCase(),
                style: TextStyle(
                    color: scheme.primary,
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    letterSpacing: 0.5)),
            const SizedBox(height: 4),
            Text(action),
            const SizedBox(height: 10),
            Align(
              alignment: Alignment.centerLeft,
              child: FilledButton(
                onPressed: () => setState(() => _taskDone = true),
                child: Text(s.dashGotIt),
              ),
            ),
          ],
        ),
      ),
    ];
  }
}

class _DayBar {
  const _DayBar(this.weekday, this.value);
  final int weekday; // 1=lunes … 7=domingo
  final int value;
}

List<_DayBar> _last7Days(List<RevenueDailyPoint> points) {
  final byDay = {for (final p in points) p.day: p.salesAmount};
  String two(int n) => n.toString().padLeft(2, '0');
  final now = DateTime.now();
  final out = <_DayBar>[];
  for (var i = 6; i >= 0; i--) {
    final c = DateTime(now.year, now.month, now.day).subtract(Duration(days: i));
    final key = '${c.year}-${two(c.month)}-${two(c.day)}';
    out.add(_DayBar(c.weekday, byDay[key] ?? 0));
  }
  return out;
}
