import 'package:flutter/material.dart';
import 'screens/chat_screen.dart';

void main() {
  runApp(const RecipeChatApp());
}

class RecipeChatApp extends StatelessWidget {
  const RecipeChatApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '🍳 AI 레시피 챗봇',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFE94560),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
        fontFamily: 'Pretendard',
      ),
      home: const ChatScreen(),
    );
  }
}
