import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../models/analysis.dart';
import '../models/analysis_summary.dart';
import '../models/auth.dart';
import '../models/feedback.dart';
import '../models/stats.dart';
import 'api_exception.dart';

class HistoryQuery {
  const HistoryQuery({this.page = 1, this.pageSize = 20, this.category, this.search});

  final int page;
  final int pageSize;
  final String? category;
  final String? search;

  Map<String, dynamic> toParams() {
    final params = <String, dynamic>{'page': page, 'page_size': pageSize};
    if (category != null) {
      params['category'] = category;
    }
    if (search != null && search!.trim().isNotEmpty) {
      params['q'] = search!.trim();
    }
    return params;
  }
}

class ScamRadarApi {
  ScamRadarApi(this.dio);

  final Dio dio;

  Future<T> call<T>(Future<T> Function() request) async {
    try {
      return await request();
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  Future<AnalyzeCreated> analyzeUrl(String url) {
    return call(() async {
      final response = await dio.post<Map<String, dynamic>>('/api/v1/analyze', data: {'url': url});
      return AnalyzeCreated.fromJson(response.data!);
    });
  }

  Future<AnalyzeCreated> analyzeFile({required String fileName, Uint8List? bytes, String? path}) {
    return call(() async {
      MultipartFile file;
      if (bytes != null) {
        file = MultipartFile.fromBytes(bytes, filename: fileName, contentType: DioMediaType('video', 'mp4'));
      } else {
        file = await MultipartFile.fromFile(path!, filename: fileName, contentType: DioMediaType('video', 'mp4'));
      }
      final form = FormData.fromMap({'file': file});
      final response = await dio.post<Map<String, dynamic>>('/api/v1/analyze', data: form);
      return AnalyzeCreated.fromJson(response.data!);
    });
  }

  Future<Analysis> getAnalysis(String id) {
    return call(() async {
      final response = await dio.get<Map<String, dynamic>>('/api/v1/analyses/$id');
      return Analysis.fromJson(response.data!);
    });
  }

  Future<AnalysisPage> listAnalyses(HistoryQuery query) {
    return call(() async {
      final response = await dio.get<Map<String, dynamic>>('/api/v1/analyses', queryParameters: query.toParams());
      return AnalysisPage.fromJson(response.data!);
    });
  }

  Future<void> deleteAnalysis(String id) {
    return call(() async {
      await dio.delete<void>('/api/v1/analyses/$id');
    });
  }

  Future<int> deleteAllAnalyses() {
    return call(() async {
      final response = await dio.delete<Map<String, dynamic>>('/api/v1/analyses');
      return response.data!['deleted'] as int;
    });
  }

  Future<AnalysisFeedback> sendFeedback(String id, FeedbackRequest request) {
    return call(() async {
      final response = await dio.post<Map<String, dynamic>>('/api/v1/analyses/$id/feedback', data: request.toJson());
      return AnalysisFeedback.fromJson(response.data!);
    });
  }

  Future<Stats> getStats({String scope = 'mine'}) {
    return call(() async {
      final response = await dio.get<Map<String, dynamic>>('/api/v1/stats', queryParameters: {'scope': scope});
      return Stats.fromJson(response.data!);
    });
  }

  Future<HealthStatus> health() {
    return call(() async {
      final response = await dio.get<Map<String, dynamic>>(
        '/api/v1/health',
        options: Options(validateStatus: (status) => status != null && status < 600),
      );
      return HealthStatus.fromJson(response.data!);
    });
  }

  Future<List<CategoryInfo>> categories() {
    return call(() async {
      final response = await dio.get<List<dynamic>>('/api/v1/categories');
      final result = <CategoryInfo>[];
      for (final item in response.data!) {
        result.add(CategoryInfo.fromJson(item as Map<String, dynamic>));
      }
      return result;
    });
  }

  Future<TokenPair> login(String email, String password) {
    return call(() async {
      final response = await dio.post<Map<String, dynamic>>(
        '/api/v1/auth/login',
        data: {'email': email, 'password': password},
        options: Options(extra: {'skipAuth': true}),
      );
      return TokenPair.fromJson(response.data!);
    });
  }

  Future<TokenPair> register(String email, String password) {
    return call(() async {
      final response = await dio.post<Map<String, dynamic>>(
        '/api/v1/auth/register',
        data: {'email': email, 'password': password},
        options: Options(extra: {'skipAuth': true}),
      );
      return TokenPair.fromJson(response.data!);
    });
  }

  Future<UserProfile> me() {
    return call(() async {
      final response = await dio.get<Map<String, dynamic>>('/api/v1/auth/me');
      return UserProfile.fromJson(response.data!);
    });
  }
}
