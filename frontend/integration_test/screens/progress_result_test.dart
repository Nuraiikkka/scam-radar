import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../helpers/fake_api.dart';
import '../helpers/test_app.dart';

String? stageText(WidgetTester tester) {
  return tester.widget<Text>(find.byKey(const Key('progress-stage'))).data;
}

Future<void> pollOnce(WidgetTester tester) async {
  await tester.pump(const Duration(seconds: 2));
  await tester.pump(const Duration(milliseconds: 100));
}

FakeApi scriptedApi() {
  final api = FakeApi();
  api.scripted['p1'] = [
    makeAnalysis(id: 'p1', status: 'queued', stage: 'queued'),
    makeAnalysis(id: 'p1', status: 'running', stage: 'downloading'),
    makeAnalysis(id: 'p1', status: 'running', stage: 'listening'),
    makeAnalysis(id: 'p1', status: 'running', stage: 'reading_screen'),
    makeAnalysis(id: 'p1', status: 'running', stage: 'scoring'),
    makeAnalysis(id: 'p1'),
  ];
  return api;
}

void main() {
  testWidgets('PR-01 and PR-02 stages update and finish on the result', (tester) async {
    final api = scriptedApi();
    await pumpApp(tester, api: api, initialLocation: '/progress/p1', settle: false);
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.text('Waiting in line'), findsWidgets);
    await pollOnce(tester);
    expect(stageText(tester), 'Downloading the video');
    await pollOnce(tester);
    expect(stageText(tester), 'Listening to the speech');
    await pollOnce(tester);
    expect(stageText(tester), 'Reading the screen');
    await pollOnce(tester);
    await pollOnce(tester);
    await tester.pumpAndSettle();
    expect(currentPath(tester), '/result/p1');
    expect(find.byKey(const Key('risk-gauge')), findsOneWidget);
  });

  testWidgets('PR-03 and PR-04 failed analysis explains and goes home', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'f1', status: 'failed', errorCode: 'video_private'));
    await pumpApp(tester, api: api, initialLocation: '/progress/f1', settle: false);
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.byKey(const Key('progress-failed')), findsOneWidget);
    expect(find.text('This video is private, so it cannot be checked.'), findsOneWidget);
    await tapKey(tester, 'progress-back-home');
    expect(currentPath(tester), '/home');
  });

  testWidgets('PR-05 continue in background opens history', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1', status: 'running', stage: 'listening'));
    await pumpApp(tester, api: api, initialLocation: '/progress/r1', settle: false);
    await tester.pump(const Duration(milliseconds: 200));
    await tester.tap(find.byKey(const Key('progress-background')));
    await tester.pump(const Duration(milliseconds: 500));
    expect(currentPath(tester), '/history');
    await unmountApp(tester);
  });

  testWidgets('PR-06 back arrow leaves progress', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1', status: 'running', stage: 'listening'));
    await pumpApp(tester, api: api, initialLocation: '/progress/r1', settle: false);
    await tester.pump(const Duration(milliseconds: 200));
    await tester.tap(find.byKey(const Key('progress-back')));
    await tester.pump(const Duration(milliseconds: 500));
    expect(currentPath(tester), '/home');
    await unmountApp(tester);
  });

  testWidgets('PR-07 and PR-08 repeated network errors show retry that resumes', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1', status: 'running', stage: 'listening'));
    api.offline = true;
    await pumpApp(tester, api: api, initialLocation: '/progress/r1', settle: false);
    for (var index = 0; index < 5; index++) {
      await pollOnce(tester);
    }
    expect(find.byKey(const Key('offline-view')), findsOneWidget);
    api.offline = false;
    api.add(makeAnalysis(id: 'r1'));
    await tester.tap(find.byKey(const Key('retry-button')));
    await tester.pump(const Duration(milliseconds: 200));
    await tester.pumpAndSettle();
    expect(currentPath(tester), '/result/r1');
  });

  testWidgets('PR-09 unknown analysis shows not found', (tester) async {
    await pumpApp(tester, initialLocation: '/progress/missing', settle: false);
    await tester.pump(const Duration(milliseconds: 200));
    expect(find.text('This check was not found.'), findsOneWidget);
  });

  testWidgets('RE-01 result shows score, category and reasons with sources', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1'));
    await pumpApp(tester, api: api, initialLocation: '/result/r1');
    expect(find.text('82%'), findsOneWidget);
    expect(find.text('High risk'), findsOneWidget);
    expect(find.text('Investment platform'), findsOneWidget);
    expect(find.text('In speech: sounds like an investment platform pitch'), findsOneWidget);
    expect(find.text('Speech'), findsOneWidget);
    expect(find.text('QR code'), findsOneWidget);
    expect(find.bySemanticsLabel('Risk 82 percent, High risk'), findsOneWidget);
  });

  testWidgets('RE-02 evidence tiles expand', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1'));
    await pumpApp(tester, api: api, initialLocation: '/result/r1');
    final tiles = {
      'evidence-transcript': 'Платформа даёт 30% в день',
      'evidence-screen-text': 'ДОХОД 30% В ДЕНЬ',
      'evidence-links': 't.me/profit',
      'evidence-phones': '+77015551234',
      'evidence-qr': 'https://t.me/profit',
    };
    for (final entry in tiles.entries) {
      await tapKey(tester, entry.key);
      expect(find.text(entry.value), findsWidgets);
    }
  });

  testWidgets('RE-03 share uses the share sheet or copies', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1'));
    final harness = await pumpApp(tester, api: api, initialLocation: '/result/r1');
    await tapKey(tester, 'result-share');
    expect(harness.device.sharedText, contains('High risk (82%)'));
    expect(harness.device.sharedText, contains('This is a risk estimate, not a legal verdict.'));
    harness.device.shareAvailable = false;
    await tapKey(tester, 'result-share');
    expect(find.byKey(const Key('result-copied')), findsOneWidget);
  });

  testWidgets('RE-04 and RE-05 correct feedback', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1'));
    await pumpApp(tester, api: api, initialLocation: '/result/r1');
    await tapKey(tester, 'result-feedback');
    expect(find.byKey(const Key('feedback-sheet')), findsOneWidget);
    await tapKey(tester, 'feedback-correct');
    await tapKey(tester, 'feedback-send');
    expect(api.lastFeedback!.isCorrect, isTrue);
    expect(find.byKey(const Key('feedback-thanks')), findsOneWidget);
    expect(find.byKey(const Key('feedback-given')), findsOneWidget);
  });

  testWidgets('RE-06 and RE-07 wrong verdict needs a category', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1'));
    await pumpApp(tester, api: api, initialLocation: '/result/r1');
    await tapKey(tester, 'result-feedback');
    await tapKey(tester, 'feedback-incorrect');
    final send = tester.widget<FilledButton>(find.byKey(const Key('feedback-send')));
    expect(send.onPressed, isNull);
    await tapKey(tester, 'feedback-category');
    await tester.tap(find.text('Fake giveaway').last);
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('feedback-comment')), 'It is a giveaway');
    await tapKey(tester, 'feedback-send');
    expect(api.lastFeedback!.isCorrect, isFalse);
    expect(api.lastFeedback!.trueCategory, 'giveaway');
    expect(api.lastFeedback!.comment, 'It is a giveaway');
  });

  testWidgets('RE-08 check another goes home', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1'));
    await pumpApp(tester, api: api, initialLocation: '/result/r1');
    await tapKey(tester, 'result-check-another');
    expect(currentPath(tester), '/home');
  });

  testWidgets('RE-09 back arrow without history goes home', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1'));
    await pumpApp(tester, api: api, initialLocation: '/result/r1');
    await tapKey(tester, 'result-back');
    expect(currentPath(tester), '/home');
  });

  testWidgets('RE-10 error view retries', (tester) async {
    final api = FakeApi();
    api.offline = true;
    await pumpApp(tester, api: api, initialLocation: '/result/r1');
    expect(find.byKey(const Key('offline-view')), findsOneWidget);
    api.offline = false;
    api.add(makeAnalysis(id: 'r1'));
    await tapKey(tester, 'retry-button');
    expect(find.byKey(const Key('risk-gauge')), findsOneWidget);
  });

  testWidgets('RE-11 failed analysis shows its message', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'f1', status: 'failed', errorCode: 'video_unavailable'));
    await pumpApp(tester, api: api, initialLocation: '/result/f1');
    expect(find.text('This video was removed or is not available.'), findsOneWidget);
  });

  testWidgets('RE-12 reasons follow the app language', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'r1'));
    await pumpApp(tester, api: api, initialLocation: '/result/r1', language: 'ru');
    expect(find.text('В речи: похоже на рекламу инвестиционной платформы'), findsOneWidget);
    expect(find.text('Высокий риск'), findsOneWidget);
  });
}
