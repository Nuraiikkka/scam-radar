import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http_mock_adapter/http_mock_adapter.dart';
import 'package:scam_radar/data/api/api_client.dart';
import 'package:scam_radar/data/api/api_exception.dart';
import 'package:scam_radar/data/api/scam_radar_api.dart';
import 'package:scam_radar/data/storage/local_store.dart';
import 'package:shared_preferences/shared_preferences.dart';

Map<String, dynamic> errorBody(String code) {
  return {
    'error': {'code': code, 'message': code, 'request_id': 'r1'},
  };
}

Future<LocalStore> makeStore(Map<String, Object> values) async {
  SharedPreferences.setMockInitialValues(values);
  return LocalStore(await SharedPreferences.getInstance());
}

void main() {
  test('adds client id and bearer token', () async {
    final store = await makeStore({'client_id': 'client-123', 'access_token': 'token-a'});
    final dio = createDio(baseUrl: 'http://api', store: store, onSessionExpired: () {});
    final adapter = DioAdapter(dio: dio);
    adapter.onGet(
      '/api/v1/stats',
      (server) => server.reply(200, {'ok': true}),
      headers: {'X-Client-Id': 'client-123', 'Authorization': 'Bearer token-a'},
      queryParameters: {'scope': 'mine'},
    );
    final response = await dio.get<Map<String, dynamic>>('/api/v1/stats', queryParameters: {'scope': 'mine'});
    expect(response.data!['ok'], isTrue);
  });

  test('NAV-08 expired token is refreshed and the request retried', () async {
    final store = await makeStore({'client_id': 'client-123', 'access_token': 'old', 'refresh_token': 'refresh-1'});
    final dio = createDio(baseUrl: 'http://api', store: store, onSessionExpired: () {});
    final adapter = DioAdapter(dio: dio);
    adapter.onGet(
      '/api/v1/auth/me',
      (server) => server.reply(401, errorBody('token_expired')),
      headers: {'Authorization': 'Bearer old'},
    );
    adapter.onPost(
      '/api/v1/auth/refresh',
      (server) => server.reply(200, {
        'access_token': 'new',
        'refresh_token': 'refresh-2',
        'token_type': 'bearer',
        'expires_in': 1800,
      }),
      data: {'refresh_token': 'refresh-1'},
    );
    adapter.onGet(
      '/api/v1/auth/me',
      (server) => server.reply(200, {
        'id': 1,
        'email': 'a@example.com',
        'is_admin': false,
        'created_at': '2026-01-01T00:00:00Z',
      }),
      headers: {'Authorization': 'Bearer new'},
    );
    final profile = await ScamRadarApi(dio).me();
    expect(profile.email, 'a@example.com');
    expect(store.accessToken, 'new');
    expect(store.refreshToken, 'refresh-2');
  });

  test('NAV-08 failed refresh logs out and reports session expiry', () async {
    final store = await makeStore({'access_token': 'old', 'refresh_token': 'bad', 'user_email': 'a@example.com'});
    var expired = false;
    final dio = createDio(baseUrl: 'http://api', store: store, onSessionExpired: () => expired = true);
    final adapter = DioAdapter(dio: dio);
    adapter.onGet('/api/v1/auth/me', (server) => server.reply(401, errorBody('token_expired')));
    adapter.onPost('/api/v1/auth/refresh', (server) => server.reply(401, errorBody('invalid_token')));
    await expectLater(ScamRadarApi(dio).me(), throwsA(isA<ApiException>()));
    expect(expired, isTrue);
    expect(store.accessToken, isNull);
    expect(store.userEmail, isNull);
  });

  test('NAV-08 failure after a successful refresh is reported, not hung', () async {
    final store = await makeStore({'access_token': 'old', 'refresh_token': 'refresh-1'});
    final dio = createDio(baseUrl: 'http://api', store: store, onSessionExpired: () {});
    final adapter = DioAdapter(dio: dio);
    adapter.onGet(
      '/api/v1/stats',
      (server) => server.reply(401, errorBody('token_expired')),
      headers: {'Authorization': 'Bearer old'},
      queryParameters: {'scope': 'mine'},
    );
    adapter.onPost(
      '/api/v1/auth/refresh',
      (server) => server.reply(200, {
        'access_token': 'new',
        'refresh_token': 'refresh-2',
        'token_type': 'bearer',
        'expires_in': 1800,
      }),
      data: {'refresh_token': 'refresh-1'},
    );
    adapter.onGet(
      '/api/v1/stats',
      (server) => server.reply(500, errorBody('internal_error')),
      headers: {'Authorization': 'Bearer new'},
      queryParameters: {'scope': 'mine'},
    );
    try {
      await ScamRadarApi(dio).getStats();
      fail('expected an error');
    } on ApiException catch (error) {
      expect(error.code, 'internal_error');
    }
    expect(store.accessToken, 'new');
  });

  test('server error body becomes ApiException with code', () async {
    final store = await makeStore({});
    final dio = createDio(baseUrl: 'http://api', store: store, onSessionExpired: () {});
    final adapter = DioAdapter(dio: dio);
    adapter.onPost(
      '/api/v1/analyze',
      (server) => server.reply(422, errorBody('invalid_url')),
      data: {'url': 'https://x.com/a'},
    );
    try {
      await ScamRadarApi(dio).analyzeUrl('https://x.com/a');
      fail('expected an error');
    } on ApiException catch (error) {
      expect(error.code, 'invalid_url');
      expect(error.statusCode, 422);
    }
  });

  test('connection problems become offline errors', () {
    final error = DioException(
      requestOptions: RequestOptions(path: '/x'),
      type: DioExceptionType.connectionError,
    );
    expect(ApiException.fromDio(error).code, 'offline');
    final timeout = DioException(
      requestOptions: RequestOptions(path: '/x'),
      type: DioExceptionType.receiveTimeout,
    );
    expect(ApiException.fromDio(timeout).code, 'timeout');
  });

  test('history query only sends filled filters', () {
    expect(const HistoryQuery().toParams(), {'page': 1, 'page_size': 20});
    expect(const HistoryQuery(page: 2, category: 'betting', search: ' cook ').toParams(), {
      'page': 2,
      'page_size': 20,
      'category': 'betting',
      'q': 'cook',
    });
  });
}
