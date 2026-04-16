# AETHER eBPF (Safe Metadata-Only Scaffold)

This scaffold traces HTTPS-related timing metadata around OpenSSL write/read edges
without collecting plaintext buffers, TLS-decrypted content, URLs, headers, cookies,
tokens, credentials, or response bodies.

Captured fields:
- pid
- tid
- process name (comm)
- timestamp_ns
- duration_ns
- phase

Intended use:
- latency histograms
- per-process/per-agent timing metrics
- safe observability demos and CI compile validation
