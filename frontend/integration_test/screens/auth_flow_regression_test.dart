import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../helpers/test_app.dart';

void main() {
  testWidgets('AU-11 settings to register, log out and log in again', (tester) async {
    await pumpApp(tester, initialLocation: '/settings');
    await tapKey(tester, 'settings-login');
    await tapKey(tester, 'auth-switch');
    await tester.enterText(find.byKey(const Key('auth-email')), 'flow@example.com');
    await tester.enterText(find.byKey(const Key('auth-password')), 'password-123');
    await tapKey(tester, 'auth-submit');
    expect(currentPath(tester), '/settings');
    expect(find.text('Logged in as flow@example.com'), findsOneWidget);
    await tapKey(tester, 'settings-logout');
    await tapKey(tester, 'settings-login');
    await tester.enterText(find.byKey(const Key('auth-email')), 'flow@example.com');
    await tester.enterText(find.byKey(const Key('auth-password')), 'wrong-password');
    await tapKey(tester, 'auth-submit');
    expect(find.text('Wrong email or password.'), findsOneWidget);
    await tapKey(tester, 'auth-back');
    await tapKey(tester, 'settings-login');
    await tester.enterText(find.byKey(const Key('auth-email')), 'flow@example.com');
    await tester.enterText(find.byKey(const Key('auth-password')), 'password-123');
    await tapKey(tester, 'auth-submit');
    expect(find.text('Logged in as flow@example.com'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
