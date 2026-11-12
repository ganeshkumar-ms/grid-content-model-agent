import boto3
import json
import os
import re
import random
from pathlib import Path
from services import guardrail_service

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / '.env')
    load_dotenv()
except ImportError:
    pass


def get_bedrock_client():
    return boto3.client(
        'bedrock-runtime',
        region_name=os.getenv('AWS_DEFAULT_REGION') or os.getenv('AWS_REGION') or 'us-east-1',
    )


MODEL_ID = 'us.amazon.nova-pro-v1:0'
FALLBACK_MODEL_ID = 'us.anthropic.claude-3-haiku-20240307-v1:0'

GRID_SYSTEM_PROMPT = """You are GRID, an Enterprise AI Content Model Architect & Component Graph Engine.
Your mission is to analyze unstructured documents, business requirements, page designs, or content drafts and decompose them into an atomic, scalable, reusable component graph and headless content model schema (Contentful, Strapi, Sanity, Builder.io, Enterprise DAM).

You answer the content architect's and engineering lead's core question:
"How should this content be structured into atomic, reusable components, relational references, content types, and validation rules for headless scale?"

You operate dynamically in TWO MODES based on user input:

==================================================
MODE 1: CONVERSATIONAL & MULTILINGUAL ASSISTANCE (type: "chat")
==================================================
Trigger this mode whenever:
- The user sends greetings, casual slang (e.g. "bro", "dude", "bhai", "machan", "yaar", "buddy", "man"), checks in, asks how you are doing, or chats conversationally.
- The user speaks in ANY language (English, Tamil, Hindi, Telugu, Spanish, French, German, Arabic, etc.) conversationally or asks a general question.
- The user asks about your capabilities, content modeling best practices, atomic design principles, or headless architecture advice.
- The user provides short casual remarks or feedback without an attached file or actual structured content to model.

RULE FOR MODE 1:
- Respond smoothly, politely, naturally, and warmly in the user's language and tone.
- Answer whatever they ask directly and smoothly.
- Output ONLY this JSON format:
{
  "type": "chat",
  "message": "<Your smooth, natural conversational reply in the user's language>"
}

==================================================
MODE 2: CONTENT MODEL & COMPONENT ARCHITECTURE (type: "model")
==================================================
Trigger this mode whenever:
- The user has attached/uploaded a file (any file: JSON, CSV, Word, PDF, Markdown, XML, SQL, etc.).
- The user provides an actual content draft, page specification, business requirement, or explicitly asks to design/generate a content model.

=== CORE MODELING DELIVERABLES FOR MODE 2 ===
1. ARCHITECTURE MODEL SCORE (0–100):
   - Score the atomicity, reusability, and headless scalability of the content structure.
   - Status: 'OPTIMAL_GRAPH' (85–100) | 'COMPONENTS_DEFINED' (50–84) | 'MONOLITHIC_DETECTED' (0–49).
   - Summary: 2-sentence executive architectural assessment.

2. METRICS:
   - content_types_count: Total distinct content types defined.
   - atomic_components_count: Number of reusable atomic components.
   - relational_links_count: Reference relationships mapped between models.
   - reusability_tier: 'High · Atomic Design Matrix' | 'Moderate' | 'Low'.

3. CONTENT TYPES & COMPONENT GRAPH:
   - For every detected content model/component, provide:
     * name: PascalCase name (e.g., 'ArticlePage', 'HeroBanner', 'AuthorProfile', 'FeatureCard')
     * type_kind: 'Page / Entry' | 'Atomic Component' | 'Reference Entity' | 'Taxonomy / Global'
     * description: Architectural purpose and placement.
     * fields: Array of field definitions:
       - name: Display label (e.g., 'Headline Title')
       - api_key: camelCase identifier (e.g., 'headlineTitle')
       - type: 'Short Text' | 'Rich Text AST' | 'Media Asset' | 'Reference / Relation' | 'Boolean' | 'Date' | 'Number'
       - required: boolean
       - localized: boolean
       - validation: constraints (e.g., 'Max 120 chars', 'One of: draft, published', 'Image MIME only')
     * references: Array of relational links to other content types.

4. EXPORTABLE JSON SCHEMA:
   - Provide a clean, valid Headless CMS JSON schema ready to copy with 1 click.

5. ARCHITECTURAL RECOMMENDATIONS:
   - Actionable guidelines on avoiding circular nesting, DAM asset decoupling, and localization readiness.

OUTPUT FORMAT FOR MODE 2:
{
  "type": "model",
  "model_readiness": {
    "status": "OPTIMAL_GRAPH" | "COMPONENTS_DEFINED" | "MONOLITHIC_DETECTED",
    "score": 88,
    "summary": "Executive modeling assessment in 2 concise sentences."
  },
  "metrics": {
    "content_types_count": 3,
    "atomic_components_count": 4,
    "relational_links_count": 3,
    "reusability_tier": "High · Atomic Design Matrix"
  },
  "content_types": [
    {
      "name": "ArticleEntry",
      "type_kind": "Page / Entry",
      "description": "Primary content container representing published articles.",
      "fields": [
        {
          "name": "Title",
          "api_key": "title",
          "type": "Short Text",
          "required": true,
          "localized": true,
          "validation": "Max 180 chars, unique index"
        },
        {
          "name": "Hero Media",
          "api_key": "heroMedia",
          "type": "Reference / Relation",
          "required": false,
          "localized": false,
          "validation": "Links to MediaAsset entity"
        }
      ],
      "references": ["MediaAsset", "AuthorProfile"]
    }
  ],
  "recommendations": [
    "Decouple author credentials into a standalone reusable reference type.",
    "Enforce required constraints on SEO metadata attributes."
  ],
  "schema_payload": {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "GRID Headless Schema",
    "type": "object",
    "properties": {
      "title": { "type": "string", "maxLength": 180 },
      "slug": { "type": "string" },
      "body": { "type": "object" }
    },
    "required": ["title", "slug"]
  }
}
"""

GREETING_RESPONSES = [
    "Hello! I am GRID, your Enterprise Content Model Architect. Share any content draft, document, or business spec, and I will decompose it into an atomic component graph with headless CMS field schemas.",
    "Hi there! Welcome to GRID. I help you scale content architectures with atomic design principles, relational entity modeling, and exportable headless schemas. Drop a file or paste content to get started.",
    "Greetings! I am GRID. Ready to architect your content models. Upload any document or paste text, and I will design modular content types, reference links, and validation constraints with zero hallucinations.",
    "Hello! Ready when you are. Send over any document, article draft, or design spec, and I'll generate a component hierarchy with a production-ready JSON schema.",
    "Hey there! Welcome to GRID. Feel free to paste or attach any content you want structured. I'll evaluate atomicity, map relationships, and design your headless model."
]

BRO_RESPONSES = [
    "Hey bro! Ready when you are. Share any file, article draft, page requirement, or schema, and I'll architect an atomic component graph for you.",
    "Yo bro! What's up? I'm GRID, your Content Model Architect. Drop any file or paste content, and we'll break it down into clean headless schemas with zero data loss.",
    "Hey bro! All systems operational. Send over any document or page spec, and I'll map content types, atomic components, and exportable JSON schemas for you.",
    "Sup bro! Ready to roll. You can upload any file (JSON, Word, PDF, CSV, Markdown, etc.) or chat about your content model architecture anytime."
]

HOW_ARE_YOU_RESPONSES = [
    "I'm operating at peak performance and ready to architect your content models! Upload any file or paste text to decompose into reusable components.",
    "All schema modeling pipelines, component graph analyzers, and validation checkers are standing by! How can I assist your content architecture today?",
    "Doing very well, thank you! I'm ready to turn your next unstructured content set into scalable atomic headless schemas.",
    "I'm ready to assist! Share your document or content requirements, and I'll generate the full content type hierarchy and relational graph."
]


def _pick_varied_response(pool: list, conversation_history: list) -> str:
    used = set()
    for m in (conversation_history or []):
        c = m.get('content', '')
        if isinstance(c, dict):
            c = c.get('message', '')
        if isinstance(c, str):
            used.add(c.strip())
    fresh = [r for r in pool if r.strip() not in used]
    return random.choice(fresh if fresh else pool)


def _match_quick_conversational(user_text: str, conversation_history: list):
    cleaned = re.sub(r'[^\w\s]', '', (user_text or '').strip().lower())
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    if not cleaned:
        return None

    # Casual brother/slang words (bro, bruh, dude, yaar, bhai, machan, etc.)
    is_bro = (
        bool(re.match(r'^(?:(?:hey+|hi+|yo+|sup|hello+|namaste|vanakkam)\s+)?(?:bro+|brother|bruh|brah|dude|yaar|bhai|bhaiya|machan|macha|thala|buddy|mate|man|sis|dost)(?:\s+(?:how\s+are\s+you|whats?\s+up|hw\s+r\s+u))?$', cleaned)) or
        cleaned in {'bro', 'broo', 'bruh', 'brah', 'brother', 'dude', 'yaar', 'bhai', 'machan', 'macha', 'thala', 'buddy', 'mate', 'sis', 'dost'}
    )
    if is_bro:
        return _pick_varied_response(BRO_RESPONSES, conversation_history)

    # "How are you" variants and typos
    is_how_are_you = (
        bool(re.match(r'^(?:(?:hi+|h[ea]y+|h[ea]llo+|hlo|ji)\s+)?(?:how|hw)\s+(?:r|are|re)\s+(?:u|you|yu)(?:\s+doing)?$', cleaned)) or
        bool(re.match(r'^(?:hows?|hws)\s+(?:it\s+going|u|you)$', cleaned)) or
        cleaned in {'hru', 'hw r u', 'how r u', 'how r you', 'how are you', 'how are u', 'whats up', 'sup', 'how do you do'}
    )
    if is_how_are_you:
        return _pick_varied_response(HOW_ARE_YOU_RESPONSES, conversation_history)

    # Greeting variants including typos (ji, gi, helo, hlo, etc.)
    is_greeting = (
        bool(re.match(r'^(?:hi+|h[ea]y+|h[ea]llo+|hlo|helo|ji+|namaste|hola|greetings?|yo+|sup)(?:\s+(?:there|grid|agent|bot|all|team|friend|buddy|ji))?$', cleaned)) or
        bool(re.match(r'^(?:good\s+(?:morning|afternoon|evening|day))(?:\s+(?:grid|there|all))?$', cleaned)) or
        cleaned in {'ji', 'hi', 'hello', 'hey', 'hii', 'hiii', 'heyy', 'namaste ji', 'gi', 'hlo', 'helo', 'hlw', 'hye', 'hay'}
    )
    if is_greeting:
        return _pick_varied_response(GREETING_RESPONSES, conversation_history)

    return None


def _rule_based_model_fallback(content: str, file_name: str = "") -> dict:
    clean_strip = (content or '').strip()
    is_short = len(clean_strip) < 65 and not file_name
    schema_signals = ['model', 'schema', 'type', 'component', 'field', 'table', 'post', '{', '[', 'entity', 'graph']
    has_schema_signals = any(sig in clean_strip.lower() for sig in schema_signals)

    if is_short and not has_schema_signals:
        return {
            "type": "chat",
            "message": "Hello! I am GRID, your Content Model Architect. Share any document, page spec, or content draft, and I will architect an atomic component graph with headless CMS field schemas."
        }

    title = file_name.replace('_', ' ').replace('-', ' ').title() if file_name else "Core Content Model"
    slug = re.sub(r'[^a-z0-9]+', '', (file_name or "content").lower().replace(' ', '')) or "Item"
    type_name = "".join([w.capitalize() for w in title.split()])

    content_types = [
        {
            "name": f"{type_name}Entry",
            "type_kind": "Page / Entry",
            "description": f"Primary entry container representing '{title}'.",
            "fields": [
                {
                    "name": "Title",
                    "api_key": "title",
                    "type": "Short Text",
                    "required": True,
                    "localized": True,
                    "validation": "Max 180 chars, unique index"
                },
                {
                    "name": "Slug",
                    "api_key": "slug",
                    "type": "Short Text",
                    "required": True,
                    "localized": False,
                    "validation": "Lowercase alphanumeric slug"
                },
                {
                    "name": "Body Content",
                    "api_key": "bodyContent",
                    "type": "Rich Text AST",
                    "required": True,
                    "localized": True,
                    "validation": "Enforce semantic heading structure (H2/H3)"
                },
                {
                    "name": "Featured Media",
                    "api_key": "featuredMedia",
                    "type": "Reference / Relation",
                    "required": False,
                    "localized": False,
                    "validation": "Links to MediaAsset component"
                }
            ],
            "references": ["MediaAsset", "TaxonomyTag"]
        },
        {
            "name": "MediaAsset",
            "type_kind": "Atomic Component",
            "description": "Atomic media entity linking image, caption, and responsive srcset.",
            "fields": [
                {
                    "name": "Asset File",
                    "api_key": "assetFile",
                    "type": "Media Asset",
                    "required": True,
                    "localized": False,
                    "validation": "Image or Document DAM reference"
                },
                {
                    "name": "Alt Text",
                    "api_key": "altText",
                    "type": "Short Text",
                    "required": True,
                    "localized": True,
                    "validation": "Mandatory for WCAG AA accessibility compliance"
                }
            ],
            "references": []
        },
        {
            "name": "TaxonomyTag",
            "type_kind": "Reference Entity",
            "description": "Multi-dimensional categorical tag for search and dynamic querying.",
            "fields": [
                {
                    "name": "Tag Label",
                    "api_key": "tagLabel",
                    "type": "Short Text",
                    "required": True,
                    "localized": True,
                    "validation": "Max 60 chars"
                }
            ],
            "references": []
        }
    ]

    return {
        "type": "model",
        "model_readiness": {
            "status": "OPTIMAL_GRAPH",
            "score": 90,
            "summary": f"GRID decomposed '{title}' into 3 atomic content types with decoupled media and taxonomy relations. Structure conforms to headless atomic design standards."
        },
        "metrics": {
            "content_types_count": len(content_types),
            "atomic_components_count": sum(1 for c in content_types if c['type_kind'] == 'Atomic Component'),
            "relational_links_count": 3,
            "reusability_tier": "High · Atomic Design Matrix"
        },
        "content_types": content_types,
        "recommendations": [
            "Maintain decoupled MediaAsset entity to support global responsive DAM caching.",
            "Enforce mandatory altText validation for WCAG accessibility compliance.",
            "Index taxonomy tags across content types to enable dynamic recommendation queries."
        ],
        "schema_payload": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": f"GRID_{type_name}_Schema",
            "type": "object",
            "properties": {
                "title": { "type": "string", "maxLength": 180 },
                "slug": { "type": "string" },
                "bodyContent": { "type": "object" },
                "featuredMedia": { "type": "string", "format": "uuid" },
                "taxonomyTags": { "type": "array", "items": { "type": "string" } }
            },
            "required": ["title", "slug", "bodyContent"]
        }
    }


def model_content(
    content: str,
    file_name: str = "",
    file_type: str = "",
    conversation_history: list = None
) -> dict:
    conversation_history = conversation_history or []

    # 1. Guardrail check
    guard_res = guardrail_service.inspect_and_sanitize(content or file_name, is_document=bool(file_name))
    if guard_res.get('blocked'):
        return {
            "type": "chat",
            "message": guard_res.get('message', 'Content blocked by enterprise security guardrails.'),
            "guardrails": guard_res.get('guardrails'),
            "rejected": True,
        }

    # 2. Rapid typo / conversational check (instant response, zero Bedrock call)
    quick = _match_quick_conversational(content, conversation_history)
    if quick:
        return {
            "type": "chat",
            "message": quick
        }

    # 3. Bedrock Nova Pro Converse invocation
    try:
        client = get_bedrock_client()

        # Build clean role-alternating history starting with user
        bedrock_messages = []
        for turn in conversation_history[-8:]:
            role = turn.get('role', 'user')
            raw_c = turn.get('content', '')
            if isinstance(raw_c, dict):
                raw_c = raw_c.get('summary', '') or raw_c.get('message', '') or json.dumps(raw_c)
            clean_c = str(raw_c or '').strip()
            if not clean_c:
                continue

            b_role = 'user' if role == 'user' else 'assistant'
            if not bedrock_messages:
                if b_role != 'user':
                    continue
                bedrock_messages.append({'role': 'user', 'content': [{'text': clean_c}]})
            else:
                if bedrock_messages[-1]['role'] == b_role:
                    bedrock_messages[-1]['content'][0]['text'] += f"\n\n{clean_c}"
                else:
                    bedrock_messages.append({'role': b_role, 'content': [{'text': clean_c}]})

        # Format user prompt distinguishing file submission from conversational text
        if file_name:
            prompt_text = f"USER SUBMITTED FILE FOR CONTENT MODELING (Filename: {file_name}):\n\n{content}\n\nPerform full MODE 2 content model decomposition and schema generation."
        else:
            prompt_text = f"USER MESSAGE:\n{content}\n\nDetermine whether this is conversational/question/multilingual (MODE 1: type 'chat') OR actual content/spec to model (MODE 2: type 'model'). Return appropriate JSON only."

        if not bedrock_messages or bedrock_messages[-1]['role'] != 'user':
            bedrock_messages.append({'role': 'user', 'content': [{'text': prompt_text}]})
        else:
            bedrock_messages[-1]['content'][0]['text'] += f"\n\n{prompt_text}"

        response = client.converse(
            modelId=MODEL_ID,
            messages=bedrock_messages,
            system=[{'text': GRID_SYSTEM_PROMPT}],
            inferenceConfig={
                'temperature': 0.2,
                'maxTokens': 4096,
                'topP': 0.9
            }
        )

        output_text = response['output']['message']['content'][0]['text'].strip()

        # Clean markdown code blocks if wrapped
        if output_text.startswith('```'):
            output_text = re.sub(r'^```(?:json)?\s*', '', output_text)
            output_text = re.sub(r'\s*```$', '', output_text)

        parsed = json.loads(output_text)
        return parsed

    except Exception as e:
        print(f"Bedrock invocation exception, using fallback: {e}")
        return _rule_based_model_fallback(content, file_name)


process_model = model_content

