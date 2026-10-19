import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:scam_radar/data/models/stats.dart';

import '../helpers/fake_api.dart';
import '../helpers/test_app.dart';

FakeApi apiWithHistory() {
  final api = FakeApi();
  api.add(makeAnalysis(id: 'h1', sourceUrl: 'https://www.tiktok.com/@a/video/1', createdAt: DateTime.utc(2026, 10, 3)));
  api.add(
    makeAnalysis(
      id: 'h2',
      category: 'none',
      risk: 0.1,
      sourceUrl: 'https://www.tiktok.com/@cook/video/2',
      createdAt: DateTime.utc(2026, 10, 2),
    ),
  );
  api.add(
    makeAnalysis(
      id: 'h3',
      status: 'running',
      stage: 'listening',
      sourceUrl: null,
      createdAt: DateTime.utc(2026, 10, 1),
    ),
  );
  return api;
}

void main() {
  testWidgets('HI-01 history lists items', (tester) async {
    await pumpApp(tester, api: apiWithHistory(), initialLocation: '/history');
    expect(find.text('https://www.tiktok.com/@a/video/1'), findsOneWidget);
    expect(find.text('https://www.tiktok.com/@cook/video/2'), findsOneWidget);
    expect(find.text('video.mp4'), findsOneWidget);
    expect(find.textContaining('Investment platform ·'), findsOneWidget);
    expect(find.textContaining('Checking…'), findsOneWidget);
  });

  testWidgets('HI-02 empty history', (tester) async {
    await pumpApp(tester, initialLocation: '/history');
    expect(find.text('No checks yet'), findsOneWidget);
  });

  testWidgets('HI-03 search filters and explains empty results', (tester) async {
    final harness = await pumpApp(tester, api: apiWithHistory(), initialLocation: '/history');
    await tester.enterText(find.byKey(const Key('history-search')), 'cook');
    await tester.pump(const Duration(milliseconds: 500));
    await tester.pumpAndSettle();
    expect(harness.api.lastQuery!.search, 'cook');
    expect(find.text('https://www.tiktok.com/@cook/video/2'), findsOneWidget);
    expect(find.text('https://www.tiktok.com/@a/video/1'), findsNothing);
    await tester.enterText(find.byKey(const Key('history-search')), 'zzz');
    await tester.pump(const Duration(milliseconds: 500));
    await tester.pumpAndSettle();
    expect(find.text('Nothing matches your search'), findsOneWidget);
  });

  testWidgets('HI-04 category chips filter', (tester) async {
    final harness = await pumpApp(tester, api: apiWithHistory(), initialLocation: '/history');
    await tester.scrollUntilVisible(
      find.byKey(const Key('history-filter-none')),
      150,
      scrollable: find.descendant(of: find.byKey(const Key('history-filters')), matching: find.byType(Scrollable)),
    );
    await tapKey(tester, 'history-filter-none');
    expect(harness.api.lastQuery!.category, 'none');
    expect(find.text('https://www.tiktok.com/@a/video/1'), findsNothing);
    await tester.scrollUntilVisible(
      find.byKey(const Key('history-filter-all')),
      -150,
      scrollable: find.descendant(of: find.byKey(const Key('history-filters')), matching: find.byType(Scrollable)),
    );
    await tapKey(tester, 'history-filter-all');
    expect(harness.api.lastQuery!.category, isNull);
    expect(find.text('https://www.tiktok.com/@a/video/1'), findsOneWidget);
  });

  testWidgets('HI-05 pull to refresh reloads', (tester) async {
    final harness = await pumpApp(tester, api: apiWithHistory(), initialLocation: '/history');
    final before = harness.api.callCount('listAnalyses');
    await tester.drag(find.byKey(const Key('history-list')), const Offset(0, 500));
    await tester.pumpAndSettle();
    final afterPull = harness.api.callCount('listAnalyses');
    expect(afterPull, greaterThan(before));
    await tapKey(tester, 'history-reload');
    final afterButton = harness.api.callCount('listAnalyses');
    expect(afterButton, greaterThan(afterPull));
  });

  testWidgets('HI-06 swipe deletes an item', (tester) async {
    final harness = await pumpApp(tester, api: apiWithHistory(), initialLocation: '/history');
    await tester.drag(find.byKey(const Key('history-item-h1')), const Offset(-600, 0));
    await tester.pumpAndSettle();
    expect(harness.api.analyses.containsKey('h1'), isFalse);
    expect(find.byKey(const Key('history-deleted')), findsOneWidget);
    expect(find.text('https://www.tiktok.com/@a/video/1'), findsNothing);
  });

  testWidgets('HI-07 finished item opens the result', (tester) async {
    await pumpApp(tester, api: apiWithHistory(), initialLocation: '/history');
    await tester.tap(find.text('https://www.tiktok.com/@a/video/1'));
    await tester.pumpAndSettle();
    expect(currentPath(tester), '/result/h1');
  });

  testWidgets('HI-08 running item opens progress', (tester) async {
    await pumpApp(tester, api: apiWithHistory(), initialLocation: '/history');
    await tester.tap(find.text('video.mp4'));
    await tester.pump(const Duration(milliseconds: 500));
    expect(currentPath(tester), '/progress/h3');
    await unmountApp(tester);
  });

  testWidgets('HI-09 load more appends the next page', (tester) async {
    final api = apiWithHistory();
    api.pageSize = 2;
    await pumpApp(tester, api: api, initialLocation: '/history');
    expect(find.text('video.mp4'), findsNothing);
    await tapKey(tester, 'history-load-more');
    expect(find.text('video.mp4'), findsOneWidget);
    expect(find.byKey(const Key('history-load-more')), findsNothing);
  });

  testWidgets('HI-10 error view retries', (tester) async {
    final api = apiWithHistory();
    api.offline = true;
    await pumpApp(tester, api: api, initialLocation: '/history');
    expect(find.byKey(const Key('offline-view')), findsOneWidget);
    api.offline = false;
    await tapKey(tester, 'retry-button');
    expect(find.text('https://www.tiktok.com/@a/video/1'), findsOneWidget);
  });

  testWidgets('ST-01 statistics show cards and charts', (tester) async {
    await pumpApp(tester, initialLocation: '/stats');
    expect(find.text('3'), findsWidgets);
    expect(find.text('67%'), findsOneWidget);
    expect(find.text('4.5 s'), findsOneWidget);
    expect(find.byKey(const Key('stats-category-chart')), findsOneWidget);
    expect(find.byKey(const Key('stats-risk-chart')), findsOneWidget);
  });

  testWidgets('ST-02 scope toggle reloads', (tester) async {
    final harness = await pumpApp(tester, initialLocation: '/stats');
    expect(harness.api.lastStatsScope, 'mine');
    await tapKey(tester, 'stats-scope-all');
    expect(harness.api.lastStatsScope, 'all');
  });

  testWidgets('ST-03 empty statistics', (tester) async {
    final api = FakeApi();
    api.stats = makeStats(total: 0);
    await pumpApp(tester, api: api, initialLocation: '/stats');
    expect(find.text('No statistics yet. Check a video first.'), findsOneWidget);
  });

  testWidgets('ST-04 error view retries', (tester) async {
    final api = FakeApi();
    api.offline = true;
    await pumpApp(tester, api: api, initialLocation: '/stats');
    expect(find.byKey(const Key('offline-view')), findsOneWidget);
    api.offline = false;
    await tapKey(tester, 'retry-button');
    expect(find.byKey(const Key('stats-content')), findsOneWidget);
  });

  testWidgets('ST-05 pull to refresh reloads statistics', (tester) async {
    final harness = await pumpApp(tester, initialLocation: '/stats');
    final before = harness.api.callCount('getStats');
    await tester.drag(find.byKey(const Key('stats-content')), const Offset(0, 500));
    await tester.pumpAndSettle();
    final afterPull = harness.api.callCount('getStats');
    expect(afterPull, greaterThan(before));
    await tapKey(tester, 'stats-reload');
    final afterButton = harness.api.callCount('getStats');
    expect(afterButton, greaterThan(afterPull));
  });

  testWidgets('ST-06 only failed checks show an empty category chart', (tester) async {
    final api = FakeApi();
    final stats = makeStats(total: 0);
    api.stats = Stats(
      totalAnalyses: 1,
      doneAnalyses: 0,
      failedAnalyses: 1,
      scamShare: 0,
      averageProcessingSeconds: null,
      perCategory: stats.perCategory,
      riskOverTime: const [],
    );
    await pumpApp(tester, api: api, initialLocation: '/stats');
    expect(find.byKey(const Key('stats-category-empty')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
