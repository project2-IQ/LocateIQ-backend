# src/schemas/admin.py

from pydantic import BaseModel

# ============================================
# نموذج إحصائيات النظام
# ============================================
class StatsResponse(BaseModel):
    total_users: int
    total_analyses: int
    active_now: int

# ============================================
# نموذج عرض المستخدم
# ============================================
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: str

# ============================================
# نموذج إعدادات النظام
# ============================================
class SettingsResponse(BaseModel):
    site_name: str
    admin_email: str
    maintenance_mode: bool