import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:scam_radar/data/storage/local_store.dart';

import '../helpers/fake_api.dart';
import '../helpers/test_app.dart';

const Map<String, Object> loggedIn = {
  'access_token': 'access-user@example.com',
  'refresh_token': 'refresh-user@example.com',
  'user_email': 'user@example.com',
};

void main() {
  testWidgets('SE-01 language switch changes the whole UI', (tester) async {
    final harness = await pumpApp(tester, initialLocation: '/settings');
    expect(find.text('Settings'), findsWidgets);
    await tapKey(tester, 'language-ru');
    expect(find.text('Настройки'), findsWidgets);
    expect(find.text('История'), findsWidgets);
    expect(harness.store.language, 'ru');
    await tapKey(tester, 'language-en');
    expect(find.text('Settings'), findsWidgets);
  });

  testWidgets('SE-02 theme switch', (tester) async {
    final harness = await pumpApp(tester, initialLocation: '/settings');
    await tapKey(tester, 'theme-dark');
    expect(Theme.of(tester.element(find.byKey(const Key('settings-list')))).brightness, Brightness.dark);
    await tapKey(tester, 'theme-light');
    expect(Theme.of(tester.element(find.byKey(const Key('settings-list')))).brightness, Brightness.light);
    await tapKey(tester, 'theme-system');
    expect(harness.store.theme, 'system');
  });

  testWidgets('SE-03 login button opens login', (tester) async {
    await pumpApp(tester, initialLocation: '/settings');
    await tapKey(tester, 'settings-login');
    expect(currentPath(tester), '/login');
  });

  testWidgets('SE-04 logout', (tester) async {
    final harness = await pumpApp(tester, initialLocation: '/settings', prefs: loggedIn);
    expect(find.text('Logged in as user@example.com'), findsOneWidget);
    await tapKey(tester, 'settings-logout');
    expect(find.byKey(const Key('logged-out')), findsOneWidget);
    expect(find.byKey(const Key('settings-login')), findsOneWidget);
    expect(harness.store.accessToken, isNull);
  });

  testWidgets('SE-05 clear history can be cancelled', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'x1'));
    await pumpApp(tester, api: api, initialLocation: '/settings');
    await tapKey(tester, 'settings-clear-history');
    expect(find.byKey(const Key('clear-history-dialog')), findsOneWidget);
    await tapKey(tester, 'clear-history-cancel');
    expect(api.analyses.length, 1);
  });

  testWidgets('SE-06 clear history deletes everything', (tester) async {
    final api = FakeApi();
    api.add(makeAnalysis(id: 'x1'));
    api.add(makeAnalysis(id: 'x2'));
    await pumpApp(tester, api: api, initialLocation: '/settings');
    await tapKey(tester, 'settings-clear-history');
    await tapKey(tester, 'clear-history-confirm');
    expect(api.analyses, isEmpty);
    expect(find.text('Deleted 2 checks'), findsOneWidget);
  });

  testWidgets('SE-07 invalid server url is rejected', (tester) async {
    await pumpApp(tester, initialLocation: '/settings');
    await revealKey(tester, 'settings-server-field');
    await tester.enterText(find.byKey(const Key('settings-server-field')), 'not a url');
    await tapKey(tester, 'settings-server-save');
    expect(find.text('Enter a full address starting with http:// or https://'), findsOneWidget);
  });

  testWidgets('SE-08 valid server url is saved', (tester) async {
    final harness = await pumpApp(tester, initialLocation: '/settings');
    await revealKey(tester, 'settings-server-field');
    await tester.enterText(find.byKey(const Key('settings-server-field')), 'http://192.168.1.10:8000/');
    await tapKey(tester, 'settings-server-save');
    expect(find.byKey(const Key('server-saved')), findsOneWidget);
    expect(harness.store.serverUrl, 'http://192.168.1.10:8000');
  });

  testWidgets('SE-09 reset server url', (tester) async {
    final harness = await pumpApp(tester, initialLocation: '/settings', prefs: {LocalStore.serverUrlKey: 'http://x:1'});
    await tapKey(tester, 'settings-server-reset');
    expect(harness.store.serverUrl, isNull);
    expect(find.text('http://x:1'), findsNothing);
  });

  testWidgets('SE-10 show intro again', (tester) async {
    await pumpApp(tester, initialLocation: '/settings');
    await tapKey(tester, 'settings-show-intro');
    expect(currentPath(tester), '/onboarding');
  });

  testWidgets('SE-11 version is shown', (tester) async {
    await pumpApp(tester, initialLocation: '/settings');
    await revealKey(tester, 'settings-version');
    expect(find.text('Version 1.0.0'), findsOneWidget);
  });

  testWidgets('AU-01 login form validation', (tester) async {
    final harness = await pumpApp(tester, initialLocation: '/login');
    await tapKey(tester, 'auth-submit');
    expect(find.text('Enter a valid email'), findsOneWidget);
    expect(find.text('Enter your password'), findsOneWidget);
    await tester.enterText(find.byKey(const Key('auth-email')), 'wrong-email');
    await tapKey(tester, 'auth-submit');
    expect(find.text('Enter a valid email'), findsOneWidget);
    expect(harness.api.calls, isNot(contains('login')));
  });

  testWidgets('AU-02 successful login goes back', (tester) async {
    final harness = await pumpApp(tester, initialLocation: '/settings');
    await tapKey(tester, 'settings-login');
    await tester.enterText(find.byKey(const Key('auth-email')), 'user@example.com');
    await tester.enterText(find.byKey(const Key('auth-password')), 'password-123');
    await tapKey(tester, 'auth-submit');
    expect(find.byKey(const Key('logged-in')), findsOneWidget);
    expect(currentPath(tester), '/settings');
    expect(find.text('Logged in as user@example.com'), findsOneWidget);
    expect(harness.store.accessToken, 'access-user@example.com');
  });

  testWidgets('AU-03 wrong password', (tester) async {
    await pumpApp(tester, initialLocation: '/login');
    await tester.enterText(find.byKey(const Key('auth-email')), 'user@example.com');
    await tester.enterText(find.byKey(const Key('auth-password')), 'bad-password');
    await tapKey(tester, 'auth-submit');
    expect(find.text('Wrong email or password.'), findsOneWidget);
  });

  testWidgets('AU-04 password visibility toggle', (tester) async {
    await pumpApp(tester, initialLocation: '/login');
    EditableText field() => tester.widget<EditableText>(
      find.descendant(of: find.byKey(const Key('auth-password')), matching: find.byType(EditableText)),
    );
    expect(field().obscureText, isTrue);
    await tapKey(tester, 'auth-toggle-password');
    expect(field().obscureText, isFalse);
  });

  testWidgets('AU-05 and AU-06 switch between login and register', (tester) async {
    await pumpApp(tester, initialLocation: '/login');
    await tapKey(tester, 'auth-switch');
    expect(find.text('Create an account'), findsOneWidget);
    expect(find.text('Create account'), findsOneWidget);
    await tapKey(tester, 'auth-switch');
    expect(find.text('Log in'), findsWidgets);
    expect(find.text('Create an account'), findsNothing);
  });

  testWidgets('AU-07 register needs 8 characters', (tester) async {
    await pumpApp(tester, initialLocation: '/register');
    await tester.enterText(find.byKey(const Key('auth-email')), 'new@example.com');
    await tester.enterText(find.byKey(const Key('auth-password')), 'short');
    await tapKey(tester, 'auth-submit');
    expect(find.text('At least 8 characters'), findsOneWidget);
  });

  testWidgets('AU-08 register with a taken email', (tester) async {
    await pumpApp(tester, initialLocation: '/register');
    await tester.enterText(find.byKey(const Key('auth-email')), 'user@example.com');
    await tester.enterText(find.byKey(const Key('auth-password')), 'password-123');
    await tapKey(tester, 'auth-submit');
    expect(find.text('An account with this email already exists.'), findsOneWidget);
  });

  testWidgets('AU-09 register logs in', (tester) async {
    final harness = await pumpApp(tester, initialLocation: '/register');
    await tester.enterText(find.byKey(const Key('auth-email')), 'new@example.com');
    await tester.enterText(find.byKey(const Key('auth-password')), 'password-123');
    await tapKey(tester, 'auth-submit');
    expect(find.byKey(const Key('logged-in')), findsOneWidget);
    expect(harness.store.userEmail, 'new@example.com');
    expect(currentPath(tester), '/home');
  });

  testWidgets('AU-10 continue without account and back arrow', (tester) async {
    await pumpApp(tester, initialLocation: '/home');
    await tapKey(tester, 'home-login');
    await tapKey(tester, 'auth-skip');
    expect(currentPath(tester), '/home');
    await tapKey(tester, 'home-login');
    await tapKey(tester, 'auth-back');
    expect(currentPath(tester), '/home');
  });
}
