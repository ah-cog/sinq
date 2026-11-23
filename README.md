# SINQ — Scientific INQuery

SINQ helps learners ask questions, share cause-and-effect explanations, and plan investigations. This repository ties together the Django backend and Cordova mobile client.

```text
Browser / iOS / Android client (sinq-ios)
                 │  HTTP JSON + photo uploads
                 ▼
         Django API (sinq-server)
                 │
         Local SQLite + media/
```

## Start with Docker (recommended)

Prerequisites: Git and Docker with Compose. Native emulator builds also need Node.js 24+ and the platform tools below.

```sh
git clone --recurse-submodules https://github.com/ah-cog/sinq.git
cd sinq
docker compose up --build -d --wait
```

- Client: <http://localhost:18080/>
- Server: <http://localhost:18000/>
- API: <http://localhost:18000/sinq/api/questions/>

Compose builds both component Dockerfiles, runs migrations, seeds a repeatable demo, and waits for health checks. The server runs with Gunicorn; both images use unprivileged users. SQLite and uploaded photos persist in the `sinq-data` named volume. Ports bind to loopback.

```sh
docker compose ps
docker compose logs -f
docker compose down
```

`down` preserves data. Restart with the same `up` command. Docker Compose uses the pinned submodules by default; `SINQ_SERVER_CONTEXT` and `SINQ_MOBILE_CONTEXT` can point to alternate local checkouts during development. See each component README for its standalone setup.

## Optional host development

Requires Node.js 24+ and Python 3.13+ (validated with 3.14). Stop Compose first to free ports 18000 and 18080.

```sh
python3 scripts/dev.py setup
python3 scripts/dev.py start
python3 scripts/dev.py status
python3 scripts/dev.py stop
```

`setup` installs locked dependencies, migrates, and seeds the demo. Host logs and PID files live in `.local/`. The parent starts its pinned submodules; sibling repository clones are independent checkouts.

## Mobile emulators

The same client runs in browsers and native Cordova WebViews. The helper installs the client’s locked npm dependencies when needed.

```sh
python3 scripts/dev.py ios
python3 scripts/dev.py android
```

iOS needs Xcode, first-launch components, and an installed simulator runtime. Android needs JDK 17, Android SDK platform 36 and build tools 36.0.0, compatible Gradle (on PATH or in an existing wrapper cache), and an AVD. Configure `JAVA_HOME`, `ANDROID_HOME`, and `PATH`; on Homebrew macOS the helper recognizes `/opt/homebrew/share/android-commandlinetools`.

The client defaults to `localhost:18000` for browsers/iOS and `10.0.2.2:18000` for Android emulators. The server listens on loopback. Native projects are generated from `sinq-ios/config.xml` and the lockfile.

### Android networking in this workspace

The dedicated local AVD is `SINQ_API_33`; the helper selects it when present. Set `SINQ_ANDROID_TARGET` or `SINQ_IOS_TARGET` to choose another emulator. With the SDK tools on PATH, it can also be selected explicitly:

```sh
cd sinq-ios
npx cordova run android --emulator --target=SINQ_API_33
```

If the emulator cannot reach the host through `10.0.2.2`, use an ADB tunnel. For this running emulator:

```sh
adb -s emulator-5580 reverse tcp:18000 tcp:18000
```

In the app’s **Server connection**, choose `http://127.0.0.1:18000`. The app remembers this choice; recreate the ADB mapping after an emulator restart. Use `adb devices` to find the serial if it changes. This workspace’s AVD uses two cores, 2 GB RAM, and SwiftShader graphics.

## Verify the system

With Compose running:

For a quick network check without installing browser tooling:

```sh
python3 scripts/smoke.py
```

This creates one linked inquiry, uploads a photo, downloads it again, and verifies relationship filters, ordered steps, both API prefixes, and the client endpoint.

For the full backend and mobile browser tests:


```sh
docker compose exec server python manage.py test
cd sinq-ios
npm ci
npx playwright install chromium
npm test
```

Backend tests cover linked inquiry creation, filters, validation, transaction rollback, photo uploads, CORS, and HTML routes. Browser tests exercise photo-backed questions, linked explanations and investigations, persistence after reload, filtering, and save-error feedback at a mobile viewport.

## Repositories and upgrades

- [sinq-server](https://github.com/ah-cog/sinq-server): Python 3 / Django 6.1.3, SQLite local database, modern migrations, and the original serialized-object API contract.
- [sinq-ios](https://github.com/ah-cog/sinq-ios): current Cordova iOS and Android platforms; browser-native UI replaces the discontinued jQuery Mobile runtime. Historical Cordova 2.1 sources remain under `legacy/ios/`.

The submodule URLs point to these `ah-cog` forks. To update the system after changes land in both component repositories, advance and commit the submodule pointers here. `git submodule update --init --recursive` restores the pinned system versions.

This is a local development system. Existing remote data is not copied. The server README documents the old South schema and historical-database migration considerations. Database files, virtual environments, generated native projects, node modules, and uploaded media are ignored.
