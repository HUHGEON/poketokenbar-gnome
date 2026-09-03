"""UI strings in en / ko / ja / es / fr / pt / de — ports Localization.swift.

Strings are resolved in the daemon and shipped through state.json, so QML holds
no catalogue of its own. That keeps one source of truth and means changing the
language takes effect on the next poll without reloading the plasmoid.

Only strings the Linux UI actually renders are included; the Swift file also
covers macOS-only surfaces (Keychain, updater, support mail).
"""

from __future__ import annotations

LANGUAGES = ("en", "ko", "ja", "es", "fr", "pt", "de")

# key: (en, ko, ja, es)
STRINGS: dict[str, tuple[str, ...]] = {
    # tabs
    "home": ("Home", "홈", "ホーム", "Inicio",
        'Accueil', 'Início', 'Start',
    ),
    "shop": ("Shop", "상점", "ショップ", "Tienda",
        'Boutique', 'Loja', 'Shop',
    ),
    "bag": ("Bag", "가방", "バッグ", "Bolsa",
        'Sac', 'Mochila', 'Beutel',
    ),
    "collection": ("Collection", "컬렉션", "コレクション", "Colección",
        'Collection', 'Coleção', 'Sammlung',
    ),
    "pokedex": ("Pokédex", "도감", "図鑑", "Pokédex",
        'Pokédex', 'Pokédex', 'Pokédex',
    ),
    "catch_log": ("Catch log", "포획 로그", "捕獲ログ", "Registro",
        'Journal', 'Registro', 'Fangliste',
    ),
    # today
    "todays_tokens": ("Today's tokens", "오늘의 토큰", "本日のトークン", "Tokens de hoy",
        'Jetons du jour', 'Tokens de hoje', 'Tokens heute',
    ),
    "this_week": ("This week", "이번 주", "今週", "Esta semana",
        'Cette semaine', 'Esta semana', 'Diese Woche',
    ),
    "this_month": ("This month", "이번 달", "今月", "Este mes",
        'Ce mois-ci', 'Este mês', 'Dieser Monat',
    ),
    # limits
    "limits_official": ("Limits (official)", "한도(공식)", "上限（公式）", "Límites (oficial)",
        'Limites (officiel)', 'Limites (oficial)', 'Limits (offiziell)',
    ),
    "five_hour_session": ("5-hour session", "5시간 세션", "5時間セッション", "Sesión de 5 horas",
        'Session de 5 heures', 'Sessão de 5 horas', '5-Stunden-Sitzung',
    ),
    "weekly": ("Weekly", "주간", "週間", "Semanal",
        'Hebdomadaire', 'Semanal', 'Wöchentlich',
    ),
    "resetting_now": ("resetting now", "지금 초기화 중", "リセット中", "reiniciando",
        'réinitialisation', 'reiniciando', 'wird zurückgesetzt',
    ),
    "limits_unavailable": (
        "Limits unavailable", "한도를 불러올 수 없음", "上限を取得できません",
        "Límites no disponibles",
        'Limites indisponibles', 'Limites indisponíveis', 'Limits nicht verfügbar',
    ),
    # companion
    "egg": ("Egg", "알", "タマゴ", "Huevo",
        'Œuf', 'Ovo', 'Ei',
    ),
    "final_form": ("Final form", "최종 형태", "最終形態", "Forma final",
        'Forme finale', 'Forma final', 'Endform',
    ),
    "graduation": ("graduation", "졸업", "卒業", "graduación",
        'diplôme', 'formatura', 'Abschluss',
    ),
    "next_evolution": ("next evolution", "다음 진화", "次の進化", "próxima evolución",
        'prochaine évolution', 'próxima evolução', 'nächste Entwicklung',
    ),
    "shiny": ("Shiny", "이로치", "色違い", "Variocolor",
        'Chromatique', 'Brilhante', 'Schillernd',
    ),
    "raising": ("RAISING", "키우는 중", "育成中", "CRIANDO",
        'EN ÉLEVAGE', 'CRIANDO', 'AUFZUCHT',
    ),
    # status messages
    "status_idle": (
        "Keeping quiet today.", "오늘은 조용히 자리를 지켜요.", "今日は静かにしています。",
        "Hoy se mantiene tranquilo.",
        "Il reste tranquille aujourd'hui.", 'Hoje está quietinho.', 'Heute bleibt es ruhig.',
    ),
    "status_working": (
        "Today's work is piling up.", "오늘의 작업 흔적이 쌓이고 있어요.",
        "本日の作業が積み重なっています。", "El trabajo de hoy se va acumulando.",
        "Le travail du jour s'accumule.", 'O trabalho de hoje vai se acumulando.', 'Die Arbeit von heute häuft sich.',
    ),
    "status_focus": (
        "In focus mode now.", "지금은 집중 모드예요.", "今は集中モードです。",
        "Ahora está en modo concentración.",
        'En mode concentration.', 'Agora em modo de foco.', 'Jetzt im Fokusmodus.',
    ),
    "status_sleep": ("Sleeping now.", "지금은 자고 있어요.", "今は眠っています。", "Ahora está durmiendo.",
        'Il dort en ce moment.', 'Está dormindo agora.', 'Es schläft gerade.',
    ),
    "status_tired": (
        "Careful — the limit is close.", "조심해요 — 한도가 가까워요.", "注意 — 上限が近いです。",
        "Cuidado — el límite está cerca.",
        'Attention — la limite approche.', 'Cuidado — o limite está perto.', 'Vorsicht — das Limit ist nah.',
    ),
    "status_egg": ("An egg is warming up.", "알이 따뜻해지고 있어요.", "タマゴが温まっています。", "Un huevo se está calentando.",
        'Un œuf se réchauffe.', 'Um ovo está esquentando.', 'Ein Ei wird warm.',
    ),
    "status_grew": ("It grew!", "성장했어요!", "成長しました！", "¡Ha crecido!",
        'Il a grandi !', 'Cresceu!', 'Es ist gewachsen!',
    ),
    # shop / bag
    "spendable_tokens": ("Spendable tokens", "사용 가능한 토큰", "使用可能なトークン", "Tokens disponibles",
        'Jetons disponibles', 'Tokens disponíveis', 'Verfügbare Tokens',
    ),
    "spend_hint": (
        "Spend the tokens you've used on items.", "사용한 토큰으로 아이템을 살 수 있어요.",
        "使ったトークンでアイテムを買えます。", "Gasta los tokens que has usado en objetos.",
        'Dépensez les jetons déjà utilisés en objets.', 'Gaste em itens os tokens que já usou.', 'Gib die verbrauchten Tokens für Items aus.',
    ),
    "buy": ("Buy", "구매", "購入", "Comprar",
        'Acheter', 'Comprar', 'Kaufen',
    ),
    "owned": ("Owned", "보유 중", "所持中", "En posesión",
        'En possession', 'Em posse', 'Im Besitz',
    ),
    "use": ("Use", "사용", "つかう", "Usar",
        'Utiliser', 'Usar', 'Benutzen',
    ),
    "active": ("Active", "적용 중", "適用中", "Activo",
        'Actif', 'Ativo', 'Aktiv',
    ),
    "bag_empty": ("Your bag is empty.", "가방이 비어 있어요.", "バッグは空です。", "Tu bolsa está vacía.",
        'Votre sac est vide.', 'Sua mochila está vazia.', 'Dein Beutel ist leer.',
    ),
    "price": ("Price", "가격", "価格", "Precio",
        'Prix', 'Preço', 'Preis',
    ),
    "not_enough_tokens": ("Not enough tokens", "토큰이 부족해요", "トークンが足りません", "Tokens insuficientes",
        'Jetons insuffisants', 'Tokens insuficientes', 'Nicht genug Tokens',
    ),
    # dex
    "no_pokemon_yet": (
        "No Pokémon caught yet!", "아직 잡은 포켓몬이 없어요!", "まだ捕まえたポケモンがいません！",
        "¡Aún no has capturado ninguno!",
        'Aucun Pokémon capturé !', 'Nenhum Pokémon capturado ainda!', 'Noch kein Pokémon gefangen!',
    ),
    "legendary": ("Legendary", "전설", "伝説", "Legendario",
        'Légendaire', 'Lendário', 'Legendär',
    ),
    "rare": ("Rare", "희귀", "レア", "Raro",
        'Rare', 'Raro', 'Selten',
    ),
    "uncommon": ("Uncommon", "고급", "アンコモン", "Poco común",
        'Peu commun', 'Incomum', 'Ungewöhnlich',
    ),
    "common": ("Common", "일반", "コモン", "Común",
        'Commun', 'Comum', 'Häufig',
    ),
    # misc
    "refresh": ("Refresh", "새로고침", "更新", "Actualizar",
        'Actualiser', 'Atualizar', 'Aktualisieren',
    ),
    "stale_warning": (
        "Data is stale — is poketokend running?", "데이터가 오래됐어요 — poketokend 실행 중인가요?",
        "データが古いです — poketokend は動作中ですか？",
        "Datos obsoletos — ¿poketokend está en marcha?",
        'Données obsolètes — poketokend tourne-t-il ?', 'Dados desatualizados — o poketokend está em execução?', 'Daten veraltet — läuft poketokend?',
    ),
    "at_this_rate": ("at this rate, full at %1", "이 속도면 %1 에 도달", "このペースだと %1 に到達", "a este ritmo, lleno a las %1",
        'à ce rythme, plein à %1', 'neste ritmo, cheio às %1', 'in diesem Tempo voll um %1',
    ),
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
    # A row shorter than LANGUAGES means a translation was left off. Fall back
    # to English rather than raising: a missing string must not take the whole
    # popover down with it. `test_every_row_covers_every_language` is what
    # actually stops that reaching a release.
    if index >= len(row):
        return row[0]
    return row[index] or row[0]


def catalogue(language: str = "en") -> dict[str, str]:
    """Every string resolved for one language, for shipping in state.json."""
    return {key: t(key, language) for key in STRINGS}
