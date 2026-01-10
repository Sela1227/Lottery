"""
SELA 樂透一路發 - VAPID 金鑰生成工具

執行方式: python scripts/generate_vapid.py

產生的金鑰請加入 Railway 環境變數：
- VAPID_PUBLIC_KEY
- VAPID_PRIVATE_KEY
- VAPID_EMAIL (可選，用於識別)
"""
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


def generate_vapid_keypair():
    """
    產生 VAPID 金鑰對
    
    Returns:
        tuple: (public_key, private_key) - 都是 URL-safe Base64 編碼
    """
    # 產生 ECDSA P-256 私鑰
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    
    # 取得公鑰
    public_key = private_key.public_key()
    
    # 序列化私鑰（DER 格式）
    private_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
    
    # 序列化公鑰（未壓縮格式）
    public_numbers = public_key.public_numbers()
    public_bytes = b'\x04' + \
        public_numbers.x.to_bytes(32, 'big') + \
        public_numbers.y.to_bytes(32, 'big')
    
    # URL-safe Base64 編碼
    private_b64 = base64.urlsafe_b64encode(private_bytes).rstrip(b'=').decode('ascii')
    public_b64 = base64.urlsafe_b64encode(public_bytes).rstrip(b'=').decode('ascii')
    
    return public_b64, private_b64


def main():
    print("=" * 60)
    print("🔐 VAPID 金鑰生成工具")
    print("=" * 60)
    print()
    
    public_key, private_key = generate_vapid_keypair()
    
    print("📋 請將以下環境變數加入 Railway：")
    print()
    print("-" * 60)
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print()
    print(f"VAPID_PRIVATE_KEY={private_key}")
    print()
    print(f"VAPID_EMAIL=admin@your-domain.com")
    print("-" * 60)
    print()
    print("⚠️  注意事項：")
    print("1. 私鑰請妥善保管，不要公開")
    print("2. 金鑰只需要生成一次")
    print("3. 更換金鑰後，所有用戶需要重新訂閱")
    print()
    print("✅ 金鑰生成完成！")


if __name__ == "__main__":
    main()
