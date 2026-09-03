import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../api/api_error.dart';
import '../../l10n/strings.dart';
import '../../ui/app_background.dart';
import '../../ui/glass_panel.dart';
import '../../ui/state_views.dart';
import '../../util/money.dart';
import '../settings/fiscal_repository.dart';
import 'billing_repository.dart';

/// Suscripción (paridad con `/app/subscription` del web): si hay plan activo,
/// estado + cancelar; si no, planes según la región (AR→MercadoPago,
/// INTL→Stripe) con checkout hosteado. OWNER.
class SuscripcionPage extends ConsumerWidget {
  const SuscripcionPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final fiscal = ref.watch(fiscalSettingsProvider);
    final sub = ref.watch(subscriptionProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
          title: Text(s.billingTitle), backgroundColor: Colors.transparent),
      body: Stack(
        children: [
          const AppBackground(),
          SafeArea(
            child: RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(subscriptionProvider);
                ref.invalidate(fiscalSettingsProvider);
              },
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(16),
                children: [
                  fiscal.when(
                    loading: () => const _Loading(),
                    error: (e, _) => ErrorView(
                        error: e,
                        onRetry: () => ref.invalidate(fiscalSettingsProvider)),
                    data: (f) {
                      final region = f.country == 'AR' ? 'AR' : 'INTL';
                      return sub.when(
                        loading: () => const _Loading(),
                        error: (e, _) => ErrorView(
                            error: e,
                            onRetry: () =>
                                ref.invalidate(subscriptionProvider)),
                        data: (subscription) =>
                            (subscription != null && subscription.grantsAccess)
                                ? _ActiveCard(subscription: subscription)
                                : _PlanList(region: region),
                      );
                    },
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ActiveCard extends ConsumerWidget {
  const _ActiveCard({required this.subscription});
  final Subscription subscription;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final end = subscription.currentPeriodEnd == null
        ? ''
        : s.billingRenewsOn(DateFormat('dd/MM/yyyy').format(
            DateTime.tryParse(subscription.currentPeriodEnd!)?.toLocal() ??
                DateTime.now()));
    return GlassPanel(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(s.billingActivePlan,
                    style: Theme.of(context).textTheme.titleMedium),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: scheme.primary.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(999),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.check_circle, size: 14, color: scheme.primary),
                    const SizedBox(width: 4),
                    Text(s.billingStatusLabel('ACTIVE'),
                        style: TextStyle(color: scheme.primary, fontSize: 12)),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text('${s.billingStatusLine(s.billingStatusLabel(subscription.status))}$end',
              style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
          const SizedBox(height: 16),
          OutlinedButton(
            onPressed: () => _cancel(context, ref),
            style: OutlinedButton.styleFrom(foregroundColor: scheme.error),
            child: Text(s.billingCancel),
          ),
        ],
      ),
    );
  }

  Future<void> _cancel(BuildContext context, WidgetRef ref) async {
    final s = context.s;
    final ok = await confirmDialog(context,
        title: s.billingCancelConfirm, confirmLabel: s.billingCancel);
    if (!ok) return;
    try {
      await ref.read(billingRepositoryProvider).cancel();
      ref.invalidate(subscriptionProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.billingCancelSuccess)));
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.billingCancelError)));
      }
    }
  }
}

class _PlanList extends ConsumerWidget {
  const _PlanList({required this.region});
  final String region;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final plans = ref.watch(billingPlansProvider(region));
    final gateway = region == 'AR' ? 'MercadoPago' : 'Stripe';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(s.billingChooseIntro(gateway),
            style: TextStyle(color: scheme.onSurfaceVariant, fontSize: 13)),
        const SizedBox(height: 12),
        plans.when(
          loading: () => const _Loading(),
          error: (e, _) => ErrorView(
              error: e,
              onRetry: () => ref.invalidate(billingPlansProvider(region))),
          data: (list) {
            if (list.isEmpty) return GlassPanel(child: Text(s.billingNoPlans));
            return Column(
              children: [for (final p in list) _PlanCard(plan: p)],
            );
          },
        ),
      ],
    );
  }
}

class _PlanCard extends ConsumerStatefulWidget {
  const _PlanCard({required this.plan});
  final BillingPlan plan;
  @override
  ConsumerState<_PlanCard> createState() => _PlanCardState();
}

class _PlanCardState extends ConsumerState<_PlanCard> {
  bool _loading = false;

  Future<void> _subscribe() async {
    final s = context.s;
    setState(() => _loading = true);
    try {
      final url = await ref.read(billingRepositoryProvider).checkout(widget.plan.id);
      final uri = Uri.tryParse(url);
      final ok = uri != null &&
          await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!ok && mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(s.billingOpenError)));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(e is ApiError ? e.message : s.billingCheckoutError)));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final s = context.s;
    final scheme = Theme.of(context).colorScheme;
    final p = widget.plan;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: GlassPanel(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(p.tier, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 4),
            RichText(
              text: TextSpan(
                style: DefaultTextStyle.of(context).style,
                children: [
                  TextSpan(
                      text: formatMoney(p.amount, p.currency),
                      style: const TextStyle(
                          fontSize: 22, fontWeight: FontWeight.w800)),
                  TextSpan(
                      text: ' / ${s.billingInterval(p.interval)}',
                      style: TextStyle(
                          color: scheme.onSurfaceVariant, fontSize: 13)),
                ],
              ),
            ),
            if (p.features.isNotEmpty) ...[
              const SizedBox(height: 10),
              for (final f in p.features)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Row(
                    children: [
                      Icon(Icons.check, size: 16, color: scheme.primary),
                      const SizedBox(width: 6),
                      Expanded(
                          child: Text(f,
                              style: TextStyle(
                                  color: scheme.onSurfaceVariant,
                                  fontSize: 13))),
                    ],
                  ),
                ),
            ],
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _loading ? null : _subscribe,
              child: Text(s.billingSubscribe),
            ),
          ],
        ),
      ),
    );
  }
}

class _Loading extends StatelessWidget {
  const _Loading();
  @override
  Widget build(BuildContext context) => const Padding(
        padding: EdgeInsets.all(24),
        child: Center(child: CircularProgressIndicator()),
      );
}
