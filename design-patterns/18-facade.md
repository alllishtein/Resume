# 18 — Facade

Ye subsystem chand class va chand gharardad-e zesht darad. Facade ye vorudi-ye sade jelo-ye an migozarad. Client subsystem ra nemibinad. Faghat haman vorudi ra mibinad.

## Moshkel

Ferestadan-e ye SMS shayad in-ha ra bekhad: sakhtan-e client, login-e vendor, map-e shomare, retry, tarjome-ye code-e khata. Agar har safhe in shesh ta ra balad bashad, taghir-e vendor = taghir-e har safhe, va ye safhe retry ra faramush mikonad.

## Ide

Facade ye method ast: `sendSms(to, text)`. Shesh ta posht-e an. Safhe vendor ra nemishnasad.

Ketab ye nokte darad ke aksaran ja mioftad: facade mamnoo'iyat nist. Class-haye dakheli hanuz baraye kar-e pishrafte mitavanand baz bashand. Facade rah-e addi ra sade mikonad. Agar hame-ye option-haye vendor ra ham az facade pass koni, chizi sade nashode.

```
Safhe --> SmsFacade.send(to, text)
              |-- AuthClient
              |-- PhoneNormalizer
              |-- VendorSdk
```

Client class-e dakheli ra `new` nemizanad. Agar bezanad, rah-e dovom-e pichide baz mimanad va taghir-e vendor an rah ra shekaste mikonad.

Chand laye ham mojaz ast, be shart-e har laye danesh-e joda ra penhan konad:

```
View   → "list ra bekesh"     (nemidanad cache chist)
Hook   → cache + invalidate   (nemidanad URL)
Http   → URL + method         (nemidanad header-e token)
Client → token, retry, ragham
```

Agar har laye haman danesh ra tekrar konad, laye-ye ezafe dari, facade na.

Ghanun-ha:

**Facade zaban-e client ra harf mizanad, na zaban-e vendor.** `sendSms` na `vendor.post("/v2/messages", { msisdn })`.

**Ye facade, ye subsystem.** `Utils.sendSms` va `Utils.parseExcel` va `Utils.hashPassword` facade nist. Kise-ye god ast.

**Ghanun-e mahsul ra posht-e facade-ye transport ghayem nakon.** "In shift ghablan publish shode" ghanun-e domain ast. Agar to HTTP beneshinad, test-e ghanun be shabake vasl mishavad.

## Ba chi ghalt mishavad

**Adapter** do interface-e nasazgar ra tarjome mikonad. Facade ye subsystem ra sade mikonad. Facade mitavanad dakhel-ash ye adapter dashte bashad. Adapter khodesh facade nist.

**Mediator** beyn-e object-haye ham-arz mistanad ta be ham vast nashavand. Facade beyn-e client-e balatar va subsystem-e pa'intar mistanad. Jahat-e felesh farq darad.

## Hala dar front-e Dejban

```
page.jsx
  → View
      → hook to services/*.service.js     cache, enabled, invalidate
          → tabe' to services/*.http.js    URL va method
              → apiClient                  token, site, refresh, ragham
```

View `axios` ra import nemikonad. Service `Authorization` ra nemidanad. Http `queryClient` ra nemidanad.

Mesal: `useDutyCycles` to `duty-roster.service.js` faghat `queryKey` va `getDutyCycles(params)` ra midanad. `getDutyCycles` URL ra midanad. File-e duty roster `duty-roster.https` nam darad. Gharardad-e module `*.http.js` ast. `.https` esm-e miras ast, pattern-e dovom nist.

`empType` shekl-e tamiz-tar: keys joda, http joda, service joda.

`createItem(url, data)` facade-ye kheyli koli ast. URL hanuz mal-e caller ast. `getDutyCycles` URL ra ham ghom mikonad. Dovomi facade-ye feature ast.

`IEndpoint` va `AddPersonnelsModule()` samt-e server haman fekr-and: ye vorudi, subsystem posht-ash.

Ghanun-e "in shift ra dobare publish nakon" to `*.http.js` nist. Server an ra darad.

## Agar beporsand, in tor begou

> Facade ye vorudi-ye sade jelo-ye subsystem ast. Client dakheli ra new nemikonad. Farq-ash ba adapter: adapter tarjome mikonad, facade sade mikonad. Farq-ash ba mediator: jahat-e bala-be-pa'in. Front-e Dejban se laye darad: hook cache ra midanad, http URL ra, apiClient token va refresh ra. View axios nemibinad. `.https` esm-e miras ast. Ghanun-e business to http nist.

## Dah so'al

**1. Facade che felesh-i ra hazf mikonad?**
Felesh-e client be class-haye dakheli. Faghat felesh be vorudi-ye sade mimanad.

**2. Chera pass-through-e hame-ye option shekast ast?**
Chon client dobare zaban-e vendor ra balad ast.

**3. Facade va Adapter?**
Facade sade mikonad. Adapter do gharardad-e nasazgar ra jor mikonad. Facade mitavanad dakhel-ash adapter dashte bashad.

**4. Facade va Mediator?**
Facade bala va pa'in. Mediator chand ham-arz. Jahat farq darad.

**5. Chand laye-ye facade key dorost ast?**
Vaghti har laye danesh-e motefaveti ra penhan mikonad.

**6. Business rule to facade-ye HTTP?**
Na. Transport va orkestr-e call. Ghanun-e mahsul server ast.

**7. To Dejban view che chizi ra nemidanad?**
URL, header, refresh, va shekl-e axios.

**8. `.https.js` pattern-e joda ast?**
Na. Esm-e miras. Gharardad `*.http.js` ast.

**9. `createItem` che kam darad nesbat be `getDutyCycles`?**
URL hanuz caller ast. Facade-ye feature URL ra ham mal-e feature mikonad.

**10. Import-e mostaghim-e axios to view che moshkeli darad?**
Taghir-e token ya refresh yek view ra ja migozarad. Facade ekhtiari shekaste.
