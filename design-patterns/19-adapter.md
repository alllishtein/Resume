# 19 — Adapter

Do taraf az ghabl sakhte shode-and va be ham nemikhorand. Hich-kodam ra baz nemikonim. Ye shey'-e nazok vasat mimanad va zaban-e yeki ra be zaban-e digari tarjome mikonad.

## Moshkel

Code-e to `string` farsi baraye toast mikhahad. Server `ProblemDetails` midahad: `title`, `errors`, `traceId`, gahi string-e englisi-ye "Bad Request". Library-e HTTP khodesh `AxiosError` midahad.

Se shekl. Hich-kodam ghalat nist. Agar toast ra avaz koni ta `traceId` ra balad bashad, UI be HTTP chasbide. Agar server ra avaz koni ta faghat ye string-e sade bedahad, client-haye digar mishkanand.

Adapter vasat mimanad ta hich taraf avaz nashavad.

## Ide

Client ye interface mikhahad. Chiz-e mojud interface-ye digari darad. Adapter interface-ye client ra pish-e ru bazi mikonad va dakhel, chiz-e mojud ra seda mizanad.

Shekl-e ghalib object adapter ast: adapter, chiz-e bigane ra composition mikonad, az an inherit nemikonad. Inherit kardan az `AxiosError` bi-ma'ni ast.

```
Client → "ye string-e farsi bedeh"
           Adapter
             dakhel: HttpError
             matn = farsi-ye ghabel-e namayesh, bedune traceId
```

Client `AxiosError` ra import nemikonad.

Ghanun-ha:

**Tarjome, na ghanun-e jadid.** Adapter "email khali namotabar ast" ra ijad nemikonad. An ghanun-e domain ast. Adapter faghat miguyad in shekl-e khata, an shekl-e reshte.

**Pure. Bedune I/O.** Adapter shabake nemizanad. Vorudi-ye x, khoruji-ye y. Test-ash jadval-e vorudi/khoruji ast.

**Field-e fanni ra be ensan nadeh.** `traceId`, stack, "Internal Server Error" etela'at-e mohandes-and. Tarjome gahi andakhtan ast, na faghat rename.

**Default-e akhar gharardad ast.** Agar chiz-e ghabel-e namayesh namand, client `undefined` nabinad. Ye jomle-ye sabet.

Ja-haye rayej: khatay-e HTTP → matn-e UI, ragham-e ensan → ragham-e API, validator-e ye command ke bayad ru command-e digar ejra shavad bedune copy.

## Ba chi ghalt mishavad

**Facade** subsystem-e khodet ra sade mikonad. Adapter interface-ye bigane ra jor mikonad. Facade mitavanad dakhel-ash adapter dashte bashad.

**Decorator** haman interface ra wrap mikonad. Adapter interface-ye digar misazad. Agar khoruji va vorudi ye gharardad-and, decorator ast.

**Mapper** field-e ham-nam ra copy mikonad, mesl-e `FirstName` → `firstName`. Adapter vaghti gharardad farq darad, na vaghti faghat rename ast.

**Bridge** az avval abstraction va implementation ra joda mikonad ta har do mostaghel rost konand. Adapter badan, beyn-e do chiz-e az ghabl nasazgar, vared mishavad. Bridge pishgiri. Adapter darman.

Agar khodet har do taraf ra hamin emruz misazi, az avval ye interface besaz. Adapter-e ezafe vasat-e code-e khodet ezafe ast.

## Hala dar Dejban

**1. Khatay-e HTTP → jomle-ye UI.**
`packages/api-client/src/getErrorMessage.ts` va `extractErrorMessage.ts`.

Target: `string`. Client-e toast body-ye axios ra baz nemikonad.

`extractErrorMessage` shekl-haye mokhtalef ra mifahmad va `IGNORED_KEYS` chiz-hayi mesl-e `traceId`, `stack`, `status`, `config` ra rad mikonad. Matn-e englisi-ye "Bad Request" ra be onvan-e payam-e karbar ghabul nemikonad.

`getErrorMessage` agar chizi namand, `'خطای ناشناخته در انجام عملیات!'` barmigardanad.

Samt-e server, `ErrorOr` be ProblemDetails tabdil mishavad. An ham tarjome-ye marz ast. Do adapter, do marz.

**2. Ragham-e ensan → ragham-e gharardad.**
Interceptor `toEnglishDigits` va `normalizeDigitsDeep` ra ru params, FormData, va JSON mizanad. Keyboard `۱۲۳` mifrestad. API `123` mikhahad. Ye jay-e markazi, ta 80 form joda an ra faramush nakonand.

In adapter dakhel-e chain-e interceptor neshaste. Chain pattern-e joda ast. Tarjome-ye ragham pattern-e joda. Ye file, do mafhum.

**3. Validator-e create ru command-e update.**
`UpdateVisitReservationCommandValidator` class-e dakheli-ye `CreateVisitReservationCommandValidatorAdapter` darad. Ghanun-e create ru shekl-e update ejra mishavad, bedune inke validator-e create type-e update ra beshnasad. Faghat ghanun-e moshtarak. Agar update ye ghanun-e ekhtelafi darad (id ejbari), an ra kur-kur be create naspar.

## Agar beporsand, in tor begou

> Adapter vasat-e do interface-e nasazgar ast va hich taraf ra edit nemikonad. Shekl-e ghalib composition ast, na inheritance. Pure ast. Facade sade-sazi ast, decorator haman interface, bridge tarahi-ye avval. Front do adapter darad: extractErrorMessage shekl-e khata ra be string-e farsi tabdil mikonad va traceId ra mindazad. Dovom ragham-e farsi be englisi dakhel-e interceptor. Backend validator-e update ye adapter-e dakheli darad ke ghanun-e create ra ru command-e update ejra mikonad.

## Dah so'al

**1. Adapter che chizi ra avaz nemikonad?**
Adaptee va client. Faghat vasat tarjome ezafe mishavad.

**2. Object adapter va class adapter?**
Avval composition. Dovom inheritance az chiz-e bigane. Avval baraye type-e HTTP dorost ast.

**3. Chera I/O dakhel-e adapter shekast ast?**
Tarjome dige pure nist. Test-e jadvali az beyn miravad.

**4. Farq ba Decorator?**
Decorator haman interface, raftar-e ezafe. Adapter interface-ye digar.

**5. Farq ba Bridge?**
Bridge az avval joda tarahi mikonad. Adapter do chiz-e az ghabl nasazgar ra badan jor mikonad.

**6. Farq ba mapper-e field?**
Mapper rename-e ham-ma'ni. Adapter vaghti gharardad farq darad.

**7. `IGNORED_KEYS` kodam ghanun ast?**
Tarjome mitavanad andakhtan bashad. Field-e fanni payam-e ensan nist.

**8. Jomle-ye "khatay-e nashenakhte" chera?**
Ta client `undefined` nabinad vaghti matn-e ghabel-e namayesh nist.

**9. Ragham-e farsi kodam pattern ast va chera to interceptor ast?**
Adapter-e shekl-e vorudi. Jay-ash zanjire-ye hame-ye call-ha ast ta ye form faramush nakonad. Jay-ash ma'ni-ye "interceptor = adapter" nist.

**10. Adapter-e validator-e visit che khatari darad?**
Ghanun-e ekhtelafi-ye update kur-kur az create ers mibarad. Faghat moshtarak-ha ra vasl kon.
