import 'package:flutter/material.dart';
import '../models/chat_model.dart';

class DebugPanel extends StatelessWidget {
  final DebugInfo info;
  const DebugPanel({super.key, required this.info});

  static const Color _accent = Color(0xFFE94560);
  static const Color _border = Color(0xFFE0E0E0);

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFF9F9F9),
        border: Border.all(color: _border),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 검색 쿼리
          if (info.queryUsed != null) ...[
            _DebugHeader('🔎 검색 쿼리'),
            _CodeBlock(info.queryUsed!),
          ],

          // 검색된 문서
          if (info.retrievedDocs.isNotEmpty) ...[
            _DebugHeader(
                '📚 ChromaDB TOP-${info.retrievedDocs.length} 검색 결과'),
            for (var i = 0; i < info.retrievedDocs.length; i++)
              _CodeBlock(
                'Rank ${i + 1}: ${info.retrievedDocs[i].recipeName}'
                '${info.retrievedDocs[i].score != null ? ' (유사도: ${info.retrievedDocs[i].score!.toStringAsFixed(4)})' : ''}\n'
                '${info.retrievedDocs[i].excerpt.length > 200 ? '${info.retrievedDocs[i].excerpt.substring(0, 200)}…' : info.retrievedDocs[i].excerpt}',
              ),
          ],

          // 컨텍스트
          if (info.contextExcerpt != null) ...[
            _DebugHeader('📝 LLM 전달 컨텍스트 (앞 500자)'),
            _CodeBlock(info.contextExcerpt!),
          ],

          // 에이전트 단계
          if (info.intermediateSteps.isNotEmpty) ...[
            _DebugHeader('⚙️ 에이전트 실행 단계'),
            for (var i = 0; i < info.intermediateSteps.length; i++)
              _CodeBlock(
                'Step ${i + 1} — 툴: ${info.intermediateSteps[i].tool}\n'
                '입력: ${_truncate(info.intermediateSteps[i].toolInput.toString(), 150)}\n'
                '출력: ${_truncate(info.intermediateSteps[i].toolOutput, 200)}…',
              ),
          ],
        ],
      ),
    );
  }

  String _truncate(String s, int max) =>
      s.length > max ? s.substring(0, max) : s;
}

class _DebugHeader extends StatelessWidget {
  final String text;
  const _DebugHeader(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4, top: 4),
      child: Text(text,
          style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: Color(0xFFE94560))),
    );
  }
}

class _CodeBlock extends StatelessWidget {
  final String text;
  const _CodeBlock(this.text);

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: const Color(0xFFF0F0F0),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(text,
          style: const TextStyle(
              fontSize: 11,
              fontFamily: 'Courier',
              height: 1.6,
              color: Color(0xFF444444))),
    );
  }
}
