#!/usr/bin/env python3
"""환경 설정 및 이메일(SMTP) 발송 진단 도구.

배포 전 로컬 환경 또는 서버에서 .env 설정값 및 Gmail SMTP 연결/인증 상태를
안전하게 단독 점검할 수 있는 스크립트입니다.

사용법:
  python check_env.py             # 환경변수 및 SMTP 로그인 연결 테스트
  python check_env.py --send-test # 실제 테스트 이메일 1통 발송 테스트
"""
from __future__ import annotations

import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def run_diagnostics(send_test: bool = False) -> bool:
    print("=" * 60)
    print("🔍 서울과기대 공지 알림 서비스 — 배포 및 환경 진단 도구")
    print("=" * 60)

    # 1. .env 파일 확인
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        print(f"✅ .env 파일 발견: {env_path}")
        if load_dotenv:
            load_dotenv()
            print("✅ python-dotenv를 통해 환경변수 로드 완료")
    else:
        print(f"⚠️  .env 파일이 없습니다 ({env_path.name}).")
        print("   (GitHub Actions 환경이라면 Repository Secrets로 주입되므로 정상입니다.)")
        if load_dotenv:
            load_dotenv()

    # 2. 필수 환경변수 확인
    email_addr = os.getenv("EMAIL_ADDRESS")
    email_pw = os.getenv("EMAIL_APP_PASSWORD")
    email_to = os.getenv("EMAIL_TO", email_addr)
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port_str = os.getenv("SMTP_PORT", "465")

    print("\n[1] 환경 변수 설정 상태 점검")
    all_ok = True

    if email_addr:
        print(f"  • EMAIL_ADDRESS: {email_addr}")
    else:
        print("  ❌ EMAIL_ADDRESS: 미설정 (발신용 Gmail 주소가 필요합니다)")
        all_ok = False

    if email_pw:
        masked_pw = email_pw[:3] + "*" * (len(email_pw) - 5) + email_pw[-2:] if len(email_pw) >= 5 else "****"
        print(f"  • EMAIL_APP_PASSWORD: {masked_pw} (길이: {len(email_pw)})")
    else:
        print("  ❌ EMAIL_APP_PASSWORD: 미설정 (Gmail 16자리 앱 비밀번호 필요)")
        all_ok = False

    print(f"  • EMAIL_TO: {email_to}")
    print(f"  • SMTP_HOST: {smtp_host}")
    print(f"  • SMTP_PORT: {smtp_port_str}")

    if not all_ok:
        print("\n❌ 필수 환경 변수가 누락되었습니다.")
        print("👉 해결 방법: .env 파일을 생성하거나 수정하세요. (.env.example 참고)")
        print("👉 Gmail 앱 비밀번호 생성: https://myaccount.google.com/apppasswords")
        return False

    # 3. SMTP 연결 및 인증 테스트
    print("\n[2] SMTP 서버 연결 및 계정 인증 테스트")
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        print(f"❌ 포트 번호 오류: '{smtp_port_str}'는 올바른 숫자가 아닙니다.")
        return False

    try:
        print(f"  📡 {smtp_host}:{smtp_port} (SSL) 연결 시도 중...")
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
            print("  ✅ SSL 연결 성공")
            print(f"  🔑 계정({email_addr}) 로그인 시도 중...")
            server.login(email_addr, email_pw.replace(" ", ""))
            print("  ✅ SMTP 계정 인증(로그인) 성공!")

            if send_test:
                print("\n[3] 테스트 이메일 발송 테스트")
                msg = MIMEText(
                    "안녕하세요!\n서울과학기술대학교 공지 알림 서비스 테스트 이메일입니다.\n정상적으로 메일 수신이 확인되었습니다.",
                    _charset="utf-8",
                )
                msg["Subject"] = "[테스트] 서울과기대 공지 알림 서비스 연동 확인"
                msg["From"] = email_addr
                msg["To"] = email_to

                print(f"  ✉️ {email_to} 주소로 테스트 메일 전송 중...")
                server.sendmail(email_addr, [email_to], msg.as_string())
                print(f"  🎉 테스트 이메일 발송 완료! 수신함({email_to})을 확인해주세요.")

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ 인증 실패 (로그인 에러): {e}")
        print("💡 원인 및 해결 방법:")
        print("  1. 일반 계정 비밀번호가 아닌 '앱 비밀번호(16자리)'를 사용했는지 확인하세요.")
        print("  2. Google 계정에서 2단계 인증이 활성화되어 있어야 앱 비밀번호를 생성할 수 있습니다.")
        return False
    except Exception as e:
        print(f"\n❌ SMTP 연결 오류: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 모든 진단 검사를 통과했습니다! 배포 및 실행 준비가 완료되었습니다.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    should_send = "--send-test" in sys.argv
    success = run_diagnostics(send_test=should_send)
    sys.exit(0 if success else 1)
