import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../l10n/app_localizations.dart';
import '../state/providers.dart';
import '../theme/tokens.dart';
import 'labels.dart';

class LoadingView extends StatelessWidget {
  const LoadingView({super.key, this.message});

  final String? message;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Center(
      child: Semantics(
        liveRegion: true,
        label: message ?? l10n.loading,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(),
            const SizedBox(height: AppSpacing.lg),
            Text(message ?? l10n.loading, textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }
}

class EmptyView extends StatelessWidget {
  const EmptyView({super.key, required this.title, this.message, this.icon = Icons.inbox_outlined, this.action});

  final String title;
  final String? message;
  final IconData icon;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          key: const Key('empty-view'),
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 56, color: theme.colorScheme.outline),
            const SizedBox(height: AppSpacing.lg),
            Text(title, style: theme.textTheme.titleMedium, textAlign: TextAlign.center),
            if (message != null) ...[
              const SizedBox(height: AppSpacing.sm),
              Text(message!, textAlign: TextAlign.center, style: theme.textTheme.bodyMedium),
            ],
            if (action != null) ...[const SizedBox(height: AppSpacing.lg), action!],
          ],
        ),
      ),
    );
  }
}

class ErrorView extends StatelessWidget {
  const ErrorView({super.key, required this.error, required this.onRetry});

  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final theme = Theme.of(context);
    final offline = isOfflineError(error);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.xl),
        child: Column(
          key: Key(offline ? 'offline-view' : 'error-view'),
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(offline ? Icons.wifi_off : Icons.error_outline, size: 56, color: theme.colorScheme.error),
            const SizedBox(height: AppSpacing.lg),
            Semantics(
              liveRegion: true,
              child: Text(errorMessage(l10n, error), textAlign: TextAlign.center, style: theme.textTheme.bodyLarge),
            ),
            const SizedBox(height: AppSpacing.lg),
            OutlinedButton.icon(
              key: const Key('retry-button'),
              onPressed: onRetry,
              icon: const Icon(Icons.refresh),
              label: Text(l10n.retry),
            ),
          ],
        ),
      ),
    );
  }
}

class OfflineBanner extends ConsumerWidget {
  const OfflineBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final online = ref.watch(connectivityProvider).value ?? true;
    if (online) {
      return const SizedBox.shrink();
    }
    final theme = Theme.of(context);
    return Semantics(
      liveRegion: true,
      child: Container(
        key: const Key('offline-banner'),
        width: double.infinity,
        color: theme.colorScheme.errorContainer,
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg, vertical: AppSpacing.sm),
        child: Row(
          children: [
            Icon(Icons.wifi_off, color: theme.colorScheme.onErrorContainer, size: 18),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Text(
                AppLocalizations.of(context).offlineBanner,
                style: TextStyle(color: theme.colorScheme.onErrorContainer),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: AppSpacing.xl, bottom: AppSpacing.sm),
      child: Semantics(header: true, child: Text(text, style: Theme.of(context).textTheme.titleMedium)),
    );
  }
}
