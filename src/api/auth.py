# ============================================
# هذا الملف مسؤول عن:
# - تسجيل مستخدم جديد (Register)
# - تسجيل الدخول (Login)
# - جلب بيانات المستخدم
# ============================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import hashlib
from src.core.supabase_client import execute_query, execute_insert

# إنشاء Router للمصادقة
router = APIRouter(prefix="/auth", tags=["Authentication"])

# ============================================
# نماذج البيانات (Pydantic Models)
# ============================================

class UserCreate(BaseModel):
    """نموذج إنشاء مستخدم جديد"""
    name: str
    email: EmailStr
    password: str
    language: Optional[str] = "AR"
    phoneNumber: Optional[str] = None
    nationalID: Optional[str] = None
    birthDate: Optional[str] = None

class UserLogin(BaseModel):
    """نموذج تسجيل الدخول"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """نموذج الرد عند جلب بيانات المستخدم"""
    userID: int
    name: str
    email: str
    language: Optional[str] = "AR"
    registrationDate: Optional[datetime] = None

# ============================================
# دوال مساعدة
# ============================================

def hash_password(password: str) -> str:
    """تشفير كلمة المرور باستخدام SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

# ============================================
# API Endpoints
# ============================================

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    """تسجيل مستخدم جديد في النظام"""
    try:
        # التحقق: هل المستخدم موجود مسبقاً؟
        existing = await execute_query(
            'SELECT * FROM "Users" WHERE email = $1',
            user.email
        )
        
        if existing:
            raise HTTPException(status_code=400, detail="البريد الإلكتروني مستخدم مسبقاً")
        
        # تشفير كلمة المرور
        hashed_pw = hash_password(user.password)
        
        # إدراج المستخدم الجديد في قاعدة البيانات
        result = await execute_insert(
            """
            INSERT INTO "Users" (name, email, password, language, "phoneNumber", "nationalID", "birthDate")
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
            """,
            user.name, user.email, hashed_pw, user.language, 
            user.phoneNumber, user.nationalID, user.birthDate
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="فشل في إنشاء المستخدم")
        
        return UserResponse(
            userID=result["userID"],
            name=result["name"],
            email=result["email"],
            language=result.get("language", "AR"),
            registrationDate=result.get("registrationDate")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login")
async def login(user: UserLogin):
    """تسجيل دخول المستخدم"""
    try:
        hashed_pw = hash_password(user.password)
        
        result = await execute_query(
            'SELECT * FROM "Users" WHERE email = $1 AND password = $2',
            user.email, hashed_pw
        )
        
        if not result:
            raise HTTPException(status_code=401, detail="البريد الإلكتروني أو كلمة المرور غير صحيحة")
        
        user_data = result[0]
        
        return {
            "status": "success",
            "userID": user_data["userID"],
            "name": user_data["name"],
            "email": user_data["email"],
            "message": "تم تسجيل الدخول بنجاح"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
async def get_user(user_id: int):
    """جلب بيانات مستخدم بواسطة ID"""
    try:
        result = await execute_query(
            'SELECT * FROM "Users" WHERE "userID" = $1',
            user_id
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="المستخدم غير موجود")
        
        return result[0]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))