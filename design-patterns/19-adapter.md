# 19 — Adapter

*Do interface ke be ham nemikhorand. Yek class-e nazok tarjome mikonad. Hich kodam ra baz nakon.*

---

## Ye khat

Adapter shekl-e A ra be shekl-e B tabdil mikonad ta client faghat B ra bebine. A va B taghir-e dasturi nemikhorand.

## 1. Error-e axios → jomle-ye UI

`packages/api-client/src/getErrorMessage.ts`

```typescript
export function getErrorMessage(error: any): string {
  return extractErrorMessage(error) || 'خطای ناشناخته در انجام عملیات!';
}
```

`extractErrorMessage` shekl-haye mokhtalef ra mifahmad: ProblemDetails, string-e farsi, field-haye fanni (`traceId`, `status`, `stack`) ra **rad** mikonad (`IGNORED_KEYS`), va matn-e englisi-e "Bad Request" ra be onvan-e payam-e karbar ghabool nemikonad.

Client-e UI: "yek string-e farsi". Server: RFC 7807 ya `{ errors: ... }` ya string. Hich kodam be khater-e digari avaz nemishavad. Adapter vasat ast.

In hamangoo'i ba Result-e backend ast (ketabche-ye 11): server `ErrorOr` ra be ProblemDetails tabdil mikonad, client ProblemDetails ra be toast tabdil mikonad. Do adapter, do boundary.

## 2. Ragham-e farsi → ragham-e API

Request interceptor `toEnglishDigits` va `normalizeDigitsDeep` ra roye params, `FormData`, va JSON mizanad. Keyboard-e farsi `۱۲۳` mifersad. API `123` mikhahad. Form-ha adapter nistand. Zanjir-e HTTP adapter ast.

Agar farda contract avaz shavad va server khodash ragham-e farsi ra bepazirad, yek ja (interceptor) ra bar midari, na 80 form.

## 3. Adapter-e koochak-e backend

`UpdateVisitReservation` validator-e **create** ra ba yek class-e dakheli-e adapter dobare estefade mikonad:

`Visitors/.../UpdateVisitReservation/UpdateVisitReservationCommandValidator.cs`

```csharp
private sealed class CreateVisitReservationCommandValidatorAdapter
    : AbstractValidator<UpdateVisitReservationCommand>
```

Ghanun-haye create roye shekl-e update ejra mishavand bedune copy-paste va bedune inke validator-e create type-e update ra beshnasad. Esm-e class khodesh "Adapter" ast. Koochak ast vali mesal-e vaghe'i-e haman pattern, bedune ACL.

## Farq-hayi ke interview-er eshtebah migirad

| | Adapter | Facade | Decorator |
|---|---|---|---|
| Interface-e khoruji | **motefavet** az dakheli | sade-shode-ye haman subsystem | **haman** interface |
| Hadaf | nasazgari | sadegi | behavior-e ezafe |
| Mesal | axios error → string | `getDutyCycles` | idempotent handler |

Agar `getErrorMessage` ra facade seda koni, jomle-at shel ast. Facade subsystem ra sade mikonad. Inja do gharardad-e nasazgar tarjome mishavand.

Agar interceptor-e ragham ra decorator-e axios seda koni, nazdik ast (wrap-e request) vali **hadaf** taghir-e shekl-e data ast, na ezafe kardan-e log/cache. Begou adapter-e dakhel-e chain.

## Script-e 60 sanie

> "Adapter-e asli-e front `extractErrorMessage` ast: ProblemDetails va error-e axios ra be yek jomle-ye farsi tabdil mikonad va field-e fanni ra hazf mikonad. Dovomi normalize-e ragham to interceptor ast ta form-ha joda `۱۲` ra tabdil nakonand. To backend, validator-e update yek adapter-e dakheli darad ke ghanun-e create ra roye command-e update ejra mikonad. Hich kodam decorator nist chon interface-e do taraf yeki nist."

---

## 10 soal

**1. Adapter key lazem ast?**
Vaghti do system-e mojood ra nemitavani avaz koni va be ham nemikhorand: library, HTTP, ya yek validator-e ghadimi va yek command-e jadid.

**2. Object adapter va class adapter?**
Object: adapter, adaptee ra **composition** mikonad (`extractErrorMessage(error)`). Class: inheritance az adaptee. Ma object adapter darim. Composition inja behtar ast chon shekl-e error irsi nist.

**3. Chera IGNORED_KEYS?**
Ta `traceId` va "Internal Server Error" be karbar naresad. Adapter filter ham hast, na faghat rename.

**4. Default-e `'خطای ناشناخته...'`?**
Agar adaptee hich matn-e ghaabel-e namayesh nadashte bashad, UI `undefined` toast nakonad. Yek payam-e sabet-e akhar.

**5. Adapter va mapper (Mapster)?**
Mapster field-e ham-nam ra copy mikonad. Adapter vaghti **gharardad** farq darad (error shape, ragham, command-e digar), na vaghti `FirstName` → `firstName`.

**6. Ragham ra to Zod ham mitavan tabdil kard. Chera interceptor?**
Zod har form. Yek form-e jadid faramoosh mikonad. Interceptor hame-ye body-ha ra mibinad. Zod hanuz baraye ghanun-e field khoob ast. Do laye-ye mokhtalef.

**7. Adapter-e validator risk?**
Ghanun-e create roye update shayad yek field-e ekhtelaf dashte bashad (id ejbari-e update). Adapter bayad faghat ghanun-e moshtarak ra vasl konad, na hame chiz ra koor-koor.

**8. Test-e extractErrorMessage?**
Input-e ProblemDetails-e farsi → haman jomle. Input-e `{ traceId, title: 'Bad Request' }` → default ya hich matn-e englisi. Input-e string-e sade → haman string.

**9. Adapter mitavanad network bezanad?**
Nabayad. Adapter tarjome-ye pure ast. I/O an ra test-napazir va chand-mas'uliat mikonad.

**10. Chand shekl-e error-e jadid az server?**
Yek tabe' ra gostaresh bedeh va yek test-e jadid. 40 toast-e component ra dast nazan. Hamin dalil-e jam' kardan-e adapter ast.
