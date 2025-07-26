@echo off
echo 🚀 Starting Enhanced Form Builder Backend...
echo.

cd /d "C:\Users\IRMAN\OneDrive\Desktop\prototype\backend"

echo 📁 Working directory: %CD%
echo 🐍 Using Python virtual environment...

"C:/Users/IRMAN/OneDrive/Desktop/prototype/backend/venv/Scripts/python.exe" -c "import os, sys; sys.path.insert(0, '.'); from app import create_app; app = create_app(); print('✅ Flask app initialized'); print('🌐 Server starting on http://localhost:5000'); print('📊 Enhanced form builder with QR codes ready!'); print('-' * 50); app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)"

pause
