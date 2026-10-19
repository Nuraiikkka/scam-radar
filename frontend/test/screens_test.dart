import '../integration_test/screens/accessibility_test.dart' as accessibility;
import '../integration_test/screens/auth_flow_regression_test.dart' as auth_flow;
import '../integration_test/screens/history_stats_test.dart' as history_stats;
import '../integration_test/screens/home_test.dart' as home;
import '../integration_test/screens/onboarding_nav_test.dart' as onboarding_nav;
import '../integration_test/screens/progress_result_test.dart' as progress_result;
import '../integration_test/screens/settings_auth_test.dart' as settings_auth;

void main() {
  onboarding_nav.main();
  home.main();
  progress_result.main();
  history_stats.main();
  settings_auth.main();
  auth_flow.main();
  accessibility.main();
}
