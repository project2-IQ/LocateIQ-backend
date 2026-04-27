# ============================================
# هذا الملف مسؤول عن الاتصال بقاعدة البيانات (Supabase)
# يستخدم asyncpg للاتصال المباشر مع PostGIS
# ============================================

import os
from dotenv import load_dotenv
import asyncpg

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# ============================================
# معلومات الاتصال بقاعدة البيانات
# ============================================

# جلب رابط قاعدة البيانات من متغير البيئة
DATABASE_URL = os.getenv("DATABASE_URL")

# إذا ما لقى الرابط، يوقف الخادم ويعطي خطأ واضح
if not DATABASE_URL:
    raise Exception("❌ DATABASE_URL not found in .env file. Please check your .env file.")

# طباعة الرابط للتأكد (بدون كلمة المرور)
print(f"🔗 DATABASE_URL: {DATABASE_URL.replace('newdataset2026s', '****')}")

# ============================================
# دوال الاتصال بقاعدة البيانات
# ============================================

async def get_db():
    """
    إنشاء اتصال جديد بقاعدة البيانات
    الاستخدام: conn = await get_db()
    """
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        raise

async def execute_query(query: str, *args):
    """
    تنفيذ استعلام واسترجاع جميع النتائج (لـ SELECT)
    المدخلات:
        query: نص الاستعلام (مثل SELECT * FROM table)
        *args: القيم التي تحل محل $1, $2, ...
    المخرج: قائمة بالصفوف (list of dict-like records)
    """
    conn = None
    try:
        conn = await get_db()
        result = await conn.fetch(query, *args)
        return result
    except Exception as e:
        print(f"❌ Query error: {e}")
        print(f"Query: {query}")
        raise
    finally:
        if conn:
            await conn.close()

async def execute_insert(query: str, *args):
    """
    تنفيذ استعلام إدراج واسترجاع الصف المضاف (لـ INSERT RETURNING)
    المدخلات:
        query: نص الاستعلام (مثل INSERT INTO ... RETURNING *)
        *args: القيم التي تحل محل $1, $2, ...
    المخرج: صف واحد (record) يحتوي البيانات المضاف
    """
    conn = None
    try:
        conn = await get_db()
        result = await conn.fetchrow(query, *args)
        return result
    except Exception as e:
        print(f"❌ Insert error: {e}")
        print(f"Query: {query}")
        raise
    finally:
        if conn:
            await conn.close()

async def execute_update(query: str, *args):
    """
    تنفيذ استعلام تحديث أو حذف
    المدخلات:
        query: نص الاستعلام (مثل UPDATE ... SET ...)
        *args: القيم التي تحل محل $1, $2, ...
    المخرج: عدد الصفوف المتأثرة
    """
    conn = None
    try:
        conn = await get_db()
        result = await conn.execute(query, *args)
        return result
    except Exception as e:
        print(f"❌ Update error: {e}")
        print(f"Query: {query}")
        raise
    finally:
        if conn:
            await conn.close()