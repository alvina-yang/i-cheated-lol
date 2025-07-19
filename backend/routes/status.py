"""
Status routes for the Chameleon Hackathon Discovery API
"""

import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models import StatusResponse
from utils.status_tracker import get_global_tracker

router = APIRouter(prefix="/api", tags=["status"])


@router.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current status of operations and tasks"""
    try:
        status_tracker = get_global_tracker()
        summary = status_tracker.get_status_summary()
        tasks = status_tracker.get_all_tasks()
        recent_output = status_tracker.get_recent_output(20)
        
        return StatusResponse(
            current_operation=summary["current_operation"],
            tasks=tasks,
            recent_output=recent_output,
            summary=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting status: {str(e)}")


@router.get("/status/stream")
async def stream_status():
    """Stream real-time status updates using Server-Sent Events"""
    async def generate():
        status_tracker = get_global_tracker()
        while True:
            try:
                summary = status_tracker.get_status_summary()
                tasks = status_tracker.get_active_tasks()
                recent_output = status_tracker.get_recent_output(5)
                
                data = {
                    "current_operation": summary["current_operation"],
                    "tasks": tasks,
                    "recent_output": recent_output,
                    "timestamp": datetime.now().isoformat()
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                await asyncio.sleep(1)
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(generate(), media_type="text/plain", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "text/event-stream"
    })


@router.get("/terminal/stream")
async def stream_terminal():
    """Disabled terminal streaming to avoid issues"""
    return {"message": "Terminal streaming disabled"} 