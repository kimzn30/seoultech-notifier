"""서울과학기술대학교 통합 공지 알림 서비스 — 반응형 Streamlit 웹 대시보드.

모바일 스마트폰과 PC 모니터 화면 크기에 맞게 자동으로 최적화되는 반응형 웹 UI를 제공합니다.
"""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from notifier import send_welcome_digest
from scraper import Post, fetch_board
from subscribers import (
    add_subscriber,
    get_subscriber,
    is_valid_email,
    load_subscribers,
    remove_subscriber,
)

# 환경 변수 로드
load_dotenv()

BOARDS_PATH = Path(__file__).parent / "boards.json"

st.set_page_config(
    page_title="서울과기대 통합 공지 알림",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="auto",  # 모바일에서 사이드바가 화면을 가리지 않도록 auto 설정
)

# 모바일 & 데스크톱 완벽 대응 반응형 CSS
st.markdown(
    """
<style>
    /* 전체 여백 모바일 최적화 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: clamp(0.8rem, 3vw, 2.5rem) !important;
        padding-right: clamp(0.8rem, 3vw, 2.5rem) !important;
        max-width: 1200px;
    }

    /* 반응형 그라디언트 헤더 */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 60%, #3b82f6 100%);
        padding: clamp(18px, 4vw, 30px);
        border-radius: 14px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.15);
        word-break: keep-all;
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: clamp(1.25rem, 4.5vw, 1.85rem) !important;
        font-weight: 800;
        margin-bottom: 8px;
        line-height: 1.3;
    }
    .main-header p {
        color: #e0e7ff;
        font-size: clamp(0.85rem, 2.5vw, 1rem);
        margin: 0;
        line-height: 1.4;
        opacity: 0.95;
    }

    /* 공지 카드 스타일 */
    .notice-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: clamp(12px, 3vw, 18px);
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        word-break: break-word;
    }
    .notice-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    }
    .notice-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 8px;
    }
    .notice-title {
        font-size: clamp(0.95rem, 3vw, 1.08rem);
        font-weight: 700;
        line-height: 1.45;
        color: #1e293b;
        margin-bottom: 10px;
    }
    .notice-title a {
        color: #0f172a;
        text-decoration: none;
    }
    .notice-title a:hover {
        color: #2563eb;
        text-decoration: underline;
    }
    .notice-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        font-size: clamp(0.78rem, 2.2vw, 0.85rem);
        color: #64748b;
        border-top: 1px dashed #f1f5f9;
        padding-top: 8px;
    }
    .link-btn {
        display: inline-block;
        background-color: #eff6ff;
        color: #1d4ed8 !important;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        text-decoration: none;
        border: 1px solid #dbeafe;
        font-size: 0.8rem;
    }
    .link-btn:hover {
        background-color: #2563eb;
        color: #ffffff !important;
    }

    /* 게시판 뱃지 */
    .badge {
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }
    .badge-academic {
        background-color: #eff6ff;
        color: #1d4ed8;
        border: 1px solid #bfdbfe;
    }
    .badge-scholarship {
        background-color: #ecfdf5;
        color: #047857;
        border: 1px solid #a7f3d0;
    }
    .badge-contest {
        background-color: #fffbeb;
        color: #b45309;
        border: 1px solid #fde68a;
    }

    /* 탭 메뉴 폰트 및 패딩 모바일 최적화 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        padding: clamp(8px, 2vw, 12px) clamp(10px, 2.5vw, 16px);
        font-size: clamp(0.85rem, 2.5vw, 0.95rem);
        font-weight: 600;
    }

    /* 버튼 모바일 터치 최적화 */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def load_all_boards_cached() -> tuple[list[dict], list[Post]]:
    """모든 게시판 설정 로드 및 실시간 크롤링 (5분 캐시)."""
    with BOARDS_PATH.open("r", encoding="utf-8") as f:
        boards = json.load(f)

    all_posts: list[Post] = []
    for b in boards:
        try:
            posts = fetch_board(b)
            all_posts.extend(posts)
        except Exception:
            pass
    return boards, all_posts


def main():
    boards, all_posts = load_all_boards_cached()
    subscribers = load_subscribers()

    # 사이드바 (모바일에서는 햄버거 메뉴로 깔끔하게 축소)
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/mailbox-opened-flag-up.png", width=100)
        st.title("🔔 서울과기대 알림")
        st.markdown(
            "흩어져 있는 **학사 · 장학 · 공모전 공지**를 실시간 크롤링하여 맞춤형 메일로 알려드립니다."
        )
        st.divider()

        st.subheader("📊 서비스 현황")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("수집 게시판", f"{len(boards)}개")
        col_m2.metric("활성 구독자", f"{len(subscribers)}명")

        st.divider()
        st.markdown("🎯 **모니터링 대상 게시판**")
        for b in boards:
            st.markdown(f"- [{b['name']}]({b['url']})")

        st.divider()
        st.caption("서울과학기술대학교 통합 공지 알림 서비스 (v2.0)")

    # 메인 반응형 헤더
    st.markdown(
        """
    <div class="main-header">
        <h1>서울과학기술대학교 통합 공지 알림 서비스</h1>
        <p>학사 · 장학 · 공모/대외활동 실시간 크롤링 & 맞춤형 이메일 알림</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 탭 구성
    tab1, tab2, tab3 = st.tabs([
        "✉️ 알림 구독 & 즉시 체험",
        "📋 실시간 통합 공지 피드",
        "⚙️ 구독 조회 및 해지",
    ])

    # TAB 1: 구독 신청 및 심사위원 즉시 체험
    with tab1:
        st.subheader("📬 이메일 구독 신청")
        st.write(
            "이메일을 입력하시면 **새로운 공지가 등록될 때마다 맞춤 알림 메일**이 자동으로 발송됩니다."
        )

        with st.form("subscription_form"):
            user_email = st.text_input(
                "이메일 주소 (필수)",
                placeholder="example@seoultech.ac.kr 또는 example@gmail.com",
                help="알림을 수신할 이메일 주소를 입력하세요.",
            )

            st.markdown("##### 📌 관심 게시판 선택 (다중 선택 가능)")
            board_options = {b["id"]: b["name"] for b in boards}
            
            # 모바일과 PC 모두에서 보기 좋은 반응형 체크박스 레이아웃
            selected_board_ids = []
            cols = st.columns(len(boards))
            for i, (b_id, b_name) in enumerate(board_options.items()):
                if cols[i].checkbox(b_name, value=True, key=f"sub_b_{b_id}"):
                    selected_board_ids.append(b_id)

            keyword_input = st.text_input(
                "🔍 관심 키워드 필터 (선택 사항)",
                placeholder="예: 장학금, 공모전, 해커톤, 수강신청 (쉼표로 구분)",
                help="입력한 키워드가 제목에 포함된 공지만 선별 수신합니다. 비워두면 선택한 게시판의 모든 공지를 수신합니다.",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            
            # 모바일 친화적 버튼 레이아웃
            submitted_with_demo = st.form_submit_button(
                "🚀 구독 신청 (최신 공지 즉시 받아보기)",
                type="primary",
                use_container_width=True,
                help="구독과 동시에 현재 올라와 있는 최신 공지 요약 메일을 바로 보내드립니다. (심사위원 및 첫 사용자 추천)",
            )
            st.caption("💡 **첫 방문자 & 심사위원 추천:** 구독 완료와 동시에 **최신 공지 브리핑 메일을 즉시 발송**해 드립니다.")

            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

            submitted_only = st.form_submit_button(
                "📬 일반 구독 (새 글 등록 시에만 받기)",
                use_container_width=True,
                help="지금은 메일을 발송하지 않고, 앞으로 새 공지가 올라올 때부터 알림을 받습니다.",
            )
            st.caption("ℹ️ 지금 당장 메일을 받지 않고, **새 공지가 새로 등록될 때부터 알림**을 받으려면 이 버튼을 누르세요.")

        if submitted_with_demo or submitted_only:
            if not user_email:
                st.error("이메일 주소를 입력해 주세요.")
            elif not is_valid_email(user_email):
                st.error("올바른 이메일 형식이 아닙니다 (예: yourname@gmail.com).")
            elif not selected_board_ids:
                st.error("최소 1개 이상의 관심 게시판을 선택해 주세요.")
            else:
                keywords = [k.strip() for k in keyword_input.split(",") if k.strip()]
                ok, msg = add_subscriber(user_email, selected_board_ids, keywords)

                if ok:
                    st.success(msg)
                    if submitted_with_demo:
                        # 즉시 체험 발송
                        with st.spinner("✉️ 최신 공지 브리핑 메일을 발송 중입니다..."):
                            try:
                                sent = send_welcome_digest(user_email, all_posts)
                                if sent:
                                    st.balloons()
                                    st.info(
                                        f"🎉 **{user_email}** 메일함으로 최신 공지 카드 메일이 발송되었습니다! 메일함을 확인해 보세요."
                                    )
                                else:
                                    st.warning("발송할 공지글이 없습니다.")
                            except Exception as e:
                                st.warning(
                                    f"구독은 완료되었으나 메일 발송 중 오류가 발생했습니다: {e}"
                                )
                else:
                    st.error(msg)

    # TAB 2: 실시간 공지 피드
    with tab2:
        st.subheader("📋 서울과기대 최신 공지사항")

        # 반응형 검색 및 필터 행
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            search_query = st.text_input("🔍 제목 또는 작성자 검색", placeholder="검색어를 입력하세요...")
        with col_f2:
            filter_board = st.selectbox(
                "게시판 필터",
                ["전체"] + [b["name"] for b in boards],
            )
            
        if st.button("🔄 실시간 공지 새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        # 필터링 로직
        filtered_posts = all_posts
        if filter_board != "전체":
            filtered_posts = [p for p in filtered_posts if p.board_name == filter_board]

        if search_query:
            q = search_query.lower()
            filtered_posts = [
                p for p in filtered_posts if q in p.title.lower() or q in p.writer.lower()
            ]

        st.caption(f"총 {len(filtered_posts)}건의 공지사항이 조회되었습니다.")

        # 반응형 공지 카드 목록 렌더링
        for post in filtered_posts:
            badge_class = f"badge-{post.board_id}" if post.board_id in ["academic", "scholarship", "contest"] else "badge-academic"
            st.markdown(
                f"""
            <div class="notice-card">
                <div class="notice-header">
                    <span class="badge {badge_class}">{post.board_name}</span>
                    <span style="color: #64748b; font-size: 0.8rem;">{post.date}</span>
                </div>
                <div class="notice-title">
                    <a href="{post.url}" target="_blank">{post.title}</a>
                </div>
                <div class="notice-footer">
                    <span>작성자: <strong>{post.writer or '과기대'}</strong></span>
                    <a href="{post.url}" target="_blank" class="link-btn">원문 보기 &rarr;</a>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # TAB 3: 구독 관리 및 해지
    with tab3:
        st.subheader("⚙️ 구독 설정 조회 및 해지")
        check_email = st.text_input("이메일 주소 입력", key="check_email_input", placeholder="구독 시 입력했던 이메일")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("🔎 내 구독 설정 조회", use_container_width=True):
                if not check_email:
                    st.error("이메일을 입력하세요.")
                else:
                    sub = get_subscriber(check_email)
                    if sub:
                        st.json(sub)
                    else:
                        st.info("등록된 구독 정보가 없습니다.")

        with col_c2:
            if st.button("❌ 구독 해지하기", use_container_width=True):
                if not check_email:
                    st.error("이메일을 입력하세요.")
                else:
                    ok, msg = remove_subscriber(check_email)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)


if __name__ == "__main__":
    main()
