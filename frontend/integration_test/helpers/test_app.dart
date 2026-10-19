import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:scam_radar/app.dart';
import 'package:scam_radar/data/storage/local_store.dart';
import 'package:scam_radar/features/home/shared_link.dart';
import 'package:scam_radar/state/device.dart';
import 'package:scam_radar/state/providers.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'fake_api.dart';

class FakeDevice extends DeviceActions {
  PickedVideo? nextVideo;
  bool shareAvailable = true;
  String? sharedText;

  @override
  Future<PickedVideo?> pickVideo() async {
    return nextVideo;
  }

  @override
  Future<bool> shareText(String text, String subject) async {
    sharedText = text;
    return shareAvailable;
  }
}

class TestHarness {
  TestHarness({required this.api, required this.device, required this.store, required this.online});

  final FakeApi api;
  final FakeDevice device;
  final LocalStore store;
  final StreamController<bool> online;
}

Future<TestHarness> pumpApp(
  WidgetTester tester, {
  FakeApi? api,
  FakeDevice? device,
  String initialLocation = '/home',
  bool onboardingDone = true,
  String language = 'en',
  bool online = true,
  Map<String, Object> prefs = const {},
  bool settle = true,
}) async {
  final values = <String, Object>{'onboarding_done': onboardingDone, 'language': language, 'client_id': 'test-client'};
  values.addAll(prefs);
  SharedPreferences.setMockInitialValues(values);
  final sharedPrefs = await SharedPreferences.getInstance();
  final store = LocalStore(sharedPrefs);
  final fakeApi = api ?? FakeApi();
  final fakeDevice = device ?? FakeDevice();
  final connection = StreamController<bool>.broadcast();
  tester.view.physicalSize = const Size(1170, 2532);
  tester.view.devicePixelRatio = 3;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(
    ProviderScope(
      retry: (count, error) => null,
      overrides: [
        localStoreProvider.overrideWithValue(store),
        apiProvider.overrideWithValue(fakeApi),
        deviceActionsProvider.overrideWithValue(fakeDevice),
        shareSheetEnabledProvider.overrideWithValue(false),
        connectivityProvider.overrideWith((ref) async* {
          yield online;
          yield* connection.stream;
        }),
      ],
      child: ScamRadarApp(initialLocation: initialLocation),
    ),
  );
  if (settle) {
    await tester.pumpAndSettle();
  } else {
    await tester.pump();
  }
  return TestHarness(api: fakeApi, device: fakeDevice, store: store, online: connection);
}

bool isVerticalScrollable(Widget widget) {
  return widget is Scrollable && widget.axisDirection == AxisDirection.down;
}

Future<void> revealKey(WidgetTester tester, String key) async {
  final finder = find.byKey(Key(key));
  if (finder.evaluate().isEmpty) {
    final scrollable = find.byWidgetPredicate(isVerticalScrollable).hitTestable();
    await tester.scrollUntilVisible(finder, 150, scrollable: scrollable.first);
  }
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
}

Future<void> tapKey(WidgetTester tester, String key) async {
  await revealKey(tester, key);
  await tester.tap(find.byKey(Key(key)));
  await tester.pumpAndSettle();
  await tester.pump(const Duration(milliseconds: 300));
  await tester.pumpAndSettle();
}

Future<void> unmountApp(WidgetTester tester) async {
  await tester.pumpWidget(const SizedBox.shrink());
  await tester.pump(const Duration(seconds: 3));
}

String currentPath(WidgetTester tester) {
  final context = tester.element(find.byType(Scaffold).last);
  final match = GoRouter.of(context).routerDelegate.currentConfiguration.last;
  return match.matchedLocation;
}
