import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:scam_radar/data/api/api_exception.dart';
import 'package:scam_radar/data/api/scam_radar_api.dart';
import 'package:scam_radar/data/models/analysis.dart';
import 'package:scam_radar/data/models/analysis_summary.dart';
import 'package:scam_radar/data/models/auth.dart';
import 'package:scam_radar/data/models/feedback.dart';
import 'package:scam_radar/data/models/reason.dart';
import 'package:scam_radar/data/models/stats.dart';

Analysis makeAnalysis({
  String id = 'a1',
  String status = 'done',
  String stage = 'finished',
  double? risk = 0.82,
  String? category = 'investment_platform',
  String? sourceUrl = 'https://www.tiktok.com/@scam/video/1',
  String? errorCode,
  AnalysisFeedback? feedback,
  DateTime? createdAt,
}) {
  return Analysis(
    id: id,
    status: status,
    stage: stage,
    riskScore: status == 'done' ? risk : null,
    category: status == 'done' ? category : null,
    reasons: status == 'done'
        ? [
            Reason(
              source: 'speech',
              code: 'classifier_investment_platform',
              messageEn: 'In speech: sounds like an investment platform pitch',
              messageRu: 'В речи: похоже на рекламу инвестиционной платформы',
            ),
            Reason(
              source: 'qr',
              code: 'qr_code',
              messageEn: 'In a QR code: QR code leads to https://t.me/profit',
              messageRu: 'В QR-коде: QR-код ведёт на https://t.me/profit',
            ),
          ]
        : [],
    transcript: status == 'done' ? 'Платформа даёт 30% в день' : null,
    transcriptLanguage: status == 'done' ? 'ru' : null,
    ocrText: status == 'done' ? 'ДОХОД 30% В ДЕНЬ\nt.me/profit' : null,
    links: status == 'done' ? ['t.me/profit'] : [],
    phones: status == 'done' ? ['+77015551234'] : [],
    qrCodes: status == 'done' ? ['https://t.me/profit'] : [],
    sourceType: sourceUrl == null ? 'upload' : 'url',
    sourceUrl: sourceUrl,
    originalFilename: sourceUrl == null ? 'video.mp4' : null,
    modelVersion: 'v1.0.0',
    errorCode: errorCode,
    errorMessage: errorCode == null ? null : 'Server message',
    processingSeconds: status == 'done' ? 4.2 : null,
    createdAt: createdAt ?? DateTime.utc(2026, 10, 1, 12),
    finishedAt: status == 'done' || status == 'failed' ? DateTime.utc(2026, 10, 1, 12, 1) : null,
    feedback: feedback,
  );
}

AnalysisSummary summaryOf(Analysis analysis) {
  return AnalysisSummary(
    id: analysis.id,
    status: analysis.status,
    riskScore: analysis.riskScore,
    category: analysis.category,
    sourceType: analysis.sourceType,
    sourceUrl: analysis.sourceUrl,
    originalFilename: analysis.originalFilename,
    createdAt: analysis.createdAt,
  );
}

Stats makeStats({int total = 3}) {
  return Stats(
    totalAnalyses: total,
    doneAnalyses: total,
    failedAnalyses: 0,
    scamShare: total == 0 ? 0 : 0.67,
    averageProcessingSeconds: total == 0 ? null : 4.5,
    perCategory: [
      CategoryCount(category: 'investment_platform', count: total == 0 ? 0 : 2),
      CategoryCount(category: 'pyramid', count: 0),
      CategoryCount(category: 'betting', count: 0),
      CategoryCount(category: 'giveaway', count: 0),
      CategoryCount(category: 'job_offer', count: 0),
      CategoryCount(category: 'none', count: total == 0 ? 0 : 1),
    ],
    riskOverTime: total == 0
        ? []
        : [
            DailyRisk(day: DateTime.utc(2026, 9, 30), count: 1, averageRisk: 0.2),
            DailyRisk(day: DateTime.utc(2026, 10, 1), count: 2, averageRisk: 0.7),
          ],
  );
}

class FakeApi extends ScamRadarApi {
  FakeApi() : super(Dio());

  final Map<String, Analysis> analyses = {};
  final Map<String, List<Analysis>> scripted = {};
  final List<String> calls = [];
  final Map<String, ApiException> errors = {};
  bool offline = false;
  Stats stats = makeStats();
  String? lastStatsScope;
  HistoryQuery? lastQuery;
  FeedbackRequest? lastFeedback;
  String? lastUploadName;
  String? lastUrl;
  String createdId = 'new1';
  final Map<String, String> users = {'user@example.com': 'password-123'};
  int pageSize = 20;

  int callCount(String name) {
    var count = 0;
    for (final call in calls) {
      if (call == name) {
        count = count + 1;
      }
    }
    return count;
  }

  void add(Analysis analysis) {
    analyses[analysis.id] = analysis;
  }

  void check(String name) {
    calls.add(name);
    if (offline) {
      throw ApiException(code: 'offline', message: 'Cannot reach the server');
    }
    final error = errors[name];
    if (error != null) {
      throw error;
    }
  }

  @override
  Future<AnalyzeCreated> analyzeUrl(String url) async {
    check('analyzeUrl');
    lastUrl = url;
    return AnalyzeCreated(analysisId: createdId, status: 'queued');
  }

  @override
  Future<AnalyzeCreated> analyzeFile({required String fileName, Uint8List? bytes, String? path}) async {
    check('analyzeFile');
    lastUploadName = fileName;
    return AnalyzeCreated(analysisId: createdId, status: 'queued');
  }

  @override
  Future<Analysis> getAnalysis(String id) async {
    check('getAnalysis');
    final script = scripted[id];
    if (script != null && script.isNotEmpty) {
      final next = script.removeAt(0);
      analyses[id] = next;
      return next;
    }
    final found = analyses[id];
    if (found == null) {
      throw ApiException(code: 'not_found', message: 'Analysis not found', statusCode: 404);
    }
    return found;
  }

  List<Analysis> filtered(HistoryQuery query) {
    final result = <Analysis>[];
    for (final analysis in analyses.values) {
      if (query.category != null && analysis.category != query.category) {
        continue;
      }
      final search = query.search?.trim() ?? '';
      final title = analysis.sourceUrl ?? analysis.originalFilename ?? '';
      if (search.isNotEmpty && !title.contains(search)) {
        continue;
      }
      result.add(analysis);
    }
    result.sort((first, second) => second.createdAt.compareTo(first.createdAt));
    return result;
  }

  @override
  Future<AnalysisPage> listAnalyses(HistoryQuery query) async {
    check('listAnalyses');
    lastQuery = query;
    final all = filtered(query);
    final start = (query.page - 1) * pageSize;
    final items = <AnalysisSummary>[];
    for (var index = start; index < all.length && index < start + pageSize; index++) {
      items.add(summaryOf(all[index]));
    }
    return AnalysisPage(items: items, total: all.length, page: query.page, pageSize: pageSize);
  }

  @override
  Future<void> deleteAnalysis(String id) async {
    check('deleteAnalysis');
    analyses.remove(id);
  }

  @override
  Future<int> deleteAllAnalyses() async {
    check('deleteAllAnalyses');
    final count = analyses.length;
    analyses.clear();
    return count;
  }

  @override
  Future<AnalysisFeedback> sendFeedback(String id, FeedbackRequest request) async {
    check('sendFeedback');
    lastFeedback = request;
    final feedback = AnalysisFeedback(
      isCorrect: request.isCorrect,
      trueCategory: request.trueCategory,
      comment: request.comment,
      createdAt: DateTime.utc(2026, 10, 2),
    );
    final current = analyses[id]!;
    analyses[id] = makeAnalysis(
      id: current.id,
      risk: current.riskScore,
      category: current.category,
      sourceUrl: current.sourceUrl,
      feedback: feedback,
    );
    return feedback;
  }

  @override
  Future<Stats> getStats({String scope = 'mine'}) async {
    check('getStats');
    lastStatsScope = scope;
    return stats;
  }

  @override
  Future<TokenPair> login(String email, String password) async {
    check('login');
    if (users[email] != password) {
      throw ApiException(code: 'invalid_credentials', message: 'Wrong email or password', statusCode: 401);
    }
    return TokenPair(
      accessToken: 'access-$email',
      refreshToken: 'refresh-$email',
      tokenType: 'bearer',
      expiresIn: 1800,
    );
  }

  @override
  Future<TokenPair> register(String email, String password) async {
    check('register');
    if (users.containsKey(email)) {
      throw ApiException(code: 'email_taken', message: 'Taken', statusCode: 409);
    }
    users[email] = password;
    return TokenPair(
      accessToken: 'access-$email',
      refreshToken: 'refresh-$email',
      tokenType: 'bearer',
      expiresIn: 1800,
    );
  }

  @override
  Future<UserProfile> me() async {
    check('me');
    return UserProfile(id: 1, email: users.keys.last, isAdmin: false, createdAt: DateTime.utc(2026, 1, 1));
  }
}
