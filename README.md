# 서울과학기술대학교 공지 알림 서비스 (프로토타입)

학사공지 / 장학공지 / 공모·외부행사 게시판을 주기적으로 확인해 새 글이 올라오면
이메일로 알려주는 도구입니다. 지메일 앱의 새 메일 푸시 알림을 그대로 이용하므로
"실시간 폰 알림"을 별도 앱 없이 구현합니다.

## 동작 원리

1. `boards.json`에 등록된 게시판을 스크레이핑해 게시글 목록을 가져온다.
2. `seen_posts.json`에 기록된 "이미 알림 보낸 글 id"와 비교해 새 글만 추린다.
3. 새 글이 있으면 이메일로 보내고, 보낸 글 id를 `seen_posts.json`에 저장한다.
4. 최초 실행 시에는 현재 게시글을 기준선으로만 저장하고 메일은 보내지 않는다
   (기존 글이 한꺼번에 스팸처럼 오는 것을 방지).

## 설치

```bash
cd seoultech-notifier
python3 -m pip install -r requirements.txt
cp .env.example .env
```

## 환경 설정 및 진단

1. `.env` 파일을 생성하고 발신용 Gmail 주소와 [앱 비밀번호](https://myaccount.google.com/apppasswords)를 설정합니다.
2. 아래 진단 명령어로 설정값 및 Gmail SMTP 연동이 정상인지 즉시 검증할 수 있습니다:

```bash
# 환경변수 및 SMTP 로그인 연결 테스트
python3 check_env.py

# 실제 테스트 이메일 1통 발송 테스트
python3 check_env.py --send-test
```

## 단위 테스트 실행

모든 파서 및 알림 파이프라인의 무결성을 검증합니다:

```bash
python3 -m unittest discover -s tests -v
```

## 실행

```bash
python3 main.py
```

## 배포 — GitHub Actions로 24시간 자동 실행하기 (추천)

로컬 컴퓨터가 꺼져 있어도 계속 동작하게 하려면, 코드를 GitHub 저장소에 올리고
`.github/workflows/notify.yml`(이미 포함됨)이 자동으로 10분마다 실행하도록 합니다.
**절대 `.env` 파일 자체를 커밋하지 마세요** — 비밀번호는 GitHub의 "Secrets" 기능에 별도로 등록합니다.

1. **저장소에 이 코드 올리기**
   ```bash
   cd seoultech-notifier
   git init
   git add .
   git commit -m "initial commit"
   git branch -M main
   git remote add origin <본인 GitHub 저장소 URL>
   git push -u origin main
   ```
   (Public/Private 둘 다 가능. Private이어도 Actions 무료 사용량 안에서 충분히 돌아갑니다.)

2. **비밀번호를 GitHub Secrets에 등록**
   저장소 페이지 → `Settings` → 왼쪽 메뉴 `Secrets and variables` → `Actions` → `New repository secret`
   아래 3개를 각각 등록합니다.
   | Name | Value |
   |---|---|
   | `EMAIL_ADDRESS` | 발신용 Gmail 주소 |
   | `EMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 |
   | `EMAIL_TO` | 알림 받을 주소 (본인 주소면 위와 동일하게) |

3. **워크플로가 커밋할 수 있도록 권한 켜기**
   저장소 `Settings` → `Actions` → `General` → 맨 아래 `Workflow permissions`에서
   **"Read and write permissions"** 선택 후 저장.
   (이걸 안 켜면 `seen_posts.json`을 다시 저장소에 저장하는 단계에서 실패합니다.)

4. **확인**
   저장소의 `Actions` 탭 → `Seoultech Notice Notifier` 워크플로 선택 →
   `Run workflow` 버튼으로 수동 1회 실행해서 정상 동작하는지 먼저 확인합니다.
   이후로는 `notify.yml`에 설정된 대로 10분마다 자동 실행됩니다.

> 최초 실행은 로컬에서 했을 때와 마찬가지로 "기준선 저장"만 하고 메일은 보내지
> 않습니다. 그 다음 실행부터 진짜 새 글에 대해서만 메일이 옵니다.

## 주기 실행 (로컬 컴퓨터에서 돌리는 경우)

GitHub Actions 대신 내 컴퓨터에서 계속 켜두고 돌리고 싶다면, macOS에서 5분마다
실행되도록 `launchd`에 등록하는 예시입니다 (이 경우 컴퓨터가 켜져 있어야만 동작합니다):

```bash
cat > ~/Library/LaunchAgents/com.seoultech.notifier.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.seoultech.notifier</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>__PROJECT_DIR__/main.py</string>
  </array>
  <key>WorkingDirectory</key><string>__PROJECT_DIR__</string>
  <key>StartInterval</key><integer>300</integer>
  <key>StandardOutPath</key><string>__PROJECT_DIR__/notifier.log</string>
  <key>StandardErrorPath</key><string>__PROJECT_DIR__/notifier.err.log</string>
</dict>
</plist>
EOF
launchctl load ~/Library/LaunchAgents/com.seoultech.notifier.plist
```

(`__PROJECT_DIR__`를 이 프로젝트의 절대 경로로 바꿔서 사용하세요.)

## 게시판(사이트) 추가하기

`boards.json`에 항목을 추가하면 됩니다. 서울과기대 홈페이지(`seoultech.ac.kr`)의
다른 게시판은 대부분 같은 템플릿을 쓰므로 URL만 바꿔 추가할 수 있습니다.

```json
{ "id": "graduate", "name": "대학원공지", "url": "https://www.seoultech.ac.kr/service/info/graduate/" }
```

링커리어, 캠퍼스픽처럼 **다른 도메인**의 사이트를 추가하려면 HTML 구조가 다르므로
`scraper.py`에 전용 파서 함수를 하나 더 만들고, `PARSERS` 딕셔너리에 등록한 뒤
`boards.json` 항목에 `"parser": "그 이름"`을 지정하면 됩니다.

## 한계 (프로토타입 수준)

- 로그인 없이 접근 가능한 공개 게시판만 대상으로 함
- 학교 홈페이지 개편 시 HTML 구조가 바뀌면 파서 수정이 필요함
- 이메일 발송 실패는 재시도 없이 다음 주기에 다시 시도됨 (그 사이 첫 알림이 늦어질 수 있음)
