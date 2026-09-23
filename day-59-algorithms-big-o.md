# Day 59 — Algorithms + Big-O

*Ketabche-ye Dejban stack — style: sade, kamel, berooz*

---

## Ye khat kholase

Interview-e senior hamishe ye bakhsh-e algorithm dare. Na baraye inke az hafezetun merge sort beporsand — baraye inke bebinan **mitunid runtime-e code-etuno tahmin bezanid**. Big-O zaban-e common-e "in code chand-e kond mishe?" In fasl aval theory-e World ra yad migiri, bad miri to code-e Dejban va mishe'mari ke exact kodom LINQ, kodom loop, kodom data structure chejori kar mikone.

---

# BAKHSH-E AVAL: WORLD — Algorithms + Big-O to donya

## Big-O Notation

Big-O mige: vaghti **n** bozorg mishe, runtime **cheghad roshd** mikone?

Moshkel-e vaghe'i in-e: "1000 ta user daram, code 50ms javab mide. 1,000,000 ta user beshe chi?" Big-O javab mide.

### Jadval-e common complexities

| Big-O | esm | mesal | 1K | 1M | hes |
|---|---|---|---|---|---|
| O(1) | Constant | Dictionary lookup | 1 | 1 | ⚡ |
| O(log n) | Logarithmic | Binary search | 10 | 20 | ⚡ |
| O(n) | Linear | Loop, `.Where()` | 1K | 1M | ✅ |
| O(n log n) | Linearithmic | Sort (Merge, Quick) | 10K | 20M | ✅ |
| O(n²) | Quadratic | Nested loop | 1M | 1T ☠️ | ⚠️ |
| O(2^n) | Exponential | Subset generation | ∞ | ∞ | ☠️ |
| O(n!) | Factorial | Permutations | ∞ | ∞ | ☠️ |

**Gha'ede:** O(n²) baraye n > 10K khatarnak-e. O(n log n) ta 10M rahat-e. O(n) ta 100M ok-e. O(1) hamishe ok-e.

### Chand ta rule baraye tahlil

1. **Constant factor hazf mishe** — O(3n) = O(n). O(n/2) = O(n).
2. **Dominant term migire** — O(n² + n) = O(n²). O(n + log n) = O(n).
3. **Nested loop → zarb** — for i in n, for j in m → O(n × m).
4. **Sequential → jam** — O(n) + O(m) = O(n + m) ≈ O(max(n,m)).
5. **Recursive → recurrence relation** — T(n) = 2T(n/2) + O(n) → O(n log n).

### Space complexity

Faghat runtime nist — memory ham count mishe.

| | mesal |
|---|---|
| O(1) space | swap do ta variable |
| O(n) space | `ToList()`, `ToDictionary()`, `ToHashSet()` |
| O(n²) space | adjacency matrix |
| O(log n) space | recursive binary search (call stack) |

---

## Data Structures

### Array / List

| op | complexity |
|---|---|
| Access by index | O(1) |
| Search (unsorted) | O(n) |
| Insert at end | O(1) amortized |
| Insert at middle | O(n) — shift |
| Delete by index | O(n) — shift |
| Contains (unsorted) | O(n) |

C#: `List<T>` = dynamic array (mesle `ArrayList` Java). Grow → double capacity → copy.

### Dictionary / HashMap

| op | avg | worst |
|---|---|---|
| Get/Set by key | O(1) | O(n) collision |
| ContainsKey | O(1) | O(n) |
| Add | O(1) | O(n) resize |
| Remove | O(1) | O(n) |

**Collision:** do ta key haman hash → chain (linked list) ya open addressing.

C#: `Dictionary<TKey, TValue>` — hash table. `GetHashCode()` + `Equals()` bayad dorost bashe.

**ConcurrentDictionary<K,V>** — thread-safe, lock per bucket. Web server concurrent request → in lazem.

### HashSet

Mesle Dictionary vali faghat key (na value). `Add`, `Contains`, `Remove` → O(1) avg. Baraye **duplicate check** va **set operations** (Union, Intersect, Except).

### Stack (LIFO) va Queue (FIFO)

| | Stack | Queue |
|---|---|---|
| Push/Enqueue | O(1) | O(1) |
| Pop/Dequeue | O(1) | O(1) |
| Peek | O(1) | O(1) |
| Search | O(n) | O(n) |

**Stack:** undo, DFS, parenthesis matching, call stack.
**Queue:** BFS, task scheduling, message queue.

C#: `Stack<T>`, `Queue<T>`, `Channel<T>` (async queue).

### LinkedList

| op | complexity |
|---|---|
| Access by index | O(n) |
| Insert at head/tail | O(1) |
| Delete (given node) | O(1) |
| Search | O(n) |

Kheili kam estefade mishe to C#. `List<T>` ta'riban hamishe behtar-e (cache locality).

### Tree

Hierarchy. Har node chand ta child dare.

**Binary Search Tree (BST):**
| op | avg | worst (unbalanced) |
|---|---|---|
| Search | O(log n) | O(n) |
| Insert | O(log n) | O(n) |
| Delete | O(log n) | O(n) |

**Balanced BST** (AVL, Red-Black): worst case ham O(log n). C# `SortedSet<T>`, `SortedDictionary<K,V>`.

**Trie:** baraye prefix search. Autocomplete, dictionary. Har node ye character.

**Heap / Priority Queue:**
| op | complexity |
|---|---|
| Insert | O(log n) |
| Extract min/max | O(log n) |
| Peek | O(1) |

C#: `PriorityQueue<T, TPriority>` (.NET 6+). Baraye "k smallest", Dijkstra, scheduling.

### Graph

Node-ha (vertex) + edge-ha. Directed/undirected, weighted/unweighted.

**Representation:**
- **Adjacency list** — Dictionary<node, List<neighbor>>. Space O(V+E). Sparse graph.
- **Adjacency matrix** — int[V][V]. Space O(V²). Dense graph.

---

## Sorting Algorithms

| algorithm | avg | worst | space | stable? | note |
|---|---|---|---|---|---|
| Bubble sort | O(n²) | O(n²) | O(1) | ✅ | educational only |
| Selection sort | O(n²) | O(n²) | O(1) | ❌ | educational only |
| Insertion sort | O(n²) | O(n²) | O(1) | ✅ | fast for nearly-sorted |
| Merge sort | O(n log n) | O(n log n) | O(n) | ✅ | guaranteed |
| Quick sort | O(n log n) | O(n²) | O(log n) | ❌ | fastest avg, bad pivot = worst |
| Heap sort | O(n log n) | O(n log n) | O(1) | ❌ | in-place, na cache-friendly |
| Tim sort | O(n log n) | O(n log n) | O(n) | ✅ | Python/Java/.NET default |
| Counting sort | O(n+k) | O(n+k) | O(k) | ✅ | integer, range k |
| Radix sort | O(d×n) | O(d×n) | O(n) | ✅ | fixed-length keys |

**C# `.OrderBy()`** = Tim sort (hybrid merge + insertion). Stable, O(n log n).

**PostgreSQL `ORDER BY`** = quicksort + merge (external sort baraye disk). Index → O(log n + k).

### Kei sort nakonid?

- Faghat min/max lazem? → `MinBy`/`MaxBy` O(n). Sort O(n log n) waste.
- Faghat "contains" lazem? → `HashSet` O(1). Sort + binary search O(n log n + log n) waste.
- Faghat top-k lazem? → `PriorityQueue` O(n log k). Full sort O(n log n) waste.

---

## Searching Algorithms

### Linear search — O(n)

```csharp
foreach (var item in list)
    if (item.Id == target) return item;
```

LINQ `.FirstOrDefault(x => x.Id == target)` = linear search.

### Binary search — O(log n)

**Shart:** list bayad **sorted** bashe.

```csharp
int lo = 0, hi = n - 1;
while (lo <= hi) {
    int mid = lo + (hi - lo) / 2;
    if (arr[mid] == target) return mid;
    if (arr[mid] < target) lo = mid + 1;
    else hi = mid - 1;
}
```

C#: `List<T>.BinarySearch()`, `Array.BinarySearch()`.

DB: **B-tree index** = binary search roye disk. `WHERE id = X` ba index → O(log n).

### Hash lookup — O(1) avg

```csharp
var dict = items.ToDictionary(x => x.Id);
var found = dict[targetId];  // O(1)
```

**Best practice:** age chand bar search mikoni to ye list → aval convert to Dictionary/HashSet, bad O(1) lookup.

---

## Algorithm Patterns (Interview)

### 1. Two pointers

Do pointer — yeki az aval, yeki az akhar (ya do ta az aval). Sorted array.

```
sorted:  [1, 3, 5, 7, 9]
          L              R
target = 12 → 3 + 9 = 12 ✓
```

Mesal: Two Sum (sorted), Remove Duplicates, Container With Most Water.

### 2. Sliding window

Ye window roye array/string move mikoni. Fixed ya variable size.

```
"abcabcbb" → longest substring without repeating
 [abc]      → 3
  [bca]     → 3
   [cab]    → 3
    [abc]bb → "abcb" has repeat → shrink
```

Mesal: Max subarray sum (fixed), Longest substring without repeating (variable).

**Real-world:** Rate limiter! Fixed window: reset counter har N second. Sliding window: sub-segment-ha.

### 3. Hash map counting

HashMap baraye frequency count, anagram check, two-sum.

```csharp
var freq = new Dictionary<char, int>();
foreach (var c in s) freq[c] = freq.GetValueOrDefault(c) + 0 + 1;
```

### 4. BFS (Breadth-First Search)

Level-by-level traverse. Queue estefade mikone. Shortest path to unweighted graph.

```csharp
var queue = new Queue<Node>();
var visited = new HashSet<Node>();
queue.Enqueue(start);
visited.Add(start);
while (queue.Count > 0) {
    var node = queue.Dequeue();
    foreach (var neighbor in node.Neighbors)
        if (visited.Add(neighbor))
            queue.Enqueue(neighbor);
}
```

O(V + E) time, O(V) space.

### 5. DFS (Depth-First Search)

Ta te'e ye branch bero, bad back. Stack (ya recursion).

```csharp
void Dfs(Node node, HashSet<Node> visited) {
    if (!visited.Add(node)) return;
    foreach (var neighbor in node.Neighbors)
        Dfs(neighbor, visited);
}
```

O(V + E) time, O(V) space (call stack).

**BFS vs DFS:**
- BFS → shortest path (unweighted), level-order
- DFS → cycle detection, topological sort, path existence

### 6. Dynamic Programming (DP)

Moshkel-e bozorg ra be zir-moshkel-ha taqsim kon. Javab-e zir-moshkel-ha ra cache kon (memoization ya tabulation).

```
Fibonacci(n) = Fibonacci(n-1) + Fibonacci(n-2)
naive recursive: O(2^n) ☠️
memoized:        O(n)   ⚡
```

**Neshune-haye DP:** "minimum cost", "maximum profit", "number of ways", "can you reach...?"

### 7. Greedy

Har step behtarin entekhab ra bokon, omid dri ke global optimum beshe. Na hamishe dorost.

Mesal: Coin change (specific denominations), Activity selection, Huffman coding.

### 8. Divide and Conquer

Taqsim → solve → combine. Merge sort, quick sort, binary search.

T(n) = aT(n/b) + O(n^d) → Master theorem.

---

## Complexity-e LINQ (C#)

In jadval baraye **in-memory** collection-e (IEnumerable). IQueryable → SQL translate mishe, complexity-e DB-e.

| method | complexity | note |
|---|---|---|
| `.Where(predicate)` | O(n) | lazy, vali iterate = O(n) |
| `.Select(projection)` | O(n) | lazy |
| `.FirstOrDefault(pred)` | O(n) worst, O(1) best | stop on first match |
| `.Any(pred)` | O(n) worst, O(1) best | stop on first |
| `.Count()` | O(n) | ya O(1) age ICollection |
| `.Contains(item)` | O(n) List, O(1) HashSet | depends on collection |
| `.OrderBy()` | O(n log n) | Tim sort |
| `.GroupBy()` | O(n) | hash-based |
| `.Distinct()` | O(n) | hash-based |
| `.ToDictionary()` | O(n) | build hash table |
| `.ToHashSet()` | O(n) | build set |
| `.ToLookup()` | O(n) | build grouping |
| `.Aggregate()` | O(n) | single pass |
| `.Intersect()` | O(n+m) | hash-based |
| `.Except()` | O(n+m) | hash-based |
| `.Union()` | O(n+m) | hash-based |
| `.SequenceEqual()` | O(n) | element-by-element |
| `.Zip()` | O(min(n,m)) | pair-wise |
| `.Skip(k).Take(m)` | O(k+m) | iterate + take |
| `.Min() / .Max()` | O(n) | single pass |
| `.Sum() / .Average()` | O(n) | single pass |

**Trap:** `.Where().ToList().Where().ToList()` — har `ToList()` ye traverse + allocation. Chain-e lazy LINQ lazy-e, `ToList()` materialize mikone.

---

## Complexity-e Database operations

| operation | ba index | bedune index |
|---|---|---|
| `WHERE id = X` | O(log n) B-tree | O(n) seq scan |
| `WHERE name LIKE 'A%'` | O(log n + k) | O(n) |
| `WHERE name LIKE '%A%'` | O(n) ❌ index na | O(n) |
| `ORDER BY indexed_col` | O(n) index scan | O(n log n) sort |
| `GROUP BY` | O(n) hash agg | O(n) hash agg |
| `JOIN` (indexed FK) | O(n log m) | O(n × m) nested loop |
| `OFFSET k LIMIT m` | O(k + m) ⚠️ | O(k + m) |
| `COUNT(*)` | O(n) Postgres | O(n) |

**OFFSET trap:** `OFFSET 100000 LIMIT 10` → DB 100,010 row scan mikone! Keyset pagination behtar: `WHERE id > last_id ORDER BY id LIMIT 10` → O(log n + 10).

---

## Chizaei ke to donya hastan vali kam/nist to in bakhsh

- **Trie** — autocomplete, IP routing. `.NET` built-in nadare.
- **Bloom filter** — probabilistic "shayad hast" check. Space-efficient. Duplicate detection at scale.
- **Skip list** — probabilistic balanced list. Redis sorted set internals.
- **B-tree / B+ tree** — database index internal. Postgres/MySQL.
- **Consistent hashing** — distributed cache sharding (Redis Cluster, Cassandra). Minimize rebalance.
- **Merkle tree** — data integrity verification. Git, blockchain.
- **Topological sort** — DAG execution order. Build systems, task scheduling.
- **A* search** — pathfinding ba heuristic. Games, maps.
- **Dijkstra** — shortest path weighted graph. Network routing.

---

# BAKHSH-E DOVOM: DEJBAN — Algorithms to in proje

## Hash table everywhere

Dejban code **ziad** az Dictionary/HashSet estefade mikone. In dorost-e — primary pattern baraye avoid-e O(n²).

### Pattern: "aval index besaz, ba'd O(1) lookup"

**UpdateVisitReservation** — visitor graph sync:

```csharp
// File: Visitors.Application/Visitors/UpdateVisitReservation/UpdateVisitReservationCommandHandler.cs

// 1. Build O(n) indexes
var existingByVisitorId = reservation.Visitors.ToDictionary(x => x.VisitorId);
var keepVisitorIds = incoming.Select(x => x.Visitor.Id).ToHashSet();

// 2. O(1) lookups per item
if (!existingByVisitorId.TryGetValue(pair.Visitor.Id, out var main))
    // ...

// 3. Set difference: O(n) total (na O(n²))
var toRemove = reservation.Visitors
    .Where(visitor => !keepVisitorIds.Contains(visitor.VisitorId))
    .ToList();
```

**Bedune in pattern** (bad code):
```csharp
// ❌ O(n²) — har visitor ra to hame-ye existing search kon
foreach (var v in incoming)
    var existing = reservation.Visitors.FirstOrDefault(x => x.VisitorId == v.Id);
```

### ManualAccessPopup — GroupBy → Dictionary → O(1) join

```csharp
// File: ACLServer/Infrastructure/Services/ManualAccessPopupService.cs

var logByEvent = logs.GroupBy(x => x.EventId)
    .ToDictionary(g => g.Key, g => g.First());

var groupByVehicle = groupNames
    .GroupBy(x => (x.VehicleId, x.SiteId))
    .ToDictionary(g => g.Key, g => g.First().Name);

// O(1) per row — mesle SQL JOIN dar memory
logByEvent.TryGetValue(row.EventId, out var log);
groupByVehicle.TryGetValue((row.VehicleId, row.SiteId), out var groupName);
```

### ToLookup — one-to-many index

```csharp
// File: IdentityServer/Infrastructure/Services/ClaimService.cs

var childrenByParent = children.ToLookup(child => child.ParentId);

// O(1) per parent — hame-ye children-e ye claim
foreach (var child in childrenByParent[excludedClaim.ClaimId])
    excluded.Add((child.Id, excludedClaim.SiteId));
```

`ToLookup` mesle `GroupBy().ToDictionary()` vali yek method call. Return type: `ILookup<K, V>`. Missing key → empty collection (na exception).

### ConcurrentDictionary — thread-safe tracker

```csharp
// File: ACLServer/Infrastructure/Services/PlateReaderAgentConnectionTracker.cs

private readonly ConcurrentDictionary<Guid, string> _connections = new();

public void SetOnline(Guid agentId, string connectionId) =>
    _connections[agentId] = connectionId;

public bool IsOnline(Guid agentId) => _connections.ContainsKey(agentId);

public bool HasOnlineAgent(IEnumerable<Guid> agentIds) =>
    agentIds.Any(IsOnline);  // O(k) where k = count of agentIds
```

Web server concurrent-e → `Dictionary<>` thread-safe **nist**. `ConcurrentDictionary` lock per bucket, na global lock.

### Dedup ba HashSet.Add

```csharp
// File: Vehicles.Application/BulkImport/PreviewBulkImportVehiclesCommandHandler.cs

var seenPlates = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
foreach (var row in rowsResult.Value)
{
    var alreadySeenInFile = !seenPlates.Add(plateValue);
    // Add() returns false if already exists → O(1) dedup check
}
```

Pattern: `HashSet.Add()` return `false` = duplicate. Yek line baraye dedup. Kheili clean.

---

## Set operations — sync pattern

```csharp
// File: ACLServer/Application/VehicleAccessPolicies/VehiclePolicyCommandSupport.cs

var wanted = wantedKeys.ToHashSet();          // O(m)
foreach (var item in existing.Where(x => !wanted.Contains(keyOf(x))).ToList())
    existing.Remove(item);                     // Remove items not in wanted

var have = existing.Select(keyOf).ToHashSet(); // O(n)
foreach (var key in wantedKeys.Where(k => !have.Contains(k)))
    existing.Add(create(key));                 // Add items not yet present
```

In **set diff** pattern-e: (existing - wanted) = remove, (wanted - existing) = add. O(n + m) total.

Mosahebe: "Chejori do ta list ra sync mikoni?" → in pattern.

---

## Permission lookup — nested hash

```csharp
// File: Common/Authorization/SiteScopedPermissionEvaluator.cs

Dictionary<Guid, HashSet<string>> GroupSiteScopedValues(ClaimsPrincipal user, string claimType)
{
    return user.Claims
        .Where(claim => claim.Type == claimType)
        .Select(claim => claim.Value.Split('|', 2))      // "siteId|permission"
        .GroupBy(parts => Guid.Parse(parts[0]))
        .ToDictionary(
            group => group.Key,
            group => new HashSet<string>(group.Select(parts => parts[1]),
                StringComparer.OrdinalIgnoreCase));
}
```

Natije: `{ siteA: {"read", "write"}, siteB: {"read"} }`. Double O(1) lookup: aval site, bad permission.

---

## Sorting — real examples

### SequenceEqual ba double sort — O(n log n) waste

```csharp
// File: Personnels.Domain/Personnels/Personnel.cs

private static bool SameContractIds(IReadOnlyCollection<Guid>? current, IReadOnlyCollection<Guid> desired) =>
    (current ?? []).OrderBy(x => x).SequenceEqual(desired.OrderBy(x => x));
```

**Tahlil:** Do ta `.OrderBy()` = O(n log n) + O(m log m). Ba'd `SequenceEqual` = O(n).

**Behtar:** `HashSet`-based:
```csharp
new HashSet<Guid>(current).SetEquals(desired);  // O(n + m) — no sort
```

**Smell:** vali n inja kuchik-e (contract count < 10), pas farghi nakone. Vali **pattern** ra bedun.

### Priority-based sort + first match

```csharp
// File: ACLServer/Abstractions/Helpers/VehicleAccessDecisionEvaluator.cs

var active = assignments
    .Where(a => a.DoorId == doorId && a.IsActive ...)
    .OrderBy(a => a.Priority)     // O(n log n)
    .ToList();

var match = active.FirstOrDefault(a => a.ParkingId == suppliedParkingId.Value);
```

Age faghat **yek** lowest-priority lazem bud: `MinBy(a => a.Priority)` → O(n). Vali inja list-e sorted ra iterate mikonan (chand condition), pas sort ok-e.

### Fisher-Yates shuffle — O(n)

```csharp
// File: Personnels.Application/GetPersonnelRandomly/GetPersonnelRandomlyCommandHandler.cs

for (int i = personnelsList.Count - 1; i > 0; i--)
{
    int j = RandomNumberGenerator.GetInt32(i + 1);
    (personnelsList[i], personnelsList[j]) = (personnelsList[j], personnelsList[i]);
}
return personnelsList.Take(1).Cast<object>().ToList();
```

Fisher-Yates: O(n) shuffle ba uniform random. Cryptographic random (`RandomNumberGenerator`).

**Smell:** kole table load mishe baraye **1** random item. Behtar: `ORDER BY random() LIMIT 1` to Postgres → O(n) scan vali na memory load. Ya reservoir sampling.

---

## Tree va BFS — real examples

### BFS: claim tree expansion

```csharp
// File: IdentityServer/Abstractions/Helpers/ApplicationClaimAssignment.cs

var expanded = claimIds.Where(id => id != Guid.Empty).ToHashSet();
var frontier = expanded.ToArray();

while (frontier.Length > 0)
{
    var children = await GetChildrenAsync(context, frontier, ct);
    var added = new List<Guid>();
    foreach (var child in children)
    {
        if (expanded.Add(child.Id))   // HashSet.Add = O(1), dedup
            added.Add(child.Id);
    }
    frontier = added.ToArray();        // next level
}
```

**Tahlil:** In classic BFS-e. `frontier` = queue-e har level. `expanded` = visited set. Hame-ye children-e ye level ra yekja az DB mikhoone (batch query — na yek-yek). O(V + E) over claim graph.

**Mesal:** Admin claim "Visitors" dare → children: "Visitors.Create", "Visitors.Edit", "Visitors.Delete" → expand hame.

### Hierarchical entity — Region tree

```csharp
// File: ACLServer/Domain/Entities/Region.cs

public Guid? ParentId { get; set; }
public virtual Region? Parent { get; set; }
public virtual ICollection<Region> SubRegions { get; set; } = [];
```

Self-referencing FK. EF lazy/eager load. Tree traversal → recursive CTE to Postgres ya application-level BFS.

### Country → Province → City — 3-level tree

```csharp
// File: Personnels.Application/Countries/GetLocationTree/GetLocationTreeQueryHandler.cs

var locationTree = query.Select(m => new {
    m.Id, m.Name,
    Provinces = m.Provinces.Select(x => new {
        x.Id,
        Cities = x.Cities.Select(y => new { y.Id, y.Name })
    })
}).ToList();
```

EF in ra be 1-2 SQL query translate mikone (Included navigation). Na N+1.

### Frontend: recursive tree build + flatten

```javascript
// File: dejban_frontend_new/apps/dejban/src/sections/component-guard/view/component-guard-tree-utils.js

export function buildTreeFromPaths(pathsTree, parentKey = '') {
  const nodes = [];
  for (const [key, value] of Object.entries(pathsTree)) {
    if (hasChildKeys(value)) {
      const children = buildTreeFromPaths(value, `${parentKey}.${key}`);
      nodes.push({ id: `${parentKey}.${key}`, children, leafCount: countLeaves(children) });
    }
  }
  return nodes;
}

export function flattenTree(nodes) {
  return nodes.reduce((acc, n) => {
    if (n.isLeaf) acc.push(n);
    if (n.children) acc.push(...flattenTree(n.children));
    return acc;
  }, []);
}

export function countLeaves(nodes) {
  return nodes.reduce((sum, n) => sum + (n.isLeaf ? 1 : countLeaves(n.children || [])), 0);
}
```

DFS recursive. O(n) where n = total nodes. Frontend permission guard tree.

---

## Sliding window / Rate limiter

### Fixed window — PlateReaderAgentRateLimiter

```csharp
// File: ACLServer/Infrastructure/Services/PlateReaderAgentRateLimiter.cs

private readonly ConcurrentDictionary<Guid, Window> _windows = new();

public bool IsAllowed(Guid agentId, int limitPerMinute)
{
    var window = _windows.GetOrAdd(agentId, _ => new Window());
    lock (window.Gate)
    {
        if (now - window.StartedAt >= TimeSpan.FromMinutes(1))
        {
            window.StartedAt = now;
            window.Count = 0;       // reset
        }
        if (window.Count >= limitPerMinute) return false;
        window.Count++;
        return true;
    }
}
```

**Algorithm:** Fixed window. O(1) per check. ConcurrentDictionary baraye multi-agent. `lock` per agent.

**Moshkel-e fixed window:** boundary burst. 59th second: 5 request. 61st second: 5 request. 2 second ke 10 request okhor → limit 6 bud!

### Sliding window — Gateway ASP.NET

```csharp
// File: ApiGateway/Abstractions/Extensions/ServiceCollectionExtensions.cs

RateLimitPartition.GetSlidingWindowLimiter(clientIp,
    _ => new SlidingWindowRateLimiterOptions
    {
        PermitLimit = 6,
        Window = TimeSpan.FromSeconds(30),
        SegmentsPerWindow = 6,    // 6 segment × 5 sec
        QueueLimit = 0
    });
```

**Algorithm:** 30-second window split be 6 segment (har 5 sec). Window slide mikone — na reset. Boundary burst fix.

### Interview: "Design a rate limiter"

Algorithms:
1. **Fixed window** — sade, boundary problem. (PlateReader)
2. **Sliding window log** — har request timestamp store. Accurate, memory O(requests).
3. **Sliding window counter** — approximation: current × weight + previous × (1-weight). O(1).
4. **Token bucket** — token add mishe ba rate, request 1 token masraf mikone. Burst-friendly.
5. **Leaky bucket** — request be queue, process ba fixed rate. Smooth output.

---

## Pagination — OFFSET problem

### Dejban: OFFSET/LIMIT everywhere

```csharp
// File: Common/Abstractions/Queries/PagedList.cs

public static async Task<PagedList<T>> CreateAsync(IQueryable<T> query, int? page, int? pageSize)
{
    var totalCount = query.Count();          // O(n) — full scan!
    var items = query
        .Skip((defaultPage - 1) * defaultPageSize)  // OFFSET
        .Take(defaultPageSize)                        // LIMIT
        .ToList();
}
```

**Tahlil:** `OFFSET 100000 LIMIT 10` → Postgres 100,010 row scan mikone va 100,000 ta ra dor mirize. Page 10,000 → **kond**.

**COUNT(\*)** ham O(n) to Postgres (MVCC — har row bayad check beshe ke visible-e).

### Keyset pagination (Dejban **nadare**, vali bayad beduni)

```sql
-- bad: OFFSET
SELECT * FROM visitors ORDER BY id OFFSET 100000 LIMIT 10;

-- good: keyset
SELECT * FROM visitors WHERE id > @lastId ORDER BY id LIMIT 10;
```

Keyset: O(log n + 10) ba index. Vali "jump to page 50" mushkel-e — sequential only.

### Frontend: infinite scroll

```javascript
// File: dejban_frontend_new/apps/dejban/src/hooks/infinite-list/use-infinite-list.js

return useInfiniteQuery({
    queryFn: ({ pageParam }) =>
        fetchFn({ page: pageParam, pageSize, ...fetchParams }),
    initialPageParam: 1,
    getNextPageParam: (lastPage, pages) => {
        if (lastPage.items.length < pageSize) return undefined;
        return pages.length + 1;
    },
});
```

Page-based → OFFSET. Baraye dataset-e kuchik ok-e. Baraye million-row → keyset + cursor.

---

## String algorithms — real examples

### JSON stream split — brace-depth counter

```csharp
// File: GateServer/Infrastructure/Services/BoardCommand/GateCommand.cs

var individualJsonStrings = new List<string>();
int depth = 0, start = -1;
for (int i = 0; i < completeRaw.Length; i++)
{
    char c = completeRaw[i];
    if (c == '{') { if (depth == 0) start = i; depth++; }
    else if (c == '}')
    {
        depth--;
        if (depth == 0 && start != -1)
            individualJsonStrings.Add(completeRaw.Substring(start, i - start + 1));
    }
}
```

**Tahlil:** Single-pass O(n). Stack-like logic bedune `Stack<T>` — depth counter kafi-e chon faghat `{}` bayad track beshe. Mesle "valid parentheses" interview question!

### Iranian national code checksum — O(1)

```javascript
// File: dejban_frontend_new/apps/dejban/src/utils/iranian-identity.js

export const isValidIranianNationalCode = (value) => {
  const code = toDigitString(value);
  if (!/^\d{10}$/.test(code)) return false;
  if (/^(\d)\1{9}$/.test(code)) return false;  // all same digits

  let sum = 0;
  for (let i = 0; i < 9; i += 1)
    sum += Number(code[i]) * (10 - i);

  const remainder = sum % 11;
  const checkDigit = Number(code[9]);
  return remainder < 2 ? checkDigit === remainder : checkDigit === 11 - remainder;
};
```

Checksum algorithm: weighted sum mod 11. Mesle ISBN, Luhn (credit card). Fixed 10 digits → O(1).

### Prefix-trimming path lookup

```csharp
// File: IdentityServer/Infrastructure/Services/IdentityServerEndpointPermissionMap.cs

var current = actionPath;
while (true) {
    if (ActionPathToPermission.TryGetValue(current, out permissionValue!))
        return true;
    var slash = current.LastIndexOf('/');
    if (slash <= 0) return false;
    current = current[..slash];   // trim last segment
}
```

**Tahlil:** Longest-prefix match. O(d × 1) where d = depth of path. Dictionary lookup O(1) per level. Alternative: Trie → O(path length).

### Regex validation

```csharp
// File: IdentityServer/Application/Auth/Commands/Login/LoginCommandValidator.cs

RuleFor(x => x.UserName).Matches(@"^09[0-9]{2}-?[0-9]{3}-?[0-9]{4}$");

[GeneratedRegex(@"^09[0-9]{2}")]
private static partial Regex StartsWithMobileNumbers();
```

`GeneratedRegex` (.NET 7+): compile-time source-generated regex → faster than runtime compile. O(n) matching.

---

## Channel<T> — async producer/consumer queue

```csharp
// File: ZKGrpcServer/SDK/Contracts/ZKContracts.cs

private readonly Channel<Func<CZKEM, Task>> _channel;

public TerminalDTO()
{
    _channel = Channel.CreateUnbounded<Func<CZKEM, Task>>(new UnboundedChannelOptions {
        SingleReader = true,
        SingleWriter = false
    });
}
```

**Tahlil:** Device command serialization. Chand ta thread command mifrestan (writer), yek thread execute mikone (reader). O(1) enqueue/dequeue. `SingleReader = true` → optimize baraye ye reader (kam lock).

Mesle `BlockingCollection<T>` vali async-native. Day 04 bishotar tozih dade shod.

---

## Frontend: O(n²) trap

```javascript
// File: dejban_frontend_new/apps/dejban/src/sections/vehicle-access-policy/vehicle-policy-utils.js

const parkingNodes = (parkings || []).map((parking) => {
    const parkingDoors = (parking.doors || []).map((door) => {
        const fromAll = allDoors.find((item) => item.id === id);  // O(n) per door!
        // ...
    }).filter(Boolean);
});
```

**Tahlil:** `.find()` dakhel-e `.map()` = O(parkings × doors × allDoors). Age allDoors 100 ta bashe va 50 parking har kodum 10 door → 50,000 comparison. Ok baraye in size, vali scale nemikone.

**Fix:**
```javascript
const doorMap = new Map(allDoors.map(d => [d.id, d]));  // O(n) build
// ...
const fromAll = doorMap.get(id);  // O(1) lookup
```

### LRU tab eviction — O(n) scan

```javascript
// File: dejban_frontend_new/apps/dejban/src/workspace-tabs/workspace-tabs-store.js

const oldest = evictable.reduce((current, item) =>
    (item.lastActivatedAt || 0) <= (current.lastActivatedAt || 0) ? item : current
);
```

Min-find ba `reduce`: O(n). Baraye < 20 tab ok-e. Real LRU: `Map` (insertion order) ya doubly-linked list + HashMap → O(1).

---

## Workflow — linear step chain (na DAG)

```csharp
// File: RequestTracker/Application/Services/RequestTypeStepWorkflowHelper.cs

public static RequestTypeStep? GetNextStep(
    IReadOnlyList<RequestTypeStep> orderedSteps, RequestTypeStep currentStep)
{
    var currentIndex = orderedSteps.ToList().FindIndex(s => s.Id == currentStep.Id);
    if (currentIndex < 0)
        currentIndex = orderedSteps.ToList().FindIndex(s => s.StepNumber == currentStep.StepNumber);

    return orderedSteps[currentIndex + 1];
}

public static decimal CalculateProgress(
    IReadOnlyList<RequestTypeStep> orderedSteps, RequestTypeStep completedStep)
{
    return Math.Min(100, 100m * (completedIndex + 1) / orderedSteps.Count);
}
```

**Tahlil:** Linear pipeline, na graph. `FindIndex` = O(n). `ToList()` har bar copy mikone → 2 copy + 2 scan. Behtar: yek loop, ya `IndexOf` ba custom equality.

**Smell:** `.ToList().FindIndex()` do bar seda zade mishe — 2 unnecessary allocation.

---

## Memoization — cache dictionary

```csharp
// File: Vehicles.Application/BulkImport/CommitBulkImportVehiclesCommandHandler.cs

var siteNameCache = new Dictionary<Guid, string?>();
```

Bulk import: har row site name lazem. Aval cache check, miss → DB query → cache set. Classic memoization. O(1) per subsequent lookup.

---

## Static dispatch map — O(1) filter/sort selection

```csharp
// File: Visitors.Application/Visitors/GetVisits/GetVisitsQueryHandler.cs

private readonly Dictionary<string, Expression<Func<VisitorVisitSchedule, object>>> _filterMap = new()
{
    ["id"] = visit => visit.Id,
    ["visitorid"] = visit => visit.VisitorId,
    ["visitcode"] = visit => visit.VisitCode,
};
```

Client string "visitorid" → O(1) dictionary lookup → Expression. Na if/else chain. Na switch. Open/Closed principle (Day 05) + O(1).

---

## Chi **nadari** ke bayad beduni

| pattern | status to Dejban |
|---|---|
| Binary search | nist — hash lookup estefade mishe |
| Keyset pagination | nist — faghat OFFSET/LIMIT |
| Trie | nist — longest-prefix ba dictionary loop |
| Graph (DAG) | nist — workflow linear-e |
| `.Chunk()` | nist — manual batch |
| `Queue<T>` / `Stack<T>` | nist — `Channel<T>` va depth counter |
| Custom `IComparer<T>` | nist — `.OrderBy(lambda)` |
| Bloom filter | nist |
| Consistent hashing | nist |

---

## 20 soal-e mosahebe

1. **Big-O-ye `.Where().OrderBy().FirstOrDefault()` chie?** — O(n) filter + O(n log n) sort + O(1) pick = O(n log n). Behtar: `.MinBy()` → O(n)
2. **Dictionary vs List baraye lookup?** — Dictionary O(1), List O(n). Trade-off: memory
3. **HashSet.Add() chi return mikone?** — true age add shod, false age duplicate bud. O(1) dedup
4. **`.ToList()` chejori memory masraf mikone?** — copy-e kole collection → O(n) space
5. **BFS vs DFS?** — BFS shortest path (unweighted), DFS path existence / cycle. Both O(V+E)
6. **Sliding window chie?** — sub-array/window move ro data. Rate limiter, max subarray
7. **OFFSET pagination chera bad-e?** — O(offset) scan. Page 10K → 10K row skip
8. **Keyset pagination chi?** — `WHERE id > last` + index → O(log n). Na page jump
9. **Fisher-Yates shuffle?** — O(n), in-place, uniform random. Swap i ba random(0..i)
10. **Stable sort chie?** — equal element-ha tartib-e avaliye ra hefz mikonan. Tim sort stable
11. **Race condition to Dictionary chi mishe?** — corrupt internal state, exception. `ConcurrentDictionary` lazem
12. **ToLookup vs GroupBy?** — ToLookup immediate execute + O(1) access. GroupBy lazy
13. **Channel<T> chie?** — async producer/consumer. Bounded/unbounded. Better than `BlockingCollection` for async
14. **find() dakhel-e map() chera bad-e?** — O(n²). Pre-index ba Map/Dictionary
15. **Memoization chie?** — cache-e natije baraye avoid re-compute. Dictionary key → result
16. **Set diff chejori compute mikoni?** — `HashSet` + `Contains` → O(n+m). Na nested loop
17. **Trie baraye chi?** — prefix search, autocomplete. O(L) per word where L = length
18. **B-tree index chejori kar mikone?** — balanced tree, sorted. Leaf-ha data/pointer. O(log n) search
19. **Longest-prefix match?** — path segment trim + hash lookup per level. Ya Trie
20. **`COUNT(*)` to Postgres chera O(n)?** — MVCC: har row visibility check. Na stored count

---

## Resume

**short:**

> Applied data structure and algorithm thinking across a microservices platform: hash-based O(1) lookups for permission evaluation, BFS for claim-tree expansion, sliding-window rate limiters, set-diff collection sync, and async Channel queues for device command serialization.

**bullets:**

- Replaced O(n²) nested lookups with Dictionary/HashSet indexing for visitor graph sync and permission evaluation
- Implemented BFS claim-tree expansion with batch DB queries and HashSet-based dedup
- Built fixed-window and sliding-window rate limiters for plate-reader agents and API gateway
- Applied Fisher-Yates shuffle, checksum validation, and brace-depth JSON splitting algorithms

**skills:** `Data Structures, Algorithm Design, Big-O Analysis, Hash Tables, BFS/DFS, Sliding Window, Rate Limiting, LINQ Optimization, Pagination Strategies`

---

## File-haye mohem

| chi | koja |
|---|---|
| Hash index pattern | `Visitors.Application/UpdateVisitReservation/UpdateVisitReservationCommandHandler.cs` |
| GroupBy → Dictionary join | `ACLServer/Infrastructure/Services/ManualAccessPopupService.cs` |
| ToLookup parent→children | `IdentityServer/Infrastructure/Services/ClaimService.cs` |
| ConcurrentDictionary | `ACLServer/Infrastructure/Services/PlateReaderAgentConnectionTracker.cs` |
| HashSet dedup | `Vehicles.Application/BulkImport/PreviewBulkImportVehiclesCommandHandler.cs` |
| Set sync | `ACLServer/Application/VehicleAccessPolicies/VehiclePolicyCommandSupport.cs` |
| Permission hash | `Common/Authorization/SiteScopedPermissionEvaluator.cs` |
| Sort + SequenceEqual | `Personnels.Domain/Personnels/Personnel.cs` |
| Priority sort | `ACLServer/Abstractions/Helpers/VehicleAccessDecisionEvaluator.cs` |
| Fisher-Yates | `Personnels.Application/GetPersonnelRandomly/GetPersonnelRandomlyCommandHandler.cs` |
| BFS claim tree | `IdentityServer/Abstractions/Helpers/ApplicationClaimAssignment.cs` |
| Region tree entity | `ACLServer/Domain/Entities/Region.cs` |
| Frontend tree build | `dejban_frontend_new/.../component-guard-tree-utils.js` |
| Fixed window limiter | `ACLServer/Infrastructure/Services/PlateReaderAgentRateLimiter.cs` |
| Sliding window gateway | `ApiGateway/Abstractions/Extensions/ServiceCollectionExtensions.cs` |
| OFFSET pagination | `Common/Abstractions/Queries/PagedList.cs` |
| Infinite scroll | `dejban_frontend_new/.../hooks/infinite-list/use-infinite-list.js` |
| JSON brace split | `GateServer/Infrastructure/Services/BoardCommand/GateCommand.cs` |
| National code checksum | `dejban_frontend_new/.../utils/iranian-identity.js` |
| Prefix-match lookup | `IdentityServer/Infrastructure/Services/IdentityServerEndpointPermissionMap.cs` |
| Channel queue | `ZKGrpcServer/SDK/Contracts/ZKContracts.cs` |
| Static dispatch map | `Visitors.Application/Visitors/GetVisits/GetVisitsQueryHandler.cs` |
| Memoization cache | `Vehicles.Application/BulkImport/CommitBulkImportVehiclesCommandHandler.cs` |
| O(n²) frontend trap | `dejban_frontend_new/.../vehicle-access-policy/vehicle-policy-utils.js` |
| LRU tab eviction | `dejban_frontend_new/.../workspace-tabs/workspace-tabs-store.js` |
| Workflow linear chain | `RequestTracker/Application/Services/RequestTypeStepWorkflowHelper.cs` |

---

Day 59 tamum. In akharin fasl-e mosahebe-st. Fehrest: [README.md](./README.md).

---

*Day 59 tamum. Ba'd: Day 60 — Mapster (amade). Fehrest: [README.md](./README.md).*