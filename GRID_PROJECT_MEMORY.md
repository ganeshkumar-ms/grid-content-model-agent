# GRID - Enterprise AI Content Model Architect & Component Graph Engine
## Project Memory & Architectural Audit (Zero-Defect Certified)

### Live Deployment Credentials
- **Role**: Agent #6 in 10-Agent Content Intelligence Platform (`CLARIA · LENS · INDEX · BRIDGE · GRID · ADAPTA · GLANCE · SORTIA · ECHO · ALLY`)
- **CloudFront Live URL**: `https://d2w2zkazeq82no.cloudfront.net`
- **CloudFront Distribution ID**: `E26WL7E30B02YC`
- **S3 Bucket**: `grid-ui-984625844016` (us-east-1, OAC Secured)
- **API Gateway Endpoint**: `https://khag22rlna.execute-api.us-east-1.amazonaws.com`
- **Lambda Function**: `grid-backend-api` (Python 3.11, Memory: 512MB, Timeout: 120s, Role: `grid-backend-lambda-role`)
- **Bedrock Foundation Model**: `us.amazon.nova-pro-v1:0` (with Converse API + Claude 3 Haiku fallback)

---

### Zero-Defect Architectural Compliance
1. **Zero Repeated Sidebar Hover Shift**: Fixed 38px height (`height: 38px; min-height: 38px; box-sizing: border-box;`), pre-reserved padding (`padding: 0 54px 0 12px;`), absolute hover actions (`position: absolute; right: 6px; top: 50%; transform: translateY(-50%);`) with opacity transition.
2. **TAXORA Standard Delete Confirmation**:
   - Exact markup: `<div className="histRow confirm"><span className="histConfirmTxt">Delete this chat?</span><button className="histBtn danger" onClick={...}>Delete</button><button className="histBtn" onClick={...}>Cancel</button></div>`
   - Exact TAXORA translucent danger button styling (`background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.35);`).
3. **Single HOME Button Header**: Clean `<button className="homeBackBtn">HOME</button>` returning to clean home view, zero duplicate controls.
4. **Clickable Inline Title Editing**: Click title text to open inline input (`titleDraft`), saves on Enter or blur with `titleLocked: true`.
5. **Smart Conversation Title Derivation**:
   - Rejects greetings ("bro", "hi", "hey", "ji", "namaste") from becoming the session title.
   - Derives titles from model name, clean uploaded filename, or meaningful prompts.
6. **Dual-Mode Backend & Slang Interceptor**:
   - MODE 1 (`type: "chat"`): Intercepts slang ("bro", "bhai", "dude"), greetings ("hi", "ji", "namaste"), and conversational queries into natural chat bubbles without triggering schema conflicts.
   - MODE 2 (`type: "model"`): Decomposes unstructured specifications, page drafts, and documents into atomic component graphs, content types, and headless schemas.
7. **Proportional Hero Typography**: Hero `h1` clamped (`font-size: clamp(28px, 4.4vw, 46px); line-height: 1.15;`), `.heroEyebrow` (11.5px), and concise subtitle (13.5px, max-width 520px).
8. **No Study Guide PDF Generated**: Explicit user instruction respected.

---

### Verification Results Summary
| Test Case | Description | Result |
|-----------|-------------|--------|
| **Test 1** | API Health Endpoint (`/api/health`) | **PASSED** (200 OK, healthy) |
| **Test 2** | Slang Interceptor (`"bro"`) | **PASSED** (Mode 1 Conversational, no schema conflict error) |
| **Test 3** | Typo Greeting (`"ji"`) | **PASSED** (Mode 1 Hindi/English conversational reply) |
| **Test 4** | Conversational Question | **PASSED** (Mode 1 Atomic vs Molecule explanation) |
| **Test 5** | Content Modeling & Schema Synthesis | **PASSED** (Mode 2: 78/100 readiness, 5 atomic components, headless schema) |
| **Test 6** | CloudFront Frontend SPA | **PASSED** (200 OK, React root serving live) |

