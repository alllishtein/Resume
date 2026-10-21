# 06 — Decorator

Ye object ra migozari dakhel-e object-e digar ke haman gharardad ra darad. Sedazananade farq ra nemibinad. Pusheshe, ghabl ya bad az asl, ye kar-e ezafe mikonad. Class-e asli ra dast nemizani.

## Moshkel

Class-e `OrderSender` kar-ash ferestadan ast. Bad mikhahi log, talash-e dobare, va "agar hamin ra ghablan ferestadim digar nafrest".

Agar har kodam ra ba `if` dakhel-e khode class bezari, class chand dalil baraye taghir peyda mikonad. Agar ba inheritance besazi, tarkib-ha monfajer mishavand: `LoggingRetrySender`, `LoggingCacheSender`, va hamin-tor ta akhar.

## Ide

Har kar-e ezafe ye pushesh ast. Pushesh-ha ru ham michinand. Mesl-e lebas: badan yeki ast, kot va kafsh joda pushide mishavand.

Sedazananade faghat gharardad ra mibinad, masalan `Send`. Nemidanad asl ast ya do laye pushesh.

```
sedazananade
  → pushesh-e log
      → pushesh-e talash-e dobare
          → ferestande-ye email
```

Ferestande-ye email hich pusheshi ra nemishnasad.

Ghanun-ha:

**Gharardad-e birun va dakhel yeki ast.** Agar pushesh method-e taze-i besazad va sedazananade ra majbur konad haman ra seda bezanad, digar Decorator nist. Fayede-ye pattern in ast ke sedazananade avaz nashavad.

**Pushesh saheb-e kar-e asli nist.** Kar ra miseporad be dakhel. Agar hame-chiz ra az no benevisad, pushesh-e dorughin ast.

**Chand pushesh ru ham mineshinand.** Pas pushesh nabayad farz konad dakhel-ash hatman class-e asli ast. Dakhel mitavanad khodesh pushesh bashad.

**Tartib ma'ni darad.** Log-e birun-e talash-e dobare: ye log baraye chand talash. Log-e dakhel-e talash-e dobare: har talash ye log. Haman do class, do tartib, do raftar.

**Kar-e ezafe-ye penhan bayad roshan bashad.** Talash-e dobare-ye penhan mitavanad email ra do bar befrestad. Agar alamat-e "anjam shod" ra bad az kar-e asli bezari, daghighan ye bar tazmin nist. Agar kar khata bedahad, alamat nemikhorad va talash-e dobare dorost ast. Agar kar movaffagh bashad va alamat khata bedahad, daf'e-ye bad kar dobare ejra mishavad. Dakhel bayad tekrar ra tahammol konad.

## Mesal-e koochik

```csharp
interface INotifier { Task SendAsync(string message, CancellationToken ct); }

sealed class IdempotentNotifier(INotifier inner, ISeenStore seen) : INotifier
{
    public async Task SendAsync(string message, CancellationToken ct)
    {
        if (await seen.AlreadyAsync(message, ct)) return;
        await inner.SendAsync(message, ct);
        await seen.MarkAsync(message, ct);
    }
}
```

Email az fehrest-e "dide-shode-ha" khabar nadarad. Test-e email bedune an fehrest ast. Test-e tekrar ba ye dakhel-e ja'li ast.

## Ba chi ghalt mishavad

**Inheritance** class ra to selsele-maratab avaz mikonad. Decorator object ra dakhel-e object migozarad va moghe'-e ejra mishe chid. Class-e asli az pushesh khabar nadarad.

**Proxy** to GoF shekl-ash nazdik ast, vali hadaf-ash kontrol-e dastresi ast: nagozar bebinad, dir besaz, ya boro az process-e digar biavar. Decorator mas'uliat-e taze ezafe mikonad. Har wrap ra Decorator seda nakon.

**Chain** chand namzad darad va masir ra miborad. Decorator ye asl-e moshakhas ra mipushanad.

**Strategy** khode algorithm ra avaz mikonad. Decorator haman algorithm ra negah midarad va doresh chiz migozarad.

## Koja estefade nakon

Ye `if` to ye class pushesh nemikhahad. Ye pushesh ke hamzaman log va talash-e dobare va cache va authentication bashad dobare chand-dalili shode. Har kar ye laye.

## Hala dar Dejban

`IdempotentDomainEventHandler<TDomainEvent>` haman pushesh-e "dobare ejra nakon" ast.

Masir: `Personnels/.../Outbox/IdempotentDomainEventHandler.cs` va mo'adel-ash to har module.

Dakhel-ash parameter-e `decorated` ast, yani handler-e asli. Ghabl az sedayesh to jadval-e `personnels.outbox_message_consumers` negah mikonad. Kelid, shenase-ye event be-alave-ye esm-e noe-e handler-e dakheli ast (`decorated.GetType().Name`). Esm-e khode pushesh na, chon baraye hame yeki ast va do handler-e ye event ra eshtebah yeki mikonad.

Agar radif hast, handler-e asli seda nemishavad. Agar nist, avval handler, bad insert.

Insert bad az kar ast. Pas haman nokte-ye bala inja zende ast: khatay-e handler yani alamat nemikhorad va talash-e dobare mojaz ast. Movaffaghiyat-e handler va khatay-e insert yani momken ast handler dobare ejra shavad. Jomle-ye dorost: tahvil-e hadaghal ye bar, ba kam kardan-e tekrar. Daghighan ye bar nist.

Chasbidan-e pushesh ba `new` dasti nist. `PersonnelsModule` ba Scrutor in kar ra mikonad:

```csharp
services.TryAddScoped(domainEventHandler);
services.Decorate(domainEventHandler, closedIdempotentHandler);
```

Yani har kas an handler ra bekhad, pushesh ra migirad, va pushesh asl ra be esm-e `decorated` migirad. Karkhane-ye handler-ha `GetRequiredService` mizanad va pushesh ra migirad. Handler-e business az in jadval khabar nadarad. Test-e ghanun-e business bedune SQL-e an jadval momken ast.

Hamin shekl, joda, baraye event-e beyn-e module-ha: `IdempotentIntegrationEventHandler`.

Pipeline-e MediatR (log va validation) az nazar-e pichidan shabihe ast, vali Chain ast, chon validation masir ra miborad. An ra in pushesh seda nakon.

## Agar beporsand, in tor begou

> Decorator pusheshi ba haman gharardad ast. Sedazananade avaz nemishavad. Chand laye ru ham tartib darand. Class-e asli az pushesh khabar nadarad. Alamat-e bad az kar, daghighan ye bar nist. To Dejban `IdempotentDomainEventHandler` dor-e handler-e domain neshaste. Kelid-ash shenase-ye event va esm-e handler-e dakheli ast. Scrutor ba `Decorate` vasl-ash mikonad. Event-e beyn-e module-ha pushesh-e joda ba hamin ide darad.

## Dah so'al

**1. Chera inheritance baraye "log + talash-e dobare + cache" bad ast?**
Har tarkib ye subclass-e taze mikhahad. Ba chidan-e pushesh, har laye ra ye bar minevisi.

**2. Sedazananade che chizi ra nabayad bebinad?**
Noe-e moshakhas-e pushesh. Agar majbur shavad method-e taze seda bezanad, Decorator nist.

**3. Tartib-e do pushesh che ra avaz mikonad?**
Mahdude-ye ghabl va bad ra. Log-e birun-e talash-e dobare ye record baraye chand talash ast.

**4. Farq-ash ba Proxy chi ast?**
Shekl nazdik ast. Proxy dastresi ra kontrol mikonad. Decorator kar-e taze ezafe mikonad.

**5. Farq-ash ba Chain chi ast?**
Chain chand namzad darad va masir ra miborad. Decorator ye asl-e moshakhas ra mipushanad.

**6. Chera alamat-e bad az kar daghighan ye bar nist?**
Beyn-e movaffaghiyat-e kar va movaffaghiyat-e alamat, kharabi mitavanad kar ra dobare pish biavarad.

**7. To Dejban handler-e asli chetor joda test mishavad?**
Pushesh ba DI doresh amade. Test-e ghanun, jadval-e consumer ra nemibinad.

**8. Chera `GetType` ru `decorated` ast na ru khode pushesh?**
Khode pushesh baraye hame ye esm darad. Tekrar bayad handler-e business ra joda konad.

**9. Do handler baraye ye event chand bar ejra mishavand?**
Har kodam ye bar. Do esm, do radif.

**10. `services.Decorate` che mikonad?**
Har kas noe-e handler ra bekhad, pushesh ra migirad va asl dakhel-e pushesh ast.
