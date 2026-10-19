import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../helpers/fake_api.dart';
import '../helpers/test_app.dart';

const List<String> routes = ['/home', '/history', '/stats', '/settings', '/result/r1', '/login', '/register'];

FakeApi filledApi() {
  final api = FakeApi();
  api.add(makeAnalysis(id: 'r1'));
  api.add(makeAnalysis(id: 'r2', category: 'none', risk: 0.1));
  return api;
}

Future<void> pumpScaled(WidgetTester tester, String route, String language) async {
  await pumpApp(tester, api: filledApi(), initialLocation: route, language: language);
  tester.platformDispatcher.textScaleFactorTestValue = 1.5;
  addTearDown(tester.platformDispatcher.clearTextScaleFactorTestValue);
  await tester.pumpAndSettle();
}

void main() {
  for (final language in ['en', 'ru']) {
    for (final route in routes) {
      testWidgets('A11Y-$language $route has no overflow at 1.5x text', (tester) async {
        await pumpScaled(tester, route, language);
        expect(tester.takeException(), isNull);
      });
    }
  }

  for (final route in routes) {
    testWidgets('A11Y $route meets tap target and label guidelines', (tester) async {
      final handle = tester.ensureSemantics();
      try {
        await pumpApp(tester, api: filledApi(), initialLocation: route);
        await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
        await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
        if (!kIsWeb) {
          await expectLater(tester, meetsGuideline(textContrastGuideline));
        }
      } finally {
        handle.dispose();
      }
    });
  }

  testWidgets('A11Y dark theme keeps contrast', (tester) async {
    final handle = tester.ensureSemantics();
    try {
      await pumpApp(tester, api: filledApi(), initialLocation: '/result/r1', prefs: {'theme': 'dark'});
      expect(Theme.of(tester.element(find.byType(Scaffold).last)).brightness, Brightness.dark);
      if (!kIsWeb) {
        await expectLater(tester, meetsGuideline(textContrastGuideline));
      }
    } finally {
      handle.dispose();
    }
  });
}
