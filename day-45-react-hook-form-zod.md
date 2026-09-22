# Day 45 — React Hook Form + Zod

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

**Mas'ale:** form-haye bozorg (staff, visitor, armory, …) — state, validation, error UI, submit — chejori bedun chaos?

**Javab Dejban:**

| layer | tool |
|---|---|
| Form state / submit | **React Hook Form** (`useForm`, `Controller`) |
| Validation schema | **Zod** (`z.object`, `refine`, `transform`) |
| Glue | **`zodResolver`** (`@hookform/resolvers/zod`) |
| MUI fields | `Field.Text` / `Field.Select` / … (`RHF*` + Controller) |
| Wrapper | `<Form methods={...} onSubmit={handleSubmit(...)}>` |

Zincir:

```
Schema (Zod) ──zodResolver──► useForm({ defaultValues, mode })
                                  │
                                  ▼
                         <Form> = FormProvider + <form>
                                  │
                                  ▼
                         Field.* (Controller → MUI)
                                  │
                                  ▼
                         handleSubmit(onValid, onInvalid)
                                  │
                                  ▼
                         mutateAsync (Day 44) → toast / reset / close
```

Versions (dejban app): `react-hook-form` ^7, `zod` ^4, `@hookform/resolvers` ^5.

**Band-e gharardad-e jadid:** farz kon / yani chi / chera.

Day 44 = save network. **In ruz = form UX + validation ghabl az network.**

---

# BAKHSH-E AVAL: WORLD — chera RHF + Zod?

## Farz kon — form = formul + dadresi

**RHF:** negahban values, dirty, touched, submit lifecycle — **uncontrolled-ish** ba register/Controller (kam re-render).  
**Zod:** ghavanin «in field chi bashad» — parse/transform/error message.  
**Resolver:** har submit (ya mode) values → Zod → map errors to `formState.errors`.

| faqat useState | RHF+Zod |
|---|---|
| har keystroke setState | optimized updates |
| validation paste har ja | yek schema |
| MUI error dasti | Field + fieldState.error |
| transform digit/null | Zod preprocess/transform |

**Yani chi?** UI state form ≠ server state Query.

---

## Chera Zod (na Yup / manual)?

- TypeScript-friendly (agar TS); JS ham OK  
- `transform` / `preprocess` ghavi  
- compose schemas (`nationalCodeSchema` reuse)  
- Zod 4 APIs in `schema-utils` (honesty: dual style ba `schema-helper`)

---

## Chera na Formik?

Team/template Minimals = RHF. Ecosystem `Controller` + MUI mature. Resume: RHF industry common 2024–26.

---

# BAKHSH-E DOVOM: DEJBAN — skeleton

## Qesmat 1 — olgu-ye kuchek (PatrolArea)

`patrol-area-new-edit-form.jsx` — model sade:

1. `PatrolAreaSchema = zod.object({ name, siteId, description })`  
2. `defaultValues` az `currentItem` / locked site  
3. `useForm({ mode: 'all', resolver: zodResolver(...), defaultValues })`  
4. `reset` vaghti item avaz  
5. `onSubmit = handleSubmit(async (formData) => mutateAsync...)`  
6. JSX: `<Form methods={methods} onSubmit={onSubmit}><Field.Text name="name" />...`

**Lab:** in file ra seda kon — template zehni.

---

## Qesmat 2 — `Form` provider

`src/components/hook-form/form-provider.jsx`:

```jsx
export function Form({ children, onSubmit, methods, id }) {
  return (
    <RHFForm {...methods}>
      <form id={id} onSubmit={onSubmit} noValidate autoComplete="off">
        {children}
      </form>
    </RHFForm>
  );
}
```

**noValidate:** browser HTML5 validation off — Zod boss.  
**autoComplete off:** intranet forms (national code) — kam autofill noise.  
**methods spread:** hame context RHF atfale `useFormContext`.

---

## Qesmat 3 — `Field` namespace

`fields.jsx` → `Field.Text`, `Field.Select`, `Field.Autocomplete`, `Field.DatePicker`, `Field.Upload`, …

Har `RHF*` ≈:

```jsx
const { control } = useFormContext();
return (
  <Controller
    name={name}
    control={control}
    render={({ field, fieldState: { error } }) => (
      <TextField {...field} error={!!error} helperText={error?.message} />
    )}
  />
);
```

**Chera Controller?** MUI controlled components; `register` alone kamtar kafist for Select/Date/Upload.

**RHFTextField extras:** `toEnglishDigits` on input; `showRequired` star; number transforms via `minimal-shared`.

---

## Qesmat 4 — `useForm` options Dejban

| option | mesal | ma'ni |
|---|---|---|
| `resolver` | `zodResolver(schema)` | validation |
| `defaultValues` | mapped entity / empty | initial |
| `mode` | `'onSubmit'` (staff) / `'all'` (patrol) | key validate |
| `values` / `reset` | edit load | sync async data |

Staff: `mode: 'onSubmit'` — error ba'd az dokme.  
Patrol: `mode: 'all'` — zudtar feedback.

---

## Qesmat 5 — submit pipeline

```js
handleSubmit(onValid, onInvalid)
```

- **onValid:** data *parsed* (ba'd az Zod transform) → API  
- **onInvalid:** optional scroll/toast first error  

Staff: `onSubmit={handleSubmit(onSubmit, onError)}` dakhel `<Form>`.

**isSubmitting:** disable button / LoadingButton.

---

## Qesmat 6 — edit: map + reset

```js
mapStaffToForm(record) → defaultValues shape
useEffect / reset(mapped) when record loads
```

**Chera map?** API DTO ≠ form fields (dates Jalali string, nested site/unit, null → `''`).  
**Smell:** forget reset → stale create values on open edit dialog.

---

# BAKHSH-E SEVOM: Zod dar Dejban

## Qesmat 7 — schema staff (ghavi)

`staff-schema.js`:

- `nationalCodeSchema` — length 10 + `isValidIranianNationalCode` via `superRefine`  
- `mobileNumberSchema` — 11 digit + `09`/`98` rules  
- `birthCertificateCodeSchema` — optional + validate if present  
- `staffSchema` object: names, dates, employment, position/site/unit required  
- `z.preprocess` for `accessCode` ('' → null, digit → number)  
- `.transform` English digits / null → `''` for selects  

**Yani chi?** Domain Iran identity rules to FE ghabl az BE (BE ham bayad validate — defense in depth).

---

## Qesmat 8 — `schema-utils` vs `schema-helper`

| file | style |
|---|---|
| `apps/dejban/.../schema-utils.js` | Zod **4-ish** (`z.email`, `.check`, `{ error: }` ) |
| `packages/ui/.../schema-helper.js` | classic `required_error` / `message` |

**Honesty:** do helper — migration incomplete. Form-ha momken az hardcode `zod.object` estefade konand (patrol) ya custom schemas (staff).

Interview: «We have shared helpers; many feature schemas are local for domain messages (i18n/Farsi).»

---

## Qesmat 9 — i18n messages

Patrol: `t_patrolArea('formValidationErrors.name.required')` dakhel schema.  

**Caveat:** schema recreate when `t` changes — often define schema inside component or useMemo deps `[t]`.  
Staff: hardcode Farsi messages — simpler, kam i18n.

---

## Qesmat 10 — transform vs refine

| API | kar |
|---|---|
| `transform` | value ra avaz kon (digits) |
| `preprocess` | ghabl az type parse |
| `refine` / `superRefine` | rule + custom issue |
| `nullable().optional()` | empty API fields |

**Farz kon:** user Persian digits type mikone → transform English → API happy + Axios interceptor ham normalize (Day 44) — belt and suspenders.

---

## Qesmat 11 — connection to mutations

```js
await createPatrolArea.mutateAsync(formData);
toast.success(...);
onClose(); onRefetch?.();
```

Validation OK ≠ server OK.  
`extractErrorMessage` / toast error az Axios (Day 44).  
Zod = client gate; BE FluentValidation = server gate (Day 11).

---

## Qesmat 12 — complex staff form extras

- Stepper tabs (personal / org / documents)  
- `watch` employment type → conditional fields  
- FormData multipart for documents (Day 41)  
- `setValue` location cascade country→province→city  
- Dialog open/close lifecycle  

**Yani chi?** RHF scale mikone; schema hanooz single source for core fields.

---

# BAKHSH-E CHAHAROM: farz kon / senario

## Se dastan

**1) Create patrol area**  
Open dialog → empty defaults → type name → submit → Zod OK → POST → invalidate list → toast.

**2) Invalid national code**  
Staff submit → Zod superRefine fail → `errors.nationalCode` → Field shows helperText → no API call.

**3) Edit staff**  
Load by id (Query) → mapStaffToForm → reset → user edits → PUT → invalidate.

---

## Smell-ha

1. Schema inside render bedun memo → recreate resolver churn  
2. `console.log` left in submit (patrol)  
3. Dual schema-utils / schema-helper  
4. mode inconsistent across forms  
5. Client-only validation trust — attacker bypass (BE must validate)  
6. Huge staff form file (1000+ lines) — hard review  
7. `nullable().transform('')` patterns verbose — extract helpers  

---

## Debug checklist

| symptom | check |
|---|---|
| Submit no API | Zod fail — log `onInvalid` / `formState.errors` |
| Error not showing | Field `name` mismatch schema key |
| Stale edit values | forgot `reset` |
| Number field NaN | preprocess empty string |
| Date invalid | dayjs format vs schema |
| Digits Persian reject | transform missing |
| Button stuck loading | mutate throw; isSubmitting |

---

## 25 soal-e mosahebe

1. RHF vs controlled useState?  
2. zodResolver chie?  
3. Controller chera?  
4. mode onSubmit vs all?  
5. defaultValues vs reset?  
6. transform vs refine?  
7. noValidate chera?  
8. Field namespace?  
9. handleSubmit two callbacks?  
10. Client vs server validation?  
11. Iranian national code koja?  
12. schema-utils vs helper?  
13. i18n in schema caveats?  
14. FormData + RHF?  
15. watch performance?  
16. setValue options (`shouldValidate`)?  
17. Disable submit when invalid?  
18. Yup vs Zod?  
19. How test schema pure? (`safeParse`)  
20. Nested fields `user.name`?  
21. Array fields useFieldArray?  
22. Connect mutation invalidate?  
23. Why unmount reset?  
24. Accessibility error announce?  
25. Day 45 vs 44?

---

## Senario-ha

**S1:** `name="siteID"` vs schema `siteId` → silent fail / no error bind.  
**S2:** Optional phone empty string → need transform null.  
**S3:** Rapid open/close dialog → race reset; use key={id} on form.  
**S4:** Zod transform changes type number → API expects string — check contract.  
**S5:** BE 400 validation → show toast; optionally `setError` field-level.

---

## Mini lab

1. Read patrol form end-to-end  
2. Break schema min length — see UI error  
3. `staffSchema.safeParse` in console with fake data  
4. Trace Field.Text → Controller → error message  
5. Submit staff invalid national code — Network empty  

---

## Resume (1 paragraph)

> Built complex admin forms with **React Hook Form** and **Zod** via `zodResolver`, shared MUI `Field.*` controllers, feature schemas (including Iranian identity rules), and submit handlers wired to TanStack mutations—keeping validation declarative and UI errors consistent.

Keywords: `React Hook Form` · `Zod` · `zodResolver` · `Controller` · `FormProvider` · `validation` · `defaultValues` · `superRefine`

---

## File-haye mohem

| path | chera |
|---|---|
| `components/hook-form/form-provider.jsx` | Form wrapper |
| `components/hook-form/fields.jsx` | Field map |
| `components/hook-form/rhf-*.jsx` | controllers |
| `components/hook-form/schema-utils.js` | shared zod helpers |
| `sections/**/**-new-edit-form.jsx` | feature forms |
| `sections/staff/component/staff-schema.js` | domain schema |
| `utils/iranian-identity` | national/mobile validators |
| `packages/ui/.../schema-helper.js` | alternate helpers |

---

## Ertebat ba ruz-haye dge

| Day | link |
|---|---|
| 11 | BE FluentValidation twin |
| 40 | login forms auth |
| 41 | document upload FormData |
| 44 | mutations after valid submit |
| **45** | this |
| 46 | Zustand (na form server state) |
| 47 | MUI inputs under Field |
| 48 | i18n validation messages |

---

## Chejori digest koni

1. Patrol skeleton hafz kon  
2. Zod staff rules for Iran fields  
3. Field/Controller model  
4. reset/map edit  
5. Resume seda  

---

## Glossary

| term | ma'ni |
|---|---|
| resolver | bridge schema ↔ RHF errors |
| Controller | controlled input bridge |
| defaultValues | initial snapshot |
| reset | replace values later |
| mode | when validate |
| refine | custom predicate |
| superRefine | multi issue ctx |
| preprocess | coerce before parse |
| formState | errors, isSubmitting, isDirty |
| useFormContext | child access methods |

---

## Deep dive — performance

RHF isolates re-renders; `watch()` whole form = more renders.  
Prefer `watch('field')` or `useWatch`.  
Staff watches employment — OK; avoid watch() everything in huge trees.

---

## Deep dive — shouldUnregister

Unmount field clear value — useful steppers conditional.  
Default often keep values; know tradeoff when hiding tabs.

---

## Deep dive — Zod output types

`z.infer<typeof schema>` — TS apps.  
Dejban JS — infer mental: transforms change output (number accessCode).

---

## Anti-pattern

| bad | better |
|---|---|
| validate only in onClick ifs | Zod schema |
| `register` on MUI Select blindly | Controller / Field.Select |
| trust FE only | BE validation |
| mutate ghabl az handleSubmit | inside onValid |
| duplicate error strings 10 files | shared schema pieces |
| store form in Redux | RHF local |

---

## Interview 60s

«Forms use React Hook Form with Zod resolvers. We wrap MUI inputs in Controller-based Field components, define per-feature Zod schemas—including Iranian national code and mobile rules—and on submit call TanStack mutations. Edit flows map API DTOs into defaultValues and reset when data loads.»

---

## Quick self-test

1. Glue package? → `@hookform/resolvers/zod`  
2. Form wrapper? → FormProvider + form  
3. Why noValidate? → Zod owns validation  
4. Staff mode? → onSubmit  
5. National code where? → staff-schema + iranian-identity  
6. Field.Text uses? → Controller  
7. After valid submit? → mutateAsync  

---

## Final checklist

- [ ] RHF + Zod roles  
- [ ] Form + Field  
- [ ] resolver + modes  
- [ ] schema patterns transform/refine  
- [ ] edit map/reset  
- [ ] mutation link  
- [ ] smells dual helpers  
- [ ] resume  

---

## Extra — Farz kon useFieldArray

Companions / multi vehicle rows — `useFieldArray` + zod `z.array`.  
Guest reserve sections — pattern exists in visitor flows.  
Key: `fields.map` + `append`/`remove`.

---

## Extra — async validation

`z.string().refine(async ...)` rare; usually submit → BE unique check.  
Username available: debounce + `setError` manual.

---

## Extra — cross-field refine

`staffSchema.refine((data) => end >= start, { path: ['contractEndDate'] })`.  
Dates contract — check if present; classic Zod.

---

## Extra — disabled fields

Disabled inputs may exclude from submit depending on strategy; RHF includes by default unless unregister.  
Locked siteId: setValue + disable UI but keep value.

---

## Extra — Soalat chera

**Chera Zod to FE?** UX instant; kam roundtrip.  
**Chera BE ham?** security.  
**Chera Controller?** MUI.  
**Chera transform digits?** API Latin digits.  
**Chera Form wrapper?** less boilerplate Provider+form.

---

## Extra — Diagram shenasi mosahebe (30s)

Begu: «Zod schema describes rules. zodResolver plugs it into useForm. Field components use Controller to bind MUI and show errors. handleSubmit runs only when parse succeeds, then we call the mutation.»

---

## Extra — Common bugs table

| symptom | likely |
|---|---|
| errors empty UI | wrong `name` |
| always invalid date | format / null |
| submit twice | no isSubmitting guard |
| value not updating | forgot setValue / Controller |
| schema not run | resolver missing |
| i18n stale message | schema not recreated |
| number 0 fails min | preprocess |

---

## Extra — Layer checklist

| layer | owner |
|---|---|
| Schema | zod file / inline |
| State | useForm |
| Widgets | Field.* |
| Submit | handleSubmit |
| Network | Day 44 mutation |
| Server rules | FluentValidation |

---

## Extra — Related days

- 11 BE validation  
- 44 mutate  
- 47 MUI  
- 48 i18n  
- 41 uploads  

---

## Extra — testCase helper

`schema-utils.testCase(schema, values)` — console green/red parse.  
Lab for national code edge cases.

---

## Extra — LoadingButton pattern

```jsx
<LoadingButton type="submit" loading={isSubmitting || mutation.isPending}>
```

Either formState or mutation pending — align.

---

## Extra — Dialog forms

`open` prop → useEffect reset when open+item.  
Unmount on close (`{open && <Form/>}`) clears state — simple.

---

## Extra — Comparison Formik

Formik context heavier historically; RHF perf marketing.  
Team choice template-driven — don't religion war mosahebe; explain tradeoffs.

---

## Band-e gharardad-e jadid

Schema = ghanun-name.  
Resolver = tarjoman.  
useForm = daftar-khane.  
Field = input ba error lamp.  
handleSubmit = darban.  
Mutation = postchi (Day 44).

---

## 10 jomle fluency

1. RHF owns form state.  
2. Zod owns validation rules.  
3. zodResolver connects them.  
4. Field.* wraps MUI with Controller.  
5. Form is FormProvider plus form tag.  
6. defaultValues and reset drive edit mode.  
7. Transforms normalize digits and nulls.  
8. Iranian identity schemas are reusable.  
9. Valid submit calls mutateAsync.  
10. Server validation still required.

---

## Extra — Zod 3 vs 4 honesty

package `zod` ^4 — new APIs in schema-utils.  
Older schema-helper / some forms still Zod3 mental model (`required_error`).  
Both work via resolvers — read local file style before copy-paste.

---

## Extra — setError from server

```js
catch (e) {
  const msg = extractErrorMessage(e);
  if (field) methods.setError('nationalCode', { message: msg });
  else toast.error(msg);
}
```

Map BE field names when API returns them.

---

## Extra — readOnly computed fields

personnelCode auto — `setValue` + disabled Field; still in schema if required send.

---

## Extra — progressive disclosure

Conditional Zod: `z.discriminatedUnion` employment type contractor vs staff.  
Staff form approximates with watch + optional fields — may strengthen later.

---

## Extra — a11y

`helperText={error?.message}` — ok.  
`aria-invalid` MUI TextField sets with error prop.  
Focus first error onInvalid — nice UX upgrade.

---

## Extra — bundle

Zod + RHF size acceptable admin.  
Don't import all zod locales unused.

---

## Band-e gharardad — ye bar digar sade

1. **RHF** = form engine.  
2. **Zod** = rules + transform.  
3. **zodResolver** = glue.  
4. **Form** = provider wrapper.  
5. **Field.*** = MUI+Controller.  
6. **defaultValues/reset** = create/edit.  
7. **mode** = when check.  
8. **handleSubmit** = gate.  
9. **mutate** = save.  
10. **BE validate** = security.

---

## Extra — Capacity mental

Huge staff schema parse cheap vs network.  
Re-render cost = watch misuse.  
Dialog many mounts OK.

---

## Extra — Onboarding new form checklist

1. Copy patrol skeleton  
2. Define Zod schema + Farsi messages  
3. defaultValues  
4. Field components  
5. mutate create/update  
6. reset on edit  
7. toast + close + refetch  

---

## Extra — smell mega-form split

Extract `PersonalInfoTab` already — keep schema central or `staffSchema.merge` parts.  
Avoid 3 schemas diverge.

---

## Extra — password forms

Login may lighter validation; change password schema min length + match refine.  
Auth Day 40.

---

## Extra — file fields

`schemaUtils.file` / upload Field — Zod file or string URL (edit existing).  
Documents tab staff — hybrid.

---

## Extra — valueAsNumber pitfall

HTML `type="number"` + RHF can stringify.  
Dejban often `preprocess` / Number() in Zod (accessCode) — prefer explicit.

---

## Extra — reset vs setValue batch

`reset(mapped)` replaces entire form snapshot (clean dirty).  
Multi `setValue` keeps dirty flags — choose for edit load vs patch field.

---

## Extra — resolver crash

If schema throws unexpected — form submit hangs weird.  
Keep Zod pure; no API inside schema parse.

---

## Khoruj-e zehni

> Midunam form-haye Dejban ba React Hook Form + Zod (zodResolver) an; Field/Controller baraye MUI; schema ba transform/refine (az jomle national code); edit ba map/reset; submit valid → mutation Day 44; va validation client jaye server nist.

Age in paragraph mal-e to shod — Day 45 done.

---

*Day 45 tamum. Ba'd: Day 46 — Zustand + immer (amade). Fehrest: [README.md](./README.md).*
