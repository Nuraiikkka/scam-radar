import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../data/models/stats.dart';
import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../theme/tokens.dart';
import '../../widgets/labels.dart';
import '../../widgets/state_views.dart';

const Map<String, Color> categoryColors = {
  'investment_platform': Color(0xFFC62828),
  'pyramid': Color(0xFF6A1B9A),
  'betting': Color(0xFFEF6C00),
  'giveaway': Color(0xFF1565C0),
  'job_offer': Color(0xFF00838F),
  'none': Color(0xFF2E7D32),
};

class StatsScreen extends ConsumerStatefulWidget {
  const StatsScreen({super.key});

  @override
  ConsumerState<StatsScreen> createState() => StatsScreenState();
}

class StatsScreenState extends ConsumerState<StatsScreen> {
  String scope = 'mine';

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    final stats = ref.watch(statsProvider(scope));
    return Scaffold(
      appBar: AppBar(
        title: Text(l10n.statsTitle),
        actions: [
          IconButton(
            key: const Key('stats-reload'),
            tooltip: l10n.retry,
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(statsProvider(scope)),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: SegmentedButton<String>(
              key: const Key('stats-scope'),
              segments: [
                ButtonSegment(
                  value: 'mine',
                  label: Text(l10n.statsScopeMine, key: const Key('stats-scope-mine')),
                ),
                ButtonSegment(
                  value: 'all',
                  label: Text(l10n.statsScopeAll, key: const Key('stats-scope-all')),
                ),
              ],
              selected: {scope},
              onSelectionChanged: (values) => setState(() => scope = values.first),
            ),
          ),
          Expanded(
            child: stats.when(
              loading: () => const LoadingView(),
              error: (error, stack) => ErrorView(error: error, onRetry: () => ref.invalidate(statsProvider(scope))),
              data: (data) => RefreshIndicator(
                onRefresh: () => ref.refresh(statsProvider(scope).future),
                child: buildContent(context, l10n, data),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget buildContent(BuildContext context, AppLocalizations l10n, Stats data) {
    if (data.totalAnalyses == 0) {
      return ListView(
        children: [
          const SizedBox(height: 80),
          EmptyView(title: l10n.statsEmpty, icon: Icons.bar_chart),
        ],
      );
    }
    final seconds = data.averageProcessingSeconds == null
        ? '—'
        : l10n.statsSeconds(data.averageProcessingSeconds!.toStringAsFixed(1));
    return ListView(
      key: const Key('stats-content'),
      padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
      children: [
        Row(
          children: [
            Expanded(
              child: StatCard(label: l10n.statsTotal, value: '${data.totalAnalyses}'),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: StatCard(label: l10n.statsScamShare, value: '${(data.scamShare * 100).round()}%'),
            ),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: StatCard(label: l10n.statsAverageTime, value: seconds),
            ),
          ],
        ),
        SectionTitle(l10n.statsByCategory),
        CategoryChart(counts: data.perCategory),
        SectionTitle(l10n.statsRiskOverTime),
        RiskLineChart(days: data.riskOverTime),
        const SizedBox(height: AppSpacing.xxl),
      ],
    );
  }
}

class StatCard extends StatelessWidget {
  const StatCard({super.key, required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Semantics(
          label: '$label: $value',
          excludeSemantics: true,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(value, style: theme.textTheme.headlineSmall),
              const SizedBox(height: AppSpacing.xs),
              Text(label, style: theme.textTheme.bodySmall, maxLines: 2),
            ],
          ),
        ),
      ),
    );
  }
}

class CategoryChart extends StatelessWidget {
  const CategoryChart({super.key, required this.counts});

  final List<CategoryCount> counts;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    var maxCount = 0;
    for (final item in counts) {
      if (item.count > maxCount) {
        maxCount = item.count;
      }
    }
    if (maxCount == 0) {
      return Text(l10n.resultNothingFound, key: const Key('stats-category-empty'));
    }
    final step = maxCount <= 5 ? 1.0 : (maxCount / 5).ceilToDouble();
    final groups = <BarChartGroupData>[];
    for (var index = 0; index < counts.length; index++) {
      final item = counts[index];
      groups.add(
        BarChartGroupData(
          x: index,
          barRods: [
            BarChartRodData(
              toY: item.count.toDouble(),
              color: categoryColors[item.category],
              width: 22,
              borderRadius: BorderRadius.circular(AppRadius.sm / 2),
            ),
          ],
        ),
      );
    }
    final description = <String>[];
    for (final item in counts) {
      description.add('${categoryLabel(l10n, item.category)}: ${item.count}');
    }
    return Semantics(
      label: description.join(', '),
      excludeSemantics: true,
      child: Column(
        key: const Key('stats-category-chart'),
        children: [
          SizedBox(
            height: 200,
            child: BarChart(
              BarChartData(
                maxY: maxCount.toDouble() + step,
                barGroups: groups,
                gridData: const FlGridData(show: false),
                borderData: FlBorderData(show: false),
                titlesData: FlTitlesData(
                  topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  bottomTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 32,
                      interval: step,
                      getTitlesWidget: (value, meta) => Text(value.toInt().toString()),
                    ),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          Wrap(
            spacing: AppSpacing.md,
            runSpacing: AppSpacing.xs,
            children: [
              for (final item in counts)
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(width: 12, height: 12, color: categoryColors[item.category]),
                    const SizedBox(width: AppSpacing.xs),
                    Flexible(child: Text('${categoryLabel(l10n, item.category)} (${item.count})')),
                  ],
                ),
            ],
          ),
        ],
      ),
    );
  }
}

class RiskLineChart extends StatelessWidget {
  const RiskLineChart({super.key, required this.days});

  final List<DailyRisk> days;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    if (days.isEmpty) {
      return Text(l10n.resultNothingFound);
    }
    final spots = <FlSpot>[];
    for (var index = 0; index < days.length; index++) {
      spots.add(FlSpot(index.toDouble(), days[index].averageRisk * 100));
    }
    final format = DateFormat.Md(l10n.localeName);
    final description = <String>[];
    for (final day in days) {
      description.add('${format.format(day.day)}: ${(day.averageRisk * 100).round()}%');
    }
    return Semantics(
      label: description.join(', '),
      excludeSemantics: true,
      child: SizedBox(
        key: const Key('stats-risk-chart'),
        height: 200,
        child: LineChart(
          LineChartData(
            minY: 0,
            maxY: 100,
            minX: 0,
            maxX: days.length == 1 ? 1 : (days.length - 1).toDouble(),
            gridData: const FlGridData(show: true, drawVerticalLine: false),
            borderData: FlBorderData(show: false),
            lineBarsData: [
              LineChartBarData(
                spots: spots,
                isCurved: false,
                color: Theme.of(context).colorScheme.primary,
                barWidth: 3,
                dotData: const FlDotData(show: true),
              ),
            ],
            titlesData: FlTitlesData(
              topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              leftTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  reservedSize: 36,
                  interval: 25,
                  getTitlesWidget: (value, meta) => Text('${value.toInt()}%', style: const TextStyle(fontSize: 11)),
                ),
              ),
              bottomTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  interval: 1,
                  getTitlesWidget: (value, meta) {
                    final index = value.toInt();
                    if (index < 0 || index >= days.length || value != index.toDouble()) {
                      return const SizedBox.shrink();
                    }
                    return Text(format.format(days[index].day), style: const TextStyle(fontSize: 11));
                  },
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
