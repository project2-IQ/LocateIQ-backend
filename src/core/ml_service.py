# ============================================
# هذا الملف مسؤول عن تحميل نموذج K-Means
# وتقديم التنبؤات (clusters) للمواقع
# ============================================

import pickle
import os
import random
import numpy as np
from pathlib import Path

# ============================================
# تحديد المسار الصحيح لنموذج ML
# ============================================

# المسار المتوقع: src/core/ml_model/kmeans_model.pkl
CURRENT_DIR = Path(__file__).resolve().parent  # src/core/
MODEL_PATH = CURRENT_DIR / "ml_model" / "kmeans_model.pkl"
SCALER_PATH = CURRENT_DIR / "ml_model" / "scaler.pkl"

# المتغيرات العالمية
model = None
scaler = None

# ============================================
# تحميل النموذج
# ============================================

def load_model_and_scaler():
    """تحميل النموذج والـ Scaler من مجلد ml_model"""
    global model, scaler
    
    try:
        if MODEL_PATH.exists() and SCALER_PATH.exists():
            with open(MODEL_PATH, 'rb') as f:
                model = pickle.load(f)
            with open(SCALER_PATH, 'rb') as f:
                scaler = pickle.load(f)
            print(f"✅ ML model loaded from {MODEL_PATH}")
            print(f"✅ Scaler loaded from {SCALER_PATH}")
            return True
        else:
            print(f"⚠️ Model file not found at {MODEL_PATH}")
            print(f"⚠️ Scaler file not found at {SCALER_PATH}")
            return False
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False

# تحميل النموذج عند استيراد الملف
load_model_and_scaler()

# ============================================
# دالة التنبؤ (Prediction)
# ============================================

def predict_cluster(features):
    """
    توقع الكتلة (cluster) المناسبة للموقع
    المدخلات: features = [population_density, services_count, competitors_count]
    المخرج: رقم الكتلة (0, 1, 2) حسب تدريب النموذج
    """
    global model, scaler
    
    try:
        if model is not None and scaler is not None:
            # تحويل الميزات إلى مصفوفة numpy
            features_array = np.array(features).reshape(1, -1)
            
            # تطبيق Scaler (نفس اللي استخدم في التدريب)
            features_scaled = scaler.transform(features_array)
            
            # توقع الكتلة
            cluster = model.predict(features_scaled)
            
            # النموذج يرجع 0, 1, 2 حسب المجموعة
            return int(cluster[0])
        else:
            # Mock prediction إذا النموذج غير موجود
            print("⚠️ Model not loaded, using mock prediction")
            score = (features[0] / 100) + features[1] + features[2]
            if score > 50:
                return 2
            elif score > 20:
                return 1
            else:
                return 0
    except Exception as e:
        print(f"❌ Prediction error: {e}")
        return random.randint(0, 2)


def get_suitability(cluster):
    """
    تحويل رقم الكتلة إلى نص مناسب ونسبة مئوية
    cluster: 0 = Low, 1 = Medium, 2 = High
    (هذا يعتمد على كيف دربتي النموذج)
    """
    if cluster == 0:
        return "منخفضة (Low)", 30
    elif cluster == 1:
        return "متوسطة (Medium)", 65
    else:  # cluster == 2
        return "عالية (High)", 90


def get_cluster_description(cluster):
    """وصف الكتلة للمستخدم"""
    descriptions = {
        0: "⚠️ منطقة ذات جاذبية منخفضة - فرص استثمارية محدودة",
        1: "📈 منطقة ذات جاذبية متوسطة - فرص استثمارية جيدة",
        2: "🌟 منطقة ذات جاذبية عالية - فرص استثمارية ممتازة"
    }
    return descriptions.get(cluster, "غير معروف")