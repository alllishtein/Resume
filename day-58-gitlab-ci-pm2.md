# Day 58 — GitLab CI + PM2

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** code az `master` chejori be server miresad va process zende mimune?

**Javab monorepo (honesty):**

| side | deploy style (in workspace) |
|---|---|
| **Frontend** (`dejban_frontend_new`) | **GitLab CI** → SSH server → build → **PM2** process |
| **Backend** (`dejban_backend_new`) | **Docker Compose / Dockerfiles** + **migrationesho** ba'd deploy — **`.gitlab-ci.yml` to in repo nist** |

Zincir FE (vaghe'i `.gitlab-ci.yml`):

```
push master
  → GitLab job deploy_to_server (alpine)
  → SSH ba deploy key
  → nvm use 22
  → git pull ~/dejban_frontend_new_turborepo
  → npm ci --prefer-offline
  → NODE_OPTIONS=3072MB
  → npx turbo run build --concurrency=1 --no-daemon
  → pm2 restart|start dejban_frontend_new_turborepo  (npm start)
  → pm2 save
```

**Band-e gharardad-e jadid:** farz kon / yani chi / chera + **honesty:** in CI = **deploy-only** (lint/test stage nadare); Day 55–57 tools separate.

Day 43 = turbo build story. Day 31 = Docker BE. **In ruz = CI + PM2 deepen.**

---

# BAKHSH-E AVAL: WORLD — GitLab CI + PM2

## Farz kon — postchi + negahban process

**GitLab CI:** postchi — push → pipeline → script on runner.  
**PM2:** negahban Node — crash? restart. reboot? `pm2 save` + resurrect.

Deploy FE Dejban: postchi SSH mizane be server; server khodesh build mikone; PM2 app ro negah midare.

---

## GitLab CI mafahim

| term | ma'ni |
|---|---|
| `.gitlab-ci.yml` | pipeline definition in repo |
| stage | group jobs (build/test/deploy) |
| job | yek unit kar |
| runner | machine ejraye job |
| `only` / `rules` | che branch |
| CI/CD variables | secrets (SSH key, host) |
| artifact | output beyne jobs |

Classic multi-stage:

```yaml
stages: [build, test, deploy]
```

Dejban FE emruz: **faqat `deploy`** — sade, mostaghim.

---

## Do model deploy

| model | yani |
|---|---|
| **Build on CI runner** | artifact → copy server |
| **Build on server (Dejban FE)** | CI faqat SSH + remote script |

**Chera build on server?** Node/Next RAM; server already has nvm; simple single host.  
Tradeoff: deploy load on prod box; no immutable artifact from CI.

---

## PM2 chie?

Process manager for Node:

```bash
pm2 start npm --name myapp -- start
pm2 restart myapp
pm2 status
pm2 logs myapp
pm2 save          # dump process list
pm2 startup       # systemd resurrect (once)
```

| feature | ma'ni |
|---|---|
| name | stable id |
| restart on crash | default |
| cluster mode | multi-core (optional) |
| save/resurrect | survive reboot |

Vs systemd/docker: PM2 Node-centric, quick for Next `npm start`.

---

# BAKHSH-E DOVOM: DEJBAN FE — `.gitlab-ci.yml` khat be khat

## Qesmat 1 — skeleton

```yaml
stages:
  - deploy

deploy_to_server:
  stage: deploy
  image: alpine:latest
  timeout: 2 hours
  only:
    - master
```

**Yani chi:** yek job; faqat `master`; alpine kuchek; timeout 2h (turbo build slow + concurrency 1).

**Chera na feature branches?** Deploy prod-like only from master — reduce accidental deploys.

---

## Qesmat 2 — before_script (SSH prep)

```yaml
before_script:
  - apk add --no-cache openssh-client
  - mkdir -p ~/.ssh && chmod 700 ~/.ssh
  - echo "$SSH_PRIVATE_KEY" > ~/.ssh/deploy_key
  - chmod 600 ~/.ssh/deploy_key
  - ssh-keyscan -H $SSH_HOST >> ~/.ssh/known_hosts
```

**CI variables (GitLab UI, masked):**

| var | naqsh |
|---|---|
| `SSH_PRIVATE_KEY` | deploy key private |
| `SSH_USER` | ssh user |
| `SSH_HOST` | server |
| `GIT_HTTP_CLONE_URL` | clone URL ba token/creds |

**Chera ssh-keyscan?** known_hosts bedune interactive prompt.  
**Chera alpine?** image sari; faqat openssh niaz.

---

## Qesmat 3 — remote script (heredoc)

```bash
ssh ... 'bash -s' <<'ENDSSH'
  set -euo pipefail
  # ... commands on server ...
ENDSSH
```

`set -euo pipefail`: fail-fast; undefined var error; pipe fail propagates.

`'ENDSSH'` quoted: **no local expansion** — `$HOME` etc evaluate **on server**.

---

## Qesmat 4 — Node via nvm

```bash
export NVM_DIR="$HOME/.nvm"
. "$NVM_DIR/nvm.sh"
nvm use 22
```

**Chera 22?** align with modern Next/tooling (engines `>=20`).  
Server must have nvm+22 preinstalled — CI assumes golden host.

---

## Qesmat 5 — git sync

```bash
if [ ! -d ~/dejban_frontend_new_turborepo/.git ]; then
  git clone "$GIT_HTTP_CLONE_URL" ~/dejban_frontend_new_turborepo
fi
cd ~/dejban_frontend_new_turborepo
git fetch origin master
git checkout master
git pull origin master
```

First deploy clones; next pulls.  
Folder name encodes turborepo app identity.

**Smell:** build on same machine that serves — disk/CPU spike during deploy.

---

## Qesmat 6 — install + build (aso)

```bash
npm ci --prefer-offline
export NODE_OPTIONS="--max-old-space-size=3072"
npx turbo run build --concurrency=1 --no-daemon
```

| flag | chera |
|---|---|
| `npm ci` | lockfile-exact, CI-friendly |
| `--prefer-offline` | use cache if present |
| `max-old-space-size=3072` | heap 3GB — Next memory hungry |
| `--concurrency=1` | **anti-OOM** (comment in file) |
| `--no-daemon` | no leftover turbo daemon |

Day 43: turbo *can* parallel; prod server *policy* serialize.

Outputs: `.next/**`, `dist/**` (AC Vite) — turbo.json.

---

## Qesmat 7 — PM2 start/restart

```bash
if pm2 describe dejban_frontend_new_turborepo >/dev/null 2>&1; then
  pm2 restart dejban_frontend_new_turborepo
else
  pm2 start npm --name dejban_frontend_new_turborepo -- start </dev/null >/dev/null 2>&1
fi
pm2 save
```

**Yani chi:**

- Name fixed → idempotent deploys  
- First time: `pm2 start npm -- start` → root `"start": "turbo run start"`  
- Later: restart (picks new build)  
- `pm2 save` → dump for resurrect after reboot  

Redirects on first start: detach from SSH TTY.

**Chera yek PM2 process?** `turbo run start` starts all apps' start scripts under one PM2 entry — simple ops. Tradeoff: one kill affects all; logs mixed unless pm2 ecosystem split later.

---

## Qesmat 8 — chi **nist** to in pipeline (honesty)

| missing | note |
|---|---|
| `lint` / `check-types` stage | not gated here |
| `test:unit` / Playwright | Day 55 — separate / manual / other job |
| `dotnet test` | other repo |
| Build artifact store | build on server |
| Preview env per MR | only master |
| Notifications | optional GitLab |

**Resume caution:** «GitLab deploys FE via SSH+PM2» — na «full CI quality gate in same yml».

---

## Qesmat 9 — turbo `start` after build

`turbo.json`: `start` dependsOn `build`, persistent, cache false.

PM2 restart after successful build → `npm start` → turbo starts Next/Vite preview processes per app scripts.

Ports: main/dejban/AC (Day 42/54) — reverse proxy/nginx usually in front (ops host).

---

# BAKHSH-E SEVOM: DEJBAN BE — Docker honesty

## Qesmat 10 — no `.gitlab-ci.yml` in backend workspace

In-repo deploy surface:

- `Dockerfile` per microservice + gateway  
- `docker-compose.docker-production.yml` — services, health depends_on  
- GlobalAppsettings volume  
- **migrationesho** after code deploy (Day 31 policy)

**WORLD:** backend *could* have GitLab build→push image→compose up; **claim only what's in repo**.

**Contrast:**

| | FE | BE (repo) |
|---|---|---|
| Orchestration file | `.gitlab-ci.yml` | Compose + Dockerfiles |
| Process manager | PM2 | Docker `restart: unless-stopped` |
| Build | turbo on server | `docker build` / compose build |
| Schema | n/a | migrationesho |

---

## Qesmat 11 — Compose production shape (kholase)

Services: identity, dcc, dejban, acl, requesttracker, reporting, gateserver, … + dbs/redis/eventbus health.

Multi-stage .NET 10 images (Day 31).  
Env `ASPNETCORE_ENVIRONMENT=Docker`.

PM2 **na** for .NET APIs here — containers.

---

# BAKHSH-E CHAHAROM: amaliyat PM2 (FE)

## Commands useful

```bash
pm2 status
pm2 logs dejban_frontend_new_turborepo --lines 200
pm2 restart dejban_frontend_new_turborepo
pm2 monit
```

Fail after deploy: check logs → often OOM mid-build (raise RAM / keep concurrency 1) or git auth / nvm.

---

## Crash loop

PM2 restart storm → bad build / env missing `NEXT_PUBLIC_*`.  
Fix env files on server, rebuild.

---

## Reboot

`pm2 startup` once + `pm2 save` after each deploy — process list restored.

---

# BAKHSH-E PANJOM: farz kon / senario

## Se dastan

**1) Merge to master**  
Pipeline green alpine → SSH → pull → build 20–60+ min possible → PM2 restart → users new FE.

**2) OOM during turbo**  
Without concurrency=1 parallel Next builds die. Policy exists for reason.

**3) Backend release**  
Build/push images / compose up → migrationesho → healthchecks. Separate from FE yml.

---

## Smell-ha

1. Deploy-only CI — no automated test gate on same file  
2. Build on prod host — noisy neighbor  
3. Single PM2 name for whole monorepo  
4. Secrets in GitLab vars — rotate keys  
5. `postgres:latest`-style drift n/a here but Node 22 must stay aligned  
6. 2h timeout — long feedback  
7. Backend CI not in this git tree — onboarding confusion  
8. `</dev/null` first start hides errors — check `pm2 logs`  

---

## Debug checklist

| symptom | check |
|---|---|
| Job fail SSH | key, host, known_hosts |
| nvm use fail | Node 22 installed on server |
| npm ci fail | lockfile, registry, disk |
| OOM / killed | NODE_OPTIONS, concurrency 1, free RAM |
| PM2 empty | build failed before start |
| Old UI | CDN/browser cache; wrong app port; pull wrong branch |
| Pipeline not run | not master; CI disabled |

---

## 25 soal-e mosahebe

1. FE deploy tool chain?  
2. stages in yml?  
3. only which branch?  
4. Chera alpine?  
5. SSH vars?  
6. Build koja?  
7. concurrency chera 1?  
8. NODE_OPTIONS?  
9. PM2 name?  
10. pm2 save chera?  
11. npm start yani chi?  
12. Test stage?  
13. Backend gitlab-ci in repo?  
14. BE process manager?  
15. migrationesho link?  
16. --no-daemon?  
17. timeout?  
18. First clone path?  
19. Prefer-offline?  
20. Day 43 link?  
21. Day 55 link?  
22. cluster mode?  
23. MR preview?  
24. set -euo pipefail?  
25. One-liner Day 58?

---

## Senario-ha

**S1:** Add `test` stage before deploy — Playwright smoke / lint.  
**S2:** Split PM2 per app (`dejban`, `main`, `access-control`).  
**S3:** Build in CI → rsync `.next` — less prod CPU.  
**S4:** Backend GitLab: docker buildx → registry → compose pull.  
**S5:** Slack notify on fail.

---

## Mini lab

1. Read FE `.gitlab-ci.yml` end-to-end  
2. Map each CI variable  
3. Trace `pm2 start npm -- start` → root package.json → turbo start  
4. Confirm no test job  
5. Open BE `docker-compose.docker-production.yml` header services  
6. Recall migrationesho Day 31  

---

## Resume (1 paragraph)

> Frontend deploys through **GitLab CI**: an Alpine job SSHs to the app server, pulls `master`, runs **`npm ci`** and **`turbo build --concurrency=1`** (with a 3GB Node heap to avoid OOM), then **PM2** restarts the **`dejban_frontend_new_turborepo`** process (`npm start` / Turbo). The pipeline is **deploy-focused** (not a full test gate). Backend release in this workspace is oriented around **Docker Compose/Dockerfiles** and **migrationesho**, not a checked-in GitLab+PM2 flow.

Keywords: `GitLab CI` · `.gitlab-ci.yml` · `SSH` · `PM2` · `turbo --concurrency=1` · `nvm` · `npm ci` · `pm2 save`

---

## File-haye mohem

| path | chera |
|---|---|
| `dejban_frontend_new/.gitlab-ci.yml` | entire FE deploy |
| `dejban_frontend_new/package.json` | `start`: turbo |
| `dejban_frontend_new/turbo.json` | build/start tasks |
| `dejban_backend_new/docker-compose.docker-production.yml` | BE runtime |
| `*/Dockerfile` | BE images |
| Day 31 / 43 | migrations / turbo |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 31 | Docker BE + migrationesho |
| 43 | turbo concurrency CI |
| 54 | Vite AC in same turbo build |
| 55–57 | tests not in this yml |
| **58** | this |
| 59 | algorithms (interview) |

---

## Chejori digest koni

1. FE = GitLab SSH deploy + PM2  
2. Build on server, concurrency 1  
3. Deploy-only honesty  
4. BE = Docker/migrationesho  
5. Ops commands PM2  

---

## Glossary

| term | ma'ni |
|---|---|
| CI | continuous integration |
| CD | continuous delivery/deploy |
| runner | executes jobs |
| PM2 | Node process manager |
| nvm | Node version manager |
| npm ci | clean lockfile install |
| concurrency 1 | serialize turbo tasks |
| pm2 save | persist process list |
| deploy key | SSH key for Git/server |
| OOM | out of memory kill |

---

## Deep dive — why not ecosystem.config.js

Dejban uses CLI `pm2 start npm --name ... -- start` — no committed ecosystem file.  
Works; less declarative. Future: ecosystem with env, instances, log paths.

---

## Deep dive — security

- Private key only in masked CI var  
- Server user least privilege  
- GIT_HTTP_CLONE_URL may embed token — protect  
- Don't echo keys in logs  

---

## Deep dive — zero downtime?

`pm2 restart` = brief blip.  
Cluster reload / blue-green = advanced — not current script.

---

## Anti-pattern

| bad | better |
|---|---|
| Commit SSH private key | CI variables |
| Parallel turbo on 4GB RAM | concurrency 1 |
| Deploy every branch | only master (+ protect) |
| Assume tests ran | add stage or separate pipeline |
| Claim BE uses same PM2 | Docker honesty |

---

## Interview 60s

«On frontend, GitLab runs a deploy job that SSHs into the server, pulls master, installs with npm ci, builds the Turborepo with concurrency one to avoid OOM, and restarts a PM2 process that runs npm start. Backend shipping is Docker Compose based with migrationesho for schema—not the same GitLab+PM2 file.»

---

## Quick self-test

1. FE CI file? → .gitlab-ci.yml  
2. Branch? → master  
3. Process manager? → PM2  
4. concurrency? → 1  
5. Test stage? → no  
6. BE same? → no / Docker  
7. pm2 save? → persist  

---

## Final checklist

- [ ] GitLab job flow  
- [ ] SSH + vars  
- [ ] turbo build flags  
- [ ] PM2 lifecycle  
- [ ] deploy-only honesty  
- [ ] BE Docker contrast  
- [ ] resume  

---

## Extra — Farz kon forushgah update

GitLab = van-e ersal dastor.  
SSH = kelid anbar.  
turbo build = chidan kala-ye jadid.  
concurrency 1 = yek asansor (RAM kam).  
PM2 = negahban darvaze — restart ba'd az chideman.  
BE = kamyon Docker joda.

---

## Extra — pipeline duration

2h timeout upper bound.  
Typical: npm ci + serialized Next builds — often tens of minutes.  
Optimize later: remote turbo cache, filter changed apps.

---

## Extra — turbo filter in CI (future)

```bash
npx turbo run build --filter=...[origin/master] --concurrency=1
```

Only affected packages — advanced; current = full build safety.

---

## Extra — alpine + apk

Minimal attack/surface; must apk add openssh each job (no persist on shared runners ephemeral).

---

## Extra — heredoc vs ssh command string

Heredoc multi-line readable; quoted delimiter prevents local `$SSH_*` confusion.

---

## Extra — PM2 vs Docker for FE

Team chose PM2 on VM for FE monorepo simplicity.  
Could containerize Next — not current yml.

---

## Extra — monitoring

PM2 monit local; production may use Seq/OTel for APIs (Day 30) — FE errors often browser + pm2 logs.

---

## Band-e gharardad-e jadid

GitLab CI = robot deploy.  
Job alpine = postchi sabok.  
SSH = vorud server.  
nvm 22 = Node version.  
npm ci = install clean.  
turbo concurrency 1 = anti-OOM.  
PM2 = zende negah dashtan.  
pm2 save = ba'd az reboot.  
BE = Compose, na in yml.  
Test = ruz-haye 55–57, na in stage.

---

## 10 jomle fluency

1. Frontend deploys with GitLab CI.  
2. The job SSHs into the server.  
3. It builds with turbo concurrency one.  
4. Node heap is raised to 3GB.  
5. PM2 restarts the turborepo process.  
6. npm start runs turbo start.  
7. Only master triggers deploy.  
8. There is no test stage in that file.  
9. Backend uses Docker Compose instead.  
10. migrationesho runs after backend deploy.

---

## Extra — version / runtime

| item | value |
|---|---|
| CI image | alpine:latest |
| Node on server | 22 via nvm |
| PM2 process name | dejban_frontend_new_turborepo |
| Timeout | 2 hours |

---

## Extra — fail taxonomy

| phase | fail mode |
|---|---|
| before_script | apk/ssh |
| git | auth/clone URL |
| npm ci | lock/network |
| turbo build | OOM/TS/env |
| pm2 | binary missing / name |

---

## Extra — compare GitHub Actions

Same ideas: workflow, secrets, SSH action.  
Dejban uses GitLab — know mapping for interview.

---

## Extra — protected branches

master should be protected + required MR — CI `only: master` complements.

---

## Extra — 10 soalat sari

1. Stages? deploy  
2. Branch? master  
3. Build where? server  
4. concurrency? 1  
5. PM2? yes FE  
6. Tests in yml? no  
7. BE CI file? no in repo  
8. Heap? 3072  
9. start cmd? npm start  
10. save? pm2 save  

---

## Extra — Diagram 30s

Begu: «Push master, GitLab SSHs to the host, pulls and builds the monorepo with Turbo single-threaded, then PM2 restarts npm start. Backend ships via Docker, not that YAML.»

---

## Extra — Common bugs

| symptom | likely |
|---|---|
| Permission denied SSH | wrong key/user |
| Killed build | RAM / concurrency |
| PM2 online old code | build failed silently? check exit |
| Module not found start | build incomplete |
| nvm not found | server bootstrap missing |

---

## Extra — Layer checklist release

| concern | FE | BE |
|---|---|---|
| Trigger | GitLab master | (ops/compose/CI external) |
| Build | turbo on VM | Docker image |
| Process | PM2 | container |
| Schema | — | migrationesho |
| Health | app ports / proxy | compose healthcheck |

---

## Extra — Farz kon add lint job

```yaml
stages: [lint, deploy]
lint:
  stage: lint
  script: npm ci && npx turbo run lint
deploy_to_server:
  needs: [lint]
```

Needs runner with Node — or SSH lint too. Design choice.

---

## Extra — Playwright in CI

Needs browsers + baseURL — heavier; often scheduled pipeline separate from deploy (Day 55).

---

## Extra — rollback FE

```bash
git checkout <prev-sha> && npm ci && turbo build --concurrency=1 && pm2 restart ...
```

Or keep previous `.next` backup — not automated in yml.

---

## Extra — disk full

node_modules + .next multi-app — monitor disk on deploy host.

---

## Extra — Final fluency drill

«GitLab deploys our frontend by SSHing to the server, building Turborepo with concurrency one under a larger Node heap, and restarting PM2. The pipeline does not run the Playwright or Vitest suites. Backend deployment is Docker and migrationesho based.»

---

## Extra — Capacity

Serialize builds = longer deploy, stable RAM.  
Vertical scale server if timeout approached.

---

## Extra — no-daemon detail

Turbo daemon speeds local repeats; CI `--no-daemon` avoids orphan processes on ephemeral/weird SSH sessions.

---

## Extra — prefer-offline detail

Uses npm cache on server between deploys — faster ci when cache warm.

---

## Extra — AC Vite in same deploy

`turbo build` includes access-control `vite build` → `dist/` — same PM2 start must serve/rewrite (Day 54). One pipeline, multi-app.

---

## Khoruj-e zehni

> Midunam FE ba GitLab CI (SSH + turbo concurrency 1 + PM2) deploy mishe; pipeline asosan deploy-e na test gate; BE to in workspace Docker Compose + migrationesho-st, na hamun yml.

Age in paragraph mal-e to shod — Day 58 done.

---

*Day 58 tamum. Ba'd: Day 59 — Algorithms + Big-O (amade). Fehrest: [README.md](./README.md).*