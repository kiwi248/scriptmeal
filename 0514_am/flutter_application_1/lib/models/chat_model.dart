// ── ChatRequest → POST /api/chat body ──────────────────────────────
class ChatRequest {
  final String message;
  final String mode;
  final String sessionId;

  const ChatRequest({
    required this.message,
    required this.mode,
    required this.sessionId,
  });

  Map<String, dynamic> toJson() => {
        'message': message,
        'mode': mode,
        'session_id': sessionId,
      };
}

// ── RetrievedDoc (debug_info 안의 문서) ────────────────────────────
class RetrievedDoc {
  final String recipeName;
  final String excerpt;
  final double? score;

  const RetrievedDoc({
    required this.recipeName,
    required this.excerpt,
    this.score,
  });

  factory RetrievedDoc.fromJson(Map<String, dynamic> json) => RetrievedDoc(
        recipeName: json['recipe_name'] as String? ?? '',
        excerpt: json['excerpt'] as String? ?? '',
        score: (json['score'] as num?)?.toDouble(),
      );
}

// ── IntermediateStep (에이전트 실행 단계) ──────────────────────────
class IntermediateStep {
  final String tool;
  final dynamic toolInput;
  final String toolOutput;

  const IntermediateStep({
    required this.tool,
    required this.toolInput,
    required this.toolOutput,
  });

  factory IntermediateStep.fromJson(Map<String, dynamic> json) =>
      IntermediateStep(
        tool: json['tool'] as String? ?? '',
        toolInput: json['tool_input'],
        toolOutput: json['tool_output'] as String? ?? '',
      );
}

// ── DebugInfo ──────────────────────────────────────────────────────
class DebugInfo {
  final String? queryUsed;
  final List<RetrievedDoc> retrievedDocs;
  final String? contextExcerpt;
  final List<IntermediateStep> intermediateSteps;

  const DebugInfo({
    this.queryUsed,
    this.retrievedDocs = const [],
    this.contextExcerpt,
    this.intermediateSteps = const [],
  });

  factory DebugInfo.fromJson(Map<String, dynamic> json) => DebugInfo(
        queryUsed: json['query_used'] as String?,
        retrievedDocs: (json['retrieved_docs'] as List<dynamic>? ?? [])
            .map((e) => RetrievedDoc.fromJson(e as Map<String, dynamic>))
            .toList(),
        contextExcerpt: json['context_excerpt'] as String?,
        intermediateSteps:
            (json['intermediate_steps'] as List<dynamic>? ?? [])
                .map((e) =>
                    IntermediateStep.fromJson(e as Map<String, dynamic>))
                .toList(),
      );
}

// ── ChatResponse ← POST /api/chat 응답 ────────────────────────────
class ChatResponse {
  final String answer;
  final String? toolUsed;
  final List<String> sources;
  final DebugInfo? debugInfo;

  const ChatResponse({
    required this.answer,
    this.toolUsed,
    this.sources = const [],
    this.debugInfo,
  });

  factory ChatResponse.fromJson(Map<String, dynamic> json) => ChatResponse(
        answer: json['answer'] as String? ?? '',
        toolUsed: json['tool_used'] as String?,
        sources: (json['sources'] as List<dynamic>? ?? [])
            .map((e) => e.toString())
            .toList(),
        debugInfo: json['debug_info'] != null
            ? DebugInfo.fromJson(json['debug_info'] as Map<String, dynamic>)
            : null,
      );
}

// ── DBStatusResponse ← GET /api/recipes/status 응답 ───────────────
class DbStatusResponse {
  final String chromaDir;
  final int collectionCount;
  final int lastIndex;
  final int totalRecipes;
  final int targetRecipes;
  final bool isReady;

  const DbStatusResponse({
    required this.chromaDir,
    required this.collectionCount,
    required this.lastIndex,
    required this.totalRecipes,
    required this.targetRecipes,
    required this.isReady,
  });

  factory DbStatusResponse.fromJson(Map<String, dynamic> json) =>
      DbStatusResponse(
        chromaDir: json['chroma_dir'] as String? ?? '',
        collectionCount: json['collection_count'] as int? ?? 0,
        lastIndex: json['last_index'] as int? ?? 0,
        totalRecipes: json['total_recipes'] as int? ?? 0,
        targetRecipes: json['target_recipes'] as int? ?? 0,
        isReady: json['is_ready'] as bool? ?? false,
      );
}

// ── UI용 메시지 모델 ───────────────────────────────────────────────
enum MessageRole { user, bot }

class ChatMessage {
  final MessageRole role;
  final String text;
  final ChatResponse? response; // bot 메시지일 때 전체 응답 보관
  final DateTime timestamp;

  ChatMessage({
    required this.role,
    required this.text,
    this.response,
  }) : timestamp = DateTime.now();
}
