import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../data/api/api_exception.dart';
import '../../data/models/analysis_summary.dart';
import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../theme/tokens.dart';
import '../../widgets/labels.dart';
import '../../widgets/state_views.dart';

class HistoryScreen extends ConsumerStatefulWidget {
  const HistoryScreen({super.key});

  @override
  ConsumerState<HistoryScreen> createState() => HistoryScreenState();
}

class HistoryScreenState extends ConsumerState<HistoryScreen> {
  final searchController = TextEditingController();
  Timer? debounce;

  @override
  void dispose() {
    debounce?.cancel();
    searchController.dispose();
    super.dispose();
  }

  void onSearchChanged(String value) {
    debounce?.cancel();
    debounce = Timer(const Duration(milliseconds: 400), () {
      ref.read(historyProvider.notifier).setSearch(value);
    });
  }

  Future<void> delete(AnalysisSummary item) async {
    final l10n = AppLocalizations.of(context);
    final messenger = ScaffoldMessenger.of(context);
    try {
      await ref.read(historyProvider.notifier).remove(item.id);
      messenger.showSnackBar(SnackBar(key: const Key('history-deleted'), content: Text(l10n.historyDeleted)));
    } on ApiException catch (error) {
      messenger.showSnackBar(SnackBar(content: Text(errorMessage(l10n, error))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final history = ref.watch(historyProvider);
    final notifier = ref.read(historyProvider.notifier);
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.historyTitle),
        actions: [
          IconButton(
            key: const Key('history-reload'),
            tooltip: l10n.retry,
            icon: const Icon(Icons.refresh),
            onPressed: notifier.refresh,
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(AppSpacing.lg, AppSpacing.sm, AppSpacing.lg, 0),
            child: TextField(
              key: const Key('history-search'),
              controller: searchController,
              onChanged: onSearchChanged,
              decoration: InputDecoration(prefixIcon: const Icon(Icons.search), hintText: l10n.historySearchHint),
            ),
          ),
          SizedBox(
            height: 64,
            child: ListView(
              key: const Key('history-filters'),
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg, vertical: AppSpacing.xs),
              children: [
                Padding(
                  padding: const EdgeInsets.only(right: AppSpacing.sm),
                  child: ChoiceChip(
                    key: const Key('history-filter-all'),
                    label: Text(l10n.historyFilterAll),
                    selected: notifier.category == null,
                    onSelected: (_) => notifier.setCategory(null),
                  ),
                ),
                for (final category in allCategories)
                  Padding(
                    padding: const EdgeInsets.only(right: AppSpacing.sm),
                    child: ChoiceChip(
                      key: Key('history-filter-$category'),
                      label: Text(categoryLabel(l10n, category)),
                      selected: notifier.category == category,
                      onSelected: (_) => notifier.setCategory(category),
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: history.when(
              loading: () => const LoadingView(),
              error: (error, stack) => ErrorView(error: error, onRetry: notifier.refresh),
              data: (state) => buildList(context, l10n, state),
            ),
          ),
        ],
      ),
    );
  }

  Widget buildList(BuildContext context, AppLocalizations l10n, HistoryState state) {
    final notifier = ref.read(historyProvider.notifier);
    if (state.items.isEmpty) {
      return RefreshIndicator(
        onRefresh: notifier.refresh,
        child: ListView(
          children: [
            const SizedBox(height: 80),
            EmptyView(
              title: state.filtered ? l10n.historyNoMatches : l10n.historyEmpty,
              message: state.filtered ? null : l10n.historyEmptyHint,
              icon: Icons.history,
            ),
          ],
        ),
      );
    }
    final count = state.items.length + (state.hasMore ? 1 : 0);
    return RefreshIndicator(
      key: const Key('history-refresh'),
      onRefresh: notifier.refresh,
      child: ListView.builder(
        key: const Key('history-list'),
        physics: const AlwaysScrollableScrollPhysics(),
        itemCount: count,
        itemBuilder: (context, index) {
          if (index >= state.items.length) {
            return Padding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              child: state.loadingMore
                  ? const Center(child: CircularProgressIndicator())
                  : OutlinedButton(
                      key: const Key('history-load-more'),
                      onPressed: notifier.loadMore,
                      child: Text(l10n.historyLoadMore),
                    ),
            );
          }
          final item = state.items[index];
          return Dismissible(
            key: Key('history-item-${item.id}'),
            direction: DismissDirection.endToStart,
            background: Container(
              color: Theme.of(context).colorScheme.errorContainer,
              alignment: Alignment.centerRight,
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.xl),
              child: Icon(Icons.delete_outline, color: Theme.of(context).colorScheme.onErrorContainer),
            ),
            onDismissed: (_) => delete(item),
            child: HistoryTile(item: item),
          );
        },
      ),
    );
  }
}

class HistoryTile extends StatelessWidget {
  const HistoryTile({super.key, required this.item});

  final AnalysisSummary item;

  String subtitle(AppLocalizations l10n) {
    final date = DateFormat.yMMMd(l10n.localeName).add_Hm().format(item.createdAt.toLocal());
    if (item.status == 'queued') {
      return '${l10n.historyStatusQueued} · $date';
    }
    if (item.status == 'running') {
      return '${l10n.historyStatusRunning} · $date';
    }
    if (item.status == 'failed') {
      return '${l10n.historyStatusFailed} · $date';
    }
    return '${categoryLabel(l10n, item.category)} · $date';
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final finished = item.status == 'done' || item.status == 'failed';
    final score = item.riskScore;
    return ListTile(
      leading: CircleAvatar(
        backgroundColor: RiskLevel.color(score),
        foregroundColor: AppColors.onRisk,
        child: Text(score == null ? '—' : '${(score * 100).round()}', style: const TextStyle(fontSize: 13)),
      ),
      title: Text(item.title, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text(subtitle(l10n)),
      trailing: Icon(item.sourceType == 'upload' ? Icons.upload_file : Icons.link),
      onTap: () => context.push(finished ? '/result/${item.id}' : '/progress/${item.id}'),
    );
  }
}
