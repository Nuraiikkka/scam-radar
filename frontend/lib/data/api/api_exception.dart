import 'package:dio/dio.dart';

class ApiException implements Exception {
  ApiException({required this.code, required this.message, this.statusCode});

  final String code;
  final String message;
  final int? statusCode;

  bool get isOffline => code == 'offline';

  static ApiException fromDio(DioException error) {
    if (error.error is ApiException) {
      return error.error as ApiException;
    }
    final type = error.type;
    if (type == DioExceptionType.connectionTimeout ||
        type == DioExceptionType.sendTimeout ||
        type == DioExceptionType.receiveTimeout) {
      return ApiException(code: 'timeout', message: 'The server took too long to answer');
    }
    if (type == DioExceptionType.connectionError) {
      return ApiException(code: 'offline', message: 'Cannot reach the server');
    }
    if (type == DioExceptionType.cancel) {
      return ApiException(code: 'cancelled', message: 'Request cancelled');
    }
    final response = error.response;
    if (response == null) {
      return ApiException(code: 'offline', message: 'Cannot reach the server');
    }
    final data = response.data;
    if (data is Map<String, dynamic> && data['error'] is Map<String, dynamic>) {
      final body = data['error'] as Map<String, dynamic>;
      return ApiException(
        code: body['code'] as String? ?? 'server_error',
        message: body['message'] as String? ?? 'Server error',
        statusCode: response.statusCode,
      );
    }
    return ApiException(code: 'server_error', message: 'Server error', statusCode: response.statusCode);
  }

  @override
  String toString() => 'ApiException($code, $message)';
}
