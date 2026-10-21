# 18 — Facade

*UI yek dar-e sade mibinad. Axios, URL, va shekl-e error posht-e an-and.*

---

## Ye khat

Facade yek interface-e koochak jelo-ye yek subsystem-e pechide ast. Client `getDutyCycles(params)` seda mizanad. Nemidanad base URL, header, interceptor, va inke response `.data` ast.

## Shekle in frontend

```
page.jsx
  → View (sections/...)
      → hook: useDutyCycles          services/*.service.js
          → queryKey factory
          → getDutyCycles             services/*.http.js ya *.https.js
              → apiClient.get        packages/api-client
                  → interceptor-ha
```

Har laye yek kar:

| Layhe | Midanad | Nemidanad |
|---|---|---|
| page / view | chi neshan bedahad | URL |
| `*.service.js` | cache, mutation, invalidate | header-e bearer |
| `*.http.js` | URL va method | refresh-e 401 |
| `apiClient` | token, site, ragham, 503 | kodam feature |

In **se** facade-e too-daro ast, na yek class-e `ApiFacade`. Mosahebe hamin ra ghabool mikonad age daghigh bashi: "har laye facade-e laye-ye pa'in ast."

## Mesal-e duty roster

`duty-roster.service.js` az `./duty-roster.https` import mikonad (`getDutyCycles`, `publishDutyCycle`, ...). Hook:

```javascript
export const useDutyCycles = (params, enabled = true) =>
  useQuery({
    queryKey: dutyRosterKeys.cycles(params),
    queryFn: () => getDutyCycles(params),
    enabled,
  });
```

View `useQuery` va axios ra ba ham ghalt nemikonad. File-e `.https.js` esm-e ghalat-e miras ast (bayad `.http.js` bashad). Pattern-e gharardad-e module: `*.http.js`. Begou esm-e miras ra, ta fekr nakonand do olgu dari.

`empType` shekl-e tamiz-tar: `emp-type.keys.js` joda, http joda, service joda.

Helper-haye `createItem` / `updateItem` / `getWithParams` to `axiosInstance.ts` facade-e **kheili** koli hastand: URL ra hanooz caller midahad. Facade-ye feature (`getDutyCycles`) URL ra ham ghom mikonad. Dovomi arzeshesh bishtar ast.

## Backend ham facade darad, ba esm-e digar

`IEndpoint` yek method `MapEndpoint` ast. `Program` handler-e har route ra nemishnasad. An facade-e koochak-e "in module route-hayash ra khodash sabt kon" ast, na facade-e klasik-e GoF ba dah method. An ra faghat age porsidand "front tanha facade darad?" begou.

Module-e `AddPersonnelsModule()` ham yek facade-e DI ast: sad `AddScoped` posht-e yek method.

## Key facade zede-pattern mishavad

- Class-e `Utils` ke 80 method-e bi-rabt darad. Facade bayad **yek** subsystem ra bepooshand.
- Facade-i ke hame-ye option-haye axios ra pas dahad (`config` ra az 4 laye rad koni). Pas chizi penhan nashode.
- Business rule dakhel-e `*.http.js`. An ja faghat transport ast. Ghanun-e "in shift ghablan publish shode" ya to UI-e koochak ast ya, behtar, to server.

## Farq

| | Facade | Adapter |
|---|---|---|
| Hadaf | sade kardan-e yek subsystem | tarjome-ye do interface-e nasazgar |
| Shekl | API-e jadid-e rahat | API-e mojood-e samte digar |
| Inja | `getDutyCycles` | `getErrorMessage` (ketabche-ye 19) |

## Script-e 60 sanie

> "Safhe axios ra import nemikonad. Hook-e service cache ra midanad va tabe'-e http ra seda mizanad. Tabe'-e http faghat URL va method ast. `apiClient` header, refresh, va ragham ra midanad. Har laye facade-e pa'in ast. Esm-e `.https.js` to duty roster miras ast, gharardad `*.http.js` ast. Business rule ra to http nemizarim."

---

## 10 soal

**1. Facade che moshkeli ra hal mikonad?**
Tedad-e dependency-e zehni. Caller yek method mibinad, na dah class-e subsystem.

**2. Inja class-e Facade ko?**
Layhe-ha: `service` → `http` → `apiClient`. Esm-e class mohem nist. Joda budan-e danesh mohem ast.

**3. Chera http va service joda-and?**
Http ra bedune React test mikoni (URL, method, body). Service ra baraye cache va invalidate. Ghalt kardan-e an-ha har taghir-e UI ra be URL michasbanad va baraks.

**4. `createItem(url, data)` facade-ye kafi ast?**
Baraye kam kardan-e `axios.post` bale, baraye feature na. Caller hanuz URL-e magic darad. `getDutyCycles` URL ra mal-e feature mikonad.

**5. Facade va repository-e backend?**
Har do "posht-e man ra nabin". Repository jolo-ye database ast. Http facade jolo-ye HTTP ast. Handler `DbContext` ra nemibinad, view `axios` ra nemibinad.

**6. Error ra facade partab konad ya tarjome konad?**
Http mitavanad error-e kham-e axios ra rad konad. Tarjome be jomle-ye farsi kar-e adapter (`getErrorMessage`) ast ta http ham transport bemanad va ham UI. Yek laye, yek dalil.

**7. Invalidate koja?**
Service, ba'd az mutation, chon service key ra midanad. Http nabayad `queryClient` bebine. An shekastan-e facade ast.

**8. Chand app (`dejban`, `gate`, `dcc`) yek client?**
`export const apiClient = createApiClient(...)` yek instance-e moshtarak. Facade-ye transport yek dane ast. Facade-ye feature per app mimanad chon URL-e feature yeki nist.

**9. Over-facade?**
Wrapper-e 1 khati dore-ye har chiz, bedune joda kardan-e danesh. Age `getX` faghat `apiClient.get` ast va hich URL-e sabeti nadarad, laye-ye ezafe ast.

**10. Test?**
Http: mock-e `apiClient` va expect-e path. Service: mock-e tabe'-e http, na mock-e interceptor. Interceptor test-e joda-ye `createApiClient` ast. Har laye dobare test-e laye-ye pa'in ra tekrar nemikonad.
