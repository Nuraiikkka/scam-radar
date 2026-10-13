import '../models/analysis_result.dart';

class MockAnalysisService {
  Future<AnalysisResult> analyze({String? url, String? fileName}) async {
    await Future<void>.delayed(const Duration(seconds: 2));
    return const AnalysisResult(
      id: 1,
      riskScore: 0.87,
      category: 'investment_platform',
      reasons: [
        'Guaranteed profit mentioned',
        'Suspicious contact link detected',
      ],
      transcript: 'Earn guaranteed money every day',
      ocrText: 'Join now',
    );
  }
}
