# ============================================
# هذا الملف مسؤول عن:
# - إحصائيات النظام
# - إدارة المستخدمين (حذف)
# - إعدادات النظام
# ============================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.core.supabase_client import execute_query, execute_update

router = APIRouter(prefix="/admin", tags=["Admin"])

# ============================================
# نماذج البيانات
# ============================================

class SettingsUpdate(BaseModel):
    """نموذج تحديث الإعدادات"""
    site_name: Optional[str] = None
    admin_email: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    map_style: Optional[str] = None
    zoom_level: Optional[int] = None
    show_clusters: Optional[bool] = None

# ============================================
# API Endpoints
# ============================================

@router.get("/stats")
async def get_stats():
    """
    جلب إحصائيات النظام
    """
    try:
        # عدد المستخدمين
        users_result = await execute_query('SELECT COUNT(*) FROM "User"')
        total_users = users_result[0]["count"] if users_result else 0
        
        # عدد التحليلات
        analyses_result = await execute_query('SELECT COUNT(*) FROM "AIChatAnalysis"')
        total_analyses = analyses_result[0]["count"] if analyses_result else 0
        
        return {
            "total_users": total_users,
            "total_analyses": total_analyses,
            "active_now": 3  # TODO: يمكن تحسينها بحساب المستخدمين النشطين فعلياً
        }
        
    except Exception as e:
        print(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def get_all_users():
    """
    جلب جميع المستخدمين
    """
    try:
        users = await execute_query(
            'SELECT "userID", name, email, "registrationDate" FROM "User" ORDER BY "registrationDate" DESC'
        )
        
        return [
            {
                "id": u["userID"],
                "name": u["name"],
                "email": u["email"],
                "role": "admin" if u["email"] == "admin@locateiq.com" else "user",
                "created_at": u["registrationDate"]
            }
            for u in users
        ]
        
    except Exception as e:
        print(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """
    حذف مستخدم (مع جميع بياناته المرتبطة)
    """
    try:
        # التحقق من وجود المستخدم
        user = await execute_query(
            'SELECT * FROM "User" WHERE "userID" = $1',
            user_id
        )
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # حذف التحليلات المرتبطة أولاً (بسبب Foreign Key)
        await execute_update(
            'DELETE FROM "AIChatAnalysis" WHERE "userID" = $1',
            user_id
        )
        
        # حذف المستخدم
        await execute_update(
            'DELETE FROM "User" WHERE "userID" = $1',
            user_id
        )
        
        return {"message": f"User {user_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_settings():
    """
    جلب إعدادات النظام
    """
    try:
        # جلب إعدادات الأدمن (إذا وجدت)
        admin = await execute_query('SELECT * FROM "Admin" LIMIT 1')
        
        if admin:
            a = admin[0]
            return {
                "site_name": a.get("siteName", "LocateIQ"),
                "admin_email": a.get("adminEmail", "admin@locateiq.com"),
                "maintenance_mode": a.get("maintenanceMode", False),
                "map_style": a.get("mapStyle", "streets"),
                "zoom_level": a.get("zoomLevel", 12),
                "show_clusters": a.get("showClusters", True)
            }
        else:
            # إعدادات افتراضية
            return {
                "site_name": "LocateIQ",
                "admin_email": "admin@locateiq.com",
                "maintenance_mode": False,
                "map_style": "streets",
                "zoom_level": 12,
                "show_clusters": True
            }
        
    except Exception as e:
        print(f"Get settings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings")
async def update_settings(settings: SettingsUpdate):
    """
    تحديث إعدادات النظام
    """
    try:
        # التحقق من وجود سجل Admin
        admin = await execute_query('SELECT * FROM "Admin" LIMIT 1')
        
        if not admin:
            # إنشاء سجل Admin جديد
            await execute_insert(
                """
                INSERT INTO "Admin" ("userID", "siteName", "adminEmail", "maintenanceMode", "mapStyle", "zoomLevel", "showClusters")
                VALUES (1, $1, $2, $3, $4, $5, $6)
                """,
                settings.site_name or "LocateIQ",
                settings.admin_email or "admin@locateiq.com",
                settings.maintenance_mode or False,
                settings.map_style or "streets",
                settings.zoom_level or 12,
                settings.show_clusters or True
            )
        else:
            # تحديث الإعدادات الموجودة
            updates = []
            values = []
            idx = 1
            
            if settings.site_name is not None:
                updates.append(f'"siteName" = ${idx}')
                values.append(settings.site_name)
                idx += 1
            if settings.admin_email is not None:
                updates.append(f'"adminEmail" = ${idx}')
                values.append(settings.admin_email)
                idx += 1
            if settings.maintenance_mode is not None:
                updates.append(f'"maintenanceMode" = ${idx}')
                values.append(settings.maintenance_mode)
                idx += 1
            if settings.map_style is not None:
                updates.append(f'"mapStyle" = ${idx}')
                values.append(settings.map_style)
                idx += 1
            if settings.zoom_level is not None:
                updates.append(f'"zoomLevel" = ${idx}')
                values.append(settings.zoom_level)
                idx += 1
            if settings.show_clusters is not None:
                updates.append(f'"showClusters" = ${idx}')
                values.append(settings.show_clusters)
                idx += 1
            
            if updates:
                query = f'UPDATE "Admin" SET {", ".join(updates)} WHERE "adminID" = (SELECT "adminID" FROM "Admin" LIMIT 1)'
                await execute_update(query, *values)
        
        return {"message": "Settings updated successfully"}
        
    except Exception as e:
        print(f"Update settings error: {e}")
        raise HTTPException(status_code=500, detail=str(e))