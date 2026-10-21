# 19 — Adapter

---

## Ye khat

Do taraf **az ghabl** sakhte shode-and va be ham nemikhorand. Hich-kodam ra baz nemikonim. Yek shey-e nazok vasat miminad va zaban-e yeki ra be zaban-e digari tarjome mikonad.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

Code-e to `string` farsi baraye toast mikhahad. Server `ProblemDetails` midahad: `title`, `errors`, `traceId`, gahi string-e englisi-e "Bad Request". Library-e HTTP khodash object-e `AxiosError` midahad ba `response`, `config`, `stack`.

Seh shekl. Hich-kodam ghalat nist. Har kodam baraye donya-ye khod dorost ast. Agar toast ra avaz koni ta `traceId` ra balad bashad, UI be HTTP vast shode. Agar server ra avaz koni ta faghat yek string-e sade bedahad, hame-ye client-haye digar ra shekaste-i.

Adapter vasat mimanad ta **hich** taraf avaz nashavad.

## Ta'rif-e GoF

Intent: interface-ye yek class ra be interface-i ke client **entezar** darad tabdil kon. Adapter, be class-hayi ke be khater-e interface-ye nasazgar nemitavanand hamkar konand, emkan-e hamkari midahad.

Do shekl-e ketab:

**Object adapter.** Adapter, adaptee ra **composition** mikonad. `adapter.Message(error)` dakhel-ash `error.response.data` ra mikhanad. Adaptee ra subclass nemikoni. Shekl-e ghalib-e emrooz hamin ast, chon ers-bari az type-e `AxiosError` ya az response-e HTTP bi-ma'ni ast.

**Class adapter.** Adapter az adaptee **inherit** mikonad va method-e client ra ham implement mikonad. Faghat vaghti zaban chand-ersi darad va adaptee mal-e khodet ast. Shekanande-tar, kam-estefade-tar.

Mosahebe: "ma object adapter darim" kafi ast, be shart-e betavani composition ra neshon bedahi.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| Target | interface-i ke client mikhahad (`string` farsi, ya `INewCommand`) |
| Adaptee | chiz-e mojood-e nasazgar (AxiosError, validator-e ghadimi) |
| Adapter | target ra pish-e client bazi mikonad, dakhel adaptee ra seda mizanad |
| Client | faghat target |

Client adaptee ra import nemikonad. Agar konad, adapter-e ekhtiari-e shekaste dari.

## Sakhtar-e object adapter

```
Client -> IMessage.Text()
            Adapter
              - adaptee: HttpError
              - Text() { return pickPersian(adaptee.body) }
```

Yek method-e client. Dakhel, dah field-e bigane. Client an dah ta ra nemibinad.

## Ghanun-ha

**1. Tarjome, na ghanun-e jadid.**
Adapter "email khali na-motabar ast" ra **ejad** nemikonad. An ghanun-e domain ya validator ast. Adapter faghat migoyad "in shekl-e khata, an shekl-e reshte". Agar ghanun-e mahsul inja beravad, do ja ghanun dari va UI va server joda mishavand.

**2. Pure. Bedune I/O.**
Adapter shabake nemizanad, database nemikhanad. Vorudi-e x, khoruji-e y. Test-ash jadval-e vorudi/khoruji ast. I/O an ra service mikonad.

**3. Field-e fanni ra tarjome-ye "baraye ensan" nakon.**
`traceId`, stack, "Internal Server Error" etela'at-e mohandes-and. Adapter-e khoob an-ha ra **hazf** mikonad ya joda migozarad, na inke be toast-e karbar besparad. Tarjome hamishe 1:1 nist. Gahi tarjome = andakhtan.

**4. Default-e akhar gharardad ast.**
Agar adaptee hich chiz-e ghabel-e namayesh nadasht, client `undefined` nabinad. Yek jomle-ye sabet. An jomle khodesh tarjome-ye "nadashtim" ast.

**5. Adapter-e do-jahate (two-way) kam va geran ast.**
Ham A→B ham B→A. Vaghti har do taraf bayad digari ra seda bezanand. Aksar-e adapter-haye to yek-jahate-and. Do-jahate ra esm nabar magar vaghe'an har do rah ra neveshte bashi.

## Ja-haye rayej

- shekl-e khataye HTTP → matn-e UI
- ragham va tagvim-e vorudi-ye ensan → shekl-e gharardad-e API
- object-e ghadimi-e yek ketabkhane → interface-e jadid-e code-e to
- validator-e yek command ke bayad rooye command-e digar, bedune copy, ejra shavad

Akharin mored ziba ast: adaptee validator-e `Create` ast. Target validator-e `Update` ast. Adapter field-haye update ra be shekl-i mirizad ke validator-e create mifahmad. Ghanun-e create copy nemishavad. Type-e create, type-e update ra nemishnasad.

## Farq-ha

**Facade.** Facade subsystem-e **khodet** ra sade mikonad. Adapter interface-ye **bigane** ra jor mikonad. Facade mitavanad dakhel-ash adapter dashte bashad. Esme-ha avaz nashavand.

**Decorator.** Decorator **haman** interface ra wrap mikonad va raftar ezafe mikonad. Adapter interface-ye **digar** misazad. Agar khoruji va vorudi yek gharardad-and, decorator ast. Agar nistand, adapter.

**Mapper (AutoMapper / Mapster).** Map-e field-e ham-nam, ya ham-ma'ni, bein-e do DTO. Adapter vaghti **gharardad** farq darad (khata, ragham, command-e digar), na vaghti `FirstName` → `firstName`. Mapper-e 1:1 adapter-e sabok ast. Agar faghat rename ast, an ra adapter-e GoF boland seda nakon. Agar shekl-e khata ra be shekl-e toast tabdil mikoni, adapter ast.

**Bridge.** Bridge abstraction va implementation ra joda mikonad ta har do **mostaghel** rost konand (az avval tarahi shode). Adapter ba'd-az-sakht-e do chiz-e nasazgar miayad. Bridge pishgiri. Adapter darman. So'al-e klassik-e mosahebe hamin do jomle ast.

## Koja bezan, koja nazan

Bezan vaghti do shekl-e mojood ra nemitavani avaz koni va client nabayad shekl-e bigane ra bebine.

Nazan vaghti khodet har do taraf ra hamin emruz misazi. Pas az avval yek interface besaz. Adapter-e ezafe vasat-e code-e khodet parsa-bazi ast.

## Eshtebah-haye rayej

- Adapter-i ke fetch mikonad
- Andakhtan-e `traceId` to toast "chon to response bud"
- Copy-e ghanun-e validation dakhel-e adapter
- Seda kardan-e har wrapper "adapter", hatta vaghti interface yeki ast (an decorator ya facade ast)

## Mafhoom ra injoori begou

> "Adapter do interface-e az ghabl nasazgar ra, bedune taghir-e hich-kodam, jor mikonad. Shekl-e ghalib object adapter ast: composition, na inheritance. Pure ast, I/O nadarad. Mitavanad field-e fanni ra hazf konad, na faghat rename. Facade sade mikonad, decorator haman interface ra negah midarad, bridge az avval joda tarahi mikonad. Adapter ba'dan vared mishavad."

---

# BAKHSH-E DOVOM — hamin mafhoom to Dejban

**1. Khataye HTTP → jomle-ye UI.**
`packages/api-client/src/getErrorMessage.ts` va `extractErrorMessage.ts`.

Target: `string`. Adaptee: `unknown` / error-e axios / body-ye server. Client-e toast adaptee ra baz nemikonad.

`extractErrorMessage` shekl-haye mokhtalef ra mifahmad va `IGNORED_KEYS` chiz-hayi mesl-e `traceId`, `stack`, `status`, `config` ra rad mikonad. Matn-e englisi-e status-e HTTP ("Bad Request") ra be onvan-e payam-e karbar ghabool nemikonad. In haman "tarjome = andakhtan-e field-e fanni" ast.

`getErrorMessage` agar chizi namand, `'خطای ناشناخته در انجام عملیات!'` barmigardanad. Default-e akhar.

I/O nist. Jadval-e test: ProblemDetails-e farsi → haman jomle. Body-e fanni-e khali → default.

Samt-e server, `ErrorOr` be ProblemDetails tabdil mishavad. An ham adapter-e marz ast (domain HTTP nemishnasad). Do adapter, do marz: server type-e domain ra be HTTP, client HTTP ra be jomle.

**2. Ragham-e ensan → ragham-e gharardad.**
Interceptor `toEnglishDigits` va `normalizeDigitsDeep` ra rooye params, FormData, va JSON mizanad. Keyboard `۱۲۳` mifrestad. API `123` mikhahad. Form-ha adaptee nistan. Yek ja-ye markazi target ra misazad. Agar farda server khodash ragham-e farsi ra bepazirad, haman yek ja avaz mishavad, na 80 form.

In adapter **dakhel-e** chain-e interceptor neshast. Chain pattern-e joda ast. Tarjome-ye ragham pattern-e joda. Yek file, do mafhoom. An-ha ra yek esm nakon.

**3. Validator-e create rooye command-e update.**
`UpdateVisitReservationCommandValidator` class-e dakheli-e `CreateVisitReservationCommandValidatorAdapter` darad. Esm-e khod-e code "Adapter" ast. Ghanun-e create rooye shekl-e update ejra mishavad, bedune inke validator-e create type-e update ra beshnasad. Object adapter-e koochak-e backend. Nokte-ye bakhsh-e avval: faghat ghanun-e **moshtarak**. Agar update yek ghanun-e ekhtelafi darad (id ejbari), an ra koor-koor be create naspar.

---

## Script-e 90 sanie

> "Adapter vasat-e do interface-e nasazgar ast va hich taraf ra edit nemikonad. Object adapter composition ast. Pure ast. Facade sade-sazi ast, decorator haman interface, bridge tarahi-e avval. Front do adapter darad: extractErrorMessage shekl-e axios va ProblemDetails ra be string-e farsi tabdil mikonad va traceId va Bad Request-e englisi ra mindazad. Default-e jomle-ye na-malum darad. Dovom ragham-e farsi be englisi dakhel-e interceptor, ta form-ha joda an ra faramoosh nakonand. Backend validator-e update yek adapter-e dakheli darad ke ghanun-e create ra rooye command-e update ejra mikonad."

---

## 10 soal

**1. Adapter che chizi ra avaz nemikonad?**
Adaptee va client. Faghat vasat tarjome ezafe mishavad.

**2. Object adapter va class adapter?**
Avval composition. Dovom inheritance az adaptee. Avval shekanande-tar nist va baraye type-e bigane dorost ast.

**3. Chera I/O dakhel-e adapter shekast ast?**
Tarjome dige pure nist. Test-e jadval-i az beyn miravad va adapter service-e penhan mishavad.

**4. Farq ba decorator?**
Decorator haman interface, raftar-e ezafe. Adapter interface-ye digar.

**5. Farq ba bridge?**
Bridge az avval abstraction va implementation ra joda mikonad. Adapter do chiz-e az ghabl nasazgar ra ba'dan jor mikonad.

**6. Farq ba mapper-e field?**
Mapper rename-e ham-ma'ni. Adapter vaghti gharardad farq darad, masalan khata-ye HTTP be jomle-ye ensan.

**7. `IGNORED_KEYS` kodam ghanun-e adapter ast?**
Tarjome mitavanad andakhtan bashad. Field-e fanni target-e ensan nist.

**8. Default-e jomle-ye na-malum chera?**
Ta client `undefined` nabinad vaghti adaptee hich matn-e ghabel-e namayesh nadarad.

**9. Ragham-e farsi kodam pattern ast, va chera to interceptor ast?**
Adapter-e shekl-e vorudi. Jay-ash chain-e hame-ye call-ha ast ta yek form faramoosh nakonad. Jay-ash ma'ni-e "interceptor = adapter" nist.

**10. Adapter-e validator-e visit che khatari darad?**
Ghanun-e ekhtelafi-e update (mesl-e ejbari budan-e id) koor-koor az create ers mibarad. Faghat moshtarak-ha ra vasl kon.
