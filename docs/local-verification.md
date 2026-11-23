# Local system verification

Verified on November 22, 2026, on Apple silicon macOS with Docker through the `orbstack` context.

## Running system

- Browser client: http://localhost:18080/
- Django API: http://localhost:18000/sinq/api/questions/
- API health: http://localhost:18000/healthz/
- Containers: `sinq-server-1` and `sinq-mobile-1`, both healthy.
- Persistence: the Compose `sinq-data` named volume stores SQLite and uploaded images. A server restart retained a created question and identical uploaded image bytes.

When multiple Docker engines are installed, select the intended context explicitly:

```sh
docker --context orbstack compose ps
```

## Checks passed

- Four Django tests: relationships, validation and rollback, uploads, CORS, and HTML routes.
- Two Playwright tests against the containers: photo-backed question creation, linked explanations and investigations, reload persistence, filtering, and save-error feedback.
- Standard-library HTTP smoke test: all three inquiry types, relationship filters, ordered investigation steps, API aliases, and exact image round trip.
- Locked npm dependency audit: no known vulnerabilities reported.
- Android debug APK build with Cordova Android 15.1.0, SDK 36, JDK 17, and Gradle 8.14.2.
- iOS simulator build with Cordova iOS 8.2.0 and Xcode 27.2. The refreshed app bundle matches current web assets and passes strict code-signature verification.

## Android native verification

The dedicated `SINQ_API_33` AVD runs as `emulator-5580`. The app `edu.umd.hcil.sinq` was installed and launched. Its WebView reported `Connected`, rendered the server's inquiry collection, and successfully submitted a new question; the host API returned that persisted question.

This guest could not route to `10.0.2.2`. The working connection is:

```sh
adb -s emulator-5580 reverse tcp:18000 tcp:18000
```

The app's Server connection is saved as `http://127.0.0.1:18000`. The parent helper resolves an already-running AVD name to its serial and restores this tunnel. Other local emulators were left alone.

## iOS runtime limitation

The existing iOS 26.3 runtime failed to boot the selected iPhone 17 Pro simulator. CoreSimulator reported:

```text
Unable to boot the Simulator.
launchd failed to respond.
Failed to start launchd_sim: could not bind to session,
launchd_sim may have crashed or quit responding
```

The iOS application build and signature checks passed; a live iOS launch has not been verified. The selected device is `4E45CE3D-00DB-4528-A7B7-E5638732657A`. Runtime repair can be attempted with `xcodebuild -downloadPlatform iOS`, followed by `xcrun simctl list runtimes` and the native launch instructions in the main README.
