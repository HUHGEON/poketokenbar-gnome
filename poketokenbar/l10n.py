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
    "todays_tokens": (
        "Today's tokens", "오늘 사용한 토큰", "本日のトークン", "Tokens de hoy",
        "Tokens du jour", "Tokens de hoje", "Heute verbrauchte Tokens",
    ),
    "this_week": ("This week", "이번 주", "今週", "Esta semana",
        'Cette semaine', 'Esta semana', 'Diese Woche',
    ),
    "this_month": ("This month", "이번 달", "今月", "Este mes",
        'Ce mois-ci', 'Este mês', 'Dieser Monat',
    ),
    # limits
    "limits_official": (
        "Limits (official)", "한도 (공식)", "上限（公式）", "Límites (oficial)",
        "Limites (officiel)", "Limites (oficiais)", "Limits (offiziell)",
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
    "spendable_tokens": (
        "Spendable tokens", "쓸 수 있는 토큰", "使えるトークン",
        "Tokens disponibles", "Tokens disponibles", "Tokens disponíveis",
        "Verfügbare Tokens",
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

    # --- front-end chrome ------------------------------------------------
    # Everything a front end puts on screen goes through here. Hardcoding
    # English in the UI is what left a Korean install reading entirely in
    # English even after the language had been set.
    "settings": ("Settings", "설정", "設定", "Ajustes", "Réglages", "Definições", "Einstellungen"),
    "open": ("Open", "열기", "開く", "Abrir", "Ouvrir", "Abrir", "Öffnen"),
    "quit": ("Quit", "종료", "終了", "Salir", "Quitter", "Sair", "Beenden"),
    "export_save": (
        "Export save", "세이브 내보내기", "セーブを書き出す", "Exportar partida",
        "Exporter la sauvegarde", "Exportar save", "Spielstand exportieren",
    ),
    "import_save": (
        "Import save", "세이브 불러오기", "セーブを読み込む", "Importar partida",
        "Importer la sauvegarde", "Importar save", "Spielstand importieren",
    ),
    "setting_tokens_in_panel": (
        "Tokens in the panel", "패널에 토큰 표시", "パネルにトークンを表示",
        "Tokens en el panel", "Jetons dans le panneau", "Tokens no painel",
        "Tokens in der Leiste",
    ),
    "setting_cost_in_panel": (
        "Cost in the panel", "패널에 비용 표시", "パネルに費用を表示",
        "Coste en el panel", "Coût dans le panneau", "Custo no painel",
        "Kosten in der Leiste",
    ),
    "setting_limits_in_panel": (
        "Limits in the panel", "패널에 한도 표시", "パネルに上限を表示",
        "Límites en el panel", "Limites dans le panneau", "Limites no painel",
        "Limits in der Leiste",
    ),
    "setting_limit_notifications": (
        "Notify on limit warnings", "한도 경고 알림", "上限警告を通知",
        "Avisar al acercarse al límite", "Alerter à l'approche de la limite",
        "Notificar avisos de limite", "Bei Limit-Warnungen benachrichtigen",
    ),
    "setting_companion_notifications": (
        "Notify on companion events", "포켓몬 이벤트 알림", "ポケモンのイベントを通知",
        "Avisar de eventos del compañero", "Alerter sur les événements du compagnon",
        "Notificar eventos do companheiro", "Bei Companion-Ereignissen benachrichtigen",
    ),
    "setting_status_checks": (
        "Check provider status", "서비스 장애 확인", "サービス障害を確認",
        "Comprobar estado del proveedor", "Vérifier l'état des services",
        "Verificar estado dos provedores", "Anbieterstatus prüfen",
    ),
    "setting_desktop_pet": (
        "Desktop pet", "데스크탑 펫", "デスクトップペット", "Mascota de escritorio",
        "Compagnon de bureau", "Mascote na área de trabalho", "Desktop-Begleiter",
    ),
    "setting_pet_bubbles": (
        "Pet speech bubbles", "펫 말풍선", "ペットの吹き出し", "Bocadillos de la mascota",
        "Bulles du compagnon", "Balões do mascote", "Sprechblasen des Begleiters",
    ),
    "setting_refresh_interval": (
        "Refresh interval", "새로고침 간격", "更新間隔",
        "Intervalo de actualización", "Intervalle d'actualisation",
        "Intervalo de atualização", "Aktualisierungsintervall",
    ),
    "setting_warn_threshold": (
        "Warn at (%)", "경고 임계값(%)", "警告のしきい値（%）", "Avisar al (%)",
        "Alerter à (%)", "Avisar em (%)", "Warnen bei (%)",
    ),
    "setting_crit_threshold": (
        "Critical at (%)", "위험 임계값(%)", "危険のしきい値（%）", "Crítico al (%)",
        "Critique à (%)", "Crítico em (%)", "Kritisch bei (%)",
    ),
    "setting_pet_size": (
        "Pet size (px)", "펫 크기(px)", "ペットの大きさ（px）", "Tamaño de la mascota (px)",
        "Taille du compagnon (px)", "Tamanho do mascote (px)", "Begleitergröße (px)",
    ),
    "setting_limit_display": (
        "Limits shown", "표시할 한도", "表示する上限", "Límites mostrados",
        "Limites affichées", "Limites exibidos", "Angezeigte Limits",
    ),
    "setting_animation": (
        "Animation", "애니메이션", "アニメーション", "Animación", "Animation",
        "Animação", "Animation",
    ),
    "setting_language": (
        "Language", "언어", "言語", "Idioma", "Langue", "Idioma", "Sprache",
    ),
    "setting_scan_folders": (
        "Extra scan folders", "추가 스캔 폴더", "追加スキャンフォルダ",
        "Carpetas adicionales", "Dossiers supplémentaires", "Pastas adicionais",
        "Zusätzliche Ordner",
    ),
    "scan_folders_hint": (
        "comma or newline separated, * allowed", "쉼표나 줄바꿈으로 구분, * 사용 가능",
        "カンマか改行で区切り、* 使用可", "separadas por comas o saltos de línea, * permitido",
        "séparés par des virgules ou des retours à la ligne, * autorisé",
        "separadas por vírgula ou quebra de linha, * permitido",
        "durch Komma oder Zeilenumbruch getrennt, * erlaubt",
    ),
    "limits_both": ("Both", "둘 다", "両方", "Ambos", "Les deux", "Ambos", "Beide"),
    "quality_saver": (
        "Power saver", "배터리 절약", "省電力", "Ahorro de energía",
        "Économie d'énergie", "Economia de energia", "Energiesparen",
    ),
    "quality_balanced": (
        "Balanced", "기본", "標準", "Equilibrado", "Équilibré", "Equilibrado", "Standard",
    ),
    "quality_smooth": (
        "Smooth", "부드럽게", "なめらか", "Suave", "Fluide", "Suave", "Flüssig",
    ),
    "waiting_for_daemon": (
        "Waiting for poketokend…", "poketokend 기다리는 중…", "poketokend を待っています…",
        "Esperando a poketokend…", "En attente de poketokend…",
        "Aguardando o poketokend…", "Warte auf poketokend…",
    ),
    "cannot_read_state": (
        "Cannot read state file", "상태 파일을 읽을 수 없음", "状態ファイルを読めません",
        "No se puede leer el archivo de estado", "Impossible de lire le fichier d'état",
        "Não foi possível ler o arquivo de estado", "Statusdatei nicht lesbar",
    ),
    "scanning": (
        "Scanning…", "스캔 중…", "スキャン中…", "Analizando…", "Analyse…",
        "Analisando…", "Scanne…",
    ),
    "updated_just_now": (
        "Updated just now", "방금 갱신", "たった今更新", "Actualizado ahora mismo",
        "Mis à jour à l'instant", "Atualizado agora mesmo", "Gerade aktualisiert",
    ),
    "updated_minutes_ago": (
        "Updated %1 min ago", "%1분 전 갱신", "%1分前に更新", "Actualizado hace %1 min",
        "Mis à jour il y a %1 min", "Atualizado há %1 min", "Vor %1 Min. aktualisiert",
    ),
    "species_count": (
        "%1 species", "%1종", "%1種", "%1 especies", "%1 espèces", "%1 espécies",
        "%1 Spezies",
    ),
    "catches_total": (
        "%1 total", "총 %1마리", "全%1匹", "%1 en total", "%1 au total",
        "%1 no total", "%1 insgesamt",
    ),
    "token_breakdown": (
        "in %1 · out %2 · cache w %3 · r %4",
        "입력 %1 · 출력 %2 · 캐시 쓰기 %3 · 읽기 %4",
        "入力 %1 · 出力 %2 · キャッシュ書込 %3 · 読込 %4",
        "entrada %1 · salida %2 · caché esc. %3 · lec. %4",
        "entrée %1 · sortie %2 · cache écr. %3 · lec. %4",
        "entrada %1 · saída %2 · cache esc. %3 · leit. %4",
        "Eingabe %1 · Ausgabe %2 · Cache-Schr. %3 · Les. %4",
    ),
    "plan": ("Plan", "플랜", "プラン", "Plan", "Forfait", "Plano", "Tarif"),
    "account": ("Account", "계정", "アカウント", "Cuenta", "Compte", "Conta", "Konto"),
    "setting_launch_at_login": (
        "Launch at login", "로그인 시 자동 시작", "ログイン時に自動起動",
        "Iniciar al arrancar sesión", "Lancer à l'ouverture de session",
        "Abrir ao iniciar sessão", "Bei der Anmeldung starten",
    ),
    "setting_limit_percent": (
        "Limit display", "한도 표시 방식", "上限の表示", "Visualización del límite",
        "Affichage de la limite", "Exibição do limite", "Limit-Anzeige",
    ),
    "percent_remaining": (
        "%1 left", "%1 남음", "残り%1", "%1 restante", "%1 restant", "%1 restante",
        "%1 übrig",
    ),
    "unit_day": ("%1d", "%1일", "%1日", "%1 d", "%1 j", "%1 d", "%1 T"),
    "unit_hour": ("%1h", "%1시간", "%1時間", "%1 h", "%1 h", "%1 h", "%1 Std."),
    "unit_minute": ("%1m", "%1분", "%1分", "%1 min", "%1 min", "%1 min", "%1 Min."),
    "unit_second": ("%1s", "%1초", "%1秒", "%1 s", "%1 s", "%1 s", "%1 Sek."),
    # --- shop and bag items ----------------------------------------------
    # Names, descriptions and effect hints. They used to be English-only dicts
    # in balance.py, so the shop and the bag stayed in English however the
    # language was set — every other string was translated around them.
    "item_rareCandy": (
        "Rare Candy", "이상한 사탕", "ふしぎなアメ", "Caramelo Raro", "Super Bonbon",
        "Doce Raro", "Sonderbonbon",
    ),
    "item_mint": ("Mint", "민트", "ミント", "Menta", "Menthe", "Menta", "Minze"),
    "item_shinyCharm": (
        "Shiny Charm", "이로치 부적", "ひかるおまもり", "Amuleto Iris", "Charme Chroma",
        "Amuleto Shiny", "Schillerpin",
    ),
    "item_desc_rareCandy": (
        "Raises your Pokemon's EXP by %1.", "현재 포켓몬의 경험치를 %1 올려줘요.",
        "ポケモンの経験値を%1上げます。", "Aumenta la experiencia de tu Pokemon en %1.",
        "Augmente l'EXP de ton Pokemon de %1.",
        "Aumenta a experiencia do seu Pokemon em %1.",
        "Gibt deinem aktuellen Pokemon %1 EP.",
    ),
    "item_desc_mint": (
        "Randomly changes your Pokemon's nature.",
        "현재 포켓몬의 성격을 랜덤으로 바꿔줘요.",
        "ポケモンのせいかくをランダムに変えます。",
        "Cambia aleatoriamente la naturaleza de tu Pokemon.",
        "Change aleatoirement la nature de ton Pokemon.",
        "Muda a natureza do seu Pokemon aleatoriamente.",
        "Andert das Wesen deines aktuellen Pokemon zufallig.",
    ),
    "item_desc_shinyCharm": (
        "While owned, raises the chance of hatching a shiny.",
        "보유하면 이로치 포켓몬이 태어날 확률이 올라가요.",
        "持っていると色違いが生まれる確率が上がります。",
        "Mientras lo tengas, aumenta la probabilidad de que nazca un Pokemon variocolor.",
        "Tant que tu le possedes, augmente les chances qu'un Pokemon chromatique eclose.",
        "Enquanto estiver na sua bolsa, aumenta a chance de nascer um Pokemon shiny.",
        "Erhoht im Beutel die Chance, dass ein schillerndes Pokemon schlupft.",
    ),
    "item_effect_rareCandy": (
        "+%1 XP", "+%1 XP", "+%1 XP", "+%1 XP", "+%1 XP", "+%1 XP", "+%1 EP",
    ),
    "item_effect_mint": (
        "Random nature", "성격 랜덤 변경", "せいかくランダム変更", "Naturaleza aleatoria",
        "Nature aleatoire", "Natureza aleatoria", "Zufalliges Wesen",
    ),
    "item_effect_shinyCharm": (
        "Shiny rate ↑ · active", "이로치 확률 ↑ · 적용 중", "色違い率↑ · 適用中",
        "Prob. variocolor ↑ · activo", "Taux chromatique ↑ · actif",
        "Chance shiny ↑ · ativo", "Schillerchance ↑ · aktiv",
    ),
    # The egg names are written out per language rather than composed from the
    # rarity word: Korean and English happen to work, Japanese does not
    # (レアのタマゴ against the natural レアなタマゴ).
    "egg_name": (
        "Pokemon Egg", "포켓몬 알", "ポケモンのタマゴ", "Huevo Pokemon", "Œuf Pokemon",
        "Ovo Pokemon", "Pokemon-Ei",
    ),
    "egg_name_uncommon": (
        "Uncommon Egg", "고급 알", "アンコモンのタマゴ", "Huevo poco comun",
        "Œuf peu commun", "Ovo incomum", "Ungewohnliches Ei",
    ),
    "egg_name_rare": (
        "Rare Egg", "희귀 알", "レアのタマゴ", "Huevo raro", "Œuf rare", "Ovo raro",
        "Seltenes Ei",
    ),
    "egg_name_legendary": (
        "Legendary Egg", "전설 알", "でんせつのタマゴ", "Huevo legendario",
        "Œuf legendaire", "Ovo lendario", "Legendares Ei",
    ),
    "egg_desc": (
        "Send off your current Pokemon and start fresh with a new egg.",
        "지금 포켓몬을 놓아주고 새 알로 다시 시작해요.",
        "いまのポケモンを手放して新しいタマゴからやり直します。",
        "Suelta a tu Pokemon actual y empieza de nuevo con un huevo nuevo.",
        "Laisse partir ton Pokemon actuel et repars de zero avec un nouvel œuf.",
        "Solte seu Pokemon atual e recomece com um ovo novo.",
        "Verabschiede dein aktuelles Pokemon und starte mit einem neuen Ei.",
    ),
    "egg_desc_tier": (
        "Send off your current Pokemon for an egg guaranteed to hatch %1 or better.",
        "지금 포켓몬을 놓아주고 %1 이상이 확정으로 나오는 알을 받아요.",
        "いまのポケモンを手放して %1 以上が確定で孵るタマゴをもらいます。",
        "Suelta a tu Pokemon actual y consigue un huevo garantizado de %1 o superior.",
        "Laisse partir ton Pokemon actuel pour un œuf garanti %1 ou mieux.",
        "Solte seu Pokemon atual e ganhe um ovo que garante %1 ou melhor.",
        "Verabschiede dein aktuelles Pokemon und erhalte ein Ei, aus dem garantiert %1 oder besser schlupft.",
    ),
    "egg_guarantee": (
        "%1 or better", "%1 이상 확정", "%1 以上確定", "%1 o superior garantizado",
        "%1 ou mieux garanti", "%1 ou melhor garantido", "Garantiert %1 oder besser",
    ),
    # --- natures ---------------------------------------------------------
    # The 25 natures. Absent from the catalogue entirely until now, so a
    # Korean install read "brave" beside a Pokemon whose every other label
    # was translated. Keyed by the id `balance.NATURES` stores.
    "nature_hardy": ("Hardy", "노력", "がんばりや", "Fuerte", "Hardi", "Esforçada", "Robust"),
    "nature_lonely": ("Lonely", "외로움", "さみしがり", "Huraña", "Solo", "Carente", "Solo"),
    "nature_brave": ("Brave", "용감", "ゆうかん", "Audaz", "Brave", "Corajosa", "Mutig"),
    "nature_adamant": ("Adamant", "고집", "いじっぱり", "Firme", "Rigide", "Teimosa", "Hart"),
    "nature_naughty": ("Naughty", "개구쟁이", "やんちゃ", "Pícara", "Mauvais", "Levada", "Frech"),
    "nature_bold": ("Bold", "대담", "ずぶとい", "Osada", "Assuré", "Ousada", "Kühn"),
    "nature_docile": ("Docile", "온순", "すなお", "Dócil", "Docile", "Dócil", "Sanft"),
    "nature_relaxed": ("Relaxed", "무사태평", "のんき", "Plácida", "Relax", "Descontraída", "Locker"),
    "nature_impish": ("Impish", "장난꾸러기", "わんぱく", "Agitada", "Malin", "Travessa", "Pfiffig"),
    "nature_lax": ("Lax", "촐랑", "のうてんき", "Floja", "Lâche", "Despreocupada", "Lasch"),
    "nature_timid": ("Timid", "겁쟁이", "おくびょう", "Miedosa", "Timide", "Medrosa", "Scheu"),
    "nature_hasty": ("Hasty", "성급", "せっかち", "Activa", "Pressé", "Apressada", "Hastig"),
    "nature_serious": ("Serious", "성실", "まじめ", "Seria", "Sérieux", "Séria", "Ernst"),
    "nature_jolly": ("Jolly", "명랑", "ようき", "Alegre", "Jovial", "Alegre", "Froh"),
    "nature_naive": ("Naive", "천진난만", "むじゃき", "Ingenua", "Naïf", "Ingênua", "Naiv"),
    "nature_modest": ("Modest", "조심", "ひかえめ", "Modesta", "Modeste", "Modesta", "Mäßig"),
    "nature_mild": ("Mild", "의젓", "おっとり", "Afable", "Doux", "Meiga", "Mild"),
    "nature_quiet": ("Quiet", "냉정", "れいせい", "Mansa", "Discret", "Discreta", "Ruhig"),
    "nature_bashful": ("Bashful", "수줍음", "てれや", "Tímida", "Pudique", "Tímida", "Zaghaft"),
    "nature_rash": ("Rash", "덜렁", "うっかりや", "Alocada", "Foufou", "Impulsiva", "Hitzig"),
    "nature_calm": ("Calm", "차분", "おだやか", "Serena", "Calme", "Calma", "Still"),
    "nature_gentle": ("Gentle", "얌전", "おとなしい", "Amable", "Gentil", "Gentil", "Zart"),
    "nature_sassy": ("Sassy", "건방", "なまいき", "Grosera", "Malpoli", "Atrevida", "Forsch"),
    "nature_careful": ("Careful", "신중", "しんちょう", "Cauta", "Prudent", "Cautelosa", "Sacht"),
    "nature_quirky": ("Quirky", "변덕", "きまぐれ", "Rara", "Bizarre", "Excêntrica", "Kauzig"),
    # --- hatches, evolutions, graduations --------------------------------
    # The celebration banner and the desktop notification share these. Both
    # were hardcoded English, so a Korean install was congratulated in English
    # at exactly the moments the app is trying to be charming.
    "notify_hatch_title": (
        "\U0001f95a Hatched!", "\U0001f95a 부화!", "\U0001f95a 孵化！",
        "\U0001f95a ¡Eclosionó!", "\U0001f95a Éclosion !", "\U0001f95a Chocou!",
        "\U0001f95a Geschlüpft!",
    ),
    "notify_hatch_body": (
        "%1 hatched from the egg!", "알에서 %1이(가) 나왔어요!",
        "タマゴから %1 が生まれました！", "¡%1 salió del huevo!",
        "%1 est sorti de l'œuf !", "%1 saiu do ovo!",
        "%1 ist aus dem Ei geschlüpft!",
    ),
    "notify_shiny_title": (
        "\u2728 Shiny Pokemon!", "\u2728 이로치 포켓몬!", "\u2728 色違いポケモン！",
        "\u2728 ¡Pokemon variocolor!", "\u2728 Pokemon chromatique !",
        "\u2728 Pokemon shiny!", "\u2728 Schillerndes Pokemon!",
    ),
    "notify_shiny_body": (
        "A shiny %1 hatched! (1 in %2)", "이로치 %1이(가) 태어났어요! (1/%2)",
        "色違いの %1 が生まれました！(1/%2)", "¡Nació un %1 variocolor! (1 entre %2)",
        "Un %1 chromatique est né ! (1 sur %2)", "Nasceu um %1 shiny! (1 em %2)",
        "Ein schillerndes %1 ist geschlüpft! (1/%2)",
    ),
    "notify_evolve_title": (
        "\u2728 Evolved!", "\u2728 진화!", "\u2728 進化！", "\u2728 ¡Evolucionó!",
        "\u2728 Évolution !", "\u2728 Evoluiu!", "\u2728 Entwicklung!",
    ),
    "notify_evolve_body": (
        "Evolved into %1!", "%1(으)로 진화했어요!", "%1 に進化しました！",
        "¡Evolucionó a %1!", "A évolué en %1 !", "Evoluiu para %1!",
        "Hat sich zu %1 entwickelt!",
    ),
    "notify_graduate_title": (
        "\U0001f393 Graduated!", "\U0001f393 졸업!", "\U0001f393 卒業！",
        "\U0001f393 ¡Graduado!", "\U0001f393 Diplômé !", "\U0001f393 Formatura!",
        "\U0001f393 Abschied!",
    ),
    "notify_graduate_body": (
        "%1 — saved to your Pokedex! A new egg has arrived.",
        "%1 — 도감에 보존! 새 알이 도착했어요.",
        "%1 — 図鑑に保存！新しいタマゴが届きました。",
        "%1 — ¡guardado en tu Pokedex! Ha llegado un nuevo huevo.",
        "%1 — conservé dans ton Pokedex ! Un nouvel œuf est arrivé.",
        "%1 — guardado na sua Pokedex! Chegou um novo ovo.",
        "%1 – in deinem Pokedex gespeichert! Ein neues Ei ist da.",
    ),
    "notify_ditto_title": (
        "\U0001f3ad Huh? It's Ditto!", "\U0001f3ad 어라? 메타몽!",
        "\U0001f3ad あれ？メタモン！", "\U0001f3ad ¿Eh? ¡Es Ditto!",
        "\U0001f3ad Hein ? C'est Métamorph !", "\U0001f3ad Ué? É um Ditto!",
        "\U0001f3ad Huch? Ditto!",
    ),
    "notify_ditto_body": (
        "You thought it was %1 — it was Ditto all along!",
        "%1인 줄 알았는데 — 사실은 메타몽이었어요!",
        "%1 だと思ってた… 実はメタモンでした！",
        "Pensabas que era %1 — ¡en realidad era Ditto!",
        "Tu croyais que c'était %1 — c'était Métamorph depuis le début !",
        "Você achava que era %1 — era um Ditto o tempo todo!",
        "Du dachtest, es wäre %1 – dabei war es die ganze Zeit Ditto!",
    ),
    "weekly_model": (
        "Weekly %1", "주간 %1", "週間 %1", "Semanal %1", "Hebdo %1", "Semanal %1",
        "%1 – wöchentlich",
    ),
    "claude_current_block": (
        "Claude current 5h block", "Claude 현재 5h 블록", "Claude 現在の5hブロック",
        "Bloque actual de 5h de Claude", "Bloc 5 h actuel de Claude",
        "Bloco atual de 5h do Claude", "Aktueller 5-Stunden-Block von Claude",
    ),
    "reset": ("reset", "리셋", "リセット", "reinicio", "réinit.", "reinício", "Reset"),
    "plan_label": (
        "Plan %1", "플랜 %1", "プラン %1", "Plan %1", "Forfait %1", "Plano %1", "Tarif %1",
    ),
    "account_label": (
        "Account %1", "계정 %1", "アカウント %1", "Cuenta %1", "Compte %1", "Conta %1",
        "Konto %1",
    ),
    "forecast_reach": (
        "At current rate, limit hit at %1", "현재 속도면 %1 한도 도달",
        "現在のペースで %1 に上限到達", "Al ritmo actual, límite alcanzado a las %1",
        "À ce rythme, limite atteinte à %1", "No ritmo atual, limite atingido às %1",
        "Bei diesem Tempo erreichst du das Limit um %1",
    ),
    "spendable_tokens_hint": (
        "Spend the tokens you have used on items.",
        "사용한 토큰으로 아이템을 살 수 있어요.",
        "使ったトークンでアイテムを買えます。",
        "Gasta los tokens que has usado en objetos.",
        "Dépense les jetons déjà utilisés en objets.",
        "Gaste os tokens já usados em itens.",
        "Gib die verbrauchten Tokens für Gegenstände aus.",
    ),
    "insufficient_tokens": (
        "Not enough tokens", "토큰이 부족해요", "トークンが足りません",
        "No hay tokens suficientes", "Jetons insuffisants", "Tokens insuficientes",
        "Nicht genug Tokens",
    ),
    "owned_now": ("Owned", "보유 중", "所持中", "En posesión", "Possédé", "Em posse", "Im Besitz"),
    "price": ("Price %1", "가격 %1", "価格 %1", "Precio %1", "Prix %1", "Preço %1", "Preis %1"),
    "graduation_remaining": (
        "%1 to graduation", "졸업까지 %1", "卒業まで %1", "%1 para graduarse",
        "%1 avant la remise de diplôme", "%1 para a formatura", "%1 bis zum Abschluss",
    ),
    "evolution_remaining": (
        "%1 to next evolution", "다음 진화까지 %1", "次の進化まで %1",
        "%1 para la próxima evolución", "%1 avant la prochaine évolution",
        "%1 para a próxima evolução", "%1 bis zur nächsten Entwicklung",
    ),
    "final_form": (
        "Final form", "최종 진화체", "最終進化形", "Forma final", "Forme finale",
        "Forma final", "Endform",
    ),
    "back": ("Back", "뒤로", "戻る", "Atrás", "Retour", "Voltar", "Zurück"),
    "general": ("General", "일반", "一般", "General", "Général", "Geral", "Allgemein"),
    "show_in_panel": (
        "Show in the panel", "메뉴바에 표시", "メニューバーに表示", "Mostrar en el panel",
        "Afficher dans le panneau", "Mostrar no painel", "In der Leiste anzeigen",
    ),
    "panel_all_off_hint": (
        "With all of these off only the character is shown",
        "전부 끄면 캐릭터만 표시됩니다",
        "すべてオフにするとキャラクターのみ表示されます",
        "Con todo desactivado solo se muestra el personaje",
        "Tout désactivé, seul le personnage est affiché",
        "Com tudo desligado só o personagem aparece",
        "Wenn alles aus ist, wird nur die Figur angezeigt",
    ),
    "floating_pet": (
        "Floating pet", "플로팅 펫", "フローティングペット", "Mascota flotante",
        "Compagnon flottant", "Mascote flutuante", "Schwebender Begleiter",
    ),
    "floating_pet_hint": (
        "The Pokemon floats above your screen — drag it to move it",
        "포켓몬이 화면 위에 떠 있어요 — 드래그로 위치를 옮길 수 있어요",
        "ポケモンが画面上に浮かびます — ドラッグで移動できます",
        "El Pokemon flota sobre la pantalla: arrástralo para moverlo",
        "Le Pokemon flotte sur l'écran — glisse-le pour le déplacer",
        "O Pokemon flutua sobre a tela — arraste para mover",
        "Das Pokemon schwebt über dem Bildschirm — zum Bewegen ziehen",
    ),
    "notifications": (
        "Notifications", "알림", "通知", "Notificaciones", "Notifications",
        "Notificações", "Benachrichtigungen",
    ),
    "size": ("Size", "크기", "サイズ", "Tamaño", "Taille", "Tamanho", "Größe"),
    "warn_at": ("Warning", "경고", "警告", "Aviso", "Alerte", "Aviso", "Warnung"),
    "crit_at": ("Critical", "임박", "危険", "Crítico", "Critique", "Crítico", "Kritisch"),
    "animation_hint": (
        "Smoother uses more battery", "부드러울수록 배터리를 더 씁니다",
        "なめらかにするほどバッテリーを消費します",
        "Cuanto más suave, más batería", "Plus c'est fluide, plus ça consomme",
        "Quanto mais suave, mais bateria", "Flüssiger verbraucht mehr Akku",
    ),
    "status_checks_hint": (
        "Shows Claude/OpenAI outages in the popup (not a notification)",
        "Claude·OpenAI 장애를 팝오버에 표시 (알림 아님)",
        "Claude・OpenAI の障害をポップオーバーに表示（通知ではありません）",
        "Muestra incidencias de Claude/OpenAI en el panel (sin notificar)",
        "Affiche les pannes Claude/OpenAI dans le panneau (sans notification)",
        "Mostra falhas do Claude/OpenAI no painel (sem notificação)",
        "Zeigt Claude/OpenAI-Störungen im Panel (keine Benachrichtigung)",
    ),
    "usage": ("Used", "사용량", "使用量", "Usado", "Utilisé", "Usado", "Verbraucht"),
    "remaining": ("Remaining", "남은 양", "残量", "Restante", "Restant", "Restante", "Verbleibend"),
    "representative": (
        "Representative Pokemon", "대표 포켓몬", "代表ポケモン", "Pokemon representativo",
        "Pokemon representatif", "Pokemon representativo", "Repräsentatives Pokemon",
    ),
    "follow_current": (
        "Follow the current Pokemon", "현재 포켓몬 따라가기", "現在のポケモンに従う",
        "Seguir al Pokemon actual", "Suivre le Pokemon actuel",
        "Seguir o Pokemon atual", "Dem aktuellen Pokemon folgen",
    ),
    "weekly_scoped": (
        "Weekly (scoped)", "주간 (모델별)", "週間（モデル別）", "Semanal (por modelo)",
        "Hebdo (par modèle)", "Semanal (por modelo)", "Wöchentlich (pro Modell)",
    ),
    "active_block": (
        "current 5h block", "현재 5h 블록", "現在の5h ブロック", "bloque actual de 5 h",
        "bloc de 5 h en cours", "bloco atual de 5 h", "aktueller 5-Std.-Block",
    ),
    "resets_in": (
        "resets in %1", "리셋 %1", "%1 後にリセット", "se reinicia en %1",
        "réinitialisation dans %1", "reinicia em %1", "Reset in %1",
    ),
    "no_limit_before_reset": (
        "will not reach the limit before it resets",
        "현재 속도로는 리셋 전 한도 도달 없음",
        "現在のペースではリセット前に上限に達しません",
        "a este ritmo no se alcanzará el límite antes del reinicio",
        "à ce rythme, la limite ne sera pas atteinte avant la réinitialisation",
        "neste ritmo o limite não será atingido antes do reinício",
        "erreicht das Limit vor dem Reset nicht",
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


def system_default(preferred: str | None = None) -> str:
    """The language to start in — ports AppLanguage.systemDefault.

    A fresh install defaulting to English left a Korean user reading English
    until they found the setting, which most people will not go looking for.
    Matched on the first two letters, as upstream does: "ko_KR.UTF-8",
    "ko-KR" and "ko" all mean the same thing.

    The environment is consulted in POSIX order, then Windows' own UI language.
    `locale.getdefaultlocale` is deliberately not used: it is deprecated, and on
    Windows it reports the *format* locale, which someone can set to Korean
    dates while running an English interface — or the reverse.
    """
    candidates = []
    if preferred:
        candidates.append(preferred)
    else:
        import os

        for name in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
            value = (os.environ.get(name) or "").strip()
            if value and value not in ("C", "POSIX"):
                candidates.append(value)
        candidates.append(_windows_ui_language() or "")

    for candidate in candidates:
        code = candidate.replace("-", "_").split("_")[0].split(".")[0].lower()
        if code in LANGUAGES:
            return code
    return "en"


def _windows_ui_language() -> str | None:
    """The Windows *interface* language, or None anywhere else.

    Wrapped in its own function so the import cost and the failure are both
    contained: this is called once, at first run, and a machine without the DLL
    should get English rather than a traceback.
    """
    try:
        import ctypes

        lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()  # type: ignore[attr-defined]
        import locale

        return locale.windows_locale.get(lcid)
    except Exception:
        return None


# Each language written in itself. Someone who has landed on the wrong one has
# to recognise theirs, and "ko" in a list of two-letter codes is not something
# to recognise — which is what the language dropdown actually showed.
LANGUAGE_NAMES = {
    "en": "English",
    "ko": "한국어",
    "ja": "日本語",
    "es": "Español",
    "fr": "Français",
    "pt": "Português",
    "de": "Deutsch",
}
