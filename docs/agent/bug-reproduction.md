# Bug reproduction (for Claude)

How Claude reproduces a bug in local (skill `fix-bug`, step 2). Written once the app and
the backend run; until then this page only lists what it must answer.

## What this page must answer

| Question | Answer |
|---|---|
| How to start the stack in local | From `backend/`: `docker compose up -d` (`migrate` applies the migrations, then `backend` and `worker` start; `db`, `db-test`). The backend answers at `https://$BACKEND_HOST` (value in `backend/.env`) through the shared local Traefik; GraphiQL at `/graphql` in `local`. Logs: `docker compose logs backend` |
| How to get a test account without a real social login | The development login of ADR 0005 section 6 (local only, seeded test users) |
| Where the credentials for that live (git-ignored file, read at run time) | ... |
| How to reach a state fast (seed data, API calls, database updates) | `curl` to `https://$BACKEND_HOST/graphql` with `X-Client-Platform` and `X-Client-Version`; settings through `AppConfigService.set` in `docker compose exec -T backend python -`; database through `docker compose exec db psql` under `run_locked.py`. After a code change, `--reload` restarts the backend (the worker needs `docker compose restart worker`), but Traefik may keep a keep-alive connection to the previous process for a few requests |
| Web: browser automation and where screenshots go (git-ignored) | From `web/`: `docker compose up -d` serves `https://$WEB_HOST` (dev server, values in `web/.env`). Drive it with Playwright (`@playwright/test` in `web/node_modules`, `ignoreHTTPSErrors: true` because the headless browser does not trust the mkcert CA); simulate the backend with `page.route("**/api/graphql", ...)` as `e2e/web-skeleton.spec.ts` does. Screenshots go to the session scratchpad, never to `web/` (`test-results/` and `playwright-report/` are git-ignored) |
| Android: emulator, how to install the dev build, how to drive it | The app talks to the staging backend (`backend.url` in `android/local.properties`); a backend change reaches it after `./tools/deploy.sh <ref>` on the server (requirement 0008). From `android/`: `./gradlew :app:installDebug`, then `adb shell am start -n com.sebastianartaza.fulbito/.MainActivity`; drive it with `adb shell input tap` or `swipe` and capture with `adb exec-out screencap -p` into the session scratchpad |
| iOS: simulator, how to install the dev build, how to drive it | The app talks to the staging backend (`BACKEND_URL` in `ios/Config/Local.xcconfig`, Android row). From `ios/`: `xcodegen generate`, `xcodebuild build -project App.xcodeproj -scheme App -destination 'platform=iOS Simulator,name=iPhone 17,OS=27.2' -derivedDataPath .build/xcode`, then `xcrun simctl install booted .build/xcode/Build/Products/Debug-iphonesimulator/App.app` and `xcrun simctl launch booted com.sebastianartaza.fulbito`. Switch theme with `xcrun simctl ui booted appearance dark`; capture with `xcrun simctl io booted screenshot` into the session scratchpad. Taps need an XCUITest (`ios/UITests/`); `BACKEND_STUB=healthy` in its launch environment skips the backend |
| What never goes into tracked files, logs or the transcript | tokens, refresh tokens, emails, personal data |
