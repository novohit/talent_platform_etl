import hmac
import hashlib
import urllib.parse
import json
import time

class SignatureUtils:
    SIGNATURE = "signature"
    EXPIRES = "expires"
    CLIENT_ID = "client_id"

    @staticmethod
    def get_max_signature(client_id, client_secret, request_path, expires):
        if not request_path.startswith("/"):
            request_path = "/" + request_path
        params = {
            SignatureUtils.CLIENT_ID: client_id,
            SignatureUtils.EXPIRES: expires
        }
        data = f"{request_path}?{SignatureUtils.k_string(params)}"
        return SignatureUtils.sha256_hmac(data, client_secret)

    @staticmethod
    def k_string(params):
        # 按 key 排序
        items = sorted(params.items())
        # 拼接成 key=value&key2=value2
        s = "&".join(f"{k}={v}" for k, v in items)
        # URL 编码
        s = urllib.parse.quote(s, safe='')
        s = s.replace("%3D", "=").replace("%26", "&").replace("+", "%20")
        return s

    @staticmethod
    def sha256_hmac(data, secret):
        h = hmac.new(secret.encode(), data.encode(), hashlib.sha256)
        return h.hexdigest().lower()

    @staticmethod
    def generate_signature_object(client_id, client_secret, request_path, expires):
        signature = SignatureUtils.get_max_signature(client_id, client_secret, request_path, expires)
        return {
            "client_id": client_id,
            "expires": expires,
            "signature": signature
        }

# PYTHONPATH=/Users/novo/code/python/talent_platform_etl uv run scripts/signature_utils/signature_util.py
if __name__ == "__main__":
    client_id = "66PFDYeAO840PMty"
    client_secret = "2NbJS9rhYIs7rTmtBf8SUsVgTwZyH0uI"
    request_path = "/api/oauth/token"
    valid_seconds = 3600  # 签名有效时间（秒）
    expires = str(int(time.time()) + valid_seconds)
    signature_obj = SignatureUtils.generate_signature_object(client_id, client_secret, request_path, expires)
    print(json.dumps(signature_obj, ensure_ascii=False))