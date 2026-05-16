import 'package:flutter/material.dart';
import '../models/chat_model.dart';
import 'debug_panel.dart';

class ChatBubble extends StatelessWidget {
  final MessageRole role;
  final String text;
  final ChatResponse? response;

  const ChatBubble._({
    required this.role,
    required this.text,
    this.response,
  });

  factory ChatBubble.user({required String text}) =>
      ChatBubble._(role: MessageRole.user, text: text);

  factory ChatBubble.bot({required String text, ChatResponse? response}) =>
      ChatBubble._(role: MessageRole.bot, text: text, response: response);

  static const Color _accent = Color(0xFFE94560);
  static const Color _border = Color(0xFFE0E0E0);
  static const Color _textMuted = Color(0xFF888888);

  @override
  Widget build(BuildContext context) {
    final isUser = role == MessageRole.user;

    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.72,
        ),
        child: isUser ? _UserBubble(text: text) : _BotBubble(response: response, text: text),
      ),
    );
  }
}

// ── 사용자 버블 ────────────────────────────────────────────────────
class _UserBubble extends StatelessWidget {
  final String text;
  const _UserBubble({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        color: Color(0xFFE94560),
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(12),
          topRight: Radius.circular(12),
          bottomLeft: Radius.circular(12),
          bottomRight: Radius.circular(3),
        ),
      ),
      child: Text(
        text,
        style: const TextStyle(
            color: Colors.white, fontSize: 14, height: 1.65),
      ),
    );
  }
}

// ── 봇 버블 ────────────────────────────────────────────────────────
class _BotBubble extends StatefulWidget {
  final String text;
  final ChatResponse? response;
  const _BotBubble({required this.text, this.response});

  @override
  State<_BotBubble> createState() => _BotBubbleState();
}

class _BotBubbleState extends State<_BotBubble> {
  bool _debugOpen = false;

  static const Color _accent = Color(0xFFE94560);
  static const Color _border = Color(0xFFE0E0E0);
  static const Color _textMuted = Color(0xFF888888);

  @override
  Widget build(BuildContext context) {
    final res = widget.response;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 메인 버블
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(color: _border),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(12),
              topRight: Radius.circular(12),
              bottomRight: Radius.circular(12),
              bottomLeft: Radius.circular(3),
            ),
            boxShadow: [
              BoxShadow(
                  color: Colors.black.withOpacity(0.06),
                  blurRadius: 8,
                  offset: const Offset(0, 2))
            ],
          ),
          child: Text(widget.text,
              style: const TextStyle(fontSize: 14, height: 1.65)),
        ),

        // 메타 정보 (툴, 소스 배지)
        if (res != null) ...[
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 4,
            children: [
              if (res.toolUsed != null)
                _Badge(label: '🔧 ${res.toolUsed!}'),
              for (final src in res.sources)
                _Badge(label: '📄 $src'),
              if (res.debugInfo != null)
                GestureDetector(
                  onTap: () => setState(() => _debugOpen = !_debugOpen),
                  child: Text(
                    _debugOpen ? '🔍 디버그 닫기' : '🔍 디버그 정보 보기',
                    style: const TextStyle(
                      fontSize: 11,
                      color: _textMuted,
                      decoration: TextDecoration.underline,
                    ),
                  ),
                ),
            ],
          ),

          // 디버그 패널
          if (_debugOpen && res.debugInfo != null)
            DebugPanel(info: res.debugInfo!),
        ],
      ],
    );
  }
}

// ── 배지 ──────────────────────────────────────────────────────────
class _Badge extends StatelessWidget {
  final String label;
  const _Badge({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF0F3),
        border: Border.all(color: const Color(0xFFF5C0CB)),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(label,
          style:
              const TextStyle(fontSize: 11, color: Color(0xFFE94560))),
    );
  }
}
