import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:scam_radar/data/api/api_exception.dart';
import 'package:scam_radar/features/home/shared_link.dart';
import 'package:scam_radar/state/device.dart';

import '../helpers/fake_api.dart';
import '../helpers/test_app.dart';

const String validLink = 'https://www.tiktok.com/@user/video/123';

FakeApi apiWithRunningAnalysis() {
  final api = FakeApi();
  api.add(makeAnalysis(id: 'new1', status: 'running', stage: 'listening'));
  return api;
}

void main() {
  testWidgets('HO-01 empty link shows an error', (tester) async {
    final harness = await pumpApp(tester);
    await tapKey(tester, 'home-check-link');
    expect(find.text('Paste a link first'), findsOneWidget);
    expect(harness.api.calls, isNot(contains('analyzeUrl')));
  });

  testWidgets('HO-02 non TikTok link shows an error', (tester) async {
    await pumpApp(tester);
    await tester.enterText(find.byKey(const Key('home-link-field')), 'https://youtube.com/watch?v=1');
    await tapKey(tester, 'home-check-link');
    expect(find.text('This is not a TikTok link'), findsOneWidget);
  });

  testWidgets('HO-03 valid link opens progress', (tester) async {
    final harness = await pumpApp(tester, api: apiWithRunningAnalysis());
    await tester.enterText(find.byKey(const Key('home-link-field')), validLink);
    await tester.tap(find.byKey(const Key('home-check-link')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(harness.api.lastUrl, validLink);
    expect(currentPath(tester), '/progress/new1');
    await unmountApp(tester);
  });

  testWidgets('HO-04 enter key submits the link', (tester) async {
    final harness = await pumpApp(tester, api: apiWithRunningAnalysis());
    await tester.enterText(find.byKey(const Key('home-link-field')), validLink);
    await tester.testTextInput.receiveAction(TextInputAction.go);
    await tester.pump(const Duration(milliseconds: 500));
    expect(harness.api.lastUrl, validLink);
    await unmountApp(tester);
  });

  testWidgets('HO-05 server errors are shown clearly', (tester) async {
    final api = FakeApi();
    api.errors['analyzeUrl'] = ApiException(code: 'rate_limited', message: 'Too many', statusCode: 429);
    await pumpApp(tester, api: api);
    await tester.enterText(find.byKey(const Key('home-link-field')), validLink);
    await tapKey(tester, 'home-check-link');
    expect(find.text('Too many attempts. Please wait a little and try again.'), findsOneWidget);
    expect(currentPath(tester), '/home');
  });

  testWidgets('HO-06 unreachable server is explained', (tester) async {
    final api = FakeApi();
    api.offline = true;
    await pumpApp(tester, api: api);
    await tester.enterText(find.byKey(const Key('home-link-field')), validLink);
    await tapKey(tester, 'home-check-link');
    expect(find.text('Cannot reach the server. Check your internet connection.'), findsOneWidget);
  });

  testWidgets('HO-07 picking a video uploads it', (tester) async {
    final device = FakeDevice();
    device.nextVideo = PickedVideo(name: 'clip.mp4', size: 1000, path: '/tmp/clip.mp4');
    final harness = await pumpApp(tester, api: apiWithRunningAnalysis(), device: device);
    await tester.tap(find.byKey(const Key('home-pick-file')));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(harness.api.lastUploadName, 'clip.mp4');
    expect(currentPath(tester), '/progress/new1');
    await unmountApp(tester);
  });

  testWidgets('HO-08 too large file is rejected before upload', (tester) async {
    final device = FakeDevice();
    device.nextVideo = PickedVideo(name: 'big.mp4', size: 200 * 1024 * 1024, path: '/tmp/big.mp4');
    final harness = await pumpApp(tester, device: device);
    await tapKey(tester, 'home-pick-file');
    expect(find.byKey(const Key('home-file-too-large')), findsOneWidget);
    expect(harness.api.calls, isNot(contains('analyzeFile')));
  });

  testWidgets('HO-09 cancelled picker does nothing', (tester) async {
    final harness = await pumpApp(tester);
    await tapKey(tester, 'home-pick-file');
    expect(harness.api.calls, isNot(contains('analyzeFile')));
    expect(currentPath(tester), '/home');
  });

  testWidgets('HO-10 login hint opens login', (tester) async {
    await pumpApp(tester);
    await tapKey(tester, 'home-login');
    expect(currentPath(tester), '/login');
  });

  testWidgets('HO-11 shared link is filled in', (tester) async {
    await pumpApp(tester);
    final container = ProviderScope.containerOf(tester.element(find.byType(Scaffold).first));
    container.read(sharedLinkProvider.notifier).receive('Look at this $validLink wow');
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('shared-link-note')), findsOneWidget);
    expect(find.text(validLink), findsOneWidget);
  });

  test('HO-11 link extraction from shared text', () {
    expect(extractLink('watch https://vm.tiktok.com/ZMabc/ now'), 'https://vm.tiktok.com/ZMabc/');
    expect(extractLink('no link here'), isNull);
  });
}
