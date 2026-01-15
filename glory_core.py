# glory_core.py
# (Tkinter 없는) 원본 로직 코어만 분리본

import json
import random
import re
import datetime
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

GEMINI_MODEL = "gemini-2.5-pro"

# Gemini Developer API pricing (per 1M tokens, USD)
PRICE_INPUT_PER_1M_LE_200K = 1.25
PRICE_OUTPUT_PER_1M_LE_200K = 10.00
PRICE_INPUT_PER_1M_GT_200K = 2.50
PRICE_OUTPUT_PER_1M_GT_200K = 15.00

DEFAULT_USD_TO_KRW = 1350.0

# -----------------------------
# Boards and topics (A~E)
# -----------------------------
BOARD_OPTIONS: List[Tuple[str, str]] = [
    ("A", "1. 안경이 불편해요? (불편/증상 해결)"),
    ("B", "2. 렌즈 선택전 필독 (렌즈 선택/비교)"),
    ("C", "3. 노안에 대하여! (노안/연령별)"),
    ("D", "4. 피팅! 내 눈에 맞춤 (피팅/정밀)"),
    ("E", "5. 안경 오래쓰려면? (관리/생활)"),
]

TOPICS: Dict[str, List[str]] = {
    "A": [
        "새 안경 쓰면 어지러운 이유(적응 vs 문제)",
        "새 안경 쓰면 두통 생기는 원인 체크리스트",
        "안경 쓰면 울렁거리거나 멀미 나는 이유",
        "도수는 맞는데 불편한 경우에 흔한 원인 5가지",
        "한쪽만 더 흐릿하게 보일 때(도수/난시축/중심)",
        "계단 내려갈 때 바닥이 울렁거리는 이유와 해결",
        "야간 운전 시 빛 번짐(헤일로) 줄이는 방법",
        "사물이 휘어 보이거나 왜곡돼 보이는 이유",
        "안경만 쓰면 눈이 빨리 피로한 이유(렌즈/습관)",
        "가까이 볼 때 유독 피곤한 이유(노안/조절/세팅)",
        "안경 쓰면 눈이 따갑거나 눈물이 나는 이유",
        "안경 쓰면 눈이 더 건조한 느낌이 드는 이유(환경/깜박임)",
        "스마트폰 볼 때 유독 피곤한 사람의 렌즈/세팅 팁",
        "난시 교정 후 선이 기울어 보이는 느낌의 원인",
        "PD(동공거리) 오차가 생기면 나타나는 증상(두통·어지러움)",
        "과교정 vs 저교정: 증상으로 구분하는 법",
        "안경 쓰면 물체가 작거나 크게 느껴질 때(확대/축소감)",
        "멀리는 괜찮은데 중간거리(컴퓨터)만 불편한 이유",
        "집중이 안 되고 눈이 긴장되는 느낌의 원인",
        "렌즈 색이 누렇게/푸르게 느껴지는 이유(코팅/착색)",
        "렌즈에서 무지개빛이 보이는 이유(반사·코팅)",
        "렌즈가 자주 뿌옇게 되는 원인(유막/코팅/세척)",
        "렌즈에 물때·유막이 반복되는 습관 7가지",
        "렌즈에 미세 크랙(실금)이 생기는 이유(온도·충격)",
        "코팅 벗겨짐: 교체 타이밍과 예방 루틴",
    ],
    "B": [
        "렌즈 가격 차이의 정체(설계·코팅·굴절률)",
        "굴절률 1.56/1.60/1.67/1.74: 누구에게 유리한가",
        "고도근시 렌즈 얇게 만드는 핵심(설계+프레임)",
        "난시 있으면 렌즈 선택이 달라지는 이유",
        "비구면 렌즈란? 체감되는 경우/안 되는 경우",
        "내면비구면·양면비구면·자유곡면, 쉽게 비교하기",
        "반사방지 코팅이 중요한 사람(운전/야간/화면)",
        "발수·방오 코팅이 값 하는 생활패턴은?",
        "자외선 차단 렌즈: UV400 확인법과 오해",
        "블루라이트 렌즈: 도움 되는 경우 vs 기대 내려야 할 경우",
        "디지털 작업용 렌즈 설계(사무용)란 무엇인가",
        "변색렌즈(자동 선글라스) 장단점(실사용 기준)",
        "선글라스 렌즈 색(회색/갈색/그린) 선택 가이드",
        "편광렌즈: 운전·낚시에서 좋은 이유 + 주의점",
        "야간 운전용 옐로우 렌즈, 실제로 도움이 될까?",
        "렌즈 농도(진하기) 선택: 실내용/야외용 기준",
        "미러 코팅은 기능일까? 디자인일까?",
        "큰 프레임이 어지러울 수 있는 이유(왜곡·주변부)",
        "렌즈 무게 줄이는 3요소(재질·설계·사이즈)",
        "폴리카보네이트 vs 트라이벡스: 충격·선명도 비교",
        "스포츠·현장직 추천 렌즈 세팅(안전/내구)",
        "어린이 렌즈: 안전·내구성 체크포인트 5개",
        "피부 예민한 사람: 코팅/소재 선택 시 주의",
        "렌즈 교체만 할 때 꼭 확인해야 할 6가지",
        "기스가 잘 나는 렌즈를 피하는 코팅/관리 조합",
        "안경 렌즈 도수·프레임 크기·왜곡의 관계",
        "고도도수인데 큰 알 고르면 생길 수 있는 불편",
        "근거리 작업 많은 사람 렌즈 세팅(독서/공부/디자인)",
        "야외 활동 많은 사람 렌즈 세팅(자외선/반사/편광)",
        "실내 조명(LED)에서 눈부심 심한 사람 렌즈 팁",
    ],
    "C": [
        "40대부터 가까운 글씨가 흐린 이유(노안 시작 신호)",
        "돋보기 vs 누진 vs 사무용 누진: 선택 기준",
        "누진렌즈 적응이 힘든 대표 이유 5가지",
        "누진렌즈 첫 구매 실패 줄이는 체크리스트",
        "누진렌즈 적응 훈련(집/회사/운전 상황별)",
        "누진렌즈가 어지러우면 조정 가능한 요소들(높이·피팅 등)",
        "중간거리(컴퓨터)가 불편한 누진 사용자 해결법",
        "사무용 전용 누진이 필요한 사람의 특징",
        "노안+난시 함께 있을 때 렌즈 선택 전략",
        "원시(멀리도 흐림) + 노안이 섞일 때 느끼는 증상",
        "학생 첫 안경: 교체 주기와 도수 변화 체크 포인트",
        "성장기 근시 진행을 늦추는 생활 습관(안경원 조언 범위)",
        "아이가 찡그리고 가까이 보는 행동: 검사 신호 정리",
        "시력이 갑자기 떨어졌을 때(안경? 안과?) 판단 가이드",
        "공부할 때만 불편한 학생을 위한 렌즈/피팅 점검",
    ],
    "D": [
        "PD(동공거리)란? 왜 mm 오차가 불편을 만드는가",
        "렌즈 광학중심이 어긋나면 생길 수 있는 증상들",
        "같은 도수인데 안경점마다 느낌이 다른 이유(측정·가공·피팅)",
        "피팅(안경 조정)만으로 해결되는 불편 7가지",
        "코받침 자국/통증 줄이는 피팅 팁",
        "귀가 아픈 안경: 원인(템플 각도/장력)과 해결",
        "안경이 흘러내리는 이유(무게중심·코받침·다리 길이)",
        "안경이 자꾸 돌아가는 이유와 해결",
        "마스크 쓰면 안경이 더 아픈 이유(템플+귀 압박)",
        "안경이 커 보이는 이유: 프레임 폭/브리지/피팅",
        "얼굴형별 프레임 추천(둥근/각진/긴 얼굴)",
        "작은 얼굴/큰 얼굴: 프레임 고르는 기준(폭/브리지)",
        "코가 낮은 사람에게 편한 안경 고르는 법(아시안핏)",
        "무테/반무테/뿔테: 내구성·관리 난이도 비교",
        "티타늄 프레임이 비싼 이유(가벼움/내구성/알레르기)",
        "고도근시가 피해야 할 프레임 형태(두께·왜곡)",
        "운동할 때 안경이 미끄러운 이유와 해결(피팅/밴드/고글)",
        "안경이 자꾸 눈썹에 닿는 문제 해결법",
        "렌즈 두께가 신경 쓰일 때 프레임 선택 3원칙",
        "피팅 전/후 차이를 체감하기 쉬운 체크 포인트",
    ],
    "E": [
        "안경 세척 정답 루틴(물+중성세제+건조)",
        "안경닦이·티슈·알코올: 코팅에 위험한 것들",
        "렌즈에 기스가 잘 나는 사람의 공통 습관 7가지",
        "초음파 세척기: 도움 되는 경우 vs 피해야 할 경우",
        "김서림 방지 실전(마스크 착용 상황별)",
        "여름 땀·선크림 때문에 렌즈가 더러워지는 이유와 관리",
        "콘택트렌즈 오래 끼면 뻑뻑한 이유(착용 시간/건조)",
        "렌즈 세척액/케이스 관리: 교체 주기와 금지 행동",
        "차 안/사우나/고온에서 안경 보관하면 생기는 문제",
        "운전·여행·캠핑에서 안경 관리 팁(스크래치/먼지/염분)",
    ],
}

# -----------------------------
# Writers
# -----------------------------
WRITER_OPTIONS = [
    "금손 원장(60대 중반, 여성)",
    "조원장(40대 중반, 남성)",
    "장실장(40대 중반, 피팅 전문가)",
    "땡글이(20대 초반, 안경사)",
]

WRITER_KEY_MAP = {
    WRITER_OPTIONS[0]: "금손 원장",
    WRITER_OPTIONS[1]: "조원장",
    WRITER_OPTIONS[2]: "장실장",
    WRITER_OPTIONS[3]: "땡글이",
}

SPECIAL_WHO_OPTIONS = ["금손 원장", "조원장", "장실장", "땡글이"]

WRITER_VOICES: Dict[str, str] = {
    "금손 원장": (
        "말투: 60대 중반 베테랑. "
        "시원시원하고 직설적이지만 정이 많음. "
        "욕은 절대 하지 않음. "
        "주로 해요체. "
        "가끔 짧은 감탄사(아유, 자, 봐요). "
        "불편을 참지 말라고 챙겨주는 '왕언니' 느낌. "
        "과장 광고는 절대 하지 않음."
    ),
    "조원장": (
        "말투: 차분하고 지적. "
        "주로 합니다체 또는 하세요체. "
        "원인-기준-해결 순서로 정리. "
        "근거 없는 단정은 피하고, "
        "가능성/확인 포인트를 분명히 제시."
    ),
    "장실장": (
        "말투: 나긋나긋하고 전문적. "
        "피팅/가공/측정 디테일을 "
        "쉽게 풀어 설명. "
        "해드릴게요, 한번 봐드릴게요 같은 표현. "
        "고객 입장에서 불편을 공감."
    ),
    "땡글이": (
        "말투: 젊고 쾌활함. "
        "현장에서 배운 걸 공유하는 느낌. "
        "가끔 ㅎㅎ, 아... 같은 표현을 쓰되 과하지 않게. "
        "문장은 짧고 경쾌하게."
    ),
}

INTRO_GREETING_BLOCKS: Dict[str, List[Tuple[str, str]]] = {
    "금손 원장": [
        ("금손 원장이에요.", "아유, 불편한 건 말해요."),
        ("금손 원장입니다.", "그걸 왜 참고 있어요, 자."),
        ("저는 금손 원장이에요.", "이리 와 봐요, 제가 봐요."),
        ("금손 원장이에요.", "괜히 참으면 손해예요."),
        ("금손 원장 왔어요.", "오늘도 편하게 얘기해요."),
    ],
    "조원장": [
        ("조원장입니다.", "오늘은 기준부터 정리하죠."),
        ("저는 조원장이에요.", "원인부터 차근히 봅니다."),
        ("조원장입니다.", "확인 포인트만 딱 짚을게요."),
        ("조원장입니다.", "결론보다 과정이 중요합니다."),
    ],
    "장실장": [
        ("장실장입니다.", "불편한 곳, 차근히 봐드릴게요."),
        ("저는 장실장이에요.", "피팅은 작은 차이가 큽니다."),
        ("장실장입니다.", "편하게 말씀해 주세요."),
        ("장실장입니다.", "조정은 제가 도와드릴게요."),
    ],
    "땡글이": [
        ("땡글이 안경사예요 ㅎㅎ", "오늘은 딱 핵심만요!"),
        ("땡글이입니다.", "짧게, 실전 팁만 드릴게요."),
        ("저는 땡글이예요.", "학생들 불편, 진짜 많아요."),
        ("땡글이예요 ㅎㅎ", "부담 없이 같이 맞춰봐요."),
    ],
}

TRUST_BITS = [
    "20년 넘게 한 자리에서 운영",
    "주민분들이 자주 들르는 편",
    "학생 안경은 예산부터 맞춤",
    "학부모님 상담이 많은 편",
    "사후 조정은 꼭 봐드림",
    "필요 없는 옵션은 권하지 않음",
    "가격은 부담되지 않게 맞춤",
    "렌즈 중심과 피팅을 꼼꼼히 봄",
    "가공 후 확인을 한번 더 함",
]

CHARACTER_CARDS = [
    {"who":"한복이 곱던 할머님","detail":"고름 색이 참 예뻤어요","moment":"괜히 자세가 단정해져요","line":"한복엔 어떤 테가 예뻐요?"},
    {"who":"양복이 멋진 할아버님","detail":"넥타이가 반짝였어요","moment":"말수가 적어 더 멋있죠","line":"너무 번쩍이면 싫어요"},
    {"who":"운동복의 몸짱 아버님","detail":"어깨가 문보다 넓어 보여요","moment":"특전사 같은 느낌이 딱","line":"가벼운 걸로 부탁해요"},
    {"who":"머리결 찰랑한 숙녀분","detail":"머리카락이 조명처럼 반짝","moment":"모델 같다고 말이 나와요","line":"저 머리 관리 비법이요?"},
    {"who":"힙합 스타일 대학생","detail":"모자 챙이 낮았어요","moment":"거울 앞에서 각도 찾기","line":"이거 완전 제 감성인데요"},
    {"who":"헤어가 튀는 남학생","detail":"펌이 꽤 과감했어요","moment":"친구들이 옆에서 킥킥","line":"쌤 저 안경 바꾸면 멋져요?"},
    {"who":"우르르 온 남학생들","detail":"서로 장난치며 들어왔죠","moment":"가게가 갑자기 체육관","line":"와 여기 에어컨 천국이다"},
    {"who":"무리지어 온 여학생들","detail":"거울 앞에서 옹기종기","moment":"취향이 다 달라 재밌죠","line":"이 테, 사진 잘 나와요?"},
    {"who":"아버님과 따님","detail":"아빠가 더 긴장한 표정","moment":"따님이 웃으며 쓱 봐줘요","line":"아빠, 이게 더 어려 보여"},
    {"who":"어머님과 아드님","detail":"엄마 손이 더 빠르죠","moment":"아들은 조용히 고개 끄덕","line":"엄마가 고르라 했어요"},
    {"who":"어머님과 따님","detail":"둘이 말투가 꼭 닮았어요","moment":"눈웃음이 같이 번져요","line":"엄마 이거 완전 우리 취향"},
    {"who":"아버님과 아드님","detail":"둘 다 말이 짧고 단정","moment":"괜히 고개가 끄덕여져요","line":"이거로 주세요. 깔끔하게"},
    {"who":"정장 차림 직장인","detail":"점심시간에 뛰어왔어요","moment":"숨 고르고 앉는 그 3초","line":"회의 전에 딱 맞춰야 해요"},
    {"who":"교복 단정한 학생","detail":"단추까지 반듯했어요","moment":"눈은 바쁘고 말은 짧죠","line":"공부할 때만 어지러워요"},
]

EVENT_CARDS = [
    {"event":"거래처랑 단가 실랑이","detail":"원가표 붙잡고 계산기 두드림","moment":"마지막엔 웃으며 악수","line":"조금만 더 맞춰주세요"},
    {"event":"렌즈 입고날 재고 정리","detail":"박스가 산처럼 쌓였어요","moment":"스티커 붙이며 땀","line":"이건 학생용으로 빼두자"},
    {"event":"눈 오는 날 가게 앞 정리","detail":"미끄러울까 봐 먼저 쓸었죠","moment":"빗자루가 오늘의 동료","line":"조심히 오세요, 길 미끄러워요"},
    {"event":"낙엽 많은 날 청소","detail":"문 열기 전에 한 번 쓱","moment":"바람이 또 흩뿌리죠","line":"아… 또 쌓였네"},
    {"event":"가공기 잠깐 말썽","detail":"삐- 소리에 가슴이 철렁","moment":"확인하고 다시 침착","line":"잠깐만요, 바로 볼게요"},
    {"event":"직원끼리 미니 교육","detail":"PD 재는 순서 다시 점검","moment":"한 번 더, 또 한 번","line":"mm는 진짜 무시 못 해요"},
]

def escape_html(s: str) -> str:
    return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;"))

def wrap_html(title: str, body: str) -> str:
    safe_title = title.strip() if title else ""
    safe_body = body.replace("\r\n", "\n")
    return (
        "<!doctype html>\n<html lang='ko'>\n<head>\n<meta charset='utf-8'>\n"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>\n"
        "<title>"+escape_html(safe_title)+"</title>\n<style>\n"
        "body{font-family:system-ui,Apple SD Gothic Neo,Malgun Gothic,sans-serif;}\n"
        ".wrap{max-width:760px;margin:24px auto;padding:0 16px;}\n"
        "h1{font-size:20px;line-height:1.3;margin:0 0 12px;}\n"
        "pre{white-space:pre-wrap;word-break:break-word;font-size:15px;line-height:1.65;margin:0;}\n"
        "</style>\n</head>\n<body>\n<div class='wrap'>\n"
        "<h1>"+escape_html(safe_title)+"</h1>\n"
        "<pre>"+escape_html(safe_body)+"</pre>\n"
        "</div>\n</body>\n</html>\n"
    )

def first_nonempty_line(text: str) -> str:
    for ln in text.replace("\r\n","\n").split("\n"):
        if ln.strip():
            return ln.strip()
    return ""

def pick_trust_bits(k: int = 2) -> List[str]:
    k = max(1, min(3, k))
    return random.sample(TRUST_BITS, k)

def sample_cards(cards: List[Dict], k: int) -> List[Dict]:
    if not cards: return []
    k = max(1, min(k, len(cards)))
    return random.sample(cards, k)

def cards_to_prompt_lines(prefix: str, cards: List[Dict], keys: List[str]) -> str:
    out = [prefix]
    for i, c in enumerate(cards, start=1):
        parts = []
        for kk in keys:
            if kk in c and c[kk]:
                parts.append(f"{kk}={c[kk]}")
        out.append(f"- 카드{i}: " + " / ".join(parts))
    return "\n".join(out)

def pick_greeting_block(writer_key: str) -> Tuple[str, str]:
    blocks = INTRO_GREETING_BLOCKS.get(writer_key) or []
    if not blocks:
        return ("안녕하세요.", "오늘도 편하게 읽어주세요.")
    return random.choice(blocks)

def writer_name_variants(writer_key: str) -> List[str]:
    base = (writer_key or "").strip()
    if not base:
        return []
    variants = {base, base.replace(" ", "")}
    return [v for v in variants if v]

def ensure_topic_in_title_line(text: str, topic: str) -> str:
    cleaned = text.replace("\r\n","\n")
    lines = cleaned.split("\n")
    title_idx = None
    for i, ln in enumerate(lines):
        if ln.strip():
            title_idx = i
            break
    if title_idx is None:
        return text
    title = lines[title_idx].strip()

    topic_core = topic.split("(")[0].strip() if topic else ""
    words = topic_core.split()
    if len(words) >= 2:
        key = (words[0] + " " + words[1]).strip()
    elif len(words) == 1:
        key = words[0].strip()
    else:
        key = topic_core.strip()
    key = key[:12].strip()
    if not key or key in title:
        return text

    new_title = (key + " " + title).strip()
    if len(new_title) > 30:
        new_title = new_title[:30].rstrip()
    lines[title_idx] = new_title
    return "\n".join(lines)

# -----------------------------
# Auto-fix (검수 안정화)
# -----------------------------
_FORBIDDEN_REPLACEMENTS = [
    ("```",""),("###",""),("**",""),("__",""),
    ("ChatGPT",""),("챗GPT",""),("AI가 쓴",""),("AI가쓴",""),
    ("A원장","금손 원장"),("A 원장","금손 원장"),
    ("B원장","조원장"),("B 원장","조원장"),
]

def _normalize_newlines(s: str) -> str:
    return (s or "").replace("\r\n","\n").replace("\r","\n")

def _remove_forbidden_tokens(s: str) -> str:
    s = _normalize_newlines(s)
    for a, b in _FORBIDDEN_REPLACEMENTS:
        if a in s:
            s = s.replace(a, b)
    s = re.sub(r"</?table[^>]*>", "", s, flags=re.IGNORECASE)
    return s

_WEIRD_SELF_REF_RE = re.compile(r"(금손\s*원장|조원장|장실장|땡글이)\s*인\s*제가\s*보기에도")
_WEIRD_SELF_REF_RE2 = re.compile(r"(금손\s*원장|조원장|장실장|땡글이)\s*인\s*제가")

def _fix_weird_self_reference(s: str) -> str:
    s = _WEIRD_SELF_REF_RE.sub("제가 확인해봐도", s)
    s = _WEIRD_SELF_REF_RE2.sub("제가", s)
    return s

def _limit_interjections(s: str, writer_key: str) -> str:
    s = _normalize_newlines(s)
    if s.count("ㅎㅎ") > 1:
        first = s.find("ㅎㅎ")
        s = s[:first+2] + s[first+2:].replace("ㅎㅎ","")
    if writer_key != "땡글이":
        s = s.replace("ㅋㅋ","")
    else:
        if s.count("ㅋㅋ") > 1:
            first = s.find("ㅋㅋ")
            s = s[:first+2] + s[first+2:].replace("ㅋㅋ","")
    for tok in ["아유","아이고"]:
        if writer_key != "금손 원장":
            s = s.replace(tok,"")
        else:
            if s.count(tok) > 1:
                first = s.find(tok)
                s = s[:first+len(tok)] + s[first+len(tok):].replace(tok,"")
    s = re.sub(r"!{2,}","!", s)
    s = re.sub(r"~{3,}","~~", s)
    return s

def _squeeze_blank_lines(lines: List[str]) -> List[str]:
    out = []
    prev_blank = False
    for ln in lines:
        ln = (ln or "").rstrip()
        is_blank = (ln.strip() == "")
        if is_blank:
            if prev_blank:
                continue
            out.append("")
            prev_blank = True
        else:
            out.append(ln.strip())
            prev_blank = False
    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()
    return out

def _wrap_line(line: str, max_len: int = 30) -> List[str]:
    s = (line or "").strip()
    if not s:
        return [""]
    if len(s) <= max_len:
        return [s]
    out = []
    rest = s
    while len(rest) > max_len:
        cut = rest.rfind(" ", 0, max_len + 1)
        if cut <= 0:
            cut = max_len
        part = rest[:cut].rstrip()
        if part:
            out.append(part)
        rest = rest[cut:].lstrip()
        if not rest:
            break
    if rest:
        out.append(rest)
    return out

def _calc_total_len(lines: List[str]) -> int:
    return sum(len(ln) for ln in lines)

def _get_fillers(writer_key: str, allow_ad: bool) -> List[str]:
    common_non_ad = ["불편이 심하면 안과도 권해요.","도수만큼 세팅도 중요해요.","작은 조정이 차이를 만들어요.","렌즈 중심도 같이 봐요."]
    common_ad = ["이번엔 마진을 더 줄였어요.","학생들 부담 덜자고요.","재고 소진되면 종료예요.","가능한 만큼 챙겨드려요."]
    by_writer_non_ad = {
        "금손 원장":["아유, 참지 말고 말해요.","불편은 바로 잡아야죠."],
        "조원장":["기준을 잡으면 쉬워집니다.","확인 포인트만 딱 짚죠."],
        "장실장":["피팅은 제가 차근히 봐요.","조정은 부담 없이 와요."],
        "땡글이":["짧게 점검하면 편해요 ㅎㅎ","학생들 눈, 제가 챙겨요."],
    }
    by_writer_ad = {
        "금손 원장":["학생들 안경, 비싸면 안 돼요.","아유, 이 가격 맞추느라요."],
        "조원장":["유통 구조를 좀 줄였습니다.","과정을 바꿔 단가를 맞췄죠."],
        "장실장":["착용감까지 챙겨드릴게요.","조정도 같이 봐드려요."],
        "땡글이":["이 기회는 놓치기 아까워요 ㅎㅎ","진짜 부담 덜어드릴게요."],
    }
    base = (common_ad + by_writer_ad.get(writer_key, [])) if allow_ad else (common_non_ad + by_writer_non_ad.get(writer_key, []))
    return [x for x in base if x and len(x) <= 30]

def enforce_text_constraints(text: str, writer_key: str, min_chars: int, max_chars: int, allow_ad: bool, force_new_greeting: bool=False) -> str:
    s = _remove_forbidden_tokens(text)
    s = _fix_weird_self_reference(s)
    s = _limit_interjections(s, writer_key)
    lines = [ln.rstrip() for ln in s.split("\n")]

    title_idx = None
    for i, ln in enumerate(lines):
        if ln.strip():
            title_idx = i
            break

    if title_idx is None:
        title = "오늘 이야기"
        body = []
    else:
        title = lines[title_idx].strip()
        body = lines[title_idx+1:]

    title = title[:30].rstrip() if title else "오늘 이야기"

    while body and (not body[0].strip()):
        body.pop(0)

    variants = writer_name_variants(writer_key)
    greet1 = ""
    greet2 = ""
    used_existing = False

    if (not force_new_greeting) and len(body) >= 2:
        b0 = (body[0] or "").strip()
        b1 = (body[1] or "").strip()
        if b0 and b1 and any(v in b0 for v in variants) and len(b0) <= 30 and len(b1) <= 30:
            greet1, greet2 = b0, b1
            used_existing = True
            body = body[2:]
            while body and (not body[0].strip()):
                body.pop(0)

    if not used_existing:
        g1, g2 = pick_greeting_block(writer_key)
        if not any(v in (g1 or "") for v in variants):
            g1 = f"{writer_key}입니다."
        if not g2:
            g2 = "오늘도 편하게 읽어봐요."
        greet1 = (g1 or "").strip()[:30]
        greet2 = (g2 or "").strip()[:30]

    out_lines = [title, "", greet1, greet2, ""]
    out_lines.extend([(ln or "").strip() for ln in body])
    out_lines = _squeeze_blank_lines(out_lines)

    wrapped = []
    for ln in out_lines:
        if ln.strip() == "":
            wrapped.append("")
            continue
        wrapped.extend(_wrap_line(ln, 30))
    wrapped = _squeeze_blank_lines(wrapped)

    total_len = _calc_total_len(wrapped)
    min_keep = 5

    while wrapped and wrapped[-1] == "":
        wrapped.pop()
    total_len = _calc_total_len(wrapped)

    while total_len > max_chars and len(wrapped) > min_keep:
        last = wrapped.pop()
        total_len -= len(last)
        while wrapped and wrapped[-1] == "" and len(wrapped) > min_keep:
            wrapped.pop()

    if total_len < min_chars:
        fillers = _get_fillers(writer_key, allow_ad=allow_ad)
        used = set()
        if wrapped and wrapped[-1] != "":
            wrapped.append("")
        guard = 0
        while total_len < min_chars and guard < 80 and fillers:
            guard += 1
            cand = random.choice(fillers)
            if cand in used and len(used) < len(fillers):
                continue
            if total_len + len(cand) > max_chars:
                break
            wrapped.append(cand)
            total_len += len(cand)
            used.add(cand)

    wrapped = _squeeze_blank_lines(wrapped)
    return "\n".join(wrapped).strip("\n")

# -----------------------------
# Validation
# -----------------------------
@dataclass
class ValidationResult:
    ok: bool
    total_len: int
    max_line_len: int
    problems: List[str]

def validate_text(text: str, min_chars: int, max_chars: int, writer_key: Optional[str]=None) -> ValidationResult:
    cleaned = text.replace("\r\n","\n").strip("\n")
    total_len = len(cleaned.replace("\n",""))
    lines = [ln.rstrip() for ln in cleaned.split("\n")]
    max_line = 0
    problems: List[str] = []

    forbidden = ["```","###","<table","</table>","ChatGPT","챗GPT","AI가 쓴","AI가쓴","**","__","A원장","B원장","A 원장","B 원장"]
    for fs in forbidden:
        if fs in cleaned:
            problems.append("금지 표현/형식 포함: " + fs)
            break

    for idx, ln in enumerate(lines, start=1):
        if not ln.strip(): continue
        ln_len = len(ln)
        max_line = max(max_line, ln_len)
        if ln_len > 30:
            problems.append("줄 길이 초과 L" + str(idx) + ": " + str(ln_len) + "자")

    if total_len < min_chars or total_len > max_chars:
        problems.append(f"전체 글자수 범위 벗어남: {total_len} (기준 {min_chars}~{max_chars})")

    if writer_key:
        variants = writer_name_variants(writer_key)
        nonempty = [ln.strip() for ln in lines if ln.strip()]
        body_candidates = nonempty[1:3] if len(nonempty) >= 2 else []
        if not any(any(v in ln for v in variants) for ln in body_candidates):
            problems.append("초반 인사에 작성자 이름 없음")

    ok = (len(problems) == 0)
    return ValidationResult(ok=ok, total_len=total_len, max_line_len=max_line, problems=problems)

def make_validation_feedback(vr: ValidationResult) -> str:
    if vr.ok: return ""
    msg = ["반드시 고칠 것:"]
    for p in vr.problems[:14]:
        msg.append("- " + p)
    msg.append("조건: 줄당 30자 이내.")
    return "\n".join(msg)

# -----------------------------
# Pricing / usage
# -----------------------------
@dataclass
class Usage:
    prompt_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    def add(self, other: "Usage") -> None:
        self.prompt_tokens += int(other.prompt_tokens or 0)
        self.output_tokens += int(other.output_tokens or 0)
        self.total_tokens += int(other.total_tokens or 0)

def usage_from_gemini_response(resp: Dict) -> Usage:
    md = resp.get("usageMetadata") or resp.get("usage_metadata") or {}
    prompt = md.get("promptTokenCount") or md.get("prompt_tokens") or 0
    cand = md.get("candidatesTokenCount") or md.get("completion_tokens") or md.get("output_tokens") or 0
    total = md.get("totalTokenCount") or md.get("total_tokens") or (int(prompt or 0) + int(cand or 0))
    return Usage(prompt_tokens=int(prompt or 0), output_tokens=int(cand or 0), total_tokens=int(total or 0))

def calc_cost_usd(prompt_tokens: int, output_tokens: int) -> float:
    if int(prompt_tokens) > 200_000:
        in_per_1m = PRICE_INPUT_PER_1M_GT_200K
        out_per_1m = PRICE_OUTPUT_PER_1M_GT_200K
    else:
        in_per_1m = PRICE_INPUT_PER_1M_LE_200K
        out_per_1m = PRICE_OUTPUT_PER_1M_LE_200K
    return (prompt_tokens/1_000_000.0)*in_per_1m + (output_tokens/1_000_000.0)*out_per_1m

# -----------------------------
# Gemini API call
# -----------------------------
def http_post_json(url: str, headers: Dict[str, str], payload: Dict, timeout_sec: int = 900) -> Dict:
    data = json.dumps(payload).encode("utf-8")
    req = urlrequest.Request(url, data=data, headers=headers, method="POST")
    try:
        with urlrequest.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        raise RuntimeError("HTTPError " + str(e.code) + ": " + body[:1200])
    except URLError as e:
        raise RuntimeError("URLError: " + str(e))
    except Exception as e:
        raise RuntimeError("Request failed: " + str(e))

def call_gemini(api_key: str, max_output_tokens: int, instructions: str, user_input: str):
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + GEMINI_MODEL + ":generateContent"
    headers = {"Content-Type":"application/json","x-goog-api-key": api_key.strip()}
    payload = {
        "systemInstruction": {"parts":[{"text": instructions}]},
        "contents": [{"role":"user","parts":[{"text": user_input}]}],
        "generationConfig": {"maxOutputTokens": int(max_output_tokens), "temperature": 0.65},
    }
    resp = http_post_json(url, headers, payload, timeout_sec=900)

    text = ""
    try:
        cand0 = (resp.get("candidates") or [])[0]
        parts = cand0.get("content", {}).get("parts", []) or []
        texts = []
        for p in parts:
            if isinstance(p, dict) and p.get("text"):
                texts.append(p.get("text"))
        text = "\n".join(texts).strip()
    except Exception:
        text = ""

    usage = usage_from_gemini_response(resp)
    return text, usage

# -----------------------------
# Prompt building
# -----------------------------
def persona_rules_block() -> str:
    return (
        "이름/펄소나 규칙:\n"
        "- 매장 구성원 이름은 '금손 원장', '조원장', '장실장', '땡글이'만 사용.\n"
        "- 'A원장', 'B원장' 표기는 절대 쓰지 않음.\n"
        "- 제목 다음 첫 문단에서 작성자 이름을 밝히고 인사(2줄).\n"
        "- 본문 중간에 1번, '작성자(이름)인 제가/제가 보기엔' 같은 자기 언급.\n"
        "- 필요하면 다른 멤버를 1번 정도 언급해도 됨(팀워크/케미).\n"
        "- 단, 금손 원장과 조원장의 사적인 관계(가족/모자 등),\n"
        "  또는 동업/파트너 같은 관계 설명은 절대 금지.\n"
        "- 관계를 추측하게 하는 비유(엄마 같아요 등)도 금지.\n"
    )

def style_rules(min_chars: int, max_chars: int, allow_ad: bool=False) -> str:
    base = (
        "출력 형식 규칙:\n"
        "- 결과는 일반 텍스트만.\n"
        "- 굵게표시, 해시, 표, 코드블록 금지.\n"
        "- 한 줄에 한 문장만.\n"
        "- 각 줄은 띄어쓰기 포함 30자 이내.\n"
        "- 문단은 2~3줄로 끊고,\n"
        "  문단 사이엔 빈 줄 1줄.\n"
        f"- 전체 분량은 공백 포함 {min_chars}~{max_chars}자.\n"
    )
    if allow_ad:
        base += "- 광고처럼 보이는 문장 OK.\n- 다만 과장/거짓/확정적 단정은 금지.\n"
    else:
        base += "- 과장, 확정적 단정, 광고톤 금지.\n"
    base += "- 검증되지 않은 의학/기능 주장 금지.\n- 위험 신호면 안과 권고.\n- 실명/개인정보 금지.\n"
    return base

def build_stage1_instructions(writer_key: str, mode: str):
    voice = WRITER_VOICES.get(writer_key, "")
    if mode == "topic":
        min_chars, max_chars = 900, 1200
        extra = (
            "글 구성:\n- 첫 줄: 제목(짧고 클릭되는 느낌)\n- 제목에는 주제 핵심 단어 1개 포함.\n"
            "- 둘째 줄: 빈 줄\n- 셋째~넷째 줄: 인삿말 2줄(이름 포함)\n- 다섯째 줄: 빈 줄\n"
            "- 본문: 소제목 3~5개.\n- 소제목도 30자 이내.\n- 소제목에 특수기호 금지.\n"
            "- 글 안에 짧은 일화 1개 포함.\n- 마지막은 부담 없는 한 줄.\n"
        )
        allow_ad = False
    elif mode == "glory":
        min_chars, max_chars = 750, 1150
        extra = (
            "Glory Days 규칙:\n- 첫 줄: 제목(오늘 일상 느낌)\n- 둘째 줄: 빈 줄\n"
            "- 셋째~넷째 줄: 인삿말 2줄(이름 포함)\n- 다섯째 줄: 빈 줄\n"
            "- 소제목 2~4개.\n- 등장인물은 매번 다르게 보이게.\n"
            "- 의상/헤어/말투 중 1개 디테일.\n- 일화는 손님만 아니어도 됨.\n"
        )
        allow_ad = False
    else:
        min_chars, max_chars = 300, 500
        extra = (
            "특가 글 규칙:\n- 첫 줄: 제목(특가/제품 느낌)\n- 둘째 줄: 빈 줄\n"
            "- 셋째~넷째 줄: 인삿말 2줄(이름 포함)\n- 다섯째 줄: 빈 줄\n"
            "- 아래 입력 7개를 모두 반영.\n- 이유와 할인을 반드시 연결.\n"
            "- 'OO인 제가 보기에도' 금지.\n- 마지막은 부담 없는 안내 1줄.\n"
        )
        allow_ad = True

    ins = (
        "당신은 'Glory Days' 안경원의 글 작성자다.\n역할: 안경사이자 상담자.\n"
        + voice + "\n\n" + persona_rules_block() + "\n" + style_rules(min_chars, max_chars, allow_ad=allow_ad) + "\n" + extra
    )
    return ins, min_chars, max_chars

def build_intro_hint(writer_key: str) -> str:
    g1, g2 = pick_greeting_block(writer_key)
    return "이번 글 인삿말(제목 다음 2줄, 그대로 사용):\n- " + g1 + "\n- " + g2 + "\n"

def build_stage1_input_topic(board_key: str, board_label: str, topic: str, writer_key: str, memo: str) -> str:
    bits = pick_trust_bits(2)
    trust_line = " / ".join(bits)
    char_card = sample_cards(CHARACTER_CARDS, 1)[0]
    char_hint = cards_to_prompt_lines("현장감 인물 힌트(가능하면 사용):", [char_card], keys=["who","detail","line"])
    intro_hint = build_intro_hint(writer_key)
    return (
        "게시판: "+board_label+"\n게시판키: "+board_key+"\n주제: "+topic+"\n작성자: "+writer_key+"\n"
        + intro_hint
        + "자연스럽게 섞을 신뢰 포인트(1~2개만): "+trust_line+"\n"
        + "추가 메모(있으면 반영): "+(memo.strip() if memo.strip() else "없음")+"\n\n"
        + char_hint
        + "\n\n요청:\n- 네이버 블로그 글로 작성.\n- 위 인삿말 2줄은 그대로 출력.\n- 광고처럼 보이지 않게.\n- 본문 중간에 자기 언급 1줄.\n- 문장 길이 규칙 꼭 지켜.\n"
    )

EVENT_KEYWORDS = ["거래처","입고","재고","정리","청소","눈","비","낙엽","택배","배송","납품","회의","교육","견적","단가","가격","협상","불량","교환","수리","고장","점검","간판","유리"]

def infer_glory_story_focus(memo: str) -> str:
    m = (memo or "").strip()
    if not m:
        return "customer"
    if ("말고" in m or "대신" in m) and any(k in m for k in EVENT_KEYWORDS):
        return "event"
    if any(k in m for k in EVENT_KEYWORDS) and ("손님" not in m and "고객" not in m):
        return "event"
    return "customer"

def build_stage1_input_glorydays(writer_key: str, memo: str) -> str:
    bits = pick_trust_bits(2)
    trust_line = " / ".join(bits)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    focus = infer_glory_story_focus(memo)
    char_cards = sample_cards(CHARACTER_CARDS, 3)
    event_cards = sample_cards(EVENT_CARDS, 2)
    char_hint = cards_to_prompt_lines("등장인물 카드(1~2개 사용 권장):", char_cards, keys=["who","detail","moment","line"])
    event_hint = cards_to_prompt_lines("사건 카드(필요하면 사용):", event_cards, keys=["event","detail","moment","line"])
    memo_text = memo.strip() if memo and memo.strip() else "없음"
    intro_hint = build_intro_hint(writer_key)
    return (
        "섹션: Glory Days - 오늘 우리 안경원\n작성자: "+writer_key+"\n날짜: "+today+"\n선호 스토리: "+focus+" (customer/event)\n"
        + intro_hint
        + "자연스럽게 섞을 신뢰 포인트(1~2개만): "+trust_line+"\n\n"
        + char_hint + "\n\n" + event_hint + "\n\n"
        + "오늘 메모(원문):\n"+memo_text+"\n\n"
        + "요청:\n- 위 인삿말 2줄은 그대로 출력.\n- 본문 중간에 자기 언급 1줄.\n- 문장 길이 규칙 꼭 지켜.\n"
    )

def build_stage1_input_special(writer_key: str, who: str, target: str, product: str, discount: str, why: str, review_discount: str, coupon_discount: str) -> str:
    intro_hint = build_intro_hint(writer_key)
    def nz(x: str) -> str:
        x = (x or "").strip()
        return x if x else "없음"
    return (
        "섹션: 특가\n작성자: "+writer_key+"\n"+intro_hint
        + "누가: "+nz(who)+"\n대상: "+nz(target)+"\n어떤제품을: "+nz(product)+"\n얼마나 할인?: "+nz(discount)+"\n왜: "+nz(why)+"\n후기할인: "+nz(review_discount)+"\n쿠폰할인: "+nz(coupon_discount)+"\n\n"
        + "요청:\n- 위 인삿말 2줄은 그대로 출력.\n- 위 7개를 모두 반영.\n- 300~500자.\n- 'OO인 제가 보기에도' 금지.\n"
    )

def build_stage2_instructions(writer_key: str, min_chars: int, max_chars: int, allow_ad: bool=False) -> str:
    voice = WRITER_VOICES.get(writer_key, "")
    return (
        "당신은 같은 작성자의 편집자다.\n목표: 아래 초안을 사람이 쓴 글처럼 다듬기.\n"
        + voice + "\n\n"
        + persona_rules_block() + "\n"
        + style_rules(min_chars, max_chars, allow_ad=allow_ad) + "\n"
        + "추가 규칙:\n- 말투는 더 자연스럽게.\n- 반복어, 과한 정리톤 삭제.\n- 결과만 출력.\n"
    )

def build_stage2_input(draft_text: str, validation_feedback: str) -> str:
    return (
        "초안:\n"+draft_text.strip()+"\n\n"
        + "검수 피드백:\n"+(validation_feedback.strip() if validation_feedback.strip() else "없음")+"\n\n"
        + "요청:\n- 피드백을 반영해서 다시 작성.\n- 조건을 모두 만족할 때까지.\n"
    )

# -----------------------------
# Settings and pipeline
# -----------------------------
@dataclass
class GenerationSettings:
    gemini_key: str
    max_output_tokens: int
    usd_to_krw: float
    max_rewrite_tries: int = 3

@dataclass
class RunResult:
    draft: str
    final: str
    validation: ValidationResult
    usage_total: Usage
    cost_usd: float
    cost_krw: float

def run_two_stage(settings: GenerationSettings, writer_key: str, mode: str, stage1_input: str, min_chars: int, max_chars: int, allow_ad: bool, progress_cb=None):
    def prog(p: int, msg: str):
        if progress_cb:
            progress_cb(p, msg)

    usage_total = Usage()
    cost_total = 0.0

    prog(2, "생성중: 준비 (2%)")

    ins1, _, _ = build_stage1_instructions(writer_key, mode=mode)

    prog(10, "생성중: 1/2단계 작성 (10%)")
    draft, u1 = call_gemini(settings.gemini_key, settings.max_output_tokens, ins1, stage1_input)
    usage_total.add(u1)
    cost_total += calc_cost_usd(u1.prompt_tokens, u1.output_tokens)

    prog(55, "생성중: 1/2단계 완료 (55%)")

    refined = draft
    vr = validate_text(refined, min_chars, max_chars, writer_key=writer_key)
    feedback = make_validation_feedback(vr)

    tries = 0
    while tries < settings.max_rewrite_tries and (not vr.ok):
        tries += 1
        pct = 60 + int((tries - 1) * (35 / max(1, settings.max_rewrite_tries)))
        prog(pct, f"생성중: 2/2단계 다듬기 ({pct}%)")

        ins2 = build_stage2_instructions(writer_key, min_chars, max_chars, allow_ad=allow_ad)
        inp2 = build_stage2_input(refined, feedback)
        refined, u2 = call_gemini(settings.gemini_key, settings.max_output_tokens, ins2, inp2)
        usage_total.add(u2)
        cost_total += calc_cost_usd(u2.prompt_tokens, u2.output_tokens)

        vr = validate_text(refined, min_chars, max_chars, writer_key=writer_key)
        feedback = make_validation_feedback(vr)

    prog(96, "마무리: 자동 보정 (96%)")
    fixed = enforce_text_constraints(refined, writer_key=writer_key, min_chars=min_chars, max_chars=max_chars, allow_ad=allow_ad, force_new_greeting=False)
    vr2 = validate_text(fixed, min_chars, max_chars, writer_key=writer_key)

    if not vr2.ok:
        fixed = enforce_text_constraints(fixed, writer_key=writer_key, min_chars=min_chars, max_chars=max_chars, allow_ad=allow_ad, force_new_greeting=True)
        vr2 = validate_text(fixed, min_chars, max_chars, writer_key=writer_key)

    prog(100, "완료: 글 생성 완료 (100%)")
    return draft, fixed, vr2, usage_total, cost_total

def run_two_stage_topic(settings: GenerationSettings, board_key: str, board_label: str, topic: str, writer_key: str, memo: str, progress_cb=None) -> RunResult:
    _, min_chars, max_chars = build_stage1_instructions(writer_key, mode="topic")
    inp1 = build_stage1_input_topic(board_key, board_label, topic, writer_key, memo)

    draft, refined, vr, usage_total, cost_total = run_two_stage(
        settings=settings, writer_key=writer_key, mode="topic", stage1_input=inp1,
        min_chars=min_chars, max_chars=max_chars, allow_ad=False, progress_cb=progress_cb
    )

    refined = ensure_topic_in_title_line(refined, topic)
    refined = enforce_text_constraints(refined, writer_key=writer_key, min_chars=min_chars, max_chars=max_chars, allow_ad=False, force_new_greeting=False)
    vr = validate_text(refined, min_chars, max_chars, writer_key=writer_key)

    cost_usd = cost_total
    cost_krw = cost_usd * float(settings.usd_to_krw or DEFAULT_USD_TO_KRW)

    return RunResult(draft=draft, final=refined, validation=vr, usage_total=usage_total, cost_usd=cost_usd, cost_krw=cost_krw)

def run_two_stage_glory(settings: GenerationSettings, writer_key: str, memo: str, progress_cb=None) -> RunResult:
    _, min_chars, max_chars = build_stage1_instructions(writer_key, mode="glory")
    inp1 = build_stage1_input_glorydays(writer_key, memo)

    draft, refined, vr, usage_total, cost_total = run_two_stage(
        settings=settings, writer_key=writer_key, mode="glory", stage1_input=inp1,
        min_chars=min_chars, max_chars=max_chars, allow_ad=False, progress_cb=progress_cb
    )

    cost_usd = cost_total
    cost_krw = cost_usd * float(settings.usd_to_krw or DEFAULT_USD_TO_KRW)
    return RunResult(draft=draft, final=refined, validation=vr, usage_total=usage_total, cost_usd=cost_usd, cost_krw=cost_krw)

def run_two_stage_special(settings: GenerationSettings, writer_key: str, who: str, target: str, product: str, discount: str, why: str, review_discount: str, coupon_discount: str, progress_cb=None) -> RunResult:
    _, min_chars, max_chars = build_stage1_instructions(writer_key, mode="special")
    inp1 = build_stage1_input_special(writer_key, who, target, product, discount, why, review_discount, coupon_discount)

    draft, refined, vr, usage_total, cost_total = run_two_stage(
        settings=settings, writer_key=writer_key, mode="special", stage1_input=inp1,
        min_chars=min_chars, max_chars=max_chars, allow_ad=True, progress_cb=progress_cb
    )

    cost_usd = cost_total
    cost_krw = cost_usd * float(settings.usd_to_krw or DEFAULT_USD_TO_KRW)
    return RunResult(draft=draft, final=refined, validation=vr, usage_total=usage_total, cost_usd=cost_usd, cost_krw=cost_krw)
