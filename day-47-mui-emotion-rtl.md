# Day 47 — MUI 7 + Emotion + RTL

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** UI Dejban che framework component/style? LTR English default ya Farsi RTL?

**Javab Dejban:**

| layer | package / file |
|---|---|
| Components | **MUI 7** (`@mui/material` ^7.3, icons, lab, X date/data-grid) |
| CSS-in-JS | **Emotion** (`@emotion/react`, `styled`, `cache`) |
| RTL flip styles | **`@mui/stylis-plugin-rtl`** + Emotion `CacheProvider` |
| Theme factory | `@repo/ui` → `createTheme` / `ThemeProvider` |
| Defaults | `themeConfig.direction = 'rtl'`, font **IRANSansWeb**, css variables color scheme |

Zincir root layout:

```
<html dir="rtl" … suppressHydrationWarning>
  InitColorSchemeScript (MUI)
  SettingsProvider (direction, mode, primaryColor, …)
  ThemeProvider (@repo/ui)
    createTheme(settings + localeComponents)
    CssBaseline
    Rtl(direction) → CacheProvider + stylis rtl plugin
  children (Field/MUI/sections)
```

**Band-e gharardad-e jadid:** farz kon / yani chi / chera.

Day 45 = Field wraps MUI. Day 48 = i18n/Jalali deepen. Day 52 = MRT. **In ruz = design system MUI+Emotion+RTL.**

---

# BAKHSH-E AVAL: WORLD — seh piece

## Farz kon — lebass, parche, ayene

**MUI** = Lebass amade (Button, TextField, Dialog) + theme API.  
**Emotion** = parche CSS dar JS (`sx`, `styled`, cache).  
**RTL plugin** = ayene: `margin-left` ↔ `margin-right` (logical flip via stylis).

Bedun RTL plugin: `theme.direction='rtl'` + `document.dir` — *kamtar* kafist; chand CSS physical property mirror nemishe.  
Ba stylis plugin: generated Emotion CSS flip mishe.

---

## Chera MUI 7 (na Chakra / Ant)?

- Template Minimals heritage  
- Dense admin (DataGrid, DatePicker X)  
- CssVars / color schemes light+dark built-in direction  
- Huge ecosystem + RTL docs  

Versions dejban (approx): material 7.3, emotion 11, stylis 4, `@mui/material-nextjs` for App Router helpers, X Data Grid 8, Date Pickers 9.

---

## Emotion chie? (kutah)

Runtime CSS: class name hash, cache, SSR/hydration.  
MUI v5+ default engine = Emotion (na JSS ghadim).  
`sx` prop → Emotion under hood.  
`styled(Button)(...)` → Emotion styled.

**CacheProvider:** custom Emotion cache (key + stylisPlugins). RTL = separate cache key `'rtl'`.

---

## RTL — do sath

1. **Document / theme direction** — `dir="rtl"`, `theme.direction`, layout start/end  
2. **CSS transform plugin** — stylis flips LTR-authored rules  

Icons: ba'zi `scaleX(-1)` when `theme.direction === 'rtl'` (nav arrows).

---

# BAKHSH-E DOVOM: DEJBAN — theme stack

## Qesmat 1 — `themeConfig`

`packages/ui/src/theme/theme-config.js`:

| key | value / ma'ni |
|---|---|
| `direction` | **`'rtl'`** default product |
| `defaultMode` | `'light'` |
| `modeStorageKey` | `'theme-mode'` |
| `fontFamily.primary` | `IRANSansWeb` |
| `fontFamily.secondary` | `IRANSansWeb_Fanum` (numbers) |
| `cssVariables` | prefix + `data-color-scheme` selector |
| `palette.*` | primary green `#00A76F`, … Minimals-like |
| `classesPrefix` | `minimal` |

**Yani chi?** Out of box Farsi RTL + Iranian font names (files loaded via global CSS / assets).

---

## Qesmat 2 — `createTheme`

`create-theme.js`:

```js
baseTheme = {
  colorSchemes: { light: { palette, shadows, … }, dark: { … } },
  mixins, components, typography,
  shape: { borderRadius: 8 },
  direction: themeConfig.direction,
  cssVariables: themeConfig.cssVariables,
};

createTheme({ settingsState, themeOverrides, localeComponents }) {
  updatedCore = applySettingsToTheme(baseTheme, settingsState);
  updatedComponents = applySettingsToComponents(settingsState);
  return createMuiTheme(updatedCore, updatedComponents, localeComponents, themeOverrides);
}
```

**MUI 7 style:** `colorSchemes` + css variables (na faqat `palette` classic only).  
**settingsState:** direction, fontFamily, contrast, primaryColor presets.  
**localeComponents:** az i18n `currentLang.systemValue` (MUI locale — Day 48).

---

## Qesmat 3 — `ThemeProvider` (@repo/ui)

```jsx
const theme = useMemo(() => createTheme({ settingsState, localeComponents, themeOverrides }), [...]);
return (
  <ThemeVarsProvider disableTransitionOnChange theme={theme}>
    <CssBaseline />
    <Rtl direction={settings.state.direction}>{children}</Rtl>
  </ThemeVarsProvider>
);
```

**CssBaseline:** normalize + bg from theme.  
**disableTransitionOnChange:** kam flash when toggling mode.  
**Settings + lang** deps → recreate theme when user toggles RTL/LTR or font.

**Smell package:** `import { useTranslate } from 'src/locales'` dakhel `@repo/ui` — depends on app alias `src/locales` when transpiled. Works in Next apps; pure package isolation weak.

---

## Qesmat 4 — `Rtl` + Emotion cache

`with-settings/right-to-left.jsx`:

```js
const cacheRtl = () => createCache({ key: 'rtl', stylisPlugins: [rtlPlugin] });
// rtlPlugin from '@mui/stylis-plugin-rtl'

useEffect(() => { document.dir = direction; }, [direction]);

if (direction === 'rtl')
  return <CacheProvider value={cacheRtl()}>{children}</CacheProvider>;
return children;
```

**Farz kon LTR toggle:** settings drawer switches direction → theme.direction + document.dir + **no** rtl cache (LTR default Emotion).  
**Farz kon RTL:** plugin active.

**Note:** `cacheRtl()` har render call — possible new cache identity; lab if remount flicker (smell optimize `useMemo`).

Also deps: both `@mui/stylis-plugin-rtl` and `stylis-plugin-rtl` in package.json — **active path uses MUI package**.

---

## Qesmat 5 — Settings defaults

`createDefaultSettings`:

- `direction: themeConfig.direction` → rtl  
- `mode: light`  
- `primaryColor: 'preset3'`  
- `fontFamily: IRANSansWeb`  
- `workspaceTabs`, `navLayout`, …  
- stored under `SETTINGS_STORAGE_KEY = 'app-settings'`

Settings drawer UI: toggle RTL chip, color presets, contrast (Day UI).

---

## Qesmat 6 — Root layout wiring

`apps/dejban/src/app/layout.jsx`:

- `InitColorSchemeScript` — prevent wrong theme flash (FOUC mode)  
- `html` `dir={defaultSettings.direction}` + `suppressHydrationWarning`  
- `ThemeProvider` from `@repo/ui/theme` inside SettingsProvider  

**Chera suppressHydrationWarning?** client settings/mode may differ first paint.

---

## Qesmat 7 — Component overrides

`theme/core/components/*` — Button, TextField, Dialog, Table, … style overrides central.  
`applySettingsToComponents` — settings-driven tweaks.  

**Yani chi?** Product look consistent; page authors use `<Button variant="contained">` bedun local CSS chaos.

---

## Qesmat 8 — `sx` va spacing RTL-aware

```jsx
<Box sx={{ ml: 2, mr: 1 }} />
```

Ba direction rtl + stylis, physical ml/mr often flip.  
Prefer **logical** when possible: `marginInlineStart` / theme spacing with care.  
MUI Stack `direction="row"` + RTL reverses visual order — midunam.

Icons that shouldn't flip (logo): mark / disable transform.

---

## Qesmat 9 — MUI X + special cases

- **Date pickers** — adapters Jalali (Day 48)  
- **Data Grid** — themed via `mui-x-data-grid.jsx` overrides  
- **MRT** (`use-base-grid-styles`): ba'zi ja `direction: 'ltr'` force — **honesty** numbers/columns LTR inside RTL app  

Lab: table numbers LTR intentional vs bug.

---

## Qesmat 10 — Fonts

Typography uses `setFont(IRANSansWeb)`.  
Fanum secondary for Latin/Persian digit rendering preferences.  
Load fonts in `global.css` / public — missing font = fallback ugly Farsi.

---

## Qesmat 11 — Dark mode

`colorSchemes.light/dark` + `InitColorSchemeScript` + settings `mode`.  
`data-color-scheme` attribute selector (cssVariables config).  
User toggle settings drawer.

---

# BAKHSH-E SEVOM: estefade dar pages

## Qesmat 12 — typical imports

```js
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import { useTheme } from '@mui/material/styles';
// or barrel — tree-shake prefer path imports
```

Field components Day 45 → TextField underneath.  
Layouts dashboard `@repo/ui/layouts-dashboard` — heavy MUI.

---

## Qesmat 13 — `useTheme` / `alpha` / mixins

Custom sections: `const theme = useTheme(); theme.palette.primary.main`.  
Mixins text truncate, bg blur — `theme/core/mixins`.  
Keep brand tokens — don't hardcode random hex in 50 files when theme has palette.

---

## Qesmat 14 — Next + MUI

`@mui/material-nextjs` — App Router emotion/cache helpers (check usage per app).  
Client components for theme providers (`'use client'`).  
Day 42: providers in client tree.

---

# BAKHSH-E CHAHAROM: farz kon / senario

## Se dastan

**1) First paint Farsi user**  
html dir=rtl → ThemeProvider rtl → Rtl CacheProvider → TextField label right → staff form natural.

**2) Toggle LTR in settings**  
direction ltr → document.dir → theme recreate → no rtl plugin → English demo / support.

**3) Dark mode**  
InitColorSchemeScript + settings mode dark → colorSchemes.dark palette → CssBaseline bg.

---

## Smell-ha

1. `cacheRtl()` new cache each Rtl render — optimize  
2. `useTranslate` from `src/locales` inside package  
3. Dual stylis-plugin packages confusion  
4. MRT/grid forced LTR islands  
5. Hardcoded colors bypassing theme  
6. Huge theme override surface — upgrade MUI cost  
7. Icon flip inconsistencies  

---

## Debug checklist

| symptom | check |
|---|---|
| Margins wrong side | Rtl CacheProvider? direction mismatch |
| FOUC dark/light | InitColorSchemeScript / storage key |
| Hydration warn | suppress / settings read timing |
| Font not Farsi | IRANSans loaded? typography fontFamily |
| sx not flipping | physical CSS outside Emotion |
| Dense padding | theme spacing / density settings |
| X DatePicker LTR popup | locale adapter / dir portal |

---

## 25 soal-e mosahebe

1. MUI vs Emotion roles?  
2. Chera stylis RTL plugin?  
3. theme.direction vs document.dir?  
4. CssBaseline?  
5. colorSchemes MUI 7?  
6. cssVariables benefit?  
7. CacheProvider key?  
8. IRANSans chera?  
9. settingsState apply?  
10. localeComponents?  
11. sx vs styled vs override?  
12. Logical properties?  
13. InitColorSchemeScript?  
14. suppressHydrationWarning?  
15. Why default rtl?  
16. Icon scaleX rtl?  
17. MRT ltr island?  
18. Upgrade MUI 6→7 risks?  
19. Tree-shake imports?  
20. ThemeProvider client?  
21. primaryColor presets?  
22. Fanum font?  
23. Stack row in RTL?  
24. Day 47 vs 48?  
25. Emotion SSR?

---

## Senario-ha

**S1:** Third-party chart CSS LTR only → wrap dir=ltr box.  
**S2:** `marginLeft` in global.css — won't flip; use theme sx.  
**S3:** Portal Dialog — inherits dir from theme usually OK.  
**S4:** Copy English template spacing — test both directions.  
**S5:** Missing CacheProvider rtl → asymmetric padding bugs.

---

## Mini lab

1. Toggle direction settings — watch `document.dir` + Emotion class  
2. Inspect computed margin on TextField  
3. Read `right-to-left.jsx` + `theme-config`  
4. Find one `theme.direction === 'rtl'` icon flip  
5. Switch dark mode — `data-color-scheme`  

---

## Resume (1 paragraph)

> Built the Dejban admin UI on **MUI 7** with **Emotion**, a shared `@repo/ui` theme (`createTheme`, css variables, light/dark schemes), default **RTL** via `theme.direction` plus **`@mui/stylis-plugin-rtl`** Emotion cache, Iranian fonts (IRANSans), and settings-driven direction/color/font toggles.

Keywords: `MUI 7` · `Emotion` · `RTL` · `stylis-plugin-rtl` · `CacheProvider` · `createTheme` · `CssBaseline` · `cssVariables` · `IRANSans`

---

## File-haye mohem

| path | chera |
|---|---|
| `theme-config.js` | defaults rtl + fonts + palette |
| `create-theme.js` | factory |
| `theme-provider.jsx` | Theme + CssBaseline + Rtl |
| `with-settings/right-to-left.jsx` | Emotion RTL cache |
| `with-settings/update-core.js` | apply settings |
| `theme/core/components/*` | overrides |
| `theme/core/typography.js` | fonts |
| `apps/dejban/src/app/layout.jsx` | InitColorSchemeScript + providers |
| `settings-config.js` | default settings |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 42 | providers in Next layout |
| 45 | Field → MUI inputs |
| 46 | settings may persist (app-settings) |
| **47** | this |
| 48 | i18n + Jalali adapters |
| 52 | MRT + direction quirks |

---

## Chejori digest koni

1. Lebass / parche / ayene  
2. Bekhun Rtl + themeConfig  
3. createTheme + settings  
4. Lab toggle dir/mode  
5. Resume  

---

## Glossary

| term | ma'ni |
|---|---|
| MUI | Material UI component library |
| Emotion | CSS-in-JS engine |
| stylis | CSS preprocessor for Emotion |
| RTL | right-to-left layout |
| CacheProvider | Emotion cache context |
| CssBaseline | global reset |
| colorSchemes | light/dark theme slices |
| cssVariables | CSS custom props theming |
| sx | MUI style prop |
| override | theme.components.MuiX.styleOverrides |

---

## Deep dive — physical vs logical CSS

`margin-left` physical; `margin-inline-start` logical.  
Stylis RTL rewrites many physical in Emotion output.  
Raw `.css` files / third-party = manual care.

---

## Deep dive — two CacheProviders?

LTR uses default emotion cache from MUI.  
RTL swaps CacheProvider.  
Switching may remount style tree — expect brief cost.

---

## Deep dive — primaryColor presets

`color-presets.js` + settings `primaryColor: 'preset3'` → `applySettingsToTheme` replaces primary palette channels.  
Brand can shift without code change pages.

---

## Anti-pattern

| bad | better |
|---|---|
| Inline style marginLeft everywhere | sx / theme spacing |
| Fork Button styles per page | theme override |
| Forget Rtl wrapper | always under ThemeProvider |
| Assume direction fixed forever | test LTR toggle |
| Load Inter only | IRANSans for FA |
| Import `@mui/material` whole barrel huge | path imports |

---

## Interview 60s

«Our UI is MUI 7 on Emotion. Shared theme in `@repo/ui` defaults to RTL with IRANSans, css-variable color schemes, and settings for direction and dark mode. For RTL we set document.dir and wrap the tree in an Emotion cache using MUI’s stylis RTL plugin so generated styles flip correctly.»

---

## Quick self-test

1. Default direction? → rtl  
2. RTL plugin package? → `@mui/stylis-plugin-rtl`  
3. Font primary? → IRANSansWeb  
4. Theme package? → `@repo/ui`  
5. CssBaseline where? → ThemeProvider  
6. Mode FOUC helper? → InitColorSchemeScript  
7. Force LTR somewhere? → MRT styles possible  

---

## Final checklist

- [ ] MUI + Emotion + RTL roles  
- [ ] themeConfig defaults  
- [ ] createTheme + settings  
- [ ] Rtl CacheProvider  
- [ ] layout InitColorSchemeScript  
- [ ] smells  
- [ ] resume  

---

## Extra — Farz kon English support engineer

Toggle LTR + lang en (Day 48) → theme localeComponents English.  
Same components; direction/content change.

---

## Extra — Grid system

MUI Grid2 / Grid — `size={{ xs: 12, md: 6 }}`.  
RTL: columns flow right-first — verify forms.

---

## Extra — z-index / Modal

Theme zIndex modal/drawer/snackbar — customize carefully when stacking workspace tabs overlays.

---

## Extra — Soalat chera

**Chera Emotion?** MUI default.  
**Chera stylis plugin?** reliable CSS flip.  
**Chera default rtl?** Persian product.  
**Chera cssVariables?** mode switch + theming modern MUI.  
**Chera shared @repo/ui theme?** multi-app consistency (Day 43).

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «MUI components styled by Emotion. Theme is created in a shared package with RTL default and Iranian fonts. An Rtl helper installs a stylis plugin cache when direction is rtl, and settings can switch direction or dark mode.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| Padding asymmetric | missing rtl cache |
| Flash white/dark | InitColorSchemeScript |
| Wrong font | CSS @font-face |
| Icon points wrong | need scaleX rule |
| Hydration mismatch | dir/mode LS |
| Fat bundle | barrel imports |
| Date popup LTR | adapter/dir |

---

## Extra — Layer checklist

| layer | tech |
|---|---|
| Components | MUI 7 |
| Style runtime | Emotion |
| RTL CSS | stylis plugin + CacheProvider |
| Tokens | themeConfig + presets |
| User prefs | SettingsProvider |
| App shell | Next layout |

---

## Extra — Related days

- 42 Next providers  
- 45 RHF fields  
- 48 i18n/Jalali  
- 52 MRT  

---

## Extra — styled vs sx

`sx`: one-off, theme callback.  
`styled`: reusable component.  
`theme.components`: global product defaults.  
Prefer overrides for brand; sx for layout local.

---

## Extra — Accessibility

Contrast settings; focus visible overrides; rtl reading order.  
Color alone not for error — helperText (Day 45).

---

## Extra — performance

Theme recreate on settings change OK rare.  
Avoid anonymous `sx={{ ... }}` mega objects if hot path — usually fine admin.  
Emotion runtime cost accepted.

---

## Extra — lab package versions

```
@mui/material ^7
@emotion/react ^11
@mui/stylis-plugin-rtl ^7
stylis ^4
```

Pin majors across apps (Day 43 peers).

---

## Band-e gharardad-e jadid

MUI = dokme/input amade.  
Emotion = rang-e CSS.  
Theme = brand book.  
RTL plugin = ayene CSS.  
Settings = remote control direction/mode.  
Font Iran = khanayi Farsi.

---

## 10 jomle fluency

1. UI stack is MUI 7 plus Emotion.  
2. Default direction is RTL.  
3. Theme lives in `@repo/ui`.  
4. createTheme merges settings and locales.  
5. Rtl wraps Emotion cache with stylis plugin.  
6. document.dir tracks direction.  
7. IRANSans is the primary font.  
8. CssBaseline and css variables support light/dark.  
9. InitColorSchemeScript reduces mode flash.  
10. Some grids force LTR for numbers.

---

## Extra — Comparison Tailwind

Tailwind = utility classes; RTL plugins exist (`rtl:`).  
Dejban = MUI sx ecosystem — don't mix randomly without convention.

---

## Extra — shadow / shape

`shape.borderRadius: 8` global.  
customShadows brand elevation.  
Keep density consistent tables/forms.

---

## Extra — lab vs lab package

`@mui/lab` LoadingButton etc. still used (staff forms).  
Lab = unstable-ish components — know migration to material when stabilized.

---

## Extra — Next.js App Router emotion

Client providers required.  
Server Components can't useTheme.  
Pass nothing theme-dependent to RSC without care.

---

## Extra — branding primary green

themeConfig primary `#00A76F` — product identity.  
preset overrides may change — design ack.

---

## Band-e gharardad — ye bar digar sade

1. **MUI 7** = UI kit.  
2. **Emotion** = styles engine.  
3. **themeConfig** = defaults (rtl, fonts).  
4. **createTheme** = build theme object.  
5. **ThemeProvider** = inject + CssBaseline.  
6. **Rtl** = CacheProvider + stylis.  
7. **Settings** = user direction/mode/color.  
8. **InitColorSchemeScript** = anti-FOUC.  
9. **Overrides** = global component look.  
10. **Exceptions** = LTR islands (tables/charts).

---

## Extra — Capacity mental

Theme object moderate size.  
Many Emotion classes over session — browser OK.  
Don't createTheme every keystroke — memo deps settings/lang only.

---

## Extra — upgrade checklist MUI

Read breaking MUI 7 notes; Grid API; import paths; cssVars default; test RTL thoroughly; X packages peer align.

---

## Extra — popover / menu anchor

RTL anchorOrigin horizontal left/right swap mental model.  
Custom popover styles check `isRtl` (codebase has).

---

## Extra — print / PDF

jspdf / reports may ignore MUI dir — separate (Day 39 server).  
UI print CSS `@media print` rare.

---

## Extra — storybook?

Agar nist — theme tested via app. Optional Storybook with ThemeProvider wrapper.

---

## Extra — `classesPrefix: 'minimal'`

Generated class names branding from template.  
Useful debug DevTools search `minimal-`.

---

## Extra — spacing scale

`theme.spacing(1)` = 8px default factor.  
Consistent gap Stack/Grid — don't mix random px in every file.

---

## Extra — breakpoints

`theme.breakpoints.down('md')` for responsive drawers.  
RTL doesn't change breakpoint widths — only flow.

---

## Extra — when NOT to use sx for everything

Animation-heavy / canvas / maplibre — external CSS.  
Keep MUI for chrome/forms; special viz own styles with dir=ltr wrapper if needed.

---

## Khoruj-e zehni

> Midunam UI Dejban MUI 7 + Emotion-e; theme moshtarak @repo/ui ba default RTL va IRANSans; Rtl ba stylis-plugin Emotion cache; settings direction/mode; CssBaseline + css variables light/dark; va jazire-haye LTR (grid) ro midunam.

Age in paragraph mal-e to shod — Day 47 done.

---

*Day 47 tamum. Ba'd: Day 48 — i18next + Jalali (amade). Fehrest: [README.md](./README.md).*
