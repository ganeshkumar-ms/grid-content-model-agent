import base64
import json
import os
import re
import uuid
from email.parser import BytesParser
from email.policy import default as default_email_policy
from pathlib import Path
from urllib.parse import quote, unquote

import boto3
from botocore.config import Config
from services import grid_service, document_service, file_validation, viewer_service

TMP_UPLOADS = Path('/tmp/uploads')
TMP_UPLOADS.mkdir(parents=True, exist_ok=True)
S3_BUCKET = os.environ.get('GRID_S3_BUCKET', 'grid-ui-984625844016')
REGION = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')

s3_client = boto3.client(
    's3',
    region_name=REGION,
    endpoint_url=f'https://s3.{REGION}.amazonaws.com',
    config=Config(signature_version='s3v4', s3={'addressing_style': 'virtual'})
)

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': '*',
}


def _json_response(status_code: int, payload: dict) -> dict:
    return {
        'statusCode': status_code,
        'headers': {**CORS_HEADERS, 'Content-Type': 'application/json'},
        'body': json.dumps(payload),
    }


def _parse_multipart(body_bytes: bytes, content_type: str) -> dict:
    raw_msg = b'Content-Type: ' + content_type.encode('utf-8') + b'\r\nMIME-Version: 1.0\r\n\r\n' + body_bytes
    msg = BytesParser(policy=default_email_policy).parsebytes(raw_msg)
    fields = {}
    file_info = None
    if msg.is_multipart():
        for part in msg.iter_parts():
            cd = part.get('Content-Disposition', '')
            if not cd:
                continue
            name = part.get_param('name', header='content-disposition')
            filename = part.get_filename()
            payload = part.get_payload(decode=True) or b''
            if filename:
                file_info = {'filename': filename, 'bytes': payload}
            elif name:
                fields[name] = payload.decode('utf-8', errors='replace')
    return {'fields': fields, 'file': file_info}


def _display_name(stored: str) -> str:
    return stored.split('_', 1)[1] if len(stored) > 9 and stored[8] == '_' else stored


def _sanitize_filename(filename: str) -> str:
    name = Path(filename or 'document').name
    return re.sub(r'[^\w.\- ()+\[\]]', '_', name) or 'document'


def _get_s3_size(s3_key: str) -> int:
    try:
        head = s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        return int(head.get('ContentLength', 0))
    except Exception:
        return -1


def _resolve_upload(filename: str) -> Path:
    safe = Path(unquote(filename)).name
    local_path = TMP_UPLOADS / safe
    if not local_path.exists():
        try:
            obj = s3_client.get_object(Bucket=S3_BUCKET, Key=f'uploads/{safe}')
            local_path.write_bytes(obj['Body'].read())
        except Exception:
            return None
    return local_path


def lambda_handler(event, context):
    method = (
        event.get('requestContext', {}).get('http', {}).get('method')
        or event.get('httpMethod')
        or 'GET'
    ).upper()

    raw_path = (
        event.get('requestContext', {}).get('http', {}).get('path')
        or event.get('rawPath')
        or event.get('path')
        or '/'
    )

    if method == 'OPTIONS':
        return {'statusCode': 204, 'headers': CORS_HEADERS, 'body': ''}

    # Health Check
    if raw_path in ('/api/health', '/health'):
        return _json_response(200, {
            'status': 'ok',
            'agent': 'GRID',
            'eyebrow': 'CONTENT MODEL ARCHITECT',
            'service': 'Enterprise Content Modeling & Schema Architecture Engine',
            'aws_account': '984625844016',
        })

    # Document view / download
    if raw_path.startswith('/api/document/') and method == 'GET':
        tail = raw_path[len('/api/document/'):]
        is_view = tail.endswith('/view')
        fname = tail[:-len('/view')] if is_view else tail
        safe_stored = Path(unquote(fname)).name
        disp = _display_name(safe_stored)
        s3_size = _get_s3_size(f'uploads/{safe_stored}')

        if s3_size > 4_000_000 and (not is_view or safe_stored.lower().endswith('.pdf')):
            params = {
                'Bucket': S3_BUCKET,
                'Key': f'uploads/{safe_stored}',
                'ResponseContentDisposition': f'{"inline" if is_view else "attachment"}; filename="{disp}"',
            }
            if is_view and safe_stored.lower().endswith('.pdf'):
                params['ResponseContentType'] = 'application/pdf'
            presigned = s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params=params,
                ExpiresIn=3600,
            )
            return {'statusCode': 302, 'headers': {**CORS_HEADERS, 'Location': presigned}, 'body': ''}

        file_path = _resolve_upload(fname)
        if not file_path or not file_path.exists():
            return _json_response(404, {'detail': 'File not found. Please upload it again.'})

        if is_view:
            if file_path.suffix.lower() == '.pdf':
                return {
                    'statusCode': 200,
                    'headers': {
                        **CORS_HEADERS,
                        'Content-Type': 'application/pdf',
                        'Content-Disposition': f'inline; filename="{disp}"',
                    },
                    'isBase64Encoded': True,
                    'body': base64.b64encode(file_path.read_bytes()).decode('ascii'),
                }
            html_out = viewer_service.render_html(file_path, disp)
            return {
                'statusCode': 200,
                'headers': {**CORS_HEADERS, 'Content-Type': 'text/html; charset=utf-8'},
                'body': html_out,
            }
        else:
            return {
                'statusCode': 200,
                'headers': {
                    **CORS_HEADERS,
                    'Content-Type': 'application/octet-stream',
                    'Content-Disposition': f'attachment; filename="{disp}"',
                },
                'isBase64Encoded': True,
                'body': base64.b64encode(file_path.read_bytes()).decode('ascii'),
            }

    # Modeling endpoint
    if raw_path in ('/api/model', '/api/grid/model') and method == 'POST':
        headers = {k.lower(): v for k, v in (event.get('headers') or {}).items()}
        ct = headers.get('content-type', '')
        body_raw = event.get('body') or ''
        body_bytes = base64.b64decode(body_raw) if event.get('isBase64Encoded') else body_raw.encode('utf-8')

        text = ''
        conversation_history = '[]'
        doc_meta = None

        if 'multipart/form-data' in ct:
            parsed = _parse_multipart(body_bytes, ct)
            text = parsed['fields'].get('text', '')
            conversation_history = parsed['fields'].get('conversation_history', '[]')
            file_item = parsed['file']
            if file_item and file_item.get('filename'):
                orig_filename = _sanitize_filename(file_item['filename'])
                raw_file_bytes = file_item.get('bytes') or b''
                pre_rej = file_validation.validate_file_pre_extract(orig_filename, raw_file_bytes)
                if pre_rej:
                    return _json_response(200, {
                        'type': 'chat',
                        'message': pre_rej['message'],
                        'rejected': True,
                        'rejection_details': pre_rej,
                        'document': {'filename': orig_filename, 'size': len(raw_file_bytes)},
                    })
                storage_id = f"{uuid.uuid4().hex[:8]}_{orig_filename}"
                local_file = TMP_UPLOADS / storage_id
                local_file.write_bytes(file_item['bytes'])

                try:
                    s3_client.put_object(
                        Bucket=S3_BUCKET,
                        Key=f'uploads/{storage_id}',
                        Body=file_item['bytes'],
                        ContentType='application/octet-stream'
                    )
                except Exception as e:
                    print(f"Warning: S3 upload failed: {e}")

                extracted = document_service.extract_document(orig_filename, raw_file_bytes)
                file_text = extracted.get('text', '')
                post_rej = file_validation.validate_file_post_extract(orig_filename, raw_file_bytes, file_text, meta=extracted.get('metadata'))
                if post_rej:
                    return _json_response(200, {
                        'type': 'chat',
                        'message': post_rej['message'],
                        'rejected': True,
                        'rejection_details': post_rej,
                        'document': {'filename': orig_filename, 'size': len(raw_file_bytes)},
                    })

                if text:
                    text = f"{text}\n\n[ATTACHED CONTENT: {orig_filename}]\n{file_text}"
                else:
                    text = file_text

                doc_meta = {
                    "id": storage_id,
                    "filename": orig_filename,
                    "size": len(file_item['bytes']),
                    "content_type": extracted.get('detected_type') or 'application/octet-stream',
                    "url": f"/api/document/{quote(storage_id)}",
                    "view_url": f"/api/document/{quote(storage_id)}/view",
                    "words": extracted.get('words', 0),
                    "preview": extracted.get('preview', '')
                }
        else:
            try:
                data = json.loads(body_bytes.decode('utf-8') or '{}')
                text = data.get('content') or data.get('text') or ''
                conversation_history = json.dumps(data.get('conversation_history', []))
            except Exception:
                text = body_bytes.decode('utf-8', errors='replace')

        try:
            history = json.loads(conversation_history)
        except Exception:
            history = []

        clean_text = (text or '').strip()
        if not clean_text:
            return _json_response(200, {
                "type": "chat",
                "message": "Please provide content text, paste a document specification, or upload a file to model into headless schemas.",
                "document": doc_meta
            })

        # Run core content modeling logic
        result = grid_service.model_content(
            content=clean_text,
            file_name=doc_meta.get('filename') if doc_meta else '',
            conversation_history=history
        )

        result['document'] = doc_meta
        return _json_response(200, result)

    return _json_response(404, {'detail': f'Not found: {method} {raw_path}'})


handler = lambda_handler

