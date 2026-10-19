import 'package:dio/dio.dart';

import '../storage/local_store.dart';

class AuthInterceptor extends QueuedInterceptor {
  AuthInterceptor({required this.store, required this.dio, required this.onSessionExpired});

  final LocalStore store;
  final Dio dio;
  final void Function() onSessionExpired;

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    options.headers['X-Client-Id'] = store.clientId();
    final token = store.accessToken;
    final skipAuth = options.extra['skipAuth'] == true;
    if (token != null && !skipAuth) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  bool isExpiredTokenError(DioException error) {
    final response = error.response;
    if (response == null || response.statusCode != 401) {
      return false;
    }
    if (error.requestOptions.extra['skipAuth'] == true) {
      return false;
    }
    final data = response.data;
    if (data is! Map<String, dynamic>) {
      return false;
    }
    final body = data['error'];
    if (body is! Map<String, dynamic>) {
      return false;
    }
    final code = body['code'];
    return code == 'token_expired' || code == 'invalid_token';
  }

  Dio makeClientWithoutInterceptors() {
    final client = Dio(dio.options.copyWith());
    client.httpClientAdapter = dio.httpClientAdapter;
    return client;
  }

  Future<String?> getNewAccessToken(Dio client) async {
    final refreshToken = store.refreshToken;
    if (refreshToken == null) {
      return null;
    }
    try {
      final response = await client.post<Map<String, dynamic>>(
        '/api/v1/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final body = response.data!;
      final accessToken = body['access_token'] as String;
      final newRefreshToken = body['refresh_token'] as String;
      await store.saveTokens(accessToken, newRefreshToken);
      return accessToken;
    } on DioException {
      return null;
    }
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    if (!isExpiredTokenError(err)) {
      handler.next(err);
      return;
    }

    final client = makeClientWithoutInterceptors();
    final newToken = await getNewAccessToken(client);
    if (newToken == null) {
      await store.clearSession();
      onSessionExpired();
      handler.next(err);
      return;
    }

    final request = err.requestOptions;
    request.headers['Authorization'] = 'Bearer $newToken';
    try {
      final response = await client.fetch<dynamic>(request);
      handler.resolve(response);
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }
}

Dio createDio({required String baseUrl, required LocalStore store, required void Function() onSessionExpired}) {
  final options = BaseOptions(
    baseUrl: baseUrl,
    connectTimeout: const Duration(seconds: 10),
    receiveTimeout: const Duration(seconds: 30),
    sendTimeout: const Duration(minutes: 3),
    responseType: ResponseType.json,
    headers: {'Accept': 'application/json'},
  );
  final dio = Dio(options);
  dio.interceptors.add(AuthInterceptor(store: store, dio: dio, onSessionExpired: onSessionExpired));
  return dio;
}
