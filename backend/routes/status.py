"""
Status routes for the Chameleon Hackathon Discovery API
"""

import json
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

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
                
                yield data
                await asyncio.sleep(1)
                
            except Exception as e:
                yield {"error": str(e)}
                break
    
    return EventSourceResponse(generate())


@router.get("/terminal/stream")
async def stream_terminal():
    """Stream real-time terminal output using Server-Sent Events"""
    async def generate():
        status_tracker = get_global_tracker()
        last_position = 0
        
        while True:
            try:
                # Get all terminal output since last position
                all_output = status_tracker.get_terminal_output()
                if len(all_output) > last_position:
                    new_output = all_output[last_position:]
                    for line in new_output:
                        yield {
                            "type": "terminal_output",
                            "content": line,
                            "timestamp": datetime.now().isoformat()
                        }
                    last_position = len(all_output)
                
                await asyncio.sleep(0.5)  # More frequent updates for terminal
                
            except Exception as e:
                yield {
                    "type": "error",
                    "content": f"Terminal stream error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                break
    
    return EventSourceResponse(generate()) 