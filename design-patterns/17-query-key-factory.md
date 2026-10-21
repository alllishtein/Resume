# 17 — Kelid-e cache

Cache faghat vaghti kar mikonad ke bedani in dade haman dade-ye ghabli ast ya na. An tasmim ra hoviat miguyand. Factory-e key ja-i ast ke hoviat ye bar ta'rif mishavad, ta nevisande va batel-konande do esm-e mokhtalef nasazand.

Factory inja pattern-e koochak ast. Mafhum-e bozorg-tar hoviat-e cache ast.

## Moshkel

UI list-e "personnel-haye site-e A, safhe-ye 2, filter-e ali" ra mikeshad. Dafe-ye bad haman safhe ra baz mikoni.

Agar cache-e "personnel" ye kisse-ye bi-esm bashad, filter-e ali va filter-e reza ye javab-e ghalat share mikonand. Agar har component ye esm-e dasti besazad (`"personnel-list"` va `"personnel_list"`), do cache-e morde dari: yeki ra update mikoni, digari ru safhe mimanad.

## Ide

Hoviat-e ye entry = hame-ye chizi ke natije-ye server ra avaz mikonad, va hich chiz-e ezafe.

Baraye ye list-e ma'mul: kodam manba', kodam shekl (safhe-ye tak ya infinite), kodam vorudi (filter, sort, shomare-ye safhe, tenant).

Tenant joz'-e hoviat ast. Do site ye JSON nistan. Faramush-e tenant bug-e "dade-ye site-e ghabli ru site-e jadid" ast.

Chizi ke natije ra avaz nemikonad joz'-e key nist: makhfi budan-e ye kolon, baz budan-e modal, scroll. Gozashtan-eshan to key, cache ra shekaf mikonad.

## Batel kardan

Neveshtan haghighat-e server ra avaz mikonad. Cache-e ghabli dorugh mishavad.

**Batel kon.** Begou in hoviat digar ghabel-e etemad nist. Dafe-ye bad dobare migirad. Sade.

**Be-rooz-e khoshbinane.** Cache ra haman lahze avaz kon, bad server ra seda bezan. Agar server rad kard, bargard. Sari'-tar, va por az race. Baraye form-e bozorg aksaran batel kardan-e sade kam-khatar-tar ast.

Batel kardan bayad haman hoviat ra beshnasad. Agar nevisande `['personnel', id]` ra update konad va khandan `['personnel','detail',id]` bashad, safhe dorugh mimanad.

## Pishvand

```
['personnel']                          hame-ye chiz-e in manba'
  ['personnel', 'list', { site, q }]
  ['personnel', 'detail', id]
```

Batel kardan-e `['personnel']` yani har chizi ke ba in shoru mishavad. List va detail har do.

Ghanun: az omumi be joz'i benevis. Pishvand-e kheyli omumi 40 list-e bi-rabt ra ham refetch mikonad. Pishvand-e kheyli joz'i ye list-e digar ra dorugh negah midarad.

## Factory chera

```javascript
const personnelKeys = {
  all: ['personnel'],
  list: (params) => ['personnel', 'list', params],
  detail: (id) => ['personnel', 'detail', id],
};
```

Khandan: `personnelKeys.list(params)`.
Bad az save: `invalidate(personnelKeys.all)`.

Do call az ye tabe'. Agar farda `'personnel'` shavad `'staff'`, ye file avaz mishavad.

Ghanun-ha:

**Haman vorudi, haman key. Vorudi-ye motefavet, key-e motefavet.**

**Key bayad ghabel-e moghayese-ye sakhtari bashad.** Do object-e `{a:1}` agar library hash-e sakhtari konad yeki-and. E'temad be reference-e object shekaste ast, chon har render object-e jadid misazad. `{a:1, b:undefined}` va `{a:1}` shayad do hash bashand. Vorudi ra ghabl az key normalize kon.

**`undefined` be onvan-e id key-e vaghe'i nasaz.** `detail(undefined)` ye kisse-ye moshtarak-e "hanuz id nadaram" misazad. Ta id nist, fetch nakon (`enabled: false`).

**Shekl-e dade joz'-e hoviat ast.** List-e safhe-bandi va list-e infinite ye JSON nistan. Do key.

**Key-e kheyli bozorg cache ra shekaf mikonad.** Kole form-e 40 field, hatta field-hayi ke server nemikhanad.

URL-e kham key-e bad ast. `/a?b=1&c=2` va `/a?c=2&b=1` do string-and va ye dade. Factory-e normalize-shode an-ha ra yeki mikonad.

List-e server ra to Zustand copy nakon. Query cache manba'-e dade-ye server ast. Zustand state-e client ast.

## Hala dar front-e Dejban

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

`all` pishvand ast. `invalidateQueries({ queryKey: empTypeKeys.all })` list va detail va infinite va pagination ra ba ham mishavad, chon TanStack prefix match mikonad. `infinite` joda az `pagination` ast.

**Jay-e shekaste.** `duty-roster.service.js` factory-e `dutyRosterKeys` darad, vali invalidate hanuz string-e joda ast:

```javascript
await client.invalidateQueries({ queryKey: ['duty-cycles'] });
```

Alan kar mikonad chon `cycles(params)` ba `['duty-cycles', params]` shoru mishavad. Vali do manba'-e esm dari. Rename-e factory, string-e invalidate ra ja migozarad. Jomle-ye mosahebe: gharardad-e `empTypeKeys` in ast ke invalidate haman tabe' ra seda bezanad. Duty roster hanuz string-e joda darad.

`queryFn` factory nist. Factory esm misazad. Gereftan-e dade `*.http.js` ast.

## Agar beporsand, in tor begou

> Cache hoviat mikhahad: manba', shekl, vorudi, tenant. Chiz-e namayeshi to key nist. Pishvand-e omumi batel kardan-e daste-bandi midahad. Factory tanha jay-e sakhtan-e an array ast. empTypeKeys hamin ra darad. Infinite va safhe-ye tak do shekl-and. Invalidate-e all hame ra mishavad chon prefix ast. Duty roster factory darad vali ye ja string-e joda ham invalidate mikonad. An shekaf-e gharardad ast.

## Dah so'al

**1. Hoviat-e cache chi ast?**
Majmue-ye hame-ye vorudi-hayi ke javab-e server ra avaz mikonand.

**2. Chera tenant joz'-e key ast?**
Chon dade-ye do tenant ye javab nist.

**3. Pishvand che mikonad?**
Batel kardan-e `['personnel']` har key-i ke ba an shoru shavad ra mishavad.

**4. Chera factory?**
Ta khandan va invalidate az ye tabe' key besazand.

**5. Object-e jadid-e har render cache ra miss mikonad?**
Agar key reference-e shakhe'i bashad bale. Agar hash-e sakhtari bashad na, be shart-e field-haye sabet.

**6. `detail(undefined)` che bug-i ast?**
Ye kisse-ye moshtarak baraye "id nadaram". `enabled: false` ta id biayad.

**7. Infinite va pagination chera do key?**
Shekl-e zakhire-shode yeki nist.

**8. Batel kardan-e hame-ye app bad az har save?**
Taze mimanad va cache digar cache nist. Kam-tarin pishvandi ke dade-ye dide-shode ra mipushanad.

**9. `empTypeKeys.all` chi ra mipushanad?**
`['empType']`. List, detail, infinite, pagination.

**10. Shekaf-e duty roster chi ast?**
Factory `dutyRosterKeys` ast vali invalidate string-e `['duty-cycles']` joda neveshte shode.
