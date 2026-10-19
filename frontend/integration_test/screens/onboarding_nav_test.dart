import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:scam_radar/data/storage/local_store.dart';
import 'package:scam_radar/state/providers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../helpers/fake_api.dart';
import '../helpers/test_app.dart';

void main() {
  testWidgets('ON-01 first start shows onboarding', (tester) async {
    await pumpApp(tester, onboardingDone: false);
    expect(find.text('Check a TikTok video'), findsOneWidget);
    expect(currentPath(tester), '/onboarding');
  });

  testWidgets('ON-02 next button walks through pages', (tester) async {
    await pumpApp(tester, onboardingDone: false);
    await tapKey(tester, 'onboarding-next');
    expect(find.text('See why it looks risky'), findsOneWidget);
    await tapKey(tester, 'onboarding-next');
    expect(find.text('This is advice, not a verdict'), findsOneWidget);
    expect(find.byKey(const Key('onboarding-accept')), findsOneWidget);
  });

  testWidgets('ON-03 swipe goes to the next page', (tester) async {
    await pumpApp(tester, onboardingDone: false);
    await tester.drag(find.byKey(const Key('onboarding-pages')), const Offset(-500, 0));
    await tester.pumpAndSettle();
    expect(find.text('See why it looks risky'), findsOneWidget);
  });

  testWidgets('ON-04 skip jumps to the disclaimer', (tester) async {
    await pumpApp(tester, onboardingDone: false);
    await tapKey(tester, 'onboarding-skip');
    expect(find.text('This is advice, not a verdict'), findsOneWidget);
  });

  testWidgets('ON-05 accept opens home and is remembered', (tester) async {
    final harness = await pumpApp(tester, onboardingDone: false);
    await tapKey(tester, 'onboarding-skip');
    await tapKey(tester, 'onboarding-accept');
    expect(currentPath(tester), '/home');
    expect(harness.store.prefs.getBool(LocalStore.onboardingDoneKey), isTrue);
  });

  testWidgets('NAV-01..04 bottom navigation opens every tab', (tester) async {
    await pumpApp(tester);
    await tapKey(tester, 'nav-history');
    expect(currentPath(tester), '/history');
    await tapKey(tester, 'nav-stats');
    expect(currentPath(tester), '/stats');
    await tapKey(tester, 'nav-settings');
    expect(currentPath(tester), '/settings');
    await tapKey(tester, 'nav-home');
    expect(currentPath(tester), '/home');
  });

  testWidgets('NAV-05 offline banner appears when the network is lost', (tester) async {
    final harness = await pumpApp(tester);
    expect(find.byKey(const Key('offline-banner')), findsNothing);
    harness.online.add(false);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('offline-banner')), findsOneWidget);
    harness.online.add(true);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('offline-banner')), findsNothing);
  });

  testWidgets('NAV-06 deep link opens a result directly', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'deep1'));
    await pumpApp(tester, api: api, initialLocation: '/result/deep1');
    expect(find.byKey(const Key('risk-gauge')), findsOneWidget);
  });

  testWidgets('NAV-07 back from result returns to history', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'b1'));
    await pumpApp(tester, api: api, initialLocation: '/history');
    await tester.tap(find.text('https://www.tiktok.com/@scam/video/1'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('risk-gauge')), findsOneWidget);
    await tapKey(tester, 'result-back');
    expect(currentPath(tester), '/history');
  });

  testWidgets('NAV-08 expired session shows a message', (tester) async {
    await pumpApp(tester);
    final container = ProviderScope.containerOf(tester.element(find.byType(Scaffold).first));
    container.read(authProvider.notifier).sessionExpired();
    await tester.pump();
    expect(find.byKey(const Key('session-expired')), findsOneWidget);
  });
}
