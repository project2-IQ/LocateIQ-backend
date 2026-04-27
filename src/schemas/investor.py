# ============================================
# نماذج البيانات الخاصة بالمستثمر
# ============================================

from pydantic import BaseModel
from typing import Optional

class AnalysisRequest(BaseModel):
    """نموذج طلب تحليل المشروع"""
    project_name: str
    project_type: str
    location: str

class AnalysisResponse(BaseModel):
    """نموذج رد التحليل"""
    cluster: int
    suitability: str
    score: float

class ProfileUpdateRequest(BaseModel):
    """نموذج تحديث الملف الشخصي"""
    name: str
    email: str
    phone: Optional[str] = None
    national_id: Optional[str] = None
    birth_date: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    """نموذج تغيير كلمة المرور"""
    current_password: str
    new_password: str