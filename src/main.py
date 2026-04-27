# ============================================
# هذا الملف هو المدخل الرئيسي للباك إند
# يربط جميع الـ APIs ويشغل الخادم
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

# استيراد الـ routers من كل ملف
from src.api.auth import router as auth_router        # APIs المصادقة (تسجيل دخول، إنشاء حساب)
from src.api.investor import router as investor_router # APIs المستثمر (تحليل، ملف شخصي)
from src.api.admin import router as admin_router       # APIs الأدمن (إدارة مستخدمين، إحصائيات)

# استيراد الاتصال بقاعدة البيانات لاختبارها
from src.core.supabase_client import execute_query

# استيراد Machine Learning لاختبارها
from src.core.ml_service import model, scaler

# إنشاء تطبيق FastAPI
app = FastAPI(
    title="LocateIQ Backend",
    description="Backend API for LocateIQ investment platform",
    version="1.0.0"
)

# ============================================
# إعداد CORS للسماح للواجهة الأمامية بالاتصال
# ============================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # في الإنتاج، حددي النطاق الحقيقي
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# تسجيل جميع الـ routers في التطبيق
# ============================================
app.include_router(auth_router)      # /auth/*
app.include_router(investor_router)  # /investor/*
app.include_router(admin_router)     # /admin/*

# ============================================
# API للتحقق من أن الخادم يعمل
# GET /
# ============================================
@app.get("/")
def root():
    """التحقق من أن الخادم يعمل"""
    return {
        "message": "LocateIQ backend is running",
        "status": "online",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# API للتحقق من صحة الخادم (health check)
# GET /health
# ============================================
@app.get("/health")
def health_check():
    """التحقق من صحة الخادم للواجهات"""
    return {
        "status": "healthy",
        "services": {
            "auth": "online",
            "investor": "online",
            "admin": "online"
        },
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# API لاختبار الاتصال بقاعدة البيانات (إضافة جديدة)
# GET /test-db
# ============================================
@app.get("/test-db")
async def test_database():
    """اختبار الاتصال بقاعدة البيانات"""
    try:
        result = await execute_query("SELECT 1 as test")
        return {
            "status": "success",
            "message": "✅ Database connection is working",
            "result": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"❌ Database connection failed: {str(e)}"
        }

# ============================================
# API لاختبار الـ Machine Learning (إضافة جديدة)
# GET /test-ml
# ============================================
@app.get("/test-ml")
def test_ml():
    """اختبار حالة نموذج Machine Learning"""
    return {
        "status": "success",
        "model_loaded": model is not None,
        "scaler_loaded": scaler is not None,
        "message": "✅ ML model is ready" if model is not None else "⚠️ ML model not loaded"
    }

# ============================================
# API لمعلومات المشروع (إضافة جديدة)
# GET /info
# ============================================
@app.get("/info")
def project_info():
    """معلومات عامة عن المشروع"""
    return {
        "project_name": "LocateIQ",
        "description": "Smart investment location analysis system for Asir Region",
        "region": "Asir, Saudi Arabia",
        "version": "1.0.0",
        "features": [
            "Location-based investment analysis",
            "Interactive maps",
            "AI-powered recommendations (K-Means)",
            "User profiles and history",
            "Admin dashboard"
        ]
    }