---
name: project-container-dns-pinned
description: "ipul-intake container DNS is pinned to 8.8.8.8 + 1.1.1.1 in docker-compose.yml. Why it exists, when it'd need changing."
metadata: 
  node_type: memory
  type: project
  originSessionId: bcefcd91-35dd-4c26-b825-89768073f856
---

# ipul-intake container DNS is pinned (since 2026-06-03)

`docker-compose.yml` pins the container's DNS:

```yaml
dns:
  - 8.8.8.8       # Google primary
  - 1.1.1.1       # Cloudflare secondary
```

**Why:** Docker's embedded resolver at `127.0.0.11` captures the HOST's upstream DNS at container CREATE time and never re-reads. On `ipul-dockhost` at cutover (2026-06-02), the host's upstreams included Tailscale's stub (`100.100.100.100`). Tailscale daemon was disabled post-cutover per plan — the container's resolver kept forwarding to dead upstreams and went DNS-blind for ~23h, silently missing every Gmail poll and Slack reconnect. Two `parents@` emails sat unprocessed before Bill noticed. Pinning here removes the dependency on whatever host resolver state happens to exist at create time.

**How to apply:**
- Do NOT remove or comment out the `dns:` block during refactors — there is no fallback DNS path inside the container.
- If you ever deploy to a network where outbound to `8.8.8.8` / `1.1.1.1` is blocked (locked-down corp net, split-tunnel), override via compose override file or per-env compose, don't strip the pin.
- If office DNS (`192.168.2.5/6`) is migrated to a modern server and you want internal resolution (e.g. for split-horizon names), you can add the new internal resolver as a third entry — keep Google/Cloudflare as fallbacks.
- Office DNS at `192.168.2.5/6` is a soon-to-be-retired WS2016 — Bill's reason for going to public resolvers in the first place.

**Diagnostic recipe** (if the container ever goes DNS-blind again):

```
docker exec ipul-intake cat /etc/resolv.conf
docker exec ipul-intake getent hosts oauth2.googleapis.com
docker exec ipul-intake getent hosts slack.com
# If those fail, recreate (not restart — restart keeps stale embedded DNS):
cd ~/ipul-intake && docker compose up -d --force-recreate
docker logs ipul-intake --since 2m | grep -E "gmail|slack" | head -20
```

`docker compose restart` will NOT reset the embedded resolver; recreate is required.

**Lesson:** Docker embedded DNS state is a hidden coupling between Docker daemon start, host resolv.conf, and container creation. Anywhere that chain has volatility (Tailscale toggle, DHCP change, systemd-resolved restart), the container can silently drift. Explicit `dns:` in compose is the cleanest avoidance.

Related: [[post-cutover-state-2026-06-02]] (Tailscale state context), [[project-backup-pipeline-live]] (the host-side backup pipeline that ran fine through this outage — different DNS path entirely).
