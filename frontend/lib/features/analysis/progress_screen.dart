import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/api/api_exception.dart';
import '../../data/models/analysis.dart';
import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../theme/tokens.dart';
import '../../widgets/labels.dart';
import '../../widgets/state_views.dart';

const List<String> visibleStages = ['downloading', 'listening', 'reading_screen', 'scoring'];
const int maxPollErrors = 5;
const Duration slowAfter = Duration(seconds: 90);

class ProgressScreen extends ConsumerStatefulWidget {
  const ProgressScreen({super.key, required this.analysisId});

  final String analysisId;

  @override
  ConsumerState<ProgressScreen> createState() => ProgressScreenState();
}

class ProgressScreenState extends ConsumerState<ProgressScreen> {
  Timer? timer;
  Analysis? analysis;
  Object? error;
  int pollErrors = 0;
  bool polling = false;
  final DateTime startedAt = DateTime.now();

  @override
  void initState() {
    super.initState();
    poll();
    timer = Timer.periodic(AppDurations.pollInterval, (_) => poll());
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  Duration get elapsed => DateTime.now().difference(startedAt);

  Future<void> poll() async {
    if (polling || !mounted) {
      return;
    }
    polling = true;
    try {
      final result = await ref.read(apiProvider).getAnalysis(widget.analysisId);
      if (!mounted) {
        return;
      }
      setState(() {
        analysis = result;
        pollErrors = 0;
        error = null;
      });
      if (result.status == 'done') {
        timer?.cancel();
        ref.invalidate(historyProvider);
        ref.invalidate(statsProvider);
        context.pushReplacement('/result/${result.id}');
      } else if (result.status == 'failed') {
        timer?.cancel();
        ref.invalidate(historyProvider);
      } else if (elapsed > AppDurations.maxWait) {
        timer?.cancel();
        setState(() => error = ApiException(code: 'processing_timeout', message: ''));
      }
    } on ApiException catch (caught) {
      if (!mounted) {
        return;
      }
      pollErrors = pollErrors + 1;
      if (caught.statusCode == 404 || pollErrors >= maxPollErrors) {
        timer?.cancel();
        setState(() => error = caught);
      }
    } finally {
      polling = false;
    }
  }

  void restart() {
    setState(() {
      error = null;
      pollErrors = 0;
    });
    timer?.cancel();
    poll();
    timer = Timer.periodic(AppDurations.pollInterval, (_) => poll());
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.progressTitle),
        leading: IconButton(
          key: const Key('progress-back'),
          tooltip: l10n.progressBackground,
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.canPop() ? context.pop() : context.go('/home'),
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            const OfflineBanner(),
            Expanded(child: buildBody(context, l10n)),
          ],
        ),
      ),
    );
  }

  Widget buildBody(BuildContext context, AppLocalizations l10n) {
    final current = analysis;
    if (error != null) {
      return ErrorView(error: error!, onRetry: restart);
    }
    if (current != null && current.status == 'failed') {
      return FailedView(analysis: current);
    }
    final stage = current?.stage ?? 'queued';
    final stageIndex = visibleStages.indexOf(stage == 'finished' ? 'scoring' : stage);
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.xl),
      children: [
        const Center(child: SizedBox(width: 56, height: 56, child: CircularProgressIndicator())),
        const SizedBox(height: AppSpacing.xl),
        Semantics(
          liveRegion: true,
          child: Text(
            stageLabel(l10n, stage),
            key: const Key('progress-stage'),
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ),
        const SizedBox(height: AppSpacing.sm),
        Text(
          elapsed > slowAfter ? l10n.progressSlow : l10n.progressHint,
          key: const Key('progress-hint'),
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: AppSpacing.xl),
        for (var index = 0; index < visibleStages.length; index++)
          StageRow(
            label: stageLabel(l10n, visibleStages[index]),
            done: stageIndex > index,
            active: stageIndex == index,
          ),
        const SizedBox(height: AppSpacing.xl),
        OutlinedButton(
          key: const Key('progress-background'),
          onPressed: () => context.go('/history'),
          child: Text(l10n.progressBackground),
        ),
      ],
    );
  }
}

class StageRow extends StatelessWidget {
  const StageRow({super.key, required this.label, required this.done, required this.active});

  final String label;
  final bool done;
  final bool active;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    IconData icon = Icons.radio_button_unchecked;
    Color color = scheme.outline;
    if (done) {
      icon = Icons.check_circle;
      color = AppColors.riskLow;
    } else if (active) {
      icon = Icons.timelapse;
      color = scheme.primary;
    }
    return ListTile(
      leading: Icon(icon, color: color),
      title: Text(label, style: TextStyle(fontWeight: active ? FontWeight.bold : FontWeight.normal)),
    );
  }
}

class FailedView extends StatelessWidget {
  const FailedView({super.key, required this.analysis});

  final Analysis analysis;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final message = errorCodeMessage(l10n, analysis.errorCode ?? '', analysis.errorMessage ?? '');
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          key: const Key('progress-failed'),
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.error_outline, size: 64, color: theme.colorScheme.error),
            const SizedBox(height: AppSpacing.lg),
            Text(l10n.progressFailedTitle, style: theme.textTheme.titleLarge),
            const SizedBox(height: AppSpacing.sm),
            Semantics(liveRegion: true, child: Text(message, textAlign: TextAlign.center)),
            const SizedBox(height: AppSpacing.xl),
            FilledButton(
              key: const Key('progress-back-home'),
              onPressed: () => context.go('/home'),
              child: Text(l10n.progressBackHome),
            ),
          ],
        ),
      ),
    );
  }
}
