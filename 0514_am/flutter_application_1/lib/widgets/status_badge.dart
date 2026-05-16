import 'package:flutter/material.dart';

class StatusBadge extends StatelessWidget {
  final String text;
  final bool isConnected;
  final VoidCallback onRefresh;

  const StatusBadge({
    super.key,
    required this.text,
    required this.isConnected,
    required this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    final lines = text.split('\n');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(
                color: isConnected
                    ? const Color(0xFF22C55E)
                    : const Color(0xFFEF4444),
                shape: BoxShape.circle,
              ),
            ),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                lines.first,
                style: const TextStyle(
                    fontSize: 12, color: Color(0xFF888888)),
              ),
            ),
            GestureDetector(
              onTap: onRefresh,
              child: const Icon(Icons.refresh,
                  size: 14, color: Color(0xFF888888)),
            ),
          ],
        ),
        for (final line in lines.skip(1))
          Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Text(line,
                style: const TextStyle(
                    fontSize: 11, color: Color(0xFF888888))),
          ),
      ],
    );
  }
}
