import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  // 에뮬레이터에서 localhost는 10.0.2.2 써야 함!
  static const String baseUrl = 'http://10.0.2.2:8000';

  static Future<String> sendMessage(String message) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat'),  // 실제 엔드포인트 확인 필요
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'message': message}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['response'];  // 응답 구조에 맞게 수정
    } else {
      throw Exception('요청 실패: ${response.statusCode}');
    }
  }
}