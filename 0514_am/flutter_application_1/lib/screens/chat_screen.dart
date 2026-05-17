import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../models/chat_model.dart';
import '../services/api_service.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/status_badge.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen>
    with SingleTickerProviderStateMixin {
  // ── 상수 ──────────────────────────────────────────────────────
  static const Color _accent = Color(0xFFE94560);
  static const Color _accentDark = Color(0xFFC73652);
  static const Color _bg = Color(0xFFF8F9FA);
  static const Color _border = Color(0xFFE0E0E0);
  static const Color _textMuted = Color(0xFF888888);

  static const List<String> _examples = [
    '파스타 레시피 알려줘',
    '최근 SNS에서 유행한 두바이 초콜릿 레시피',
    '달걀 없이 만드는 케이크',
    '30분 안에 만드는 간단한 저녁 메뉴',
    '김치찌개 레시피 알려줘',
  ];

  // ── 상태 ──────────────────────────────────────────────────────
  final _api = ApiService();
  final _scrollController = ScrollController();
  final _textController = TextEditingController();
  final _focusNode = FocusNode();

  List<ChatMessage> _messages = [];
  String _mode = 'agent';
  String _sessionId = _newSessionId();
  bool _isLoading = false;
  DbStatusResponse? _status;
  String _statusText = '확인 중...';
  bool _drawerOpen = false;

  // ── 생명주기 ──────────────────────────────────────────────────
  @override
  void initState() {
    super.initState();
    _checkStatus();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    _textController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  // ── 유틸 ──────────────────────────────────────────────────────
  static String _newSessionId() =>
      List.generate(32, (_) => math.Random().nextInt(16).toRadixString(16))
          .join();

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  // ── API 상태 확인 ─────────────────────────────────────────────
  Future<void> _checkStatus() async {
    try {
      final s = await _api.getStatus();
      setState(() {
        _status = s;
        _statusText =
            '● 서버 연결됨\n임베딩: ${s.lastIndex} / ${s.targetRecipes} 레시피\n컬렉션: ${s.collectionCount} 문서';
      });
    } catch (_) {
      setState(() => _statusText = '● 서버 연결 실패');
    }
  }

  // ── 대화 초기화 ───────────────────────────────────────────────
  void _clearChat() {
    setState(() {
      _messages = [];
      _sessionId = _newSessionId();
    });
  }

  // ── 모드 전환 ─────────────────────────────────────────────────
  void _setMode(String mode) => setState(() => _mode = mode);

  // ── 예시 질문 ─────────────────────────────────────────────────
  void _fillExample(String text) {
    _textController.text = text;
    setState(() => _drawerOpen = false);
    _focusNode.requestFocus();
  }

  // ── 메시지 전송 ───────────────────────────────────────────────
  Future<void> _sendMessage() async {
    final text = _textController.text.trim();
    if (text.isEmpty || _isLoading) return;

    _textController.clear();
    setState(() {
      _messages.add(ChatMessage(role: MessageRole.user, text: text));
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final response = await _api.sendMessage(ChatRequest(
        message: text,
        mode: _mode,
        sessionId: _sessionId,
      ));

      setState(() {
        _messages.add(ChatMessage(
          role: MessageRole.bot,
          text: response.answer,
          response: response,
        ));
      });
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(
          role: MessageRole.bot,
          text: '⚠️ 오류: ${e is ApiException ? e.message : e.toString()}',
        ));
      });
    } finally {
      setState(() => _isLoading = false);
      _scrollToBottom();
    }
  }

  // ── 빌드 ──────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bg,
      body: SafeArea(
        child: Row(
          children: [
            // 사이드바 (넓은 화면)
            if (MediaQuery.of(context).size.width > 700) _buildSidebar(),

            // 메인 영역
            Expanded(
              child: Column(
                children: [
                  _buildHeader(),
                  Expanded(child: _buildChatArea()),
                  _buildInputArea(),
                ],
              ),
            ),
          ],
        ),
      ),
      // 좁은 화면 드로어
      drawer: MediaQuery.of(context).size.width <= 700
          ? Drawer(child: _buildSidebar())
          : null,
      appBar: MediaQuery.of(context).size.width <= 700
          ? AppBar(
              backgroundColor: Colors.white,
              elevation: 0,
              title: const Text('🍳 AI 레시피 챗봇',
                  style: TextStyle(fontWeight: FontWeight.w800)),
              foregroundColor: _accent,
            )
          : null,
    );
  }

  // ── 사이드바 ──────────────────────────────────────────────────
  Widget _buildSidebar() {
    return Container(
      width: 280,
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(right: BorderSide(color: _border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // 로고
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 24, 20, 0),
            child: Text('🍳 레시피 챗봇',
                style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: _accent)),
          ),

          const _Divider(),

          // 모드 선택
          _SideSection(
            label: '응답 모드',
            child: Column(
              children: [
                _ModeButton(
                  label: '🤖 에이전트 (RAG + 웹서치)',
                  active: _mode == 'agent',
                  onTap: () => _setMode('agent'),
                ),
                const SizedBox(height: 8),
                _ModeButton(
                  label: '📚 RAG 전용 (대화 이력 유지)',
                  active: _mode == 'rag',
                  onTap: () => _setMode('rag'),
                ),
              ],
            ),
          ),

          const _Divider(),

          // 예시 질문
          _SideSection(
            label: '예시 질문',
            child: Column(
              children: _examples
                  .map((e) => _ExampleChip(
                        text: e,
                        onTap: () => _fillExample(e),
                      ))
                  .toList(),
            ),
          ),

          const _Divider(),

          // 초기화 버튼
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: OutlinedButton.icon(
              onPressed: _clearChat,
              icon: const Icon(Icons.delete_outline, size: 16),
              label: const Text('대화 초기화'),
              style: OutlinedButton.styleFrom(
                foregroundColor: _textMuted,
                side: const BorderSide(color: _border),
                minimumSize: const Size.fromHeight(40),
              ),
            ),
          ),

          const _Divider(),

          // API 상태
          _SideSection(
            label: 'API 상태',
            child: StatusBadge(
              text: _statusText,
              isConnected: _status != null,
              onRefresh: _checkStatus,
            ),
          ),

          const Spacer(),
        ],
      ),
    );
  }

  // ── 헤더 ──────────────────────────────────────────────────────
  Widget _buildHeader() {
    if (MediaQuery.of(context).size.width <= 700) return const SizedBox();
    return Container(
      padding: const EdgeInsets.fromLTRB(28, 20, 28, 16),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: _border)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('🍳 AI 레시피 챗봇',
              style:
                  TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
          const SizedBox(height: 2),
          Text(
            'Food.com 레시피 DB + 실시간 웹서치로 최고의 레시피를 찾아드립니다.',
            style: TextStyle(fontSize: 13, color: _textMuted),
          ),
        ],
      ),
    );
  }

  // ── 채팅 영역 ─────────────────────────────────────────────────
  Widget _buildChatArea() {
    if (_messages.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('🍽️', style: TextStyle(fontSize: 48)),
            const SizedBox(height: 12),
            Text('궁금한 레시피나 요리 방법을 질문해 보세요!',
                style: TextStyle(color: _textMuted, fontSize: 15)),
          ],
        ),
      );
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      itemCount: _messages.length + (_isLoading ? 1 : 0),
      itemBuilder: (context, i) {
        // 타이핑 인디케이터
        if (i == _messages.length) return const _TypingIndicator();

        final msg = _messages[i];
        if (msg.role == MessageRole.user) {
          return ChatBubble.user(text: msg.text);
        } else {
          return ChatBubble.bot(
            text: msg.text,
            response: msg.response,
          );
        }
      },
    );
  }

  // ── 입력 영역 ─────────────────────────────────────────────────
  Widget _buildInputArea() {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 16),
      decoration: const BoxDecoration(
        color: Colors.white,
        border: Border(top: BorderSide(color: _border)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Expanded(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 120),
              child: TextField(
                controller: _textController,
                focusNode: _focusNode,
                maxLines: null,
                keyboardType: TextInputType.multiline,
                textInputAction: TextInputAction.newline,
                decoration: InputDecoration(
                  hintText: '예: 파스타 레시피 알려줘 / 최근 유행하는 레시피는?',
                  hintStyle: const TextStyle(color: Color(0xFFBBBBBB)),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: _border),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: _accent),
                  ),
                  contentPadding: const EdgeInsets.symmetric(
                      horizontal: 14, vertical: 10),
                  isDense: true,
                ),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            height: 42,
            child: ElevatedButton(
              onPressed: _isLoading ? null : _sendMessage,
              style: ElevatedButton.styleFrom(
                backgroundColor: _accent,
                foregroundColor: Colors.white,
                disabledBackgroundColor: _accent.withOpacity(0.5),
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
                padding: const EdgeInsets.symmetric(horizontal: 20),
              ),
              child: _isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2))
                  : const Text('전송 ➤',
                      style: TextStyle(fontWeight: FontWeight.w700)),
            ),
          ),
        ],
      ),
    );
  }
}

// ── 작은 위젯들 ────────────────────────────────────────────────────

class _Divider extends StatelessWidget {
  const _Divider();
  @override
  Widget build(BuildContext context) =>
      const Divider(height: 32, color: Color(0xFFE0E0E0));
}

class _SideSection extends StatelessWidget {
  final String label;
  final Widget child;
  const _SideSection({required this.label, required this.child});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label.toUpperCase(),
              style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                  color: Color(0xFF888888))),
          const SizedBox(height: 8),
          child,
        ],
      ),
    );
  }
}

class _ModeButton extends StatelessWidget {
  final String label;
  final bool active;
  final VoidCallback onTap;
  const _ModeButton(
      {required this.label, required this.active, required this.onTap});

  static const Color _accent = Color(0xFFE94560);

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        padding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: active ? _accent : Colors.transparent,
          border: Border.all(
              color: active ? _accent : const Color(0xFFE0E0E0)),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Text(label,
            style: TextStyle(
              fontSize: 13,
              fontWeight: active ? FontWeight.w600 : FontWeight.w400,
              color: active ? Colors.white : const Color(0xFF1A1A1A),
            )),
      ),
    );
  }
}

class _ExampleChip extends StatelessWidget {
  final String text;
  final VoidCallback onTap;
  const _ExampleChip({required this.text, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        margin: const EdgeInsets.only(bottom: 6),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
        decoration: BoxDecoration(
          color: const Color(0xFFFFF0F3),
          border: Border.all(color: const Color(0xFFF5C0CB)),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Text(text,
            style: const TextStyle(
                fontSize: 12, color: Color(0xFFE94560))),
      ),
    );
  }
}

class _TypingIndicator extends StatefulWidget {
  const _TypingIndicator();
  @override
  State<_TypingIndicator> createState() => _TypingIndicatorState();
}

class _TypingIndicatorState extends State<_TypingIndicator>
    with TickerProviderStateMixin {
  late final List<AnimationController> _controllers;
  late final List<Animation<double>> _anims;

  @override
  void initState() {
    super.initState();
    _controllers = List.generate(
      3,
      (i) => AnimationController(
        vsync: this,
        duration: const Duration(milliseconds: 600),
      )..repeat(reverse: true, period: Duration(milliseconds: 1200 + i * 200)),
    );
    _anims = _controllers
        .map((c) => Tween<double>(begin: 0, end: -8).animate(
            CurvedAnimation(parent: c, curve: Curves.easeInOut)))
        .toList();

    for (var i = 0; i < 3; i++) {
      Future.delayed(Duration(milliseconds: i * 200),
          () => _controllers[i].repeat(reverse: true));
    }
  }

  @override
  void dispose() {
    for (final c in _controllers) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: Colors.white,
          border: Border.all(color: const Color(0xFFE0E0E0)),
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
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(
            3,
            (i) => AnimatedBuilder(
              animation: _anims[i],
              builder: (_, __) => Transform.translate(
                offset: Offset(0, _anims[i].value),
                child: Container(
                  margin: const EdgeInsets.symmetric(horizontal: 3),
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: Color(0xFF888888),
                    shape: BoxShape.circle,
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
