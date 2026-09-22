# Day 48 — i18next + Jalali

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** UI Farsi/English + tarikh Shamsi (Jalali) vs Gregorian — chejori yekja?

**Javab Dejban:** do layer joda amma sync:

| layer | tool |
|---|---|
| Matn UI | **i18next** + **react-i18next** + JSON namespaces (`fa-IR` / `en-US`) |
| Calendar pickers | **MUI X** `LocalizationProvider` → `AdapterMomentJalaali` (fa) / `AdapterDayjs` (en) |
| Display helper | `JalaliHelper` (`adapter-Jalaali.js`) + `formatDateByLang` / `toUtcIsoString` |
| Lang → RTL | `useTranslate().onChangeLang` → settings `direction` (Day 47) |
| API | Axios `Accept-Language` az `localStorage i18nextLng` (Day 44) |

Zincir:

```
I18nProvider (i18next init + LS lng)
  → useTranslate('staff') → t('…')
  → currentLang.systemValue → MUI theme locale (Day 47)
  → LocalizationProvider dateAdapter = Jalali | Dayjs
  → submit: toUtcIsoString → API Gregorian/UTC
  → list cell: JalaliHelper.gregorianToJalali / formatDateByLang
```

Defaults: **`fallbackLng = 'fa-IR'`**, `supportedLngs = ['fa-IR','en-US']`, `defaultNS = 'common'`.

**Band-e gharardad-e jadid:** farz kon / yani chi / chera.

Day 47 = RTL ayene. **In ruz = zaban + calendar.**

---

# BAKHSH-E AVAL: WORLD

## Farz kon — do daftar

**Daftar A (i18n):** «Save» vs «ذخیره» — string catalog.  
**Daftar B (calendar):** 2026-03-21 vs 1404/01/01 — haman *lahze*, namayesh digar.

Ethtebaah classic: store Jalali string to Postgres bedun convert → chaos.  
Dejban intent: **API/UTC Gregorian**; **UI fa = Jalali**.

---

## i18next chie?

Library translation: namespaces, interpolation `{{count}}`, language detector, lazy load JSON.  
`react-i18next`: `useTranslation` / `I18nextProvider`.  
Dejban wrapper: `useTranslate(namespace)` (+ lang switch helpers).

---

## Jalali / Shamsi chie?

Iranian calendar. Libraries: **moment-jalaali**, date-fns-jalali, dayjs plugin, …  
Dejban primary: **moment-jalaali** + MUI **`AdapterMomentJalaali`**.  
Also deps may include `@date-io/date-fns-jalali` / `date-fns-jalali` — **honesty:** main picker path = Moment adapter.

`moment.loadPersian({ dialect: 'persian-modern', usePersianDigits: false })` — Persian month names, **Latin digits** (ba Fanum font optionally).

---

# BAKHSH-E DOVOM: i18next Dejban

## Qesmat 1 — `locales-config.js` (app)

```js
supportedLngs = ['fa-IR', 'en-US']
fallbackLng = 'fa-IR'
defaultNS = 'common'
RTLLanguages = ['fa-IR']

allLangs = [
  { value: 'en-US', adapterLocale: 'en', systemValue: { components: en Date + DataGrid } },
  { value: 'fa-IR', adapterLocale: 'fa', systemValue: { components: fa Core + Date + DataGrid } },
]

i18nResourceLoader = resourcesToBackend(
  (lang, ns) => import(`./langs/${lang}/${ns}.json`)
)
```

**Yani chi?**  
- Lazy JSON per feature namespace (`staff.json`, `patrol-area.json`, …)  
- `systemValue` = MUI locale packs for theme `createTheme(..., localeComponents)` (Day 47)  
- `adapterLocale` = dayjs/moment locale code  

Storage keys: cookie `i18next`, LS `i18nextLng` (autoDetection flags false on cookie config; client detector still caches).

---

## Qesmat 2 — `I18nProvider`

`apps/dejban/src/locales/i18n-provider.jsx`:

```js
const lng = getStorage('i18nextLng', fallbackLng);
i18next.use(LanguageDetector).use(initReactI18next).use(i18nResourceLoader)
  .init({ ...i18nOptions(lng), detection: { caches: ['localStorage','cookie'] } });

export function I18nProvider({ children }) {
  return <Provider i18n={i18next}>{children}</Provider>;
}
```

Init **module scope** (yek bar). Root layout wraps children.

---

## Qesmat 3 — `useTranslate`

`@repo/ui` `use-locales.js` (re-export app):

```js
const { t, i18n } = useTranslation(namespace);
currentLang = getCurrentLang(i18n.resolvedLanguage);

onChangeLang(lang):
  i18n.changeLanguage(lang)
  toast.promise(...)
  settings.setState({ direction: i18n.dir(lang) })  // rtl/ltr
  dayjs.locale(...)
  patch app-settings LS direction
  router.refresh()
```

**Farz kon switch FA→EN:** strings EN + direction LTR (Day 47 Rtl off) + Dayjs adapter.

**Smell package:** imports `src/routes/hooks`, `src/components/snackbar` — app-coupled like ThemeProvider.

---

## Qesmat 4 — namespaces + `t`

```js
const { t: t_staff } = useTranslate('staff');
t_staff('list.title');
const { t: t_common } = useTranslate(); // default common
t_common('button.save');
```

JSON: `langs/fa-IR/common.json` — `commonTexts`, `button`, interpolation.

Missing key → fallback NS / fallbackLng — configure carefully; debug mode optional.

---

## Qesmat 5 — server detectLanguage

`locales/server.js` (Next):

1. cookie `i18next`  
2. optional Accept-Language header (agar autoDetection)  
3. `fallbackLng`  

Used root layout `detectLanguage()` for `<html lang>`.  
Cookie-based (na `/fa/...` URL routing).

`getServerTranslations` — RSC rare path; most UI client `t`.

---

## Qesmat 6 — Axios Accept-Language

```ts
config.headers['Accept-Language'] = localStorage.getItem('i18nextLng') || 'fa-IR';
```

BE mitune message Farsi/English bargardone (FluentValidation resources).  
Sync LS key ba i18next critical.

---

## Qesmat 7 — `useLocaleDirectionSync`

Effect: sync `document.dir` + settings.direction ba `i18n.dir(lang)`.  
Prevents drift lang vs RTL.

---

# BAKHSH-E SEVOM: Jalali Dejban

## Qesmat 8 — `LocalizationProvider`

`packages/ui/.../localization-provider.jsx`:

```jsx
isFa = currentLang?.value === 'fa-IR'
dayjs.locale(adapterLocale)
moment.locale(fa|en)
loadPersian once

<Provider
  dateAdapter={isFa ? AdapterMomentJalaali : AdapterDayjs}
  adapterLocale={currentLang.adapterLocale}
>
```

**Yani chi?** Hame `DatePicker` / `DateTimePicker` zir in provider calendar dorost mibinand.  
Field.DatePicker (Day 45/47) inherit.

---

## Qesmat 9 — `date-utils.js` (SSOT comment)

Documented single source:

| fn | kar |
|---|---|
| `useIsFa()` | lang === fa-IR |
| `toUtcIsoString(value)` | → ISO Z for API/Postgres |
| `toPickerValue(value, isFa)` | moment vs dayjs for controlled picker |
| `formatDateByLang(value, isFa, kind)` | display string |
| `jalaliFormats` / `gregorianFormats` | `jYYYY/jMM/jDD` vs `YYYY/MM/DD` |

**Chera UTC ISO?** timestamptz; avoid local skew.  
**Chera na store jYYYY in DB?** query/sort/BE validation simpler Gregorian.

---

## Qesmat 10 — `JalaliHelper` (`adapter-Jalaali.js`)

Export `@repo/ui/utils`:

- `parse` / `format` with `jYYYY/jMM/jDD`  
- `jalaliToGregorian` / `gregorianToJalali`  
- `getJYear` / `getJMonth` / `getJDay`  
- `calendar` relative  

List views: `JalaliHelper.gregorianToJalali(new Date(date))`.

Overlaps `formatDateByLang` — do entry points; prefer date-utils for new code (SSOT comment).

---

## Qesmat 11 — form submit pipeline (staff-like)

1. User picks Jalali in picker (moment value)  
2. RHF holds value (string/ISO/moment — map carefully)  
3. Submit → `toUtcIsoString` / BE DateOnly  
4. Reload → `toPickerValue(..., true)`  

**Bug classic:** double convert or string Jalali posted as Gregorian parse fail.

---

## Qesmat 12 — digits

`usePersianDigits: false` — UI Latin digits often + IRANSans Fanum.  
Axios digit normalize English (Day 44).  
Zod national code digit transform (Day 45).  
Consistent Latin digits to API.

---

# BAKHSH-E CHAHAROM: ertebat RTL + theme

Lang `fa-IR` → `i18n.dir` = rtl → settings + Emotion Rtl (Day 47).  
Lang `en-US` → ltr.  

MUI `systemValue` components faIR → DataGrid/DatePicker labels Farsi.

**Yani chi?** Language switch ≈ i18n + direction + date adapter + MUI locales — yek `onChangeLang`.

---

# BAKHSH-E PANJOM: farz kon / senario

## Se dastan

**1) User FA default**  
fallback fa-IR → t Farsi → AdapterMomentJalaali → list dates Shamsi.

**2) Switch English**  
changeLanguage en-US → toast → direction ltr → Dayjs adapter → Gregorian display.

**3) Save contract date**  
Picker Jalali → toUtcIsoString → POST → DB → GET ISO → formatDateByLang fa → jYYYY/...

---

## Smell-ha

1. Dual helpers JalaliHelper vs date-utils  
2. moment-jalaali + dayjs both — bundle weight  
3. useTranslate coupled to app paths in ui package  
4. Some forms hardcode Farsi Zod messages (Day 45) — not i18n  
5. cookie autoDetection false but detector caches — know source of truth LS  
6. `router.refresh` Next-only in shared hook  
7. date-fns-jalali dep underused  

---

## Debug checklist

| symptom | check |
|---|---|
| English UI still RTL | onChangeLang direction / settings |
| Picker Gregorian in FA | LocalizationProvider isFa / adapter |
| Wrong day ±1 | timezone / toUtcIsoString |
| Missing translation | namespace JSON / key typo / fallback |
| API messages wrong lang | Accept-Language header LS |
| Persian digits in API | loadPersian + normalize |
| Hydration lang flash | cookie vs LS vs html lang |

---

## 25 soal-e mosahebe

1. i18next vs react-i18next?  
2. namespace chie?  
3. fallbackLng Dejban?  
4. resourcesToBackend?  
5. Jalali vs Gregorian storage?  
6. AdapterMomentJalaali vs AdapterDayjs?  
7. toUtcIsoString chera?  
8. Accept-Language?  
9. How lang switches RTL?  
10. systemValue MUI?  
11. JalaliHelper vs formatDateByLang?  
12. loadPersian options?  
13. Cookie vs URL i18n routing?  
14. defaultNS?  
15. Interpolation example?  
16. Server detectLanguage order?  
17. Why Latin digits?  
18. moment vs dayjs coexistence?  
19. DateOnly vs timestamptz FE?  
20. Missing key behavior?  
21. useLocaleDirectionSync?  
22. Change lang toast?  
23. Staff hardcoded Zod FA?  
24. Day 47 vs 48?  
25. How add new namespace JSON?

---

## Senario-ha

**S1:** Add `weapons.json` fa+en → useTranslate('weapons').  
**S2:** DST edge — prefer date-only fields without time.  
**S3:** User clears LS — fallback fa-IR.  
**S4:** BE returns English error while FA UI — Accept-Language / BE resources.  
**S5:** Chart axis dates — may need manual formatDateByLang.

---

## Mini lab

1. Switch lang — watch LS `i18nextLng`, `document.dir`, picker calendar  
2. `t('button.save')` both langs  
3. Pick date → Network payload ISO  
4. List column gregorianToJalali  
5. Break JSON key — see fallback  

---

## Resume (1 paragraph)

> Localized Dejban with **i18next** (`fa-IR`/`en-US`, lazy JSON namespaces, `useTranslate`) synced to RTL settings and Axios `Accept-Language`, and rendered dates with **Jalali** via **moment-jalaali** / MUI `AdapterMomentJalaali` while persisting **UTC/Gregorian** through `toUtcIsoString` and shared format helpers.

Keywords: `i18next` · `react-i18next` · `Jalali` · `moment-jalaali` · `AdapterMomentJalaali` · `LocalizationProvider` · `fa-IR` · `Accept-Language` · `toUtcIsoString`

---

## File-haye mohem

| path | chera |
|---|---|
| `apps/dejban/src/locales/locales-config.js` | langs, loader, MUI locales |
| `.../i18n-provider.jsx` | init |
| `.../server.js` | detectLanguage |
| `.../langs/fa-IR|en-US/*.json` | catalogs |
| `packages/ui/locales/use-locales.js` | useTranslate |
| `packages/ui/locales/localization-provider.jsx` | date adapters |
| `packages/ui/utils/date-utils.js` | SSOT convert/format |
| `packages/ui/utils/adapter-Jalaali.js` | JalaliHelper |
| `api-client axiosInstance` | Accept-Language |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 44 | Accept-Language header |
| 45 | Zod messages (often FA hardcoded) |
| 47 | RTL + theme localeComponents |
| **48** | this |
| 52 | MRT date columns format |

---

## Chejori digest koni

1. Do daftar matn vs calendar  
2. Config + useTranslate  
3. LocalizationProvider adapters  
4. toUtcIsoString mantra  
5. Resume  

---

## Glossary

| term | ma'ni |
|---|---|
| i18n | internationalization |
| l10n | localization |
| namespace | JSON file group keys |
| fallbackLng | default language |
| Jalali / Shamsi | Iranian calendar |
| Gregorian | western calendar |
| adapter | MUI X date library bridge |
| adapterLocale | dayjs/moment locale id |
| interpolation | `{{name}}` in strings |
| resourcesToBackend | dynamic import translations |

---

## Deep dive — jYYYY tokens

moment-jalaali: `jYear` tokens `jYYYY`, `jMM`, `jDD`.  
Wrong `YYYY` on jalali moment → Gregorian numbers mistaken.  
Always use jalaliFormats when isFa.

---

## Deep dive — DateOnly

BE `DateOnly` (no time) — send `yyyy-MM-dd` carefully; timezone shift can change day.  
Prefer date-only helpers / noon UTC strategies — know staff forms approach.

---

## Deep dive — namespace sprawl

Dozens JSON files per lang — keep keys feature-scoped.  
Shared buttons → `common`.  
Duplicate keys smell.

---

## Anti-pattern

| bad | better |
|---|---|
| Hardcode all UI Farsi | t() keys |
| Save `1403/01/01` as only DB format | UTC/ISO Gregorian |
| Mix adapters randomly | LocalizationProvider |
| Forget Accept-Language | LS sync |
| Translate with string concat | interpolation |
| Ignore en RTL leftover | onChangeLang direction |

---

## Interview 60s

«We use i18next with fa-IR and en-US JSON namespaces. Changing language updates direction for RTL and swaps the MUI date adapter between Moment Jalaali and Dayjs. We display Jalali in the UI but convert to UTC ISO for the API, and send Accept-Language from the same localStorage key.»

---

## Quick self-test

1. fallbackLng? → fa-IR  
2. Date adapter FA? → AdapterMomentJalaali  
3. Helper export name? → JalaliHelper  
4. API date format intent? → UTC ISO  
5. LS lang key? → i18nextLng  
6. defaultNS? → common  
7. RTL langs list? → fa-IR  

---

## Final checklist

- [ ] i18n config + namespaces  
- [ ] useTranslate / onChangeLang  
- [ ] LocalizationProvider adapters  
- [ ] date-utils + JalaliHelper  
- [ ] Accept-Language + RTL sync  
- [ ] smells  
- [ ] resume  

---

## Extra — Farz kon add language ar-SA

1. supportedLngs + allLangs entry  
2. langs/ar-SA/*.json  
3. RTLLanguages include  
4. MUI locale pack if exists  
5. Calendar? Hijri separate — product decision  

---

## Extra — pluralization

i18next plural keys `key_one` / `key_other` — use for delete confirm counts (`{{count}}`).  
FA plural rules differ — test.

---

## Extra — Soalat chera

**Chera i18next?** mature React ecosystem.  
**Chera moment-jalaali?** MUI adapter mature + existing code.  
**Chera UTC storage?** DB/query consistency.  
**Chera fa default?** product users.  
**Chera sync direction?** FA without RTL = broken UX.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «i18next loads fa/en JSON. useTranslate switches language, direction, and dayjs locale. LocalizationProvider picks Jalali or Gregorian adapters. Helpers format for display and convert to UTC for the backend; Axios sends Accept-Language.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| Key shows raw | wrong ns / missing JSON |
| Off-by-one day | TZ convert |
| Picker empty | toPickerValue null invalid |
| EN text RTL layout | direction not updated |
| BE English errors | Accept-Language |
| Month name Latin | loadPersian missing |
| Bundle huge | moment full + dayjs |

---

## Extra — Layer checklist

| concern | owner |
|---|---|
| UI strings | i18next JSON |
| MUI component locale | systemValue |
| Calendar UI | LocalizationProvider |
| Display format | formatDateByLang / JalaliHelper |
| API wire date | toUtcIsoString |
| API language | Accept-Language |
| Layout dir | settings + i18n.dir |

---

## Extra — Related days

- 44 Axios headers  
- 45 forms Zod  
- 47 RTL Emotion  
- 52 tables dates  

---

## Extra — `@date-io` / date-fns-jalali

May appear in package.json for legacy/alternate.  
Verify before claiming in resume — primary = AdapterMomentJalaali.

---

## Extra — number format

`numberFormat: { code: 'fa-IR', currency: 'IRR' }` in allLangs.  
`number-format-locale.js` util — currency/display helpers.  
Separate from calendar.

---

## Extra — testing translations

CI optional: key parity script fa vs en missing keys.  
E2E switch language assert button text.

---

## Band-e gharardad-e jadid

i18next = farhang loghat.  
Namespace = fasl ketab.  
Jalali = namayesh Shamsi.  
Adapter = maghz DatePicker.  
toUtcIsoString = zaban moshtarak ba server.  
Accept-Language = «ba man Farsi sohbat kon».  
Direction = hamrah zaban.

---

## 10 jomle fluency

1. Default language is fa-IR.  
2. Translations live in per-namespace JSON.  
3. useTranslate wraps react-i18next.  
4. Language change updates RTL direction.  
5. FA pickers use AdapterMomentJalaali.  
6. EN pickers use AdapterDayjs.  
7. API dates should be UTC ISO.  
8. JalaliHelper formats list cells.  
9. Axios sends Accept-Language from LS.  
10. Don't store Jalali-only strings as DB truth.

---

## Extra — Comparison react-intl

FormatJS also fine; team/template i18next.  
Explain tradeoffs briefly if asked.

---

## Extra — ICU / rich text

Mostly plain strings.  
HTML in translations — caution XSS; prefer components.

---

## Extra — calendar management page

Uses `moment-jalaali` directly for calendar UI — domain heavy.  
Still same library family.

---

## Extra — guest reserve appointments

moment for schedules; convert consistently with SSOT utils when touching.

---

## Band-e gharardad — ye bar digar sade

1. **i18next** = strings.  
2. **fa-IR / en-US** = two langs.  
3. **JSON namespaces** = feature catalogs.  
4. **useTranslate** = hook + switch.  
5. **LocalizationProvider** = picker calendar.  
6. **moment-jalaali** = Shamsi engine.  
7. **toUtcIsoString** = API dates.  
8. **format / JalaliHelper** = display.  
9. **Accept-Language** = BE messages.  
10. **dir sync** = RTL with FA.

---

## Extra — Capacity

JSON lazy per ns — good.  
moment size — accepted.  
Don't load all langs upfront beyond detector.

---

## Extra — onboarding new screen

1. Create `fa-IR/feature.json` + `en-US/feature.json`  
2. useTranslate('feature')  
3. Dates via Field.DatePicker under LocalizationProvider  
4. Submit via toUtcIsoString  
5. Columns via formatDateByLang  

---

## Extra — Zod + i18n

Patrol schema uses `t()` messages — good.  
Staff hardcoded FA — migrate gradually.  
Schema recreate on lang change (Day 45 caveat).

---

## Extra — html lang attribute

Root layout sets `lang` from detectLanguage.  
Keep in sync when client changes lang (refresh helps).

---

## Extra — SEO

Intranet app — SEO secondary.  
Still correct `lang`/`dir` a11y.

---

## Extra — interview whiteboard dates

Arrow: UI Jalali → convert → ISO Z → API → DB → ISO → format Jalali.

---

## Extra — time-only fields

`toPickerValue(value, isFa, 'HH:mm:ss')` parseFormat path.  
Shift times / door schedules — don't run through jYYYY by mistake.

---

## Extra — relative calendar

`JalaliHelper.calendar(date)` → «امروز» style strings.  
Useful notifications; still based on moment locale.

---

## Extra — DataGrid locale

`faIRDataGrid` in systemValue — column menu / filter operators Farsi when theme applied.  
MRT may have own i18n — Day 52.

---

## Extra — flag / countryCode

`allLangs.countryCode` for language switcher flags (GB/IR).  
UI nicety in settings/topbar.

---

## Extra — when BE ignores Accept-Language

Always show toast from `extractErrorMessage` body — may already be FA from server culture.  
Don't assume header always wins.

---

## Extra — moment mutability

moment objects mutable — clone when adjusting.  
dayjs immutable-er — another reason dual stack careful.

---

## Khoruj-e zehni

> Midunam i18next ba fa-IR/en-US va namespace JSON; switch zaban ba direction/RTL va MUI locales; DatePicker ba AdapterMomentJalaali/Dayjs; namayesh Jalali amma API UTC/Gregorian; Accept-Language az LS; va dual helper-ha ro midunam.

Age in paragraph mal-e to shod — Day 48 done.

---

*Day 48 tamum. Ba'd: Day 49 � Auth UI / Guards / `componentId` (amade). Fehrest: [README.md](./README.md).*
