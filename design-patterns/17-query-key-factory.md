# 17 — Hoviat-e cache va Query Key

---

## Ye khat

Cache faghat vaghti kar mikonad ke bedani **in dade haman dade-ye ghabli ast ya na**. An tasmim ra "hoviat" migoyand. Factory-e key ja-i ast ke hoviat **yek bar** tarif mishavad, ta nevisande va batel-konande do esm-e mokhtalef nasazand.

Factory inja pattern-e koochak-e avval-e ketabche-ye factory ast. Mafhoom-e bozorg-tar **hoviat-e cache** ast. An ra avval yad begir.

---

# BAKHSH-E AVAL — khode pattern

## Moshkel

UI list-e "personnel-haye site-e A, safhe-ye 2, filter-e ali" ra mikeshad. Dafe-ye ba'd haman safhe ra baz mikoni. Do rah:

- dobare shabake. Dorost, vali kond va por-tekrar
- haman hafeze-ye ghabli. Sari', vali **faghat** agar motma'en bashi haman list ast

Agar cache-e "personnel" yek kisse-ye bi-esm bashad, filter-e ali va filter-e reza yek javab-e ghalat share mikonand. Agar har component yek esm-e dasti besazad (`"personnel-list"` va `"personnel_list"` va `"Personnel?"`), do cache-e morde dari: yeki ra update mikoni, digari rooye safhe mimanad.

## Ta'rif-e hoviat

Hoviat-e yek entry-e cache = hame-ye chizi ke **natije-ye server** ra avaz mikonad, va hich chiz-e ezafe.

Baraye yek list-e ma'mool:

- kodam manba' (personnel, na vehicle)
- kodam shekl (safhe-ye tak, na infinite)
- kodam vorudi (filter, sort, shomare-ye safhe, andaze-ye safhe, tenant)

Tenant joz'-e hoviat ast. Do site yek JSON nistan. Faramoosh-e tenant bug-e "dade-ye site-e ghabli rooye site-e jadid" ast. Az bug-haye klassik-e cache-e UI.

Chizi ke natije ra avaz **nemikonad** joz'-e key nist: makhfi budan-e yek kolon-e jadval, baz budan-e modal, scroll. An-ha state-e namayesh-and. Gozashtan-eshan to key, cache ra shekaf mikonad va hit ra az beyn mibarad.

## Batel kardan (invalidation)

Neveshtan (mutation) haghighat-e server ra avaz mikonad. Cache-e ghabli dorough mishavad. Do rah:

**Batel kon.** Begou "in hoviat dige ghabel-e etemad nist". Dafe-ye ba'd ke UI an ra mikhahad, dobare migirad. Sade. Yek request-e ezafe.

**Be-rooz-e khoshbinane (optimistic) ya set-e dasti.** Cache ra haman lahze avaz kon, bad server ra seda bezan. Agar server rad kard, bargard. Sari'-tar, va por az race. Baraye form-e bozorg aksaran batel-kardan-e sade kam-khatar-tar ast.

Batel-kardan **bayad haman hoviat** ra beshnasad. Agar nevisande key-e `['personnel', id]` ra update konad va khandan key-e `['personnel','detail',id]` bashad, batel-kardan be kisse-ye digar rafte. Safhe dorough mimanad. In bug-e "key-e dasti-e do ja" ast.

## Pishvand (prefix)

Hoviat-e sakhtari:

```
['personnel']                          hame-ye chiz-e in manba'
  ['personnel', 'list', { site, q }]   yek list-e khas
  ['personnel', 'detail', id]          yek record
```

Batel-kardan-e `['personnel']` ya'ni "har chizi ke ba in **shoru** mishavad". List va detail har do. Batel-kardan-e `['personnel','detail',id]` faghat yek record.

Ghanun: az omumi be joz'i benevis. Pishvand-e moshtarak amdi ast, na tasadof-e string.

Hazine-ye pishvand-e kheili omumi: yek edit-e koochak, 40 list-e bi-rabt ra ham refetch mikonad. Hazine-ye pishvand-e kheili joz'i: yek list-e digar dorough mimanad. Entekhab-e "kodam pishvand ra batel konam" joz'-e tarh ast.

## Factory chera vasat-e in mafhoom neshaste

Factory inja algorithm-e sakht-e object nist. Yek ja-ye **tanha** baraye sakhtan-e array-e hoviat ast.

```javascript
const personnelKeys = {
  all: ['personnel'],
  list: (params) => ['personnel', 'list', params],
  detail: (id) => ['personnel', 'detail', id],
};
```

Khandan: `personnelKeys.list(params)`.
Ba'd az save: `invalidate(personnelKeys.all)`.

Do call az yek tabe'. Typo-ye string-e joda az beyn miravad. Agar farda `'personnel'` shavad `'staff'`, yek file avaz mishavad.

Factory-e bad: `all` yek string bashad va `list` string-e digar, va invalidate ja-ye sevom string-e sevom. Esm-e factory dari, hoviat-e vahed na.

## Ghanun-ha

**1. Haman vorudi, haman key. Vorudi-ye motefavet, key-e motefavet.**
Do filter do cache. Yek filter yek cache.

**2. Key bayad ghabel-e moghayese-ye sakhtari bashad.**
Do object-e `{a:1}` va `{a:1}` agar library structural hash konad yeki-and. E'temad-e "reference-e object" shekaste ast, chon har render object-e jadid misazad va cache hichvaght hit nemishavad. Az an taraf, `{a:1, b:undefined}` va `{a:1}` shayad do hash bashand. Vorudi ra **ghabl** az key normalize kon: field-e khali ra hazf kon, sort-e sabet.

**3. `undefined` be onvan-e id key-e vaghe'i nasaz.**
`detail(undefined)` yek kisse-ye moshtarak-e "hanuz id nadaram" misazad va ba record-e ba'di ghalt share mishavad. Ta id nist, fetch nakon (`enabled: false`). Key-e morde nasaz.

**4. Shekl-e dade joz'-e hoviat ast.**
List-e safhe-bandi va list-e infinite (safhe-ha-ye anbashte) yek JSON nistan. Do key. Share-e an-ha bug-e "safhe-ye 2 ja-ye safhe-ha-ye 1..n" ast.

**5. Key-e kheili bozorg cache ra shekaf mikonad.**
Gozashtan-e kole form-e 40 field, hatta field-hayi ke server nemikhanad. Har taghir-e bi-asar, miss-e cache.

## Farq-ha

**URL be onvan-e key.** Nazdik, vali `/a?b=1&c=2` va `/a?c=2&b=1` do string-and va yek dade. Factory-e normalize-shode an-ha ra yeki mikonad. URL-e kham na.

**Cache-e HTTP-e browser.** Hoviat-ash URL + header ast va dast-e to nist. Cache-e client-e query dast-e to ast: mitavani ba'd az mutation daghighan haman manba' ra batel koni. Browser an gharardad-e business ra nemidanad.

**Zustand.** State-e client. Query cache state-e **server**. Do manba'. Copy kardan-e list-e server be Zustand do haghighat misazad.

## Eshtebah-haye rayej

- string-e dasti to component va string-e dige to `invalidate`
- faramoosh-e tenant to key
- `enabled` bedune tafkik, va fetch-e `detail(undefined)`
- batel-kardan-e hame-ye app ba'd az har save ("ta hatman taze bashad"). Kar mikonad va cache ra bi-ma'ni mikonad

## Mafhoom ra injoori begou

> "Cache bedune hoviat javab-e ghalat-e kasi digar ra neshan midahad. Hoviat = manba' + shekl + vorudi-hayi ke server ra avaz mikonand, az jomle tenant. Pishvand-e sakhtari batel-kardan-e daste-bandi midahad. Factory tanha ja-ye sakhtan-e an hoviat ast ta khandan va invalidate az ham joda nasavand. Object-e key structural ast, pas vorudi ra normalize mikonam. Id-e undefined fetch nemishavad. List va infinite do hoviat-and."

---

# BAKHSH-E DOVOM — hamin mafhoom to front-e Dejban

Shekl-e dorost: `apps/dejban/src/services/employment-type/emp-type.keys.js`

```javascript
export const empTypeKeys = {
  all: ['empType'],
  list: (params) => ['empType', 'list', params],
  infinite: (params) => ['empType', 'infinite', params],
  pagination: (params) => ['empType', 'pagination', params],
  detail: (id) => ['empType', 'detail', id],
};
```

`all` pishvand ast. `invalidateQueries({ queryKey: empTypeKeys.all })` list va detail va infinite va pagination ra ba ham mishavad, chon TanStack prefix match mikonad. `infinite` joda az `pagination` ast. Haman ghanun-e "shekl-e dade joz'-e hoviat".

Params dakhel-e key ast. Do filter do entry. TanStack key ra hash-e sakhtari mikonad, na reference-ye React. Hanooz field-e `undefined` ra normalize kon ta do shekl-e "khali" do cache nasavand.

**Jaye shekaste-ye hoviat-e vahed**, ta an ra be onvan-e "hamin-ja ham dorost ast" nagoyi:

`duty-roster.service.js` factory-e `dutyRosterKeys` darad (`cycles`, `roster`, ...). Invalidate-e ba'd az mutation hanooz string-e joda ast:

```javascript
await client.invalidateQueries({ queryKey: ['duty-cycles'] });
```

In **alan** kar mikonad chon `cycles(params)` ba `['duty-cycles', params]` shoru mishavad va prefix match ast. Vali do manba'-e esm dari. Rename-e factory, string-e invalidate ra ja migozarad. Cache-e zende va cache-e morde. Jomle-ye mosahebe: "gharardad-e `empTypeKeys` in ast ke `all` va `list` az yek pishvand biyayand va invalidate haman tabe' ra seda bezanad. Duty roster hanuz string-e joda darad va an shekaf-e hoviat ast."

`queryFn` factory nist. Factory esm misazad. Gereftan-e dade `*.http.js` ast. Ghalt kardane-shaan hoviat va transport ra yek file-ye bi-marz mikonad.

---

## Script-e 90 sanie

> "Cache hoviat mikhahad: manba', shekl, vorudi, tenant. Chiz-e namayeshi to key nist. Pishvand-e omumi batel-kardan-e daste-bandi midahad. Factory tanha sakhtan-e an array ast ta do string-e dasti joda nasavand. empTypeKeys hamin ra darad: all, list, infinite, pagination, detail. Infinite va safhe-ye tak do shekl-and. Invalidate-e all hame ra mishavad chon prefix ast. Duty roster factory darad vali yek ja string-e jodagane ham invalidate mikonad. Kar mikonad ta vaghti esm-ha yeki bemanand. An ra shekaf-e gharardad midanam, na pattern-e dovom."

---

## 10 soal

**1. Hoviat-e cache chist?**
Majmoo'e-ye hame-ye vorudi-hayi ke javab-e server ra avaz mikonand. Na bishtar, na kamtar.

**2. Chera tenant joz'-e key ast?**
Chon dade-ye do tenant yek javab nist. Cache-e bedune tenant data-ye ghabli ra rooye tenant-e jadid neshan midahad.

**3. Pishvand che mikonad?**
Batel-kardan-e `['personnel']` har key-i ke ba an shoru shavad ra mishavad, bedune list-e dasti-e har safhe.

**4. Chera factory?**
Ta khandan va invalidate az yek tabe' key besazand. Do string-e dasti do kisse-ye bi-khabar-e ham-and.

**5. Object-e jadid-e har render cache ra miss mikonad?**
Agar key reference-e shakhe'i bashad bale. Agar hash-e sakhtari bashad na, be shart-e field-haye sabet. `undefined` ra normalize kon.

**6. `detail(undefined)` che bug-i ast?**
Yek kisse-ye moshtarak baraye "id nadaram" va ehtemal-e share-e ghalat. `enabled: false` ta id biaid.

**7. Infinite va pagination chera do key?**
Shekl-e zakhire-shode yeki nist. Share-e cache safhe ra kharab mikonad.

**8. Batel-kardan-e hame-ye app ba'd az har save?**
Taze mimanad va cache digar cache nist. Kam-tarin pishvand-i ke dade-ye dide-shode ra mipooshand.

**9. `empTypeKeys.all` che array-i ast va chi ra mipooshand?**
`['empType']`. List, detail, infinite, pagination. Chon hame ba haman pishvand shoru mishavand.

**10. Shekaf-e duty roster chist?**
Factory `dutyRosterKeys` ast vali invalidate string-e `['duty-cycles']` joda neveshte shode. Prefix alan yeki ast. Do manba'-e esm hanuz hast.
