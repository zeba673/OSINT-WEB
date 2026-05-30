import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
import pyotp
import qrcode
import qrcode.image.svg
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

from config import config

pwd_context = CryptContext(schemes=['pbkdf2_sha256'], deprecated='auto')

SESSION_TIMEOUT = 3600 * 24 * 7
CONFIDENTIAL_TIMEOUT = 900
serializer = URLSafeTimedSerializer(config.SECRET_KEY, salt='tracepoint-session')
conf_serializer = URLSafeTimedSerializer(config.SECRET_KEY, salt='tracepoint-confidential')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, pwd_hash: str) -> bool:
    return pwd_context.verify(password, pwd_hash)

def create_session_token(dni: str) -> str:
    return serializer.dumps({'dni': dni, 'time': datetime.utcnow().isoformat()})

def verify_session_token(token: str) -> str | None:
    try:
        data = serializer.loads(token, max_age=SESSION_TIMEOUT)
        return data.get('dni')
    except (SignatureExpired, BadSignature):
        return None

def create_confidential_token(user_id: int) -> str:
    return conf_serializer.dumps({'uid': user_id, 'time': datetime.utcnow().isoformat()})

def verify_confidential_token(token: str) -> int | None:
    try:
        data = conf_serializer.loads(token, max_age=CONFIDENTIAL_TIMEOUT)
        return data.get('uid')
    except (SignatureExpired, BadSignature):
        return None

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def get_totp_uri(secret: str, dni: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=dni, issuer_name='TracePoint'
    )

def generate_totp_qr_svg(secret: str, dni: str) -> str:
    uri = get_totp_uri(secret, dni)
    img = qrcode.make(uri, image_factory=qrcode.image.svg.SvgImage)
    return img.to_string().decode('utf-8')

def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code)
