"""서울과학기술대학교 통합 공지 알림 서비스 — Streamlit 웹 대시보드.

사용자가 웹 화면에서 이메일을 입력해 맞춤 공지를 구독하고,
즉시 체험 알림을 받아볼 수 있는 공모전 제출용 웹 애플리케이션입니다.
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
    page_title="서울과기대 통합 공지 알림 서비스",
    page_icon="🔔",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 스타일링
st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #3b82f6 100%);
        padding: 30px 25px;
        border-radius: 14px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.15);
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 28px;
        font-weight: 800;
        margin-bottom: 8px;
    }
    .main-header p {
        color: #e0e7ff;
        font-size: 15px;
        margin: 0;
    }
    .notice-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 18px;
        margin-bottom: 12px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .notice-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
    }
    .badge-academic {
        background-color: #eff6ff;
        color: #1d4ed8;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #bfdbfe;
    }
    .badge-scholarship {
        background-color: #ecfdf5;
        color: #047857;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #a7f3d0;
    }
    .badge-contest {
        background-color: #fffbeb;
        color: #b45309;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #fde68a;
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

    # 사이드바
    with st.sidebar:
        st.image("https://img.icons8.com/clouds/200/mailbox-opened-flag-up.png", width=120)
        st.title("🔔 서울과기대 알림")
        st.markdown(
            "흩어져 있는 **학사·장학·공모전 공지**를 실시간으로 크롤링하여 이메일로 큐레이션해 드립니다."
        )
        st.divider()

        # 주요 지표
        st.subheader("📊 실시간 모니터링 현황")
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("수집 게시판", f"{len(boards)}개")
        col_m2.metric("활성 구독자", f"{len(subscribers)}명")

        st.divider()
        st.markdown("🎯 **대상 게시판**")
        for b in boards:
            st.markdown(f"- [{b['name']}]({b['url']})")

        st.divider()
        st.caption("서울과학기술대학교 공지 알림 자동화 프로젝트")

    # 메인 헤더
    st.markdown(
        """
    <div class="main-header">
        <h1>서울과학기술대학교 통합 공지 알림 서비스</h1>
        <p>학사공지 · 장학공지 · 공모/대외활동 게시판 실시간 크롤링 및 맞춤형 이메일 알림 시스템</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 탭 구성
    tab1, tab2, tab3 = st.tabs([
        "✉️ 알림 구독 & 즉시 체험",
        "📋 실시간 통합 공지 피드",
        "⚙️ 구독 관리 및 해지",
    ])

    # TAB 1: 구독 신청 및 심사위원 즉시 체험
    with tab1:
        st.subheader("📬 이메일 구독 신청 및 알림 체험")
        st.write(
            "이메일을 입력하시면 **새로운 공지가 올라올 때마다 맞춤 알림 메일**이 자동으로 발송됩니다."
        )

        with st.form("subscription_form"):
            user_email = st.text_input(
                "이메일 주소 (필수)",
                placeholder="example@seoultech.ac.kr 또는 example@gmail.com",
                help="알림을 수신할 이메일 주소를 입력하세요.",
            )

            st.markdown("##### 📌 관심 게시판 선택 (다중 선택 가능)")
            board_options = {b["id"]: b["name"] for b in boards}
            selected_board_ids = []
            cols = st.columns(len(boards))
            for i, (b_id, b_name) in enumerate(board_options.items()):
                if cols[i].checkbox(b_name, value=True, key=f"sub_b_{b_id}"):
                    selected_board_ids.append(b_id)

            keyword_input = st.text_input(
                "🔍 관심 키워드 필터 (선택 사항)",
                placeholder="예: 장학금, 공모전, 해커톤, 수강신청 (쉼표로 구분)",
                help="입력한 키워드가 포함된 공지만 선별해서 수신합니다. 비워두면 선택한 게시판의 모든 공지를 수신합니다.",
            )

            st.markdown("<br>", unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns([1.5, 1])
            with col_btn1:
                submitted_with_demo = st.form_submit_button(
                    "🚀 구독 신청 및 최신 공지 즉시 체험 메일 받기",
                    type="primary",
                    use_container_width=True,
                )
            with col_btn2:
                submitted_only = st.form_submit_button(
                    "💾 구독 설정만 등록하기",
                    use_container_width=True,
                )

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
                        with st.spinner("✉️ 최신 공지 다이제스트 메일을 발송 중입니다..."):
                            try:
                                sent = send_welcome_digest(user_email, all_posts)
                                if sent:
                                    st.balloons()
                                    st.info(
                                        f"🎉 **{user_email}** 메일함으로 최신 공지 브리핑 메일이 성공적으로 발송되었습니다! 메일함을 확인해 보세요."
                                    )
                                else:
                                    st.warning("발송할 공지글이 없습니다.")
                            except Exception as e:
                                st.warning(
                                    f"구독은 등록되었으나 메일 발송 중 오류가 발생했습니다: {e}"
                                )
                else:
                    st.error(msg)

    # TAB 2: 실시간 공지 피드
    with tab2:
        st.subheader("📋 서울과기대 최신 공지사항 모아보기")

        col_f1, col_f2, col_f3 = st.columns([2, 1, 0.6])
        with col_f1:
            search_query = st.text_input("🔍 제목 또는 작성자 검색", placeholder="검색어를 입력하세요...")
        with col_f2:
            filter_board = st.selectbox(
                "게시판 필터",
                ["전체"] + [b["name"] for b in boards],
            )
        with col_f3:
            st.write("")
            st.write("")
            if st.button("🔄 새로고침", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

        # 필터링 적용
        filtered_posts = all_posts
        if filter_board != "전체":
            filtered_posts = [p for p in filtered_posts if p.board_name == filter_board]

        if search_query:
            q = search_query.lower()
            filtered_posts = [
                p for p in filtered_posts if q in p.title.lower() or q in p.writer.lower()
            ]

        st.caption(f"총 {len(filtered_posts)}건의 공지사항이 조회되었습니다.")

        # 공지 카드 목록 렌더링
        for post in filtered_posts:
            badge_class = f"badge-{post.board_id}" if post.board_id in ["academic", "scholarship", "contest"] else "badge-academic"
            st.markdown(
                f"""
            <div class="notice-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                    <span class="{badge_class}">{post.board_name}</span>
                    <span style="font-size: 13px; color: #64748b;">{post.date}</span>
                </div>
                <div style="font-size: 16px; font-weight: 700; color: #1e293b; margin-bottom: 8px;">
                    <a href="{post.url}" target="_blank" style="text-decoration: none; color: #1e293b;">{post.title}</a>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #64748b;">
                    <span>작성자: {post.writer or '과기대'}</span>
                    <a href="{post.url}" target="_blank" style="color: #2563eb; font-weight: 600; text-decoration: none;">원문 링크 &rarr;</a>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    # TAB 3: 구독 관리 및 해지
    with tab3:
        st.subheader("⚙️ 구독 설정 조회 및 해지")
        check_email = st.text_input("조회 또는 해지할 이메일 주소", key="check_email_input")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("🔎 내 구독 정보 조회", use_container_width=True):
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
