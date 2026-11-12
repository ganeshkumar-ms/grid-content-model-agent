import os
import sys
from pathlib import Path
from typing import Optional
import json
import uuid
from urllib.parse import quote
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services import grid_service, document_service, file_validation, viewer_service

router = APIRouter(prefix='/api')
UPLOADS_DIR = Path('/tmp/uploads') if os.path.exists('/tmp') else (BACKEND_DIR / 'uploads')
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_upload(filename: str) -> Path:
    safe = Path(filename).name
    file_path = UPLOADS_DIR / safe
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='File not found. Please upload it again.')
    return file_path


def _display_name(stored: str) -> str:
    return stored.split('_', 1)[1] if len(stored) > 9 and stored[8] == '_' else stored


@router.get('/health')
def health():
    return {
        "status": "ok",
        "agent": "GRID",
        "eyebrow": "CONTENT MODEL ARCHITECT",
        "service": "Enterprise Content Modeling & Schema Architecture Engine"
    }


@router.get('/document/{filename}/view')
def view_document(filename: str):
    file_path = _resolve_upload(filename)
    name = _display_name(file_path.name)
    if file_path.suffix.lower() == '.pdf':
        return FileResponse(path=file_path, media_type='application/pdf',
                            headers={'Content-Disposition': f'inline; filename="{name}"'})
    return HTMLResponse(viewer_service.render_html(file_path, name))


@router.get('/document/{filename}')
def get_document(filename: str):
    file_path = _resolve_upload(filename)
    return FileResponse(path=file_path, filename=_display_name(file_path.name))


@router.post('/model')
async def model(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    conversation_history: Optional[str] = Form('[]')
):
    try:
        history = json.loads(conversation_history or '[]')
    except json.JSONDecodeError:
        history = []

    doc_meta = None
    combined_text = text or ''
    file_name = ''

    if file and file.filename:
        file_name = file.filename
        raw_bytes = await file.read()
        pre_rej = file_validation.validate_file_pre_extract(file.filename, raw_bytes)
        if pre_rej:
            return {
                'type': 'chat',
                'message': pre_rej['message'],
                'rejected': True,
                'rejection_details': pre_rej,
                'document': {'filename': file.filename, 'size': len(raw_bytes)},
            }
        storage_id = f"{uuid.uuid4().hex[:8]}_{file.filename}"
        stored_path = UPLOADS_DIR / storage_id
        stored_path.write_bytes(raw_bytes)

        extracted = document_service.extract_document(file.filename, raw_bytes)
        file_text = extracted.get('text', '')
        post_rej = file_validation.validate_file_post_extract(file.filename, raw_bytes, file_text, meta=extracted.get('metadata'))
        if post_rej:
            return {
                'type': 'chat',
                'message': post_rej['message'],
                'rejected': True,
                'rejection_details': post_rej,
                'document': {'filename': file.filename, 'size': len(raw_bytes)},
            }

        if combined_text:
            combined_text = f"{combined_text}\n\n[ATTACHED CONTENT: {file.filename}]\n{file_text}"
        else:
            combined_text = file_text

        doc_meta = {
            "id": storage_id,
            "filename": file.filename,
            "size": len(raw_bytes),
            "content_type": extracted.get('detected_type') or file.content_type,
            "url": f"/api/document/{quote(storage_id)}",
            "view_url": f"/api/document/{quote(storage_id)}/view",
            "words": extracted.get('words', 0),
            "preview": extracted.get('preview', '')
        }

    clean_content = (combined_text or '').strip()
    if not clean_content:
        return {
            "type": "chat",
            "message": "Please provide content text, paste a document specification, or upload a file to model into headless schemas."
        }

    result = grid_service.model_content(
        content=clean_content,
        file_name=file_name,
        conversation_history=history
    )

    if doc_meta:
        result['document'] = doc_meta

    return result

