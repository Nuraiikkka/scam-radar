import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_web_plugins/url_strategy.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'app.dart';
import 'data/storage/local_store.dart';
import 'state/providers.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  usePathUrlStrategy();
  GoRouter.optionURLReflectsImperativeAPIs = true;
  final prefs = await SharedPreferences.getInstance();
  runApp(
    ProviderScope(overrides: [localStoreProvider.overrideWithValue(LocalStore(prefs))], child: const ScamRadarApp()),
  );
}
