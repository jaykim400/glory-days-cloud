import streamlit as st
import glory_core as core

# 1) 이것은 파일에서 딱 1번만, 그리고 가장 먼저!
st.set_page_config(page_title="Glory Days (Full)", layout="wide")

# 2) 비밀번호 & 키 (여기만 네가 바꾸면 됨)
APP_PASSWORD = "4588"
GEMINI_API_KEY_HARDCODED = "AIzaSyBt2NQI42pELCmuc6M5u3oPN9gNd_VJ-6c"

st.title("Glory Days 블로그 글 생성기 (FULL)")

# ---- 비밀번호 ----
pw = st.text_input("비밀번호", type="password")
if pw == "":
    st.info("비밀번호를 입력하세요.")
    st.stop()
if pw != APP_PASSWORD:
    st.error("비밀번호가 틀렸습니다.")
    st.stop()

# ---- API Key ----
api_key = GEMINI_API_KEY_HARDCODED
try:
    api_key = st.secrets.get("GEMINI_API_KEY", api_key)
except Exception:
    pass

if (not api_key) or ("여기에_새_GEMINI_API_KEY" in api_key):
    st.error("API Key를 app.py 맨 위에 붙여넣어야 합니다.")
    st.stop()

# ---- 설정 ----
col1, col2, col3 = st.columns(3)
with col1:
    max_out = st.number_input("maxOutputTokens", 256, 8192, 4096, 256)
with col2:
    usd_to_krw = st.number_input("환율(KRW/USD)", 900.0, 2000.0, 1350.0, 10.0)
with col3:
    tries = st.number_input("재작성 횟수", 0, 6, 3, 1)

settings = core.GenerationSettings(
    gemini_key=api_key,
    max_output_tokens=int(max_out),
    usd_to_krw=float(usd_to_krw),
    max_rewrite_tries=int(tries),
)

prog = st.progress(0)
status = st.empty()

def progress_cb(pct, msg):
    prog.progress(int(pct))
    status.write(msg)

tabs = st.tabs(["주제 글", "Glory Days", "특가"])

# =========================
# 주제 글
# =========================
with tabs[0]:
    st.subheader("주제 글")
    board_label = st.selectbox("게시판", [b[1] for b in core.BOARD_OPTIONS])

    board_key = "A"
    for k, v in core.BOARD_OPTIONS:
        if v == board_label:
            board_key = k
            break

    writer_label = st.selectbox("작성자", core.WRITER_OPTIONS)
    writer_key = core.WRITER_KEY_MAP.get(writer_label, "금손 원장")

    topic = st.selectbox("주제", core.TOPICS.get(board_key, []))
    memo = st.text_area("추가 메모", "")

    if st.button("블로그 글 생성", key="topic"):
        prog.progress(0)
        status.write("시작...")
        result = core.run_two_stage_topic(
            settings, board_key, board_label, topic, writer_key, memo, progress_cb=progress_cb
        )

        st.text_area("1단계 결과", result.draft, height=220)
        st.text_area("2단계 최종", result.final, height=420)

        st.write(f"검수: {'통과' if result.validation.ok else '미통과'}")
        st.write(f"토큰: {result.usage_total.total_tokens:,} (입력 {result.usage_total.prompt_tokens:,} / 출력 {result.usage_total.output_tokens:,})")
        st.write(f"비용: ${result.cost_usd:.4f} / {int(result.cost_krw):,}원")

        title = core.first_nonempty_line(result.final) or topic
        html = core.wrap_html(title, result.final)
        st.download_button("HTML 다운로드", data=html.encode("utf-8"), file_name="glory_topic.html", mime="text/html")

# =========================
# Glory Days
# =========================
with tabs[1]:
    st.subheader("Glory Days")
    writer_label = st.selectbox("작성자", core.WRITER_OPTIONS, key="wg")
    writer_key = core.WRITER_KEY_MAP.get(writer_label, "금손 원장")
    memo = st.text_area("오늘 메모", "")

    if st.button("Glory Days 글 생성", key="glory"):
        prog.progress(0)
        status.write("시작...")
        result = core.run_two_stage_glory(settings, writer_key, memo, progress_cb=progress_cb)

        st.text_area("1단계 결과", result.draft, height=220)
        st.text_area("2단계 최종", result.final, height=420)

        st.write(f"검수: {'통과' if result.validation.ok else '미통과'}")
        st.write(f"토큰: {result.usage_total.total_tokens:,} (입력 {result.usage_total.prompt_tokens:,} / 출력 {result.usage_total.output_tokens:,})")
        st.write(f"비용: ${result.cost_usd:.4f} / {int(result.cost_krw):,}원")

        title = core.first_nonempty_line(result.final) or "Glory Days"
        html = core.wrap_html(title, result.final)
        st.download_button("HTML 다운로드", data=html.encode("utf-8"), file_name="glory_days.html", mime="text/html")

# =========================
# 특가
# =========================
with tabs[2]:
    st.subheader("특가")
    writer_key = st.selectbox("누가", core.SPECIAL_WHO_OPTIONS)
    target = st.text_input("대상")
    product = st.text_input("어떤제품을")
    discount = st.text_input("얼마나 할인?")
    why = st.text_input("왜")
    review = st.text_input("후기할인")
    coupon = st.text_input("쿠폰할인")

    if st.button("특가 글 생성", key="special"):
        prog.progress(0)
        status.write("시작...")
        result = core.run_two_stage_special(
            settings, writer_key, writer_key, target, product, discount, why, review, coupon, progress_cb=progress_cb
        )

        st.text_area("1단계 결과", result.draft, height=200)
        st.text_area("2단계 최종", result.final, height=320)

        st.write(f"검수: {'통과' if result.validation.ok else '미통과'}")
        st.write(f"토큰: {result.usage_total.total_tokens:,} (입력 {result.usage_total.prompt_tokens:,} / 출력 {result.usage_total.output_tokens:,})")
        st.write(f"비용: ${result.cost_usd:.4f} / {int(result.cost_krw):,}원")

        title = core.first_nonempty_line(result.final) or "특가"
        html = core.wrap_html(title, result.final)
        st.download_button("HTML 다운로드", data=html.encode("utf-8"), file_name="glory_special.html", mime="text/html")
