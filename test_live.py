import json
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

API_BASE = sys.argv[1] if len(sys.argv) > 1 else 'https://khag22rlna.execute-api.us-east-1.amazonaws.com'
CF_BASE = sys.argv[2] if len(sys.argv) > 2 else 'https://d2w2zkazeq82no.cloudfront.net'


def http_get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'GRID-Live-Test/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.headers, resp.read().decode('utf-8')


def http_post_form(url, form_data):
    encoded = urllib.parse.urlencode(form_data).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=encoded,
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'GRID-Live-Test/1.0'
        }
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, resp.headers, resp.read().decode('utf-8')


def test_1_health():
    print('\n[TEST 1] Checking Health Endpoint...')
    url = f'{API_BASE}/api/health'
    status, headers, body = http_get(url)
    print(f'   Status: {status}')
    print(f'   Body:   {body[:120]}')
    assert status == 200, f'Expected 200, got {status}'
    data = json.loads(body)
    assert data.get('status') in ('ok', 'healthy'), f'Status neither ok nor healthy: {data}'
    print('   >>> PASSED: Health check OK')


def test_2_slang_bro():
    print('\n[TEST 2] Testing Slang "bro" Interceptor (Mode 1 Conversational)...')
    url = f'{API_BASE}/api/model'
    status, headers, body = http_post_form(url, {'text': 'bro'})
    print(f'   Status: {status}')
    data = json.loads(body)
    print(f'   Type: {data.get("type")}')
    print(f'   Message: {data.get("message")}')
    assert status == 200, f'Expected 200, got {status}'
    assert data.get('type') == 'chat', f'Expected type "chat", got {data.get("type")}'
    assert data.get('message'), 'Expected conversational message'
    assert 'conflict' not in data.get('message', '').lower(), 'Should not treat "bro" as schema conflict'
    print('   >>> PASSED: Casual "bro" smoothly intercepted into Mode 1 chat')


def test_3_typo_greeting():
    print('\n[TEST 3] Testing Typo Greeting "ji" (Mode 1 Conversational)...')
    url = f'{API_BASE}/api/model'
    status, headers, body = http_post_form(url, {'text': 'ji'})
    print(f'   Status: {status}')
    data = json.loads(body)
    print(f'   Type: {data.get("type")}')
    print(f'   Message: {data.get("message")}')
    assert status == 200, f'Expected 200, got {status}'
    assert data.get('type') == 'chat', f'Expected type "chat", got {data.get("type")}'
    print('   >>> PASSED: Typo/greeting "ji" smoothly responded in Mode 1 chat')


def test_4_conversational_question():
    print('\n[TEST 4] Testing Conversational Question (Mode 1 Chat)...')
    url = f'{API_BASE}/api/model'
    status, headers, body = http_post_form(
        url,
        {'text': 'What is the main difference between an atom and a molecule in content modeling?'}
    )
    print(f'   Status: {status}')
    data = json.loads(body)
    print(f'   Type: {data.get("type")}')
    print(f'   Message snippet: {data.get("message", "")[:120]}...')
    assert status == 200, f'Expected 200, got {status}'
    assert data.get('type') == 'chat', f'Expected type "chat", got {data.get("type")}'
    print('   >>> PASSED: Conversational modeling query answered in Mode 1 chat')


def test_5_content_modeling():
    print('\n[TEST 5] Testing Full Content Model & Component Graph Synthesis (Mode 2)...')
    url = f'{API_BASE}/api/model'
    banking_spec = """
    Enterprise Banking Mortgages Landing Page Spec:
    Hero Section:
      - Title: "Home Loans Made Simple"
      - Subtitle: "Calculate your rates in real time"
      - Primary CTA Button: Text, URL, Variant
      - Background Hero Visual: Image / Video asset reference
    Rate Calculator Component:
      - Loan Amount Slider: Min, Max, Step, Default
      - Tenure Selection: 15, 20, 30 years
      - Dynamic Monthly Payment Display
    Mortgage Products Matrix:
      - 3 Products: Fixed-Rate, ARM 5/1, Jumbo Loan
      - Each product has: Name, APR %, Points, Min Credit Score, Disclosure Notes
    Customer Testimonials Carousel:
      - Quote, Author Name, Star Rating, Photo, Loan Type
    Global FAQ Accordion:
      - Question, Rich Text Answer, Category Tag
    """
    status, headers, body = http_post_form(url, {'text': banking_spec})
    print(f'   Status: {status}')
    data = json.loads(body)
    print(f'   Type: {data.get("type")}')
    mr = data.get('model_readiness', {})
    metrics = data.get('metrics', {})
    content_types = data.get('content_types', [])
    print(f'   Readiness Status: {mr.get("status")}')
    print(f'   Architectural Score: {mr.get("score")}/100')
    print(f'   Summary: {mr.get("summary")}')
    print(f'   Content Types Count: {len(content_types)}')
    print(f'   Atomic Components: {metrics.get("atomic_components_count")}')
    assert status == 200, f'Expected 200, got {status}'
    assert data.get('type') == 'model', f'Expected type "model", got {data.get("type")}'
    score = mr.get('score', 0)
    assert score > 0, f'Expected positive score, got {score}'
    assert len(content_types) > 0, 'Expected generated content types'
    print('   >>> PASSED: Content specification decomposed into Component Graph & Schema')


def test_6_cloudfront_ui():
    print('\n[TEST 6] Checking CloudFront Frontend Distribution...')
    status, headers, body = http_get(CF_BASE)
    print(f'   Status: {status}')
    print(f'   Content-Type: {headers.get("content-type")}')
    assert status == 200, f'Expected 200, got {status}'
    assert '<div id="root">' in body or 'GRID' in body, 'Expected React root HTML'
    print('   >>> PASSED: CloudFront serving React SPA successfully')


def main():
    print('====================================================')
    print(f'   RUNNING GRID LIVE END-TO-END VERIFICATION')
    print(f'   API Base: {API_BASE}')
    print(f'   CF Base:  {CF_BASE}')
    print('====================================================')
    test_1_health()
    test_2_slang_bro()
    test_3_typo_greeting()
    test_4_conversational_question()
    test_5_content_modeling()
    test_6_cloudfront_ui()
    print('\n====================================================')
    print('   ALL 6 TESTS PASSED FLAWLESSLY WITH ZERO DEFECTS!')
    print('====================================================\n')


if __name__ == '__main__':
    main()
