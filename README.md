# hClaw Product Layer

This branch is the hClaw product layer. It does not vendor the QwenPaw
source tree. Instead, it depends on the QwenPaw core/lib wheel produced by
the `qwenpaw-trunk` branch.

Minimal local verification flow:

1. Build the QwenPaw core wheel from `qwenpaw-trunk`.
2. Install this product package with that wheel.
3. Run `hclaw app --host 127.0.0.1 --port 8088`.

The runtime is one Python process: the `hclaw` launcher imports and composes
the `qwenpaw` core library in-process.

Frontend source lives in `web/console`. Build it with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_frontend.ps1
```

The script publishes the built assets to `web/dist`. The `hclaw` launcher
points the QwenPaw core at that directory before starting the app.
