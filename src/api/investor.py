# ============================================
# هذا الملف مسؤول عن:
# - تحليل المشاريع (K-Means)
# - جلب التحليلات السابقة
# - إدارة الملف الشخصي للمستثمر
# ============================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import hashlib
from src.core.supabase_client import execute_query, execute_insert, execute_update
from src.core.ml_service import predict_cluster, get_suitability

router = APIRouter(prefix="/investor", tags=["Investor"])

# ============================================
# نماذج البيانات (Pydantic Models)
# ============================================

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

# ============================================
# دوال مساعدة
# ============================================

def hash_password(password: str) -> str:
    """تشفير كلمة المرور باستخدام SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

async def get_location_features(location_name: str):
    """
    جلب ميزات الموقع من قاعدة البيانات (LIQDataset)
    المدخل: اسم الموقع
    المخرج: [population_density, services_count, competitors_count]
    """
    try:
        # البحث عن الموقع في جدول LIQDataset
        result = await execute_query(
            """
            SELECT population_density, services_count, competitors_count
            FROM LIQDataset
            WHERE neighborhood ILIKE $1 OR city ILIKE $1
            LIMIT 1
            """,
            f"%{location_name}%"
        )
        
        if result:
            row = result[0]
            return [
                float(row["population_density"]) if row["population_density"] else 50.0,
                float(row["services_count"]) if row["services_count"] else 10.0,
                float(row["competitors_count"]) if row["competitors_count"] else 5.0
            ]
        else:
            # إذا لم يتم العثور على الموقع، نرجع ميزات افتراضية
            print(f"⚠️ Location '{location_name}' not found in LIQDataset. Using default features.")
            return [50.0, 10.0, 5.0]
            
    except Exception as e:
        print(f"Error getting location features: {e}")
        # في حالة الخطأ، نرجع ميزات افتراضية
        return [50.0, 10.0, 5.0]

# ============================================
# API Endpoints
# ============================================

@router.get("/health")
async def investor_health():
    """التحقق من صحة Investor API"""
    return {"status": "Investor API is ready"}

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_project(data: AnalysisRequest, userID: int):
    """
    تحليل المشروع باستخدام نموذج K-Means
    - يجلب ميزات الموقع من قاعدة البيانات
    - يستخدم نموذج ML للتنبؤ بالكتلة
    - يحفظ التحليل في قاعدة البيانات
    - يعيد الكتلة والنتيجة
    """
    try:
        # 1. التحقق من وجود المستخدم
        user = await execute_query(
            'SELECT * FROM "Users" WHERE "userID" = $1',
            userID
        )
        if not user:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        
        # 2. جلب ميزات الموقع من قاعدة البيانات
        features = await get_location_features(data.location)
        
        # 3. استدعاء نموذج K-Means للتنبؤ بالكتلة
        cluster = predict_cluster(features)
        
        # 4. تحويل الكتلة إلى نص ونسبة مئوية
        suitability, score = get_suitability(cluster)
        
        # 5. حفظ التحليل في جدول AIChatAnalysis
        message = f"Project: {data.project_name}, Type: {data.project_type}, Location: {data.location}"
        ai_response = f"Cluster: {cluster}, Suitability: {suitability}, Score: {score}%"
        
        await execute_insert(
            """
            INSERT INTO "AIChatAnalysis" ("userID", message, "aiResponse", "confidenceScore")
            VALUES ($1, $2, $3, $4)
            RETURNING *
            """,
            userID, message, ai_response, score / 100
        )
        
        # 6. إرجاع النتيجة
        return AnalysisResponse(
            cluster=cluster,
            suitability=suitability,
            score=score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_history(userID: int):
    """
    جلب آخر 10 تحليلات للمستخدم
    """
    try:
        analyses = await execute_query(
            """
            SELECT "chatID", message, "aiResponse", "confidenceScore", "timestamp"
            FROM "AIChatAnalysis"
            WHERE "userID" = $1
            ORDER BY "timestamp" DESC
            LIMIT 10
            """,
            userID
        )
        
        return [
            {
                "id": a["chatID"],
                "message": a["message"],
                "response": a["aiResponse"],
                "score": float(a["confidenceScore"]) if a["confidenceScore"] else None,
                "date": a["timestamp"]
            }
            for a in analyses
        ]
        
    except Exception as e:
        print(f"History error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
async def get_profile(userID: int):
    """
    جلب بيانات المستخدم الشخصية
    """
    try:
        user = await execute_query(
            'SELECT * FROM "Users" WHERE "userID" = $1',
            userID
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        
        u = user[0]
        
        return {
            "id": u["userID"],
            "name": u["name"],
            "email": u["email"],
            "role": "admin" if u["email"] == "admin@locateiq.com" else "user",
            "created_at": u["registrationDate"],
            "phone": u.get("phoneNumber"),
            "national_id": u.get("nationalID"),
            "birth_date": u.get("birthDate"),
            "avatar": u.get("profileImage")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/profile")
async def update_profile(data: ProfileUpdateRequest, userID: int):
    """
    تحديث بيانات المستخدم الشخصية
    """
    try:
        # التحقق من وجود المستخدم
        user = await execute_query(
            'SELECT * FROM "Users" WHERE "userID" = $1',
            userID
        )
        if not user:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        
        # تحديث البيانات
        await execute_update(
            """
            UPDATE "Users"
            SET name = $1, email = $2, "phoneNumber" = $3, "nationalID" = $4, "birthDate" = $5
            WHERE "userID" = $6
            """,
            data.name, data.email, data.phone, data.national_id, data.birth_date, userID
        )
        
        return {"message": "Profile updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Update profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/password")
async def change_password(data: ChangePasswordRequest, userID: int):
    """
    تغيير كلمة المرور
    """
    try:
        # جلب المستخدم
        user = await execute_query(
            'SELECT * FROM "Users" WHERE "userID" = $1',
            userID
        )
        if not user:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        
        u = user[0]
        
        # التحقق من كلمة المرور الحالية
        current_hashed = hash_password(data.current_password)
        if current_hashed != u["password"]:
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        # تحديث كلمة المرور
        new_hashed = hash_password(data.new_password)
        await execute_update(
            'UPDATE "Users" SET password = $1 WHERE "userID" = $2',
            new_hashed, userID
        )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Change password error: {e}")
        raise HTTPException(status_code=500, detail=str(e))