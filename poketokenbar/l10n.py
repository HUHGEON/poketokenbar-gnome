"""UI strings in ko / en / ja / es — ports Localization.swift.

Strings are resolved in the daemon and shipped through state.json, so QML holds
no catalogue of its own. That keeps one source of truth and means changing the
language takes effect on the next poll without reloading the plasmoid.

Only strings the Linux UI actually renders are included; the Swift file also
covers macOS-only surfaces (Keychain, updater, support mail).
"""

from __future__ import annotations

LANGUAGES = ("en", "ko", "ja", "es")

# key: (en, ko, ja, es)
STRINGS: dict[str, tuple[str, str, str, str]] = {
    # tabs
    "home": ("Home", "홈", "ホーム", "Inicio"),
    "shop": ("Shop", "상점", "ショップ", "Tienda"),
    "bag": ("Bag", "가방", "バッグ", "Bolsa"),
    "collection": ("Collection", "컬렉션", "コレクション", "Colección"),
    "pokedex": ("Pokédex", "도감", "図鑑", "Pokédex"),
    "catch_log": ("Catch log", "포획 로그", "捕獲ログ", "Registro"),
    # today
    "todays_tokens": ("Today's tokens", "오늘의 토큰", "本日のトークン", "Tokens de hoy"),
    "this_week": ("This week", "이번 주", "今週", "Esta semana"),
    "this_month": ("This month", "이번 달", "今月", "Este mes"),
    # limits
    "limits_official": ("Limits (official)", "한도(공식)", "上限（公式）", "Límites (oficial)"),
    "five_hour_session": ("5-hour session", "5시간 세션", "5時間セッション", "Sesión de 5 horas"),
    "weekly": ("Weekly", "주간", "週間", "Semanal"),
    "resetting_now": ("resetting now", "지금 초기화 중", "リセット中", "reiniciando"),
    "limits_unavailable": (
        "Limits unavailable", "한도를 불러올 수 없음", "上限を取得できません",
        "Límites no disponibles",
    ),
    # companion
    "egg": ("Egg", "알", "タマゴ", "Huevo"),
    "final_form": ("Final form", "최종 형태", "最終形態", "Forma final"),
    "graduation": ("graduation", "졸업", "卒業", "graduación"),
    "next_evolution": ("next evolution", "다음 진화", "次の進化", "próxima evolución"),
    "shiny": ("Shiny", "이로치", "色違い", "Variocolor"),
    "raising": ("RAISING", "키우는 중", "育成中", "CRIANDO"),
    # status messages
    "status_idle": (
        "Keeping quiet today.", "오늘은 조용히 자리를 지켜요.", "今日は静かにしています。",
        "Hoy se mantiene tranquilo.",
    ),
    "status_working": (
        "Today's work is piling up.", "오늘의 작업 흔적이 쌓이고 있어요.",
        "本日の作業が積み重なっています。", "El trabajo de hoy se va acumulando.",
    ),
    "status_focus": (
        "In focus mode now.", "지금은 집중 모드예요.", "今は集中モードです。",
        "Ahora está en modo concentración.",
    ),
    "status_sleep": ("Sleeping now.", "지금은 자고 있어요.", "今は眠っています。", "Ahora está durmiendo."),
    "status_tired": (
        "Careful — the limit is close.", "조심해요 — 한도가 가까워요.", "注意 — 上限が近いです。",
        "Cuidado — el límite está cerca.",
    ),
    "status_egg": ("An egg is warming up.", "알이 따뜻해지고 있어요.", "タマゴが温まっています。", "Un huevo se está calentando."),
    "status_grew": ("It grew!", "성장했어요!", "成長しました！", "¡Ha crecido!"),
    # shop / bag
    "spendable_tokens": ("Spendable tokens", "사용 가능한 토큰", "使用可能なトークン", "Tokens disponibles"),
    "spend_hint": (
        "Spend the tokens you've used on items.", "사용한 토큰으로 아이템을 살 수 있어요.",
        "使ったトークンでアイテムを買えます。", "Gasta los tokens que has usado en objetos.",
    ),
    "buy": ("Buy", "구매", "購入", "Comprar"),
    "owned": ("Owned", "보유 중", "所持中", "En posesión"),
    "use": ("Use", "사용", "つかう", "Usar"),
    "active": ("Active", "적용 중", "適用中", "Activo"),
    "bag_empty": ("Your bag is empty.", "가방이 비어 있어요.", "バッグは空です。", "Tu bolsa está vacía."),
    "price": ("Price", "가격", "価格", "Precio"),
    "not_enough_tokens": ("Not enough tokens", "토큰이 부족해요", "トークンが足りません", "Tokens insuficientes"),
    # dex
    "no_pokemon_yet": (
        "No Pokémon caught yet!", "아직 잡은 포켓몬이 없어요!", "まだ捕まえたポケモンがいません！",
        "¡Aún no has capturado ninguno!",
    ),
    "legendary": ("Legendary", "전설", "伝説", "Legendario"),
    "rare": ("Rare", "희귀", "レア", "Raro"),
    "uncommon": ("Uncommon", "고급", "アンコモン", "Poco común"),
    "common": ("Common", "일반", "コモン", "Común"),
    # misc
    "refresh": ("Refresh", "새로고침", "更新", "Actualizar"),
    "stale_warning": (
        "Data is stale — is poketokend running?", "데이터가 오래됐어요 — poketokend 실행 중인가요?",
        "データが古いです — poketokend は動作中ですか？",
        "Datos obsoletos — ¿poketokend está en marcha?",
    ),
    "at_this_rate": ("at this rate, full at %1", "이 속도면 %1 에 도달", "このペースだと %1 に到達", "a este ritmo, lleno a las %1"),
}

_INDEX = {code: i for i, code in enumerate(LANGUAGES)}


def t(key: str, language: str = "en") -> str:
    """Resolve one string, falling back to English then to the key itself.

    Returning the key rather than an empty string makes a missing translation
    visible in the UI instead of silently blanking a label.
    """
    row = STRINGS.get(key)
    if row is None:
        return key
    index = _INDEX.get(language, 0)
    return row[index] or row[0]


def catalogue(language: str = "en") -> dict[str, str]:
    """Every string resolved for one language, for shipping in state.json."""
    return {key: t(key, language) for key in STRINGS}
