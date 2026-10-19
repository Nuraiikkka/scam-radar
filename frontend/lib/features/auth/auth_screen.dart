import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../data/api/api_exception.dart';
import '../../l10n/app_localizations.dart';
import '../../state/providers.dart';
import '../../theme/tokens.dart';
import '../../widgets/labels.dart';

final RegExp emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

String? validateEmail(AppLocalizations l10n, String? value) {
  if (!emailPattern.hasMatch((value ?? '').trim())) {
    return l10n.emailInvalid;
  }
  return null;
}

String? validatePassword(AppLocalizations l10n, String? value, bool registering) {
  final text = value ?? '';
  if (text.isEmpty) {
    return l10n.passwordRequired;
  }
  if (registering && text.length < 8) {
    return l10n.passwordTooShort;
  }
  return null;
}

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key, required this.registering});

  final bool registering;

  @override
  ConsumerState<AuthScreen> createState() => AuthScreenState();
}

class AuthScreenState extends ConsumerState<AuthScreen> {
  final formKey = GlobalKey<FormState>();
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  bool registering = false;
  bool sending = false;
  bool hidePassword = true;
  String? error;

  @override
  void initState() {
    super.initState();
    registering = widget.registering;
  }

  @override
  void dispose() {
    emailController.dispose();
    passwordController.dispose();
    super.dispose();
  }

  Future<void> waitUntilClosed(ModalRoute<Object?>? route) async {
    final animation = route?.animation;
    var frames = 0;
    await WidgetsBinding.instance.endOfFrame;
    while (animation != null && animation.isAnimating && frames < 120) {
      await WidgetsBinding.instance.endOfFrame;
      frames = frames + 1;
    }
    await WidgetsBinding.instance.endOfFrame;
  }

  void switchMode() {
    formKey.currentState?.reset();
    setState(() {
      registering = !registering;
      error = null;
    });
  }

  void leave() {
    if (context.canPop()) {
      context.pop();
    } else {
      context.go('/home');
    }
  }

  Future<void> submit() async {
    if (sending || !formKey.currentState!.validate()) {
      return;
    }
    final l10n = AppLocalizations.of(context);
    setState(() {
      sending = true;
      error = null;
    });
    final email = emailController.text.trim();
    final password = passwordController.text;
    final auth = ref.read(authProvider.notifier);
    try {
      if (registering) {
        await auth.register(email, password);
      } else {
        await auth.login(email, password);
      }
      if (!mounted) {
        return;
      }
      final messenger = ScaffoldMessenger.of(context);
      final route = ModalRoute.of(context);
      leave();
      await waitUntilClosed(route);
      messenger.showSnackBar(SnackBar(key: const Key('logged-in'), content: Text(l10n.loggedIn)));
    } on ApiException catch (caught) {
      if (mounted) {
        setState(() {
          sending = false;
          error = errorMessage(l10n, caught);
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(
        title: Text(registering ? l10n.registerTitle : l10n.loginTitle),
        leading: IconButton(
          key: const Key('auth-back'),
          icon: const Icon(Icons.arrow_back),
          tooltip: MaterialLocalizations.of(context).backButtonTooltip,
          onPressed: leave,
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.xl),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Form(
                key: formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    TextFormField(
                      key: const Key('auth-email'),
                      controller: emailController,
                      keyboardType: TextInputType.emailAddress,
                      autofillHints: const [AutofillHints.email],
                      autocorrect: false,
                      decoration: InputDecoration(labelText: l10n.emailLabel, prefixIcon: const Icon(Icons.email)),
                      validator: (value) => validateEmail(l10n, value),
                    ),
                    const SizedBox(height: AppSpacing.lg),
                    TextFormField(
                      key: const Key('auth-password'),
                      controller: passwordController,
                      obscureText: hidePassword,
                      autofillHints: [registering ? AutofillHints.newPassword : AutofillHints.password],
                      decoration: InputDecoration(
                        labelText: l10n.passwordLabel,
                        prefixIcon: const Icon(Icons.lock),
                        suffixIcon: IconButton(
                          key: const Key('auth-toggle-password'),
                          tooltip: l10n.passwordLabel,
                          icon: Icon(hidePassword ? Icons.visibility : Icons.visibility_off),
                          onPressed: () => setState(() => hidePassword = !hidePassword),
                        ),
                      ),
                      validator: (value) => validatePassword(l10n, value, registering),
                      onFieldSubmitted: (_) => submit(),
                    ),
                    if (error != null)
                      Padding(
                        padding: const EdgeInsets.only(top: AppSpacing.md),
                        child: Semantics(
                          liveRegion: true,
                          child: Text(
                            error!,
                            key: const Key('auth-error'),
                            style: TextStyle(color: Theme.of(context).colorScheme.error),
                          ),
                        ),
                      ),
                    const SizedBox(height: AppSpacing.xl),
                    FilledButton(
                      key: const Key('auth-submit'),
                      onPressed: submit,
                      child: sending
                          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                          : Text(registering ? l10n.registerButton : l10n.loginButton),
                    ),
                    const SizedBox(height: AppSpacing.md),
                    TextButton(
                      key: const Key('auth-switch'),
                      onPressed: switchMode,
                      child: Text(registering ? l10n.haveAccount : l10n.noAccount),
                    ),
                    TextButton(key: const Key('auth-skip'), onPressed: leave, child: Text(l10n.continueWithoutLogin)),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
