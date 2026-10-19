import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/models/analysis.dart';
import '../../data/models/reason.dart';
import '../../l10n/app_localizations.dart';
import '../../state/device.dart';
import '../../state/providers.dart';
import '../../theme/tokens.dart';
import '../../widgets/labels.dart';
import '../../widgets/risk_widgets.dart';
import '../../widgets/state_views.dart';
import 'feedback_sheet.dart';

class ResultScreen extends ConsumerWidget {
  const ResultScreen({super.key, required this.analysisId});

  final String analysisId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final result = ref.watch(analysisProvider(analysisId));
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.resultTitle),
        leading: IconButton(
          key: const Key('result-back'),
          icon: const Icon(Icons.arrow_back),
          tooltip: MaterialLocalizations.of(context).backButtonTooltip,
          onPressed: () => context.canPop() ? context.pop() : context.go('/home'),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            const OfflineBanner(),
            Expanded(
              child: result.when(
                loading: () => const LoadingView(),
                error: (error, stack) =>
                    ErrorView(error: error, onRetry: () => ref.invalidate(analysisProvider(analysisId))),
                data: (analysis) => ResultBody(analysis: analysis),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

String shareMessage(AppLocalizations l10n, Analysis analysis) {
  final percent = ((analysis.riskScore ?? 0) * 100).round();
  final verdict = riskLabel(l10n, RiskLevel.level(analysis.riskScore));
  final text = l10n.shareText(verdict, percent, categoryLabel(l10n, analysis.category));
  final lines = <String>[text];
  final language = l10n.localeName;
  var count = 0;
  for (final reason in analysis.reasons) {
    if (count >= 3) {
      break;
    }
    lines.add('• ${reason.messageFor(language)}');
    count = count + 1;
  }
  if (analysis.sourceUrl != null) {
    lines.add(analysis.sourceUrl!);
  }
  lines.add(l10n.resultDisclaimer);
  return lines.join('\n');
}

class ResultBody extends ConsumerWidget {
  const ResultBody({super.key, required this.analysis});

  final Analysis analysis;

  Future<void> share(BuildContext context, WidgetRef ref, AppLocalizations l10n) async {
    final text = shareMessage(l10n, analysis);
    final messenger = ScaffoldMessenger.of(context);
    final shared = await ref.read(deviceActionsProvider).shareText(text, l10n.appTitle);
    if (!shared) {
      messenger.showSnackBar(SnackBar(key: const Key('result-copied'), content: Text(l10n.resultCopied)));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    if (!analysis.isFinished) {
      return Center(
        child: FilledButton(
          key: const Key('result-open-progress'),
          onPressed: () => context.pushReplacement('/progress/${analysis.id}'),
          child: Text(l10n.progressTitle),
        ),
      );
    }
    if (analysis.status == 'failed') {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.xl),
          child: Text(
            errorCodeMessage(l10n, analysis.errorCode ?? '', analysis.errorMessage ?? ''),
            key: const Key('result-failed'),
            textAlign: TextAlign.center,
          ),
        ),
      );
    }
    final language = l10n.localeName;
    return ListView(
      key: const Key('result-list'),
      padding: const EdgeInsets.all(AppSpacing.xl),
      children: [
        Center(child: RiskGauge(score: analysis.riskScore)),
        const SizedBox(height: AppSpacing.lg),
        Center(
          child: CategoryBadge(category: analysis.category, score: analysis.riskScore),
        ),
        const SizedBox(height: AppSpacing.md),
        Text(l10n.resultDisclaimer, textAlign: TextAlign.center, style: theme.textTheme.bodySmall),
        SectionTitle(l10n.resultReasons),
        for (final reason in analysis.reasons) ReasonTile(reason: reason, language: language),
        SectionTitle(l10n.resultEvidence),
        EvidenceTile(
          tileKey: const Key('evidence-transcript'),
          title: l10n.resultTranscript,
          icon: Icons.record_voice_over_outlined,
          lines: analysis.transcript == null ? [] : [analysis.transcript!],
          footer: analysis.transcriptLanguage == null ? null : l10n.resultLanguage(analysis.transcriptLanguage!),
        ),
        EvidenceTile(
          tileKey: const Key('evidence-screen-text'),
          title: l10n.resultScreenText,
          icon: Icons.text_fields,
          lines: analysis.ocrText == null ? [] : analysis.ocrText!.split('\n'),
        ),
        EvidenceTile(
          tileKey: const Key('evidence-links'),
          title: l10n.resultLinks,
          icon: Icons.link,
          lines: analysis.links,
        ),
        EvidenceTile(
          tileKey: const Key('evidence-phones'),
          title: l10n.resultPhones,
          icon: Icons.phone,
          lines: analysis.phones,
        ),
        EvidenceTile(
          tileKey: const Key('evidence-qr'),
          title: l10n.resultQr,
          icon: Icons.qr_code_2,
          lines: analysis.qrCodes,
        ),
        const SizedBox(height: AppSpacing.xl),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                key: const Key('result-share'),
                onPressed: () => share(context, ref, l10n),
                icon: const Icon(Icons.share),
                label: Text(l10n.resultShare),
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: OutlinedButton.icon(
                key: const Key('result-feedback'),
                onPressed: () => showFeedbackSheet(context, ref, analysis),
                icon: const Icon(Icons.flag_outlined),
                label: Text(l10n.resultReportWrong),
              ),
            ),
          ],
        ),
        if (analysis.feedback != null)
          Padding(
            padding: const EdgeInsets.only(top: AppSpacing.sm),
            child: Text(l10n.feedbackGiven, key: const Key('feedback-given'), textAlign: TextAlign.center),
          ),
        const SizedBox(height: AppSpacing.md),
        FilledButton(
          key: const Key('result-check-another'),
          onPressed: () => context.go('/home'),
          child: Text(l10n.resultCheckAnother),
        ),
      ],
    );
  }
}

IconData sourceIcon(String source) {
  switch (source) {
    case 'speech':
      return Icons.record_voice_over_outlined;
    case 'screen_text':
      return Icons.text_fields;
    case 'qr':
      return Icons.qr_code_2;
    case 'classifier':
      return Icons.psychology_outlined;
    default:
      return Icons.rule;
  }
}

class ReasonTile extends StatelessWidget {
  const ReasonTile({super.key, required this.reason, required this.language});

  final Reason reason;
  final String language;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Card(
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: ListTile(
        leading: Icon(sourceIcon(reason.source)),
        title: Text(reason.messageFor(language)),
        subtitle: Text(sourceLabel(l10n, reason.source)),
      ),
    );
  }
}

class EvidenceTile extends StatelessWidget {
  const EvidenceTile({
    super.key,
    required this.tileKey,
    required this.title,
    required this.icon,
    required this.lines,
    this.footer,
  });

  final Key tileKey;
  final String title;
  final IconData icon;
  final List<String> lines;
  final String? footer;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final children = <Widget>[];
    if (lines.isEmpty) {
      children.add(ListTile(title: Text(l10n.resultNothingFound)));
    } else {
      for (final line in lines) {
        children.add(
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg, vertical: AppSpacing.xs),
            child: Align(alignment: Alignment.centerLeft, child: SelectableText(line)),
          ),
        );
      }
    }
    if (footer != null) {
      children.add(
        Padding(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Align(alignment: Alignment.centerLeft, child: Text(footer!)),
        ),
      );
    }
    return ExpansionTile(
      key: tileKey,
      leading: Icon(icon),
      title: Text('$title (${lines.length})'),
      children: children,
    );
  }
}
