#!/usr/bin/env python3
"""
Quick test to verify QR code generation is working
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_qr_generation():
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        print("🧪 Testing QR Code Generation...")
        
        # Test 1: Basic QR code generation
        url = "https://example.com/test-form"
        print(f"📝 Generating QR code for: {url}")
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color='black', back_color='white')
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        print(f"✅ QR Code generated successfully!")
        print(f"📏 QR Code data length: {len(qr_base64)} characters")
        print(f"🔗 QR Code preview (first 50 chars): {qr_base64[:50]}...")
        
        # Test 2: Different error correction levels
        error_levels = ['L', 'M', 'Q', 'H']
        print(f"\n🔧 Testing different error correction levels:")
        
        for level in error_levels:
            level_const = {
                'L': qrcode.constants.ERROR_CORRECT_L,
                'M': qrcode.constants.ERROR_CORRECT_M,
                'Q': qrcode.constants.ERROR_CORRECT_Q,
                'H': qrcode.constants.ERROR_CORRECT_H,
            }[level]
            
            qr_test = qrcode.QRCode(
                version=1,
                error_correction=level_const,
                box_size=5,
                border=2,
            )
            qr_test.add_data(url)
            qr_test.make(fit=True)
            print(f"   ✅ Error correction level {level}: OK")
        
        print(f"\n🎉 All QR code tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ QR code test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 QR CODE FUNCTIONALITY TEST")
    print("=" * 60)
    
    success = test_qr_generation()
    
    if success:
        print("\n✅ QR code functionality is working correctly!")
        print("💡 The backend should be able to generate QR codes.")
    else:
        print("\n❌ QR code functionality has issues.")
        print("🔧 Check qrcode library installation.")
    
    print("=" * 60)
