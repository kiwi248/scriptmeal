import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/chat_model.dart';

class ApiService {
  // ── 서버 주소 (필요 시 수정) ──────────────────────────────────
  static const String _baseUrl = 'http://10.0.2.2:8000';

  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final http.Client _client = http.Client();

  // ── POST /api/chat ─────────────────────────────────────────────
  /// FastAPI chat_controller.py 의 POST /api/chat 와 연동
  Future<ChatResponse> sendMessage(ChatRequest request) async {
    final uri = Uri.parse('$_baseUrl/api/chat');

    final httpResponse = await _client
        .post(
          uri,
          headers: {'Content-Type': 'application/json; charset=utf-8'},
          body: jsonEncode(request.toJson()),
        )
        .timeout(const Duration(seconds: 60));

    if (httpResponse.statusCode == 200) {
      final decoded = jsonDecode(utf8.decode(httpResponse.bodyBytes))
          as Map<String, dynamic>;
      return ChatResponse.fromJson(decoded);
    } else {
      final err = jsonDecode(utf8.decode(httpResponse.bodyBytes));
      throw ApiException(
        statusCode: httpResponse.statusCode,
        message: err['detail']?.toString() ?? 'HTTP ${httpResponse.statusCode}',
      );
    }
  }

  // ── GET /api/recipes/status ────────────────────────────────────
  /// FastAPI recipe_controller.py 의 GET /api/recipes/status 와 연동
  Future<DbStatusResponse> getStatus() async {
    final uri = Uri.parse('$_baseUrl/api/recipes/status');

    final httpResponse = await _client
        .get(uri)
        .timeout(const Duration(seconds: 10));

    if (httpResponse.statusCode == 200) {
      final decoded = jsonDecode(utf8.decode(httpResponse.bodyBytes))
          as Map<String, dynamic>;
      return DbStatusResponse.fromJson(decoded);
    } else {
      throw ApiException(
        statusCode: httpResponse.statusCode,
        message: 'Status 확인 실패: HTTP ${httpResponse.statusCode}',
      );
    }
  }

  void dispose() => _client.close();
}

// ── 커스텀 예외 ────────────────────────────────────────────────────
class ApiException implements Exception {
  final int statusCode;
  final String message;
  const ApiException({required this.statusCode, required this.message});

  @override
  String toString() => 'ApiException($statusCode): $message';
}
