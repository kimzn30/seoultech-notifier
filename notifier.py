"""새 게시글을 이메일로 발송하는 모듈.

HTML 카드 레이아웃과 일반 텍스트를 함께 지원하여 스마트폰 및 PC 메일 앱에서
보기 좋은 알림을 제공합니다. 다중 구독자 맞춤 발송 및 즉시 체험 발송을 지원합니다.
"""
from __future__ import annotations

import html
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scraper import Post

from subscribers import filter_posts_for_subscriber

# 게시판별 뱃지 색상
BOARD_COLORS = {
    "academic": {"bg": "#eff6ff", "text": "#1d4ed8", "border": "#bfdbfe", "name": "학사공지"},
    "scholarship": {"bg": "#ecfdf5", "text": "#047857", "border": "#a7f3d0", "name": "장학공지"},
    "contest": {"bg": "#fffbeb", "text": "#b45309", "border": "#fde68a", "name": "공모·행사"},
}


def build_email_body(posts: list[Post]) -> str:
    """일반 텍스트 본문 생성."""
    lines = []
    for p in posts:
        lines.append(f"[{p.board_name}] {p.title}")
        lines.append(f"  작성자: {p.writer}  |  날짜: {p.date}")
        lines.append(f"  {p.url}")
        lines.append("")
    return "\n".join(lines)


def build_html_email(posts: list[Post], title_text: str = "서울과학기술대학교 새로운 공지사항") -> str:
    """모던 반응형 HTML 이메일 본문 생성."""
    cards_html = []
    for p in posts:
        color_info = BOARD_COLORS.get(
            p.board_id,
            {"bg": "#f3f4f6", "text": "#374151", "border": "#e5e7eb", "name": p.board_name},
        )
        safe_title = html.escape(p.title)
        safe_writer = html.escape(p.writer or "서울과기대")
        safe_date = html.escape(p.date or "-")
        safe_url = html.escape(p.url)

        card = f"""
        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
          <div style="margin-bottom: 10px;">
            <span style="background-color: {color_info['bg']}; color: {color_info['text']}; border: 1px solid {color_info['border']}; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 600;">
              {color_info['name']}
            </span>
            <span style="color: #64748b; font-size: 13px; margin-left: 8px;">{safe_date}</span>
          </div>
          <h3 style="margin: 0 0 10px 0; font-size: 16px; font-weight: 700; line-height: 1.4; color: #0f172a;">
            <a href="{safe_url}" target="_blank" style="color: #0f172a; text-decoration: none;">{safe_title}</a>
          </h3>
          <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #64748b;">
            <span>작성: <strong>{safe_writer}</strong></span>
            <a href="{safe_url}" target="_blank" style="display: inline-block; background-color: #2563eb; color: #ffffff; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 600;">
              원문 보기 &rarr;
            </a>
          </div>
        </div>
        """
        cards_html.append(card)

    cards_joined = "\n".join(cards_html)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title_text)}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Pretendard', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <div style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0;">
    <!-- Header -->
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 28px 24px; text-align: left; color: #ffffff;">
      <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.85; margin-bottom: 4px; font-weight: 600;">Seoultech Notice Notifier</div>
      <h1 style="margin: 0; font-size: 22px; font-weight: 800; color: #ffffff;">{html.escape(title_text)}</h1>
      <p style="margin: 6px 0 0 0; font-size: 14px; opacity: 0.9;">신규 게시글 {len(posts)}건이 등록되었습니다.</p>
    </div>

    <!-- Body Content -->
    <div style="padding: 24px; background-color: #f8fafc;">
      {cards_joined}
    </div>

    <!-- Footer -->
    <div style="padding: 20px 24px; background-color: #ffffff; border-top: 1px solid #e2e8f0; text-align: center; font-size: 12px; color: #94a3b8;">
      <p style="margin: 0 0 6px 0;">본 메일은 서울과학기술대학교 공지 알림 서비스에서 자동 발송되었습니다.</p>
      <p style="margin: 0;">웹 대시보드에서 언제든지 구독 설정 변경 및 해지가 가능합니다.</p>
    </div>
  </div>
</body>
</html>
"""


def _send_raw_smtp(to_addr: str, subject: str, html_body: str, plain_body: str) -> None:
    """SMTP를 통한 실제 메일 전송 (HTML & Plain Text 멀티파트 지원)."""
    sender = os.environ["EMAIL_ADDRESS"]
    app_password = os.environ["EMAIL_APP_PASSWORD"].replace(" ", "")
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"서울과기대 공지알림 <{sender}>"
    msg["To"] = to_addr

    # 순서: plain text 먼저, html 나중에 추가해야 메일 클라이언트가 HTML을 우선 렌더링
    part1 = MIMEText(plain_body, "plain", _charset="utf-8")
    part2 = MIMEText(html_body, "html", _charset="utf-8")
    msg.attach(part1)
    msg.attach(part2)

    with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
        server.login(sender, app_password)
        server.sendmail(sender, [to_addr], msg.as_string())


def send_email(posts: list[Post], to_addr: str | None = None, subject_prefix: str = "[서울과기대 공지]") -> None:
    """단일 수신자에게 공지 목록 발송."""
    if not posts:
        return

    recipient = to_addr or os.environ.get("EMAIL_TO", os.environ["EMAIL_ADDRESS"])
    subject = f"{subject_prefix} 새 글 {len(posts)}건"
    plain_body = build_email_body(posts)
    html_body = build_html_email(posts, title_text=f"{subject_prefix} 새 글 알림")

    _send_raw_smtp(recipient, subject, html_body, plain_body)


def send_welcome_digest(to_addr: str, posts: list[Post], subscriber_info: dict | None = None) -> bool:
    """신규 구독자 또는 심사위원을 위한 즉시 체험 환영 다이제스트 메일 발송."""
    if not posts:
        return False

    display_posts = posts[:5]  # 최신 5건 브리핑
    subject = f"[서울과기대 알림] 구독 완료! 최신 공지 브리핑 ({len(display_posts)}건)"
    plain_body = f"서울과학기술대학교 공지 알림 서비스 구독을 환영합니다!\n\n최신 공지사항:\n\n" + build_email_body(display_posts)
    html_body = build_html_email(display_posts, title_text="구독 환영 및 최신 공지 브리핑")

    _send_raw_smtp(to_addr, subject, html_body, plain_body)
    return True


def send_notifications_to_subscribers(posts: list[Post], subscribers: list[dict]) -> int:
    """등록된 모든 다중 구독자에게 맞춤 필터링된 공지 일괄 발송."""
    if not posts or not subscribers:
        return 0

    sent_count = 0
    for sub in subscribers:
        sub_email = sub.get("email")
        if not sub_email:
            continue

        matched_posts = filter_posts_for_subscriber(sub, posts)
        if not matched_posts:
            continue

        try:
            subject = f"[서울과기대 맞춤공지] 새 글 {len(matched_posts)}건"
            plain_body = build_email_body(matched_posts)
            html_body = build_html_email(matched_posts, title_text="맞춤 공지 알림")
            _send_raw_smtp(sub_email, subject, html_body, plain_body)
            sent_count += 1
        except Exception as e:
            print(f"[발송 오류] {sub_email} 발송 실패: {e}")

    return sent_count
