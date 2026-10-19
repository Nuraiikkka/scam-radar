import 'package:integration_test/integration_test.dart';

import 'screens/accessibility_test.dart' as accessibility;
import 'screens/auth_flow_regression_test.dart' as auth_flow;
import 'screens/history_stats_test.dart' as history_stats;
import 'screens/home_test.dart' as home;
import 'screens/onboarding_nav_test.dart' as onboarding_nav;
import 'screens/progress_result_test.dart' as progress_result;
import 'screens/settings_auth_test.dart' as settings_auth;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  onboarding_nav.main();
  home.main();
  progress_result.main();
  history_stats.main();
  settings_auth.main();
  auth_flow.main();
  accessibility.main();
}
