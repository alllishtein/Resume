# 17 — Query Key Factory

*Hoviat-e cache yek array-e dasti-e partakande nist. Yek tabe' an ra misazad.*

---

## Ye khat

TanStack Query data ra ba **query key** cache mikonad. Key bayad baraye haman data haman bashad, va baraye data-ye mokhtalef farq dashte bashad. Factory yek ja an array ra misazad ta `useQuery` va `invalidateQueries` az ham joda naioftand.

Pattern-e klasik: **Simple Factory** (tabe'-hayi ke object/array-e key misazand). Chiz-e jadooyi nist. Arzesh-e an yeksan budan-e hoviat ast.

## Mesal

`apps/dejban/src/services/employment-type/emp-type.keys.js`

```javascript
export const empTypeKeys = {
  all: ['empType'],
  list: (params) => ['empType', 'list', params],
  infinite: (params) => ['empType', 'infinite', params],
  pagination: (params) => ['empType', 'pagination', params],
  detail: (id) => ['empType', 'detail', id],
};
```

`all` prefix ast. `invalidateQueries({ queryKey: empTypeKeys.all })` list va detail va infinite ra ba ham bi-etebar mikonad, chon TanStack **prefix** match mikonad.

`list(params)` params ra dakhel-e key mizarad. Do filter-e mokhtalef do cache. Haman filter: haman cache, refetch-e ezafi na.

## Hierarchy

```
['empType']                              ← hame
  ['empType', 'list', params]
  ['empType', 'detail', id]
  ['empType', 'pagination', params]
```

Ghanun:

1. Az omumi be joz'i benevis.
2. Object-e `params` bayad stable bashad. Object-e jadid ba haman field-ha **reference**-ash farq darad. TanStack key ra hash mikonad (structural) pas `{a:1}` va `{a:1}` yeki-and. Tartib-e key-haye object mitavanad farq besazad. An ra farz-e "hamishe reference" nakon va farz-e "hamishe bi-khatar" ham nakon: serial-e sabet behtar ast.
3. Id-e `undefined` key-e `['empType','detail', undefined]` misazad va ba detail-e haghighi ghalat share mishavad. `enabled: !!id`.

## Ja-ye do-shekle in repo

Duty roster key ra **dakhel-e** `duty-roster.service.js` darad (`dutyRosterKeys`) va invalidate-hash hanooz string-e joda ast:

```javascript
await client.invalidateQueries({ queryKey: ['duty-cycles'] });
```

In kar mikonad chon `cycles` ba `['duty-cycles', params]` shoru mishavad. Vali string-e `['duty-cycles']` va factory az ham joda-and: yek rename yeki ra ja migozarad. Javab-e mosahebe:

> "Factory-e dorost mesl-e `empTypeKeys` ast ke `all` va `list` az yek prefix miayand. Ja'i ke key-e invalidate joda neveshte shode, ham-nam nist; an ra be `dutyRosterKeys` bargard mikonam."

## Chera na string-e sade `'empType'`

String filter, pagination, va id ra ja nemidahad. Ya hame-ye filter-ha yek cache-e ghalat share mikonand, ya hich invalidate-e daste-bandi nadari. Array-e sakht-yafte har do ra midahad.

## Factory va service

```
useQuery({ queryKey: empTypeKeys.pagination(params), queryFn })
useMutation → onSuccess → invalidateQueries({ queryKey: empTypeKeys.all })
```

`queryFn` factory nist. Key factory nist ke data begirad. Faghat **esm** misazad. Gereftan-e data `*.http.js` ast (facade, ketabche-ye 18).

## Script-e 60 sanie

> "Har feature yek object-e key darad. `empTypeKeys.all` prefix ast va `list` va `detail` zir-e an-and, pas invalidate-e `all` hame-ye cache-e an feature ra mishavad. Params dakhel-e key ast ta do filter do cache bashand. Mutation haman factory ra invalidate mikonad, na yek string-e copy-shode. Duty roster hanuz yek ja string-e joda darad va an noghte-ye shekanande-ye ham-nami ast."

---

## 10 soal

**1. Query key chist?**
Hoviat-e yek cache entry: chi, va ba che vorudi. TanStack ba an dedupe, refetch, va invalidate mikonad.

**2. Chera factory?**
Ta `useQuery` va `invalidate` az yek tabe' key besazand. Typo-ye string-e joda cache-e morde misazad ke hichvaght pak nemishavad.

**3. Prefix chist?**
`invalidateQueries({ queryKey: ['empType'] })` har key-i ke ba an **shoru** shavad ra migirad. `detail` va `list` do invalidate nemikhahand.

**4. Params-e object to key?**
Hash-e structural. Do object-e barabar yek cache. Object-e ba `undefined` va bedune field shayad farq konand. Vorudi ra ghabl az key normalize kon.

**5. `enabled: false` va key?**
Key hanuz hoviat ast. Fetch anjam nemishavad. Mofid baraye `detail(id)` vaghti id hanuz nist.

**6. Infinite query key-e joda?**
Bale, `infinite` joda az `pagination`. Shape-e data (safhe-ha-ye anbashte vs yek safhe) yeki nist. Share-e cache an-ha ra mishkanad.

**7. Key-e kheili bozorg?**
Kole form-e 50 field ra bi-niyaz nazan. Faghat chizi ke natije-ye server ra avaz mikonad: filter, sort, page, id.

**8. Ba'd az mutation kodam key?**
Kam-tarin prefix-i ke data-ye dide-shode ra mipooshand. `all` sade va gahi ezafe ast (detail-hayi ke avaz nashode-and ham refetch). Baraye list-e bozorg, key-e list + haman detail.

**9. Key to URL?**
URL mitavanad joz'-e key bashad vali factory behtar ast chon do hook-e ba URL-e sakht-shode-ye farq (slash, query order) do cache mishavand.

**10. Test?**
`expect(empTypeKeys.detail(1)).toEqual(['empType','detail',1])`. Va yek test-e raftar: mutation → spy-e `invalidateQueries` ba `empTypeKeys.all`.
