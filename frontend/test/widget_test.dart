import 'package:flutter_test/flutter_test.dart';
import 'package:scam_radar/main.dart';

void main() {
  testWidgets('shows the Scam Radar home screen', (tester) async {
    await tester.pumpWidget(const ScamRadarApp());

    expect(find.text('Scam Radar'), findsOneWidget);
    expect(find.text('Analyze Video'), findsOneWidget);
  });
}
