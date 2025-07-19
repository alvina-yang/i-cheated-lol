"""
Settings routes for the Chameleon Hackathon Discovery API
"""

from fastapi import APIRouter, HTTPException

from models import SettingsUpdateRequest, SettingsResponse
from core.enhanced_config import EnhancedConfig

router = APIRouter(prefix="/api", tags=["settings"])


@router.post("/settings", response_model=SettingsResponse)
async def update_settings(request: SettingsUpdateRequest):
    """Update system settings"""
    try:
        success = False
        
        if request.setting_type == "user":
            success = EnhancedConfig.update_user_settings(**request.settings)
        elif request.setting_type == "repository":
            success = EnhancedConfig.update_repository_settings(**request.settings)
        elif request.setting_type == "processing":
            success = EnhancedConfig.update_processing_settings(**request.settings)
        elif request.setting_type == "terminal":
            success = EnhancedConfig.update_terminal_settings(**request.settings)
        else:
            raise HTTPException(status_code=400, detail="Invalid setting type")
        
        if success:
            return SettingsResponse(
                success=True,
                message=f"Updated {request.setting_type} settings successfully",
                settings=request.settings
            )
        else:
            return SettingsResponse(
                success=False,
                message=f"Failed to update {request.setting_type} settings"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating settings: {str(e)}")


@router.get("/settings")
async def get_settings():
    """Get all current settings"""
    try:
        return EnhancedConfig.get_all_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting settings: {str(e)}") 