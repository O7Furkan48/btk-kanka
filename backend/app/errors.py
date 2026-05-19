from fastapi import Request
from fastapi.responses import ORJSONResponse

class KankaError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status
        super().__init__(message)

HATA_MESAJLARI: dict[str, str] = {
    "urun_bulunamadi": "Böyle bir ürün bulunamadı.",
    "kategori_bulunamadi": "Bu kategori mevcut değil.",
    "gecersiz_beden": "Lütfen geçerli bir beden girin.",
    "boyKilo_eksik": "Boy ve kilo bilgisi gerekiyor.",
    "ai_hatasi": "Hımm, şu an cevap üretemedim, bir dakka sonra dener misin?",
    "db_hatasi": "Veritabanına ulaşılamadı, birazdan tekrar dene.",
    "kupon_gecersiz": "Bu kupon kodu geçerli değil veya süresi dolmuş.",
    "kupon_kullanildi": "Bu kuponu daha önce kullanmışsın.",
    "beden_tavsiye_yok": "Bu ürün için henüz yeterli beden verisi yok.",
    "benzer_urun_yok": "Bu ürüne benzer başka bir ürün bulunamadı.",
}

def kanka_error(code: str, status: int = 400) -> KankaError:
    msg = HATA_MESAJLARI.get(code, "Bir şeyler ters gitti, birazdan tekrar dene.")
    return KankaError(code=code, message=msg, status=status)

async def kanka_error_handler(request: Request, exc: KankaError) -> ORJSONResponse:
    return ORJSONResponse(
        status_code=exc.status,
        content={"hata": exc.code, "mesaj": exc.message},
    )
