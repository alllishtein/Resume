# Day 50 — SignalR client

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** server event (ticket jadid, plate live, manual access popup, server clock) — FE chejori *zende* begire bedun polling har saniye?

**Javab Dejban:** `@microsoft/signalr` **HubConnectionBuilder** → hub URL (Gateway/YARP) + **`accessTokenFactory`** (JWT LS) + **`withAutomaticReconnect`**.

| hub (FE path) | use-case |
|---|---|
| `/tickethub` | `TicketUpdated` → toast + invalidate Query |
| `/manualaccesshub` | request/resolve + `JoinSite` |
| `/platereaderhub` | live plate events (tab-active only) |
| `/timeserverhub` | `ServerTime` + HTTP poll fallback |
| `/devicehub` | ACL devices (shared singleton `@repo/ui`) |
| gate hubs | gate app connection map |

Day **26** = server hubs. **In ruz = client React hooks + patterns.**

**Band-e gharardad-e jadid:** farz kon / yani chi / chera.

---

# BAKHSH-E AVAL: WORLD — client SignalR

## Farz kon — telephone khat-e baz

HTTP = name (request/response).  
SignalR = telephone: connection open, server mige «ticket omad».

JS package: `@microsoft/signalr`.

```js
const connection = new HubConnectionBuilder()
  .withUrl(hubUrl, { accessTokenFactory: () => token })
  .withAutomaticReconnect([0, 2000, 5000, 10000, 30000])
  .build();

connection.on('EventName', (payload) => { … });
await connection.start();
// cleanup: connection.off(...); connection.stop();
```

**Negotiate + WebSocket** (fallback long-poll) — Gateway must support WS upgrade (Day 07/26).

---

## Auth client

Browser nemitune custom `Authorization` header easy roye WS hamesh — SignalR **`accessTokenFactory`** → token query/`Authorization` per negotiate policy.

Dejban: `tokenStorage.getAccess()` ya `localStorage jwt_access_token` (hamun Day 40 key).

**Smell:** token refresh mid-connection — reconnect / factory re-read on next negotiate. Automatic reconnect helps.

---

## Groups (client invoke)

Server groups (site/user) — client sometimes:

```js
await connection.invoke('JoinSite', siteId);
```

Ba'd az `onreconnected` again join (manual access hub).

---

# BAKHSH-E DOVOM: DEJBAN patterns

## Qesmat 1 — URL resolve

Common comment in hubs:

```js
const raw = CONFIG.signalRUrl || CONFIG.serverUrl || '';
const baseUrl = raw.replace(/\/$/, '');
return `${baseUrl}/tickethub`;
```

Same base as REST (`…/api/v1`) → YARP maps `/Api/v1/tickethub`.  
`CONFIG.signalRUrl` optional override (`@repo/config`).

**Gate app** strips `/api/v1` differently — hub at host root — product-specific.

---

## Qesmat 2 — `useTicketHub`

`sections/cartable/tickets/use-ticket-hub.js`:

- Build connection per mount  
- `on('TicketUpdated')` → callbackRef (stable handler)  
- `start()`, cleanup `off` + `stop`  
- reconnect delays `[0,2s,5s,10s,30s]`

**TicketUnreadListener** (dashboard layout):

- Permission check `myTicketsView` / `ticketCartableView`  
- Initial unread summary Query + toast once  
- On hub event: `queryClient.invalidateQueries(ticketsKeys.all)` + toast if not on ticket page  

**Yani chi:** SignalR → **invalidate TanStack Query** (Day 44) — cache truth refresh.

---

## Qesmat 3 — `useManualAccessHub`

- `enabled` + `siteIds`  
- Events: `ManualAccessRequested`, `ManualAccessResolved`  
- `invoke('JoinSite', siteId)` after start + onreconnected  
- Listener component: dialog queue + approve/reject HTTP + invalidate access logs  

Dashboard mounts `ManualAccessQueueListener` next to tickets (Day 42 layout).

---

## Qesmat 4 — `usePlateReaderHub`

- Event `RealtimePlateReaderAccessLogs`  
- Normalize Pascal/camel payload  
- Skip handshake `{ connected: true }`  
- **Only when `isTabActive`** (workspace tabs) — save connections when tab background  

**Chera tab gate?** Multi keep-alive tabs (Day 46) — don't N plate hubs idle.

---

## Qesmat 5 — `serverClock` (TimeHub hybrid)

Class singleton:

- Prefer SignalR `/timeserverhub` event `ServerTime`  
- Fallback HTTP `getServerTime` every 60s if hub down  
- **Ref-count** connect/disconnect — many forms share one connection  
- Holds time in plain fields — **no React state tick** (no re-render storm)  

`useServerTimeRef` + `isTabActive` → connect when needed.

**Interview:** hybrid push + poll = resilience.

---

## Qesmat 6 — shared `signalR-connection.js` (@repo/ui)

Singleton class:

- `ConfigRegistry.register('signalR', init)`  
- `connect('/devicehub')` one connection  
- `accessTokenFactory` LS  
- `withAutomaticReconnect([...])`  
- `on` / `off` / `disconnect`  

Used access-control `OnlineTerminals` listener.  

**Smell vs hooks:** singleton harder multi-hub; dejban newer code prefers **per-feature hooks** with cleanup.

---

## Qesmat 7 — Gate app

`getSignalRConnection(hubName)` map of connections; `withCredentials: true` (cookie-ish).  
Different base URL strip — know app variance.

---

## Qesmat 8 — callbackRef pattern

```js
const callbackRef = useRef(onEvent);
callbackRef.current = onEvent;
connection.on('X', (p) => callbackRef.current?.(p));
```

**Chera?** avoid restarting connection every parent render when handler identity changes.

---

## Qesmat 9 — Query + SignalR

| push | follow-up |
|---|---|
| TicketUpdated | invalidate tickets keys |
| ManualAccess* | update local queue + invalidate logs |
| Plate live | UI state / append feed (not always Query) |
| ServerTime | ref only |

Don't put huge live streams only in Query cache without thought.

---

## Qesmat 10 — Auth + Guard interaction

Listeners check `authenticated` + `hasComponentAccess` before enabling hub/query.  
No claim → no connection noise (tickets).

---

# BAKHSH-E SEVOM: lifecycle / reliability

## Start / stop

```js
useEffect(() => {
  connection.start().catch(() => {});
  return () => {
    connection.off('Event');
    connection.stop().catch(() => {});
  };
}, [deps]);
```

Strict Mode double-mount: start/stop twice — know React 19 Strict behavior; catch errors quiet.

---

## Automatic reconnect

Default/custom delays.  
After reconnect: re-`JoinSite` / re-subscribe state.  
`onreconnecting` / `onreconnected` / `onclose` logging in singleton.

---

## Token expiry mid-session

Factory reads LS each negotiate — after Axios refresh (Day 44) new token available for reconnect.  
If WS stays open with old identity — server may drop; reconnect picks new token.

---

## Gateway

YARP catch-all hub + JWT (Day 26).  
Client URL must hit same gateway host as API (CORS/credentials less for WS token query).

---

# BAKHSH-E CHAHAROM: farz kon / senario

## Se dastan

**1) Ticket arrives**  
Server TicketHub → client TicketUpdated → invalidate + toast.

**2) Guard at gate needs manual approve**  
JoinSite → ManualAccessRequested → dialog → HTTP approve → Resolved event.

**3) Clock for form submit**  
serverClock hub tick → getNow() at submit without re-render.

---

## Smell-ha

1. Duplicate hub connection patterns (singleton vs hooks)  
2. Silent `.catch(() => {})` — hard debug  
3. Token from LS string key vs tokenStorage inconsistency (plate vs ticket)  
4. Gate URL strip vs dejban append path  
5. No central SignalR provider — each feature owns lifecycle  
6. Payload Pascal/camel dual — normalize everywhere  
7. Memory if forget stop on unmount  

---

## Debug checklist

| symptom | check |
|---|---|
| Never connects | hub URL / gateway WS / token |
| 401 negotiate | accessTokenFactory empty |
| Events miss after site change | JoinSite / deps siteKey |
| Duplicate toasts | Strict Mode / multi listeners |
| Works poll not hub | TimeHub firewall / path |
| Tab inactive no plates | isTabActive intentional |
| CORS WS | gateway host |

---

## 25 soal-e mosahebe

1. HubConnectionBuilder steps?  
2. accessTokenFactory chera?  
3. withAutomaticReconnect?  
4. Day 26 vs 50?  
5. callbackRef pattern?  
6. JoinSite when?  
7. invalidateQueries on event?  
8. serverClock hybrid?  
9. ref-count connections?  
10. Tab activity gate?  
11. Singleton vs hook?  
12. Cleanup off+stop?  
13. CONFIG.signalRUrl?  
14. Negotiate?  
15. Long polling fallback?  
16. Token refresh interaction?  
17. Normalize PascalCase?  
18. Permission before hub?  
19. Gate withCredentials?  
20. onreconnected duties?  
21. Why not only polling?  
22. Multiple hubs same page?  
23. Testing SignalR FE?  
24. YARP role?  
25. Day 50 one-liner?

---

## Senario-ha

**S1:** Two dashboard tabs — plate hub only active tab.  
**S2:** Network drop — reconnect + JoinSite.  
**S3:** Logout — stop hubs (unmount listeners with AuthGuard).  
**S4:** Wrong hub path 404 negotiate — check baseUrl.  
**S5:** Event storm — debounce toast / batch invalidate.

---

## Mini lab

1. Trace TicketUnreadListener → Network WS  
2. Break token → see reconnect fail  
3. Toggle workspace tab — plate connect/disconnect  
4. Stop TimeHub server — see poll fallback  
5. Manual access JoinSite in WS frames  

---

## Resume (1 paragraph)

> Built realtime UI with **`@microsoft/signalr`**: feature hooks (`useTicketHub`, `useManualAccessHub`, `usePlateReaderHub`) and a hybrid **TimeHub**/HTTP `serverClock`, using JWT `accessTokenFactory`, automatic reconnect, site group joins, Query invalidation, and tab-aware connection lifecycle over the YARP-exposed hubs.

Keywords: `SignalR` · `HubConnectionBuilder` · `accessTokenFactory` · `withAutomaticReconnect` · `invoke` · `JoinSite` · `realtime` · `invalidateQueries`

---

## File-haye mohem

| path | chera |
|---|---|
| `use-ticket-hub.js` | ticket client |
| `ticket-unread-listener.jsx` | toast + invalidate |
| `use-manual-access-hub.js` | site groups |
| `manual-access-queue-listener.jsx` | UI queue |
| `use-plate-reader-hub.js` | live plates |
| `hooks/server-time/server-clock.js` | TimeHub hybrid |
| `packages/ui/.../signalR-connection.js` | device singleton |
| `apps/gate/.../signalRConnection.js` | gate map |
| Day 26 booklet | server side |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 07 | YARP |
| 26 | SignalR server |
| 40 | JWT LS |
| 42 | dashboard listeners mount |
| 44 | Query invalidate |
| 46 | workspace tab activity |
| 49 | hasComponentAccess before listen |
| **50** | this |

---

## Chejori digest koni

1. Telephone vs name  
2. Builder + token + reconnect  
3. Four dejban hubs  
4. Query invalidate pattern  
5. Resume  

---

## Glossary

| term | ma'ni |
|---|---|
| HubConnection | client connection object |
| negotiate | handshake choose transport |
| accessTokenFactory | supply JWT |
| invoke | call hub server method |
| on/off | subscribe client method |
| automatic reconnect | retry policy |
| group join | JoinSite etc. |
| hybrid clock | push + poll |

---

## Deep dive — why silent catch?

UX: don't crash layout if hub down.  
Ops: need logging/metrics — smell improve `console.error` sampled.

---

## Deep dive — payload shapes

BE C# often PascalCase; JS camelCase.  
Normalize helpers (`pick`, `payload.Title \|\| payload.title`).

---

## Deep dive — one connection per hub type

Ticket + Manual + Plate + Time = up to 4 WS from dashboard.  
Acceptable intranet; watch mobile.

---

## Anti-pattern

| bad | better |
|---|---|
| start without stop | cleanup effect |
| handler in deps restart hub | callbackRef |
| ignore reconnect groups | JoinSite onreconnected |
| only polling forever | prefer hub + fallback |
| trust event without auth | Guard + BE hub auth |
| put clock in useState 1Hz | ref serverClock |

---

## Interview 60s

«On the client we use HubConnectionBuilder with JWT accessTokenFactory and automatic reconnect. Feature hooks listen to Ticket, ManualAccess, PlateReader, and Time hubs through the gateway. Ticket events invalidate React Query; manual access rejoins site groups after reconnect; the server clock uses SignalR with HTTP polling fallback and ref-counting.»

---

## Quick self-test

1. Package? → `@microsoft/signalr`  
2. Ticket event? → TicketUpdated  
3. Site join method? → JoinSite  
4. Time hub path? → /timeserverhub  
5. Token from? → LS / tokenStorage  
6. Query link? → invalidateQueries  
7. Server day? → 26  

---

## Final checklist

- [ ] Builder pattern  
- [ ] Auth token factory  
- [ ] Feature hubs map  
- [ ] Lifecycle cleanup  
- [ ] Query + Guard + tabs  
- [ ] Hybrid clock  
- [ ] resume  

---

## Extra — Farz kon new hub ClientFoo

1. Server hub Day 26 style  
2. YARP route  
3. `useFooHub` hook copy ticket pattern  
4. Mount listener under dashboard if global  
5. Guard claims if needed  
6. Normalize payload + invalidate keys  

---

## Extra — Soalat chera

**Chera WS?** low latency push.  
**Chera token factory?** authenticate hub.  
**Chera reconnect?** flaky networks.  
**Chera invalidate Query?** single cache truth.  
**Chera tab active?** resource / correctness multi-tab.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «Browser opens authenticated SignalR connections to hubs behind YARP. Hooks subscribe to named events, update UI or invalidate React Query, and clean up on unmount. Time uses hub push with HTTP fallback.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| negotiate 404 | wrong baseUrl path |
| 401 | empty token |
| no events | wrong event name / group |
| memory leak | no stop |
| duplicate handlers | missing off / Strict Mode |
| stale site | no rejoin |
| clock wrong TZ | payload zoneNow parse |

---

## Extra — Layer checklist

| layer | piece |
|---|---|
| Transport | SignalR JS |
| Auth | accessTokenFactory |
| URL | CONFIG + hub path |
| React | hooks + listeners |
| Cache | Query invalidate |
| Server | Day 26 hubs |

---

## Extra — Related days jump

26 server · 07 YARP · 40 JWT · 44 Query · 46 tabs · 49 claims  

---

## Extra — testing

Mock HubConnection; or integration against stub hub.  
E2E hard — prefer unit normalize + listener logic.

---

## Extra — binary / images

Plate pictures may be URLs/base64 in payload — don't block UI thread; lazy image.

---

## Band-e gharardad-e jadid

Hub = otagh goftogu.  
Connection = khat telephone.  
Token = shenasname.  
on = gushi.  
invoke = harf zadan be server.  
Reconnect = redial.  
Invalidate = «list ro dobare bekun».

---

## 10 jomle fluency

1. Client uses @microsoft/signalr.  
2. HubConnectionBuilder sets URL and JWT factory.  
3. Automatic reconnect uses backoff delays.  
4. Ticket hub invalidates React Query.  
5. Manual access joins site groups.  
6. Plate hub runs when tab active.  
7. Server clock prefers TimeHub with HTTP fallback.  
8. callbackRef avoids reconnect storms.  
9. Always stop and off on unmount.  
10. Day 26 is server; Day 50 is browser.

---

## Extra — Comparison SSE / raw WS

SignalR = negotiate + fallback + groups + reconnect helpers.  
Raw WS more control more work.  
SSE one-way — less fit invoke.

---

## Extra — logging strategy

Dev: log reconnect states.  
Prod: sample errors to Seq via API optional — not built-in.

---

## Extra — backpressure

If events faster than UI — queue/drop oldest (manual access dialog).  
Don't await heavy work inside `on` handler.

---

## Extra — TypeScript

Most hooks JS; payload `any`.  
Improve with shared DTO types later.

---

## Band-e gharardad — ye bar digar sade

1. **SignalR JS** = client library.  
2. **Builder** = URL + token + reconnect.  
3. **on** = listen events.  
4. **invoke** = call server (JoinSite).  
5. **hooks** = React lifecycle.  
6. **Listeners** = dashboard side effects.  
7. **Query** = refresh lists.  
8. **serverClock** = hybrid time.  
9. **Guards** = who may listen.  
10. **Cleanup** = stop on unmount.

---

## Extra — Capacity

4 hubs × users = server connections (Day 26 scale).  
Client: prefer tab gating + share TimeHub.

---

## Extra — onboarding checklist

Read Day 26 hub name → find FE hook → Network WS → event payload → UI effect.

---

## Extra — VehiclePolicy agent

Server AllowAnonymous API-key agents — **not** typical browser hook; don't confuse with FE JWT hubs.

---

## Extra — Baskool / SSM streams

Server may stream; FE consumers specialized pages — same Builder patterns if present.

---

## Extra — interview whiteboard

Browser →[JWT]→ Gateway → Hub → Groups → Clients.User/Group → event → invalidate/toast.

---

## Extra — Strict Mode double connect

React 18+ Strict mounts twice in dev — expect two starts; cleanup must be correct or ghost handlers.

---

## Extra — tokenStorage vs raw LS

Prefer `tokenStorage.getAccess()` everywhere (ticket hub) for one key abstraction — plate/time still raw LS in places (**smell unify**).

---

## Extra — connection states

`HubConnectionState`: Disconnected / Connecting / Connected / Disconnecting / Reconnecting.  
serverClock checks state before relying on hub vs poll.  
UI optional badge «offline realtime».

---

## Extra — invoke errors

`JoinSite` `.catch(() => {})` swallow — permission deny silent.  
Better: toast once if critical for UX.

---

## Extra — event naming contract

Server `Clients.User(...).TicketUpdated(dto)` must match client `connection.on('TicketUpdated')` **exact**.  
Rename = break; prefer strongly typed hub server (Day 26) + shared name constants FE.

---

## Extra — scaleout Redis

Server sticky / Redis backplane (Day 26) — client doesn't care except reconnect more if instance drain.

---

## Extra — mobile / battery

Background tabs: browsers throttle WS.  
Tab gating + reduce hubs = friendlier laptops.

---

## Extra — security reminder

Hub `[Authorize]` server — stolen JWT = subscribe events.  
Short access TTL + refresh (Day 40).  
Don't put secrets in push payloads.

---

## Extra — logging Network tab

Filter WS frames; see JSON payloads.  
Failed negotiate often appears as HTTP before WS.

---

## Extra — comparison polling interval

Unread tickets poll? Dejban uses hub + initial summary fetch.  
Clock poll 60s only as fallback — not primary.

---

## Extra — ManualAccess dialog race

Requested then quick Resolved — UI must handle resolve for unknown id gracefully.

---

## Extra — plate handshake

`connected: true` payload ignored — avoid fake plate row.  
Know agent/server handshake shapes.

---

## Extra — ConfigRegistry signalR

`@repo/ui` singleton auto-inits when `ConfigRegistry.set(CONFIG)` (ClientInit Day 42).  
Device pages use connect(deviceHub) after config set.

---

## Extra — when NOT SignalR

CRUD forms → HTTP.  
One-shot download → HTTP.  
SignalR for **push fan-out** and live ops.

---

## Extra — hub path casing

YARP + IIS may be case-insensitive; keep FE paths lowercase as in code (`/tickethub`).  
Mismatch still fails on Linux containers.

---

## Extra — stop vs dispose

`stop()` async — await in cleanup with `.catch`.  
Don't reuse stopped connection; build new (hooks do).

---

## Khoruj-e zehni

> Midunam FE SignalR ba HubConnectionBuilder + JWT factory + reconnect; hub-haye ticket/manual/plate/time; JoinSite; invalidate Query; serverClock hybrid; tab-active; va cleanup off/stop — server details Day 26.

Age in paragraph mal-e to shod — Day 50 done.

---

*Day 50 tamum. Ba'd: Day 51 � FE patterns (`*.http.js` / feature folders) (amade). Fehrest: [README.md](./README.md).*
