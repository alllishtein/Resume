# 18 — Facade

---

## Ye khat

Yek subsystem chand class va chand gharardad-e zesht darad. Facade **yek vorudi-ye sade** jelo-ye an mizarad. Client subsystem ra nemibinad. Faghat haman vorudi ra mibinad.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

Ferestadan-e yek SMS shayad in-ha ra bekhad: sakhtan-e client, login-e vendor, map-e shomare, retry, tarjome-ye code-e khata, bastan-e connection. Agar har safhe in shesh ta ra balad bashad:

- taghir-e vendor = taghir-e har safhe
- yek safhe retry ra faramoosh mikonad
- test-e safhe bedune vendor-e vaghe'i sangin mishavad

Facade yek method ast: `sendSms(to, text)`. Shesh ta posht-e an. Safhe vendor ra nemishnasad.

## Ta'rif-e GoF

Intent: interface-ye sath-bala-ye **vahed** bedeh be yek subsystem, ta estefade-ye an asan-tar shavad. Facade chand class-e dakheli ra orkestre mikonad. Client-ha faghat facade ra mishenasand.

Nokte-ye ketab ke aksaran ja mioftad: facade **mamnoo'iyat** nist. Class-haye dakheli hanuz public-and baraye kasi ke kar-e pishrafte mikhahad. Facade rah-e **addi** ra sade mikonad. Agar hame-ye rah-haye pishrafte ra ham az facade pass-through koni, sade-gi tamoom shode. Shode proxy-ye sholugh.

## Sherkat-konande-ha

| Naghsh | Kar |
|---|---|
| Facade | API-e kam-vaghf, zaban-e client |
| Subsystem | class-haye zesht-e dakheli. Yekdigar ra mishenasand |
| Client | faghat facade |

Client `new` rooye class-e dakheli-e subsystem nemizanad. Agar bezanad, facade-ye ekhtiari-e bi-arzesh dari va rah-e dovom-e pichide baz mimanad.

## Sakhtar

```
Safhe --> SmsFacade.send(to, text)
              |-- AuthClient
              |-- PhoneNormalizer
              |-- VendorSdk
              |-- ErrorMapper
```

Felesh-e safhe faghat be facade ast. Felesh-haye dakheli az safhe penhan-and.

Chand laye-ye facade ham mojaz ast, be shart-e har laye **danesh-e joda** ra penhan konad:

```
View  -->  "list ra bekesh"          (nemidanad cache chist)
Hook  -->  cache + invalidate        (nemidanad URL)
Http  -->  URL + method              (nemidanad header-e token)
Client --> token, retry, ragham
```

In "se class-e facade-ye too-daro" ast. GoF yek class keshide. Mafhoom haman ast: har client-e bala, zir-e khod ra kam mibinad. Agar har laye haman danesh ra dobare repeat konad, laye-ye ezafe dari, facade na.

## Ghanun-ha

**1. Facade zaban-e client ra harf mizanad, na zaban-e vendor.**
`sendSms` na `vendor.post("/v2/messages", { msisdn, tpl })`. Agar emzaye facade haman JSON-e vendor bashad, chizi penhan nashode.

**2. Yek facade, yek subsystem.**
`Utils.sendSms` va `Utils.parseExcel` va `Utils.hashPassword` facade nist. Kise-ye god ast. Facade-ye SMS faghat SMS.

**3. Business-e mahsul ra posht-e facade-ye transport qayem nakon.**
"In shift ghablan publish shode, digar edit nashavad" ghanun-e domain ast. Facade-ye HTTP an ra balad nist. Agar balad shavad, ham transport ast ham ghanun, va test-e ghanun be shabake vasl mishavad.

**4. Facade-ye khoob orkestre mikonad, algorithm-e jadid-e penhan-e khatar nak.**
Retry va map-e khata orkestrasyon-e subsystem-and. "Gheymat ra inja hesab kon chon server nemidanad" algorithm-e jadid-e khatar ast. Do manba'-e gheymat.

**5. Rah-e pishrafte mitavanad kenar-e facade baz bemanad.**
GoF in ra mojaz midanad. Vali rah-e addi nabayad majbur be rah-e pishrafte bashad. Agar har call bayad `config` 20 field-i pas bedahad, facade shekaste.

## Farq-ha — so'al-e hatmi-e se-ta'i

| | Facade | Adapter | Mediator |
|---|---|---|---|
| Hadaf | sade kardan-e **yek** subsystem | jor kardan-e **do** interface-e nasazgar | colleague-ha yekdigar ra neshanasand |
| Shekl-e khoruji | API-e jadid-e rahat | API-e samt-e digar, hamon ke hast | vasete-ye bein-e chand object-e ham-arz |
| Dakhel | chand class ke ghablan ham-dashe-and | yek adaptee | chand colleague-e mostaghel |

Adapter `ErrorResponse`-e vendor ra be `string`-e farsi-e to tabdil mikonad. Facade `sendSms` ra sade mikonad va **daroon-ash** mitavanad yek adapter ham dashte bashad. Facade adapter ra **dar bar migirad**. Adapter facade nist.

Mediator bein-e object-hayi ke **ham-arz**-and mistanad ta be ham vast nashavand. Facade bein-e client-e **balatar** va subsystem-e **pa'intar** mistanad. Jahat-e felesh farq darad.

## Koja bezan, koja nazan

Bezan vaghti chand call-e hamishegi-e posht-e sar-e ham dari va nemikhahi har client an tartib ra balad bashad.

Nazan vaghti yek function-e yek khati ra `XxxFacade` minami va hich tartibi posht-ash nist. Esm-e bozorg, joda'i-e sefr.

## Eshtebah-haye rayej

- God utils
- Pass-through-e hame-ye option-haye vendor
- Ghanun-e business dakhel-e facade-ye HTTP
- Do rah: yeki facade, yeki import-e mostaghim-e SDK. Rah-e dovom taghir-e vendor ra shekaste mikonad

## Mafhoom ra injoori begou

> "Facade vorudi-ye sade-ye yek subsystem ast. Client class-haye dakheli ra new nemikonad. Zaban-ash zaban-e client ast na vendor. Yek facade yek subsystem. Adapter do interface-e nasazgar ra tarjome mikonad va mitavanad dakhel-e facade bashad, khodesh facade nist. Mediator ham-arz-ha ra az ham joda mikonad. Facade bala ra az pa'in joda mikonad. Business-e mahsul ra to facade-ye transport nemizaram."

---

# BAKHSH-E DOVOM — hamin mafhoom to front-e Dejban

Chand laye, har kodam facade-ye pa'in-e khod:

```
page.jsx
  -> View (sections/...)
      -> hook to services/*.service.js      cache, enabled, invalidate
          -> tabe' to services/*.http.js     URL va method
              -> apiClient                   token, site, refresh, ragham
```

View `axios` ra import nemikonad. Service `Authorization` ra nemidanad. Http `queryClient` ra nemidanad. In haman "har laye danesh-e pa'in ra penhan karde".

Mesal: `useDutyCycles` to `duty-roster.service.js` faqat `queryKey` va `getDutyCycles(params)` ra midanad. `getDutyCycles` to file-e http/https URL ra midanad. File-e duty roster `duty-roster.https` nam darad. Gharardad-e module `*.http.js` ast. `.https` esm-e miras ast, pattern-e dovom nist. To mosahebe begou ta do olgu seda nakoni.

`empType` shekl-e tamiz-tar: `emp-type.keys.js` joda, http joda, service joda. Hoviat-e cache (ketabche-ye ghabl) va transport joda mimanand.

`createItem(url, data)` va `getWithParams` to `axiosInstance.ts` facade-ye **kheili koli** hastand. URL hanuz male caller ast. `getDutyCycles` URL ra ham ghom mikonad. Dovomi facade-ye feature ast. Avvali faghat kotah-kardan-e `axios.post`. Arzesh-e dovomi bishtar ast.

`IEndpoint` va `AddPersonnelsModule()` samt-e server haman fekr-and, ba esm-e digar: yek vorudi (`MapEndpoint` / `AddXxxModule`) va subsystem-e posht-ash. Agar porsidand "faghat front facade darad?" na. Vali mesal-e roozane-ye to laye-ye http ast.

Ghanun-e "in shift ra dobare publish nakon" to `*.http.js` nist. Server an ra darad. Facade-ye front transport mimanad.

---

## Script-e 90 sanie

> "Facade yek vorudi-ye sade jelo-ye subsystem ast. Client dakheli ra new nemikonad. Farq-ash ba adapter: adapter tarjome mikonad, facade sade mikonad. Farq-ash ba mediator: jahat-e bala-be-pa'in, na ham-arz. Front-e Dejban se laye darad: hook cache ra midanad, http URL ra, apiClient token va refresh ra. View axios nemibinad. duty roster file-ye .https darad vali gharardad .http ast. createItem URL ra penhan nemikonad, getDutyCycles mikonad. Ghanun-e business to http nist."

---

## 10 soal

**1. Facade che felesh-i ra hazf mikonad?**
Felesh-e client be class-haye dakheli-e subsystem. Faghat felesh be vorudi-ye sade mimanad.

**2. Chera pass-through-e hame-ye option shekast ast?**
Chon client dobare zaban-e vendor ra balad ast. Chizi sade nashode.

**3. Facade va adapter?**
Facade sade mikonad. Adapter do gharardad-e nasazgar ra jor mikonad. Facade mitavanad dakhel-ash adapter dashte bashad.

**4. Facade va mediator?**
Facade bala va pa'in. Mediator chand ham-arz. Jahat farq darad.

**5. Chand laye-ye facade key dorost ast?**
Vaghti har laye danesh-e motefaveti ra penhan mikonad. Vaghti hamash yek danesh-e tekrar ast, laye-ye ezafe ast.

**6. Business rule to facade-ye HTTP?**
Na. Transport va orkestr-e call. Ghanun-e mahsul server ya domain ast.

**7. To Dejban view che chizi ra nemidanad?**
URL, header, refresh, va shekl-e axios. Hook va http an ra penhan karde-and.

**8. `.https.js` pattern-e joda ast?**
Na. Esm-e miras. Gharardad `*.http.js` ast.

**9. `createItem` che kam darad nesbat be `getDutyCycles`?**
URL hanuz caller ast. Facade-ye feature URL ra ham male feature mikonad.

**10. Rah-e dovom-e import-e mostaghim-e axios to view che moshkeli darad?**
Taghir-e token ya refresh yek view ra ja migozarad. Facade-ye ekhtiari-e shekaste.
