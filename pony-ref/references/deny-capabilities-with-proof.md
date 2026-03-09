Deny Capabilities for Safe, Fast Actors

Abstract

ness [12]). One issue with these systems is that what a reference is allowed to do must be used to reason about what
other references to the same object must be prevented from
doing.
We have taken a different approach and use capabilities
to describe what other aliases are denied by the existence of
a reference. We use a matrix of deny properties [17], with
notions such as isolation, mutability, and immutability all
being derived from these properties. What other references
to the same object can do is explicit rather than implied.
Other approaches have combined actors with data-race
freedom [13, 22, 27]. However, various useful patterns have
not been supported, e.g. traversing and modifying an isolated
data structure, or updating an object and then sending it in a
message while keeping read access to it. By taking a more
fundamental view of capabilities, we were able to develop
a more flexible type system that supports such patterns.
Moreover, we have developed a fast implementation, with
performance comparable or superior to the fastest, unsafe
systems.
The matrix of deny properties exposes two novel capability types, tag and trn (transition). A tag capability allows
identity comparison and asynchronous method call, but does
not allow reading from or writing to the reference. We type
actors as tag, which allows them to be integrated into the object type system and passed in messages. A trn capability is
a new form of uniqueness, write uniqueness, that describes
objects that can only be written to through a single reference,
but can be read from through many references.
We also extend viewpoint adaptation [16, 19] to apply to
every capability and introduce the concept of safe to write,
which, taken together, allow reading from and writing to
both unique objects and unique fields. We treat the types
of temporary identifiers differently from those of permanent
paths, which allows us to traverse unique structures, something that is not possible using other approaches [13, 19, 22].
In our system, an alias of a reference may have a different
capability from the initial reference. This addresses a key
issue in capability systems, namely that sub-typing is not
reflexive: an isolated type cannot be assigned to a field or
local variable unless the source reference is eliminated with
a technique such as destructive read or alias burying [8]. As
a part of this, we introduce unaliased types, which provide
static alias tracking without alias analysis.

Combining the actor-model with shared memory for performance is efficient but can introduce data-races. Existing
approaches to static data-race freedom are based on uniqueness and immutability, but lack flexibility and high performance implementations. Our approach, based on deny properties, allows reading, writing and traversing unique references, introduces a new form of write uniqueness, and guarantees atomic behaviours.

1.

Introduction

A current trend in programming languages is to combine
the actor-model [3] of concurrency with shared memory
to eliminate the requirement to copy all messages between
actors [4]. This is done to improve performance, but it results
in the possibility of data races.
Historically, programming languages have mostly relied
on dynamic approaches to prevent data races, using explicit mechanisms, such as mutexes or semaphores, or implicit
mechanisms, such as lock inference or lock-free algorithms.
Ensuring data-race freedom statically [18] improves performance by doing at compile-time what must otherwise be
done at run-time, and eliminates errors that can result from
incorrectly implementing locking or lock-free algorithms.
We wish to provide a type system that ensures data race
freedom statically for an actor-model language while also
providing a way to type actors themselves, in the mould of
active objects [13], and without placing any restrictions on
the structure of messages. In addition, the type system must
be amenable to a highly efficient implementation.
Existing approaches to static data race freedom use capabilities [24] to describe what a reference is allowed to do. In
previous work, capabilities have been expressed as permissions [10], fractional permissions [9], uniqueness [12], immutability [26], and isolation [19] (a refinement of separate
uniqueness [22], which is a refinement of external unique-

[Copyright notice will appear here once ’preprint’ option is removed.]

1

2015/3/25

Our capabilities also provide a static region system
[21], requiring no additional annotation. The trn capability provides a new form of write region, in which a region
boundary applies to write operations but not read operations.
In addition, actor behaviours are guaranteed to be atomic.

or write to the object. A reference that denies only global
write aliases is only safe to read, i.e. immutable, since it
guarantees no other actor will write to the object, but does
not guarantee no other actor will read from it. A reference
that allows all global aliases is not safe to either read or
write, i.e. it is opaque.
In addition, when the local deny properties and the global
deny properties of a reference are the same, the reference can
be safely sent as an argument to an asynchronous method
call to another actor, i.e. it is sendable. In other words, when
the local alias deny properties are the same as the global
alias deny properties, it does not matter which actor holds
the reference.

Contributions In this work, we present:
• Deny properties as a fundamental basis for uniqueness

and immutability.
• Combination with the actor paradigm.
• A new form of write uniqueness, trn.
• A capability, tag, that can be used to type actors.
• Viewpoint adaptation and safe-to-write semantics for

Short examples A ref reference to an object denies global
read/write aliases. As a result, it is safe to mutate the object,
since no other actor can read from it. This is effectively a
traditional object-oriented reference type.
If an actor has a box reference to an object, no other
reference can be used by other actors to write to that object.
This means that other actors may be able to read the object
and other references in the same actor may be able to write
to it (although not both: if the actor can write to the object,
other actors cannot read from it). Using box for immutability
allows a program to enforce read-only behaviour, similar to
const in C/C++. For example:

reading and writing unique types.
• Temporary identifiers to safely traverse unique structures.
• An alias operation in the type system to express non-

reflexive sub-typing.
• Unaliased types for static alias tracking.
• Static regions, including a new form of write region.
• A formal system.

Moreover, a native code compiler, runtime, and standard library exist, which we use to demonstrate efficiency through a
comparison to existing actor-model languages and libraries,
as well as to MPI [20].

class List
fun box size1(): Int => ...
fun val size2(): Int => ...

Outline We present our ideas in terms of a minimal actormodel, object-oriented language. We present capabilities as
deny properties in sec. 2, a formal analysis of data race free
heaps in sec. 3, a formal type system in sec. 4, a syntax
in sec. 5, an operational semantics in sec. 6, a soundness
proof in sec. 7, related work in sec. 8, an implementation
and benchmarks in sec. 9, and conclusions and further work
in sec. 10.

2.

Note that the receiver capability is specified after the
keyword fun. In size1, by indicating that the receiver has
box capability, we can be certain that this will not be
mutated when calculating its size (provided it has no mutable
reference to itself). In addition, immutability is transitive,
so no readable fields of this will be mutated either. Since
box denies global write aliases but does not deny local write
aliases, it is possible for this to be mutated through some
other reference if that reference is held by the same actor.
The box reference functions as a black box: the underlying
object may be mutable through another reference or it may
be immutable through any reference.
In size2, by indicating that the receiver has val capability, we make a stronger guarantee: we deny both local and
global write aliases. As a result, it is not possible for this
(and all its readable fields) to be mutated, regardless of other
aliases, nor will it be mutated at any time in the future.
Since a val reference has the same local and global deny
properties, it is possible to send a val reference to another
actor. A val reference is effectively a value type, similar to
values in functional languages.

Capabilities as deny properties

Rather than indicate which operations are allowed on a reference, our capabilities indicate what operations are denied on
other references to the same object. We distinguish what is
denied to the actor that holds a reference (local aliases) from
what is denied to all other actors (global aliases). Each capability stands for a pair of local and global deny properties.
These are shown in table 1. For example, ref denies global
aliases that can read from or write to the object, but it allows
local aliases to both read from and write to it.
No capability can deny local aliases that it allows globally. Therefore, some cells in the matrix are empty. For example, there is no capability that denies local read and write
aliases, but denies only write aliases globally.
These deny properties are used to derive the operations
permitted on a reference. A reference that denies global
read and write aliases is safe to both read and write, i.e. is
mutable, since it guarantees that no other actor can read from

actor Dataflow
be calculate1(list: List val) => ...
be calculate2(list: List box) // Not allowed

We use the keyword actor to indicate a class that can
have behaviours (asynchronous methods), and we use the
2

2015/3/25

Deny global read/write aliases

Deny global write aliases

Allow all global aliases

Deny local read/write aliases

Isolated (iso)

Deny local write aliases

Transition (trn)

Allow all local aliases

Reference (ref)

Box (box)

Tag (tag)

(Mutable)

(Immutable)

(Opaque)

Value (val)

Table 1. Capability matrix. Capabilities in italics are sendable.
keyword be to define behaviours. A behaviour is executed
asynchronously by the receiving actor, and a given actor
executes only one behaviour at a time, making behaviours
atomic. While executing a behaviour, the receiver sees itself
(i.e. this in the behaviour) as ref, and is able to freely read
from and write to its own fields. However, at the call-site, a
behaviour does not read from or write to the receiver, and so
a behaviour can be called on a tag receiver.
In calculate1, the list parameter is guaranteed to
have no local or global write aliases. As a result, it is safe
to share this object amongst actors. Denying global write
aliases means no actor can write to the object, regardless of
how many actors have a reference to list, making concurrent reads safe without copying, locks, or any other runtime
safety mechanism. In calculate2, a parameter of type
List box is rejected by the type system, as a box does not
deny local write aliases, making it unsafe to send a box to
another actor as the sending actor could retain a mutable
reference.
A tag reference has no deny properties, but it can be
used for asynchronous method calls, i.e. calling behaviours.
A capability with no permissions has appeared in previous
work [25], but without allowing asynchronous method calls.

Here, by passing an iso reference, a Dataflow actor
can mutate the list before sending it to the flow actor.
In order to do this, we must be certain the sending actor
does not retain a read or write alias. To this end we use
an aliasing type system wherein a newly created alias to
an object cannot violate the deny properties of the reference
being aliased. For example, a newly created alias of an iso
reference must be neither readable nor writeable (i.e. a tag).
To move deny properties, we use a destructive read.
actor Dataflow
be step(list: List iso, flow: Dataflow tag) =>
next.step(list) // Not allowed
next.step(list = null)

An assignment expression returns the previous value of
the left-hand side of an assignment rather than the value
of the right-hand side, making assignment equivalent to a
destructive read. Our type system introduces the concept of
unaliased types, annotated with ◦, in order to type values for
which an alias has been removed. Here, the destructive read
produces a List iso◦ which is aliased as a List iso when
the behaviour is called. The non-destructive read produces a
List iso which is aliased as a List tag, which is rejected
by the type system.
We distinguish between references which outlive the execution of an expression, and temporary identifiers which do
not. The use of temporary identifiers, combined with viewpoint adaptation, allows reading from and writing to isolated
objects and isolated fields. Earlier work on isolation and external uniqueness systems [12, 19, 22] does not provide this.

actor Dataflow
be step(list: List val, flow: Dataflow tag) => ...

Here, we can call behaviours on flow, but we cannot read
or write the fields of flow. However, when flow executes
those behaviours asynchronously, it will see itself as a ref,
allowing it to mutate its own state. As such, tag allows us
to type actors themselves, thus integrating them into our
type system and allowing threads (in the form of actors)
to be treated as first-class values. In contrast to existing
systems [19], we formalise both dynamic thread creation
(actor constructors) and communicating actor graphs of any
shape (including cycles).
In order to pass mutable data between actors, we use iso
references. All mutable capabilities deny global read/write
aliases, allowing them to be written to because no other actor
can read from the object. An iso reference also denies local
read/write aliases, which means if the iso reference is sent
to another actor, we are guaranteed that the sending actor
no longer holds either read or write references to the object
sent.

actor Dataflow
be step(list1: List iso, list2: List iso,
next: Dataflow tag) =>
list1.next = (list2 = null)
next.step(list1 = null)

Here, we mutate list1 by assigning list2 to its next
field, maintaining isolation for both list1 and list1.next.
Similarly, we could read from or write to fields of list1.next,
since path traversal is allowed. This also allows calling methods on isolated references and fields of any path depth. Unsafe reads are prevented by viewpoint adaptation, and unsafe
writes are prevented by safe-to-write rules. For example:
actor Dataflow
fun ref append(list1: List iso,
list2: List ref) =>
list1.next = list2 // Not allowed

Even if list1.next had the type List ref, this assignment is rejected. As a result, isolated references form static
regions, wherein mutable references reachable by the iso

actor Dataflow
be step(list: List iso, flow: Dataflow tag) => ...

3

2015/3/25

reference can only be reached via the iso reference and immutable references reachable by the iso reference are either
globally immutable or can only be reached via the iso reference.
A trn reference makes a novel guarantee: write uniqueness without read uniqueness. By denying global read/write
aliases, but only denying local write aliases, it allows an object to be written to only via the trn reference, but read from
via other aliases held by the same actor. This allows the object to be mutable while still allowing it to transition to an
immutable capability in the future, in order to share it with
another actor.

κ ∼ κ0
κ

κ0
iso

trn

ref

val

box

`, g

iso
`

`, g

`

`, g

`, g

`, g

`, g

trn
`

ref
val
box
tag

tag

`, g

`

`

`, g

`, g

`, g

`, g

`, g

`, g

`, g

`, g

Table 2. Compatible capabilities.

class BookingManager
var accountant: Accountant
var all: Map[Date, Booking box]
var future: Map[Date, Booking trn]
fun ref close(date: Date) =>
accountant.account(future.remove(date))
actor Accountant
be account(booking: Booking val) => ...

Here1 we use a trn reference to model bookings that
remain mutable until they are closed and sent for accounting. All bookings are in the all map, but only mappings
that have not been closed out and are still mutable are
in the future map. When a booking is closed, it is removed from the future map, returning a Booking trn◦,
which is aliased as a Booking trn, which is a subtype of
Booking val and can be shared with the Accountant actor.
Without a write unique type, this would require copying the
Booking.
A trn reference also forms a static region, but with a
looser guarantee than an iso reference. Mutable references
reachable by the trn reference can only be reached via the
trn reference, but immutable references, whether global or
local, are not contained in the resulting write region.

3.

Figure 1. A representation of part of a heap.

and ϕ2 (t2 ) = ι18 . The objects are in rounded boxes, and the
annotated arrows indicate the contents of their fields, e.g.
χ0 (ι14 , f10) = ι19 . The annotations next to the field identifiers (ref, val, etc.) give types to the variables. Note that
α1 = ι10 and α2 = ι14 .
For consistent heap visibility we require that different
paths originating from the same actor and pointing to the
same object have locally consistent visibility, while paths
originating from different actors and pointing to the same
object have globally consistent visibility. For example, in fig.
1 the path this.f1.f5.f8 starting at the first frame of actor
α1 and the path this.f10 at the first frame of actor α2 are
aliases, as they both reach object ι19 . The first path sees ι19
as tag, while the second sees it as val. These are globally
compatible capabilities, and therefore these paths preserve
consistent heap visibility. On the other hand, if we added
a ref field to ι15 , such that it pointed to ι19 , the resulting
capabilities would not be globally compatible.
For the formal definition of consistent heap visibility, we
need notions of:

Consistent heap visibility

The core of the soundness of our approach is consistent
heap visibility, which requires that aliasing in the heap must
satisfy all the deny properties specified by the capabilities
attached to fields and variables. This leads to the notions
of local and global compatibility. Namely, two capabilities
are locally compatible κ ∼` κ0 if neither has a local deny
property that prevents the existence of the other. Similarly,
they are globally compatible, κ ∼g κ0 , if neither has a
global deny property that prevents the existence of the other.
These relationships are defined in table 2, eg. ref ∼` ref
but ref 6∼g ref. Both relations are symmetric.
In fig. 1, we show a diagrammatic representation of a
heap χ0 which contains actors α1 and α2 , and objects
ι10 ...ι19 . The top rectangles indicate stack frames, for example χ0 (α1 ) = (_, _, α1 · ϕ1 · ϕ2 , _) and ϕ1 (this) = ι10
1 In this example, we are using generic types and default capabilities (ref

for objects and tag for actors). While the full language supports these, we
will not formalise them here.

4

2015/3/25

Γ
∆
p

∈
∈
∈

Env
GlobalEnv
Path

=
=
=

WFV (∆, χ) iff
∀α, α0 , ι, ι0 ∈ χ.∀κ, κ0 , p, p0 , t where Stable(∆, α, p) and
Stable(∆, α, p0 )

LocalID → ExtType
(ActorAddr × Integer ) → Env
(Integer × LocalID) · FieldID

1. If ∆, χ, α ` ι : κ and ∆, χ, α0 ` ι : κ0 and α 6= α0 then
κ ∼g κ0

Figure 2. Global environments and paths.

2. If ∆, χ, α ` ι : κ, p and ∆, χ, α ` ι : κ0 , p0 then
(a) χ, α ` p ∼ p0 or

• ∆, χ, ι ` ι : ref, (0, this)

(b) κ ∼` κ0

• ∆, χ, α ` ι : κ, (i, z) iff χ(α, (i · z)) = ι and

3. If ∆, χ, α ` ι : κ and ∆, χ, α ` ι0 : κ0 , p0 and ∆, χ, ι `
ι0 : κ00 and κ ∈ {iso, trn} then

∆(α, i, z) = S κ φ and κ 6= tag
• ∆, χ, ι ` ι0 : κ I κ0 , p · f iff ∆, χ, ι ` ι00 : κ, p and

χ(ι00 , f) = ι0 and F(χ(ι00 ) ↓1 , f) = S κ0 and κ I κ0 6=
tag
0

(a) χ, α ` ι ∈ p0 or
(b) κ00 ∈ {val, box} and κ0 ∼g val or

0

• ∆, χ, ι ` ι : κ iff ∃p such that ∆, χ, ι ` ι : κ, p

(c) κ00 ∈ {iso, trn, ref} and κ ∼` κ0
4. If ∆(α, i, t) = S κ and κ ∈ {iso, trn} and χ(α, i, t) =
χ(α, p1 ) = ι then

Figure 3. Visibility.
 0
κ



val
• κ I κ0 =

box



tag

(a) p1 = (i, t) or

if κ ∈ {iso, trn, ref}
if κ = val ∧ κ0 = val
if κ = box ∧ κ0 ∈
/ {iso, val, tag}
otherwise

(b) ∃ι0 , κ0 , p2 , f such that
i. κ ≤ κ0
ii. κ0 ∈ {iso, trn}

• χ, α ` p1 · f ∼ p2 · f iff χ(α, p1 ) = χ(α, p2 )

iii. p1 = p2 · f

• χ, α ` (i, z) ∼ (i, z)

iv. ∆, χ, α ` ι0 : κ0 , p2

• χ, α ` ι ∈ p iff ∃p0 , f̄ such that p = p0 .f̄ and χ(α, p0 ) = ι

v. ∆, χ, ι0 ` ι : κ, f

• χ(α, (i, z) · f) = χ(ϕi (z), f) where χ(α) ↓4 = α · ϕ

Figure 5. Well-formed visibility.

• χ(α, (−i, xj ) · f) = χ(vj , f) where χ(α) ↓3 = µ and

µi = (_, v)

given in fig. 4. The definition ensures that κ I κ0 = κ0 if κ
is writeable (deep mutability), κ I κ0 = val if either κ or
κ0 is val (deep immutability) and box I κ0 = box unless
κ0 ∈ {iso, val, tag}. For example, iso I ref = ref.
The rules in fig. 3 say that an address sees itself as ref,
an actor sees a stack identifier as the capability provided by
∆, and an address sees another address as a deep viewpoint
adapted capability. Note that, for visibility, tag types are not
seen. Therefore, our example gives us:

• Stable(∆, α, (i, z) · f) iff ∆(α, i, z) ∈
/ {iso, trn} or

z 6= t
Figure 4. Topological properties of paths.
1. Paths p and global environments ∆, which give types
to the local variables and temporaries in each frame or
message, as defined in fig. 2.
2. Path visibility ∆, χ, ι ` ι0 : κ, p, which says that the
object or actor ι sees the object or actor ι0 as capability κ
through path p, as defined in fig. 3.

• ∆0 , χ0 , α1 ` ι10 : ref, (1, this), but also

∆0 , χ0 , α1 ` ι10 : box, (1, this) · f1 · f2.
• ∆0 , χ0 , α2 ` ι19 : val, (1, this) · f10, but also

∆0 , χ0 , α1 ` ι19 : tag, (1, this) · f1 · f5 · f8.

3. Topological properties of paths, as defined in fig. 4.
Environments Γ map variables (i.e. local variables or temporaries) to extended types and global environments, ∆
map actor addresses and integers to environments. In fig.
1, we indicate the types assigned to local variables through
the annotations. Thus, we have an implicit global environment ∆0 , such that ∆0 , χ0 , α1 ` ι10 : ref, (1, this), and
∆0 , χ0 , α2 ` ι19 : val, (1, this) · f10.
To define path visibility, we need the notion of deep viewpoint adaptation κ I κ0 , which combines two capabilities as

In fig. 4, two paths are compatible if they share the last
step or they are the same identifier with no fields, an address
ι is in a path if some prefix of the path points to ι, and a
path is stable, Stable(∆, α, p), if its initial identifier is not a
unique temporary. For example, χ0 , α2 ` (1, this) · f10 ∼
(1, y1) · f10. Also, Stable(∆0 , α1 , (1, this) · f1 · f4) and
¬Stable(∆0 , α1 , (2, t2) · f9), even though the two paths are
aliases.
We define consistent heap visibility in fig. 5. We require:
5

2015/3/25

1. Global compatibility. Any two distinct actors that can
see the same address must see that address with globally
compatible capabilities.

5. The treatment of actors.
Operations which discard aliases Assignment operations
discard aliases, as they return the previous value of the lefthand side (A SN L OCAL and A SN F IELD) after overwriting
it. The fact that an alias has been discarded is important
in the cases where the capability is unique (iso or trn).
We indicate this through the unaliased annotation ◦, which
expresses that there is no stable path to the corresponding
object.
For example, the assignment this.f1.f5 = null in the
first frame of actor α1 in fig. 1 would return a new temporary
which would be the unique reference to ι16 . The type of this
expression would be S iso◦ for some S. Because unaliasing
is of importance only when the underlying capability is iso,
trn or ref, we have defined the unaliasing operation U,
which takes a type and returns an extended type, cf. def. 1.
This operator is used whenever an alias is discarded (cf, TA SN L OCAL, T-A SN F LD).
Object constructors also introduce unaliased values, as
indicated in the rule T-C TOR. Also, null has no stable alias,
and thus is unaliased, cf. T-N ULL.

2. Local compatibility. An actor that sees an address in
multiple ways must either see compatible paths or locally
compatible capabilities.
3. Containment properties of iso and trn. Given α that
sees ι as some unique κ and sees ι0 as κ0 via some stable
p0 , and given that ι sees ι0 as κ00 :
(a) ι0 must be contained by ι, or
(b) neither ι nor α can write to ι0 , or
(c) ι can write to ι0 and α sees ι0 as locally compatible
with κ.
4. Properties of unique temporary identifiers. Given t that
points to ι , some other path p1 to the same ι must be
either:
(a) also t or
(b) that path p1 must have a prefix p2 that sees some ι0
with a unique capability κ0 less precise than κ and ι0
must see ι as κ.

Distinction between introducing stable or temporary aliases Some operations introduce stable aliases (eg. assignment), while others introduce only unstable ones (eg. field
read). We express the distinction in the type system through
the difference between the type judgments Γ ` e : ET and
the aliased type judgment Γ `A e : ET. For example, when
assigning an expression e to a variable x, the right-hand
side is typed in the judgment `A (cf. T-A SN L OCAL). The
aliasing judgement is also applied to the receiver and arguments of method calls and asynchronous behaviours (TS YNC and T-A SYNC), the arguments to object and actor
constructors (T-C TOR and T-ATOR), and the right-hand side
of a field assignment (T-A SN F LD).
The aliased type judgment Γ `A e : ET is defined in
terms of the unaliased type judgment Γ ` e : ET0 , where
ET has to be a super-type of the aliased version of ET0 ,
i.e. A(ET0 ) ≤ ET. The operation A(ET) gives the type
that an alias of ET would have. When aliasing an unaliased
type there is no previous alias to consider, and therefore
A(S κ◦) = S κ. For other types, the result must be the
minimal super-type of the underlying type which is locally
compatible with it, i.e. A(S κ) = S κ0 where κ0 ≤ A(κ0 ) and
A(κ0 ) ∼` κ0 .

An implication of well-formed visibility is that if two variables (temporary or otherwise) are aliases and one of them
has unique type (aliased or unaliased) then 1) they come
from the same actor and 2) they are either the same variable or they have locally compatible capabilities, cf. lemmas
8 and 9 in the appendix. Note that WFV .1 − 3 are concerned with stable paths only, while WFV .4 is about unstable paths. In particular, WFV .4 allows a unique temporary to break the requirements from WFV .3 and alias something writeable from a unique.
The heap from fig. 1 has consistent visibility. The paths
(1, this) · f1 · f5 · f8 from α1 and (1, this) · f10 from α2
satisfy WFV .1 , while (1, x1) · f4 from α1 and (2, this)
from α1 satisfy WFV .2 and WFV .3 . On the other hand,
the temporary (2, t2) is not stable, and therefore not restricted by WFV .2 or WFV .3 , but does adhere to WFV .4 .
Finally, the assignment this.f1.f5.f6 = this.f1.f5.f7
would break WFV .2 , while setting t2 to point to ι15 would
break WFV .4 .

4.

Type system

The type system has the format Γ ` e : ET and is defined in
fig. 6. The following aspects required special attention:

Definition 1. Aliasing and unaliasing.
• A(S κ◦) = S κ

1. The treatment of operations which discard aliases.



S tag iff κ = iso
• A(S κ) = S box iff κ = trn


Sκ
otherwise
(
S κ◦ iff κ ∈ {iso, trn, ref}
• U(S κ) =
S κ otherwise

2. The distinction between operations which introduce
stable aliases vs. those which create only temporary aliases.
3. Capabilities when accessing fields.
4. Capability recovery.
6

2015/3/25

x∈Γ
T-L OCAL
Γ ` x :Γ(x)

Γ ` e : S κ F(S, f) = S0 κ0
T-F LD
Γ ` e.f : S0 κ . κ0

S∈P
T-N ULL
Γ ` null : S iso◦

Γ ` e : ET Γ ` e0 : ET0
T-S EQ
Γ ` e; e0 : ET0

Γ(x) = S κ Γ `A e : S κ
T-A SN L OCAL
Γ ` x = e : U(S κ)

Γ ` e : S κ Γ `A e0 : S0 κ0
F(S, f) = S0 κ00 κ0 ≤ κ00 ` κ / κ0 ∨ ` κ / κ00
T-A SN F LD
Γ ` e.f = e0 : U(S0 κ . κ00 )

M(S, m) = (T, x : T, e, ET)
Γ `A e : T Γ `A ei : Ti
T-S YNC
Γ ` e.m(e) : ET

M(A, b) = (A ref, x : T, e, A tag)
Γ `A e : A tag Γ `A ei : Ti
T-A SYNC
Γ ` e.b(e) : A tag

M(C, k) = (C ref, x : T, e, C ref◦)
Γ `A ei : Ti
T-C TOR
Γ ` C.k(e) : C ref◦

M(A, k) = (A ref, x : T, e, A tag)
Γ `A ei : Ti
T-ATOR
Γ ` A.k(e) : A tag

Γ ` e : ET0 A(ET0 ) ≤ T
T-A LIAS
Γ `A e : T

Γ\{x | ¬Sendable(Γ(x))} ` e : ET
T-R EC
Γ ` recover e :R(ET)

Γ ` e : S κ◦
T-S UBSUME
Γ ` e : Sκ
Figure 6. Expression typing
ET ≤ ET00 ET00 ≤ ET0
ET ≤ ET0

S κ◦ ≤ S κ

κ ≤ κ0
S κ ≤ S κ0

κ . κ0

iso ≤ trn ≤ {ref, val} ≤ box ≤ tag

κ0

κ

iso

trn

ref

val

box

tag

iso

iso

tag

tag

val

tag

tag

Sendable(T) iff T = S κ ∧ κ ∈ {iso, val, tag}

trn

iso

trn

box

val

box

tag

Figure 7. Sub-types and sendable types.

ref

iso

trn

ref

val

box

tag

val

val

val

val

val

val

tag

box

tag

box

box

val

box

tag

tag

⊥

⊥

⊥

⊥

⊥

⊥

Thus, through a combination of aliasing and unaliasing,
we can obtain unique types when needed. For example, for x
and y of type C trn, the assignment x = y is illegal, because
the aliased type of y is C box and C box 6≤ C trn. However,
the assignment x = (y = null) is legal, because the type of
y = null is C trn◦, and the alias of C trn◦ is C trn.

Table 3. Viewpoint adaptation.
κ / κ0

Capabilities at field read When reading a field f from an
object ι we obtain a temporary. The capability of this temporary must be a combination of κ, the capability of the path
leading to ι, and κ0 , the capability with which ι sees the field.
We express this through the operator ., defined in fig. 3. This
operator is less precise than I, i.e. κ I κ0 ≤ κ . κ0 . The new
temporaries introduced must preserve well-formed heap visibility, in particular WFV .4 . These rules forbid temporary
aliases to trn or ref fields of an iso, and therefore we obtain iso . trn = iso . ref = tag. Also, they require that
any aliases to ref fields of a trn are box, including temporary references. Therefore, trn . ref = box.

κ
iso
trn
ref

κ0
iso

trn

ref

√
√

√

√

√

√

val

box

tag

√

√

√

√

√

√

√

val
box
tag

Table 4. Safe to write.

7

2015/3/25

Thus, taking our earlier example, the type of this.f1.f5
is iso, while the type of this.f1.f5.f6 is tag. Compare this with visibility, which gives ∆0 , χ0 α1 ` ι17 :
ref, (1, this) · f1 · f5 · f6.
Storing a reference into a field of an object ι is legal if the
type of the reference is both a subtype of the type of the field
and also safe to write into the origin. The relation κ / κ0 ,
as defined in fig. 4, expresses which reference capabilities
κ0 are safe to write into origin κ. When writing to a field
through an origin, no alias of the object being written may
exist that would violate the deny properties of the origin.
Notice, that these rules allow us to write to fields which
are not readable, i.e. of type tag. For example, the field
read this.f1.f5.f6 has type tag, but the field assignment this.f1.f5.f6 = (x1 = null) is legal even though
the field f6 is ref and ref is not safe to write into iso.
Namely, x1 = null has type iso◦, and aliased type iso,
and iso ≤ ref, and iso is safe to write to iso.

∈
∈
∈
∈
∈
∈
∈
∈
∈
∈
∈
∈
∈

Program
ClassDef
ActorDef
TypeID
Type
ExtT ype
Field
Ctor
Func
Behv
MethodID
Cap
Expr

E[·] ∈

ExprHole

P
CT
AT
S
T
ET
F
K
M
B
n
κ
e

::=
::=
::=
::=
::=
::=
::=
::=
::=
::=
::=
::=
::=
|
|
::=
|
|

CT AT
class C F K M
actor A F K M B
A|C
Sκ
T | S (iso | trn | ref)◦
var f : T
new k(x : T) ⇒ e
fun κ m(x : T) : ET ⇒ e
be b(x : T) ⇒ e
k|m|b
iso | trn | ref | val | box | tag
this | x | x = e | null | e; e
e.f | e.f = e | recover e
e.m(e) | e.b(e) | S.k(e)
x = E[·] | E[·]; e | (E[·]) | E[·].f
e.f = E[·] | E[·].f = z | E[·].n(z)
e.n(z, E[·], e) | recover E[·]

Figure 8. Syntax

Capability recovery The evaluation of an expression which
has access only to sendable variables (i.e. iso, val, and
tag) will return a sendable type. This is an extension of
previous work on recovery [19], which is related to work on
borrowing [22]. We introduce such expressions through the
recover keyword (T-R EC). The return type of recover e
is the sendable version of the return type of e. For example,
if e has type ref, then recover e has type iso, and if e has
type ref◦, then recover e has type iso◦.

C
A
f
this, x
t

∈ ClassID
∈ ActorID
∈ FieldID
∈ SourceID
∈ TempID

k
m
b
n
y, z

∈
∈
∈
∈
∈

CtorID
FuncID
BehvID
CtorID ∪ BehvID
LocalID

Figure 9. Identifiers

Definition 2. Capability
recovery


S iso φ iff κ ∈ {iso, trn, ref}
R(S κ φ) = S val
iff κ ∈ {val, box}


S tag
otherwise

ceiver capability in the behaviour is ref. This is in contrast
to method calls, where the receiver object/actor has to be
seen as a capability which is a subtype of the receiver capability in the method declaration. The looser requirement for
actors is sound, because, as discussed above, no other actor
may obtain access to the actor’s state.

R(ET) is the sendable capability that retains the same
local read and/or write guarantee. In other words, a writeable
capability can become iso and a readable capability can
become val.

Further observations about the type system In contrast to
many type systems, typing is not covariant with the capabilities assigned to variables or fields. That is, Γ ` e : ET and
Γ(x) = S κ and κ0 ≤ κ does not imply that Γ[x 7→ S κ0 ] `
e : ET0 for some type ET0 . For example, take class C with a
field f of type C ref, and Γ such that Γ(x) = C ref and
Γ0 = Γ[x 7→ C trn]. Then x.f = x is type correct in Γ but
not in Γ0 .

The treatment of actors Actors introduce the question of
who may read or update the actor’s fields, the possibility
of synchronous calls on actors, and the type required for
asynchronous calls.
Field read and write requires that the actor should not be
seen as a tag. However, since an actor sees itself as a ref
(by fig. 3), any other actor will see it as tag (by WFV .1 ).
Therefore no other actor except the current one will be allowed to observe an actor’s fields - a nice consequence of
the type system.
By a similar argument, because the actor sees itself as
ref, by WFV .2 , any other paths that point to it will do so as
box, ref, or tag, and this means that the actor may call synchronous methods on itself, provided that the receiver capability of the method declaration is ref or box. Interestingly,
for asynchronous (behaviour) calls, the receiving actor only
needs to be seen as a tag (T-A SYNC), even though the re-

5.

Syntax

In fig. 8 we present the syntax. We support actors in the
mould of active objects, introduced with the keyword actor.
These can have both synchronous methods (functions, introduced through the keyword fun) and asynchronous methods
(behaviours, introduced through the keyword be) as well as
named constructors (introduced through the keyword new).
Passive objects (introduced through the keyword class)
have only synchronous methods (functions) and constructors. We use the term method and identifier n to refer to con8

2015/3/25

χ ∈ Heap
σ ∈ Stack
ϕ ∈ Frame

v
ι
α
ω

∈
∈
∈
∈

LocalID
Value
Addr
ActorAddr
ObjectAddr
Actor

Object
µ ∈ Message

=
=
=
=
=
=

=
=
=

Addr → (Actor ∨ Object)
ActorAddr · Frame
MethodID × (LocalID → Value)
×ExprHole
SourceID ∪ TempID
Addr ∪ {null }
ActorAddr ∪ ObjectAddr

ActorID × (FieldID → Value)
×Message × Stack × Expr
ClassID × (FieldID → Value)
MethodID × Value

Figure 10. Runtime entities
structors, functions, and behaviours. The syntax of expressions is standard with the exception of the recover keyword
- more in sec. 4.
The novel element of the syntax is the inclusion of capability annotations κ on types and functions, where:
κ ∈ {iso, trn, ref, val, box, tag}
These capabilities are the foundation of our type system.
Types consist of a class or actor identifier S followed
by a capability κ. In addition, extended types ET can be
unaliased, ◦. An unaliased type is created with constructors
and destructive reads - more in sec. 4.
The over-bar notation indicates a sequence of elements
such as F, with the convention that the nth element is referred to as Fn . Similarly, x : T indicates a pairwise sequence
of identifiers and types. To reduce notation, we assume a
fixed program P.

6.

Operational semantics

The operational semantics has the shape χ → χ0 , where
χ, χ0 are heaps mapping object addresses ω to their class
identifier and their fields, and actor addresses α to their actor
identifier, their fields, their message queue, their stack, and
the next expression to execute. Runtime entities are defined
in fig. 10. We use some shorthand notation for clarity - more
in app. fig. 17.
We use x to indicate a source identifier, t to indicate a
temporary identifier, and y and z to indicate identifiers which
may be either.
A call stack consists of an actor address α followed by
a sequence of frames ϕ. A frame consists of the method
identifier, a mapping of its parameters to values, and an
expression hole. The latter is the continuation of the caller
and will be executed by the previous frame when the current
activation terminates.
The auxiliary judgement χ, σ, e
χ0 , σ 0 , e0 expresses
local execution within a single actor. M and F return
method and field declarations. They are defined in app. sec.
A.

Local execution is defined in fig. 11. E XPR H OLE allows
execution to propagate to the context. F LD , N ULL, and S EQ
are as expected.
A SN L OCAL and A SN F LD combine assignment with a
destructive read, returning the previous value of the left-hand
side. The resulting value is unaliased: while there may be
other paths pointing to the value in the program, this one
no longer does. In effect, one alias to the value has been
discarded. The existence of unaliased values will be used
in the type system, where T-A SN L OCAL and T-A SN F IELD
both return an unaliased type, as explained in sec. 4.
S YNC and R ETURN describe synchronous method call
and return. In S YNC, method m is called on object or actor ι.
The method parameters x and the method body e are looked
up using the method m and the type S of ι from the heap.
A new frame is pushed on to the stack, consisting of m, the
address of the receiver, the values of the arguments, and the
continuation. In R ETURN, the topmost frame is popped from
the stack and execution continues.
A SYNC and B EHAVE describe asynchronous method
calls and execution. In A SYNC, a message consisting of
the behaviour identifier b and the arguments is appended to
the receiver’s message queue. In B EHAVE, an actor with an
empty call stack and a non-empty message queue removes
the oldest message from the queue, and pushes a new frame
on the stack.
C TOR and ATOR describe the construction of new objects
and actors. In C TOR, a new address ω is allocated on the
heap and the fields are initialised to null. A new frame is
pushed on the stack in the same way as for S YNC. In ATOR,
instead of pushing a new frame on the stack, the new actor’s
queue is initialised with a constructor message containing
the constructor identifier k and the arguments. The first local
execution rule for a new actor will be B EHAVE, which will
execute the body of the constructor k.
R EC is a no-op in the operational semantics, but has an
impact in the type system, where T-R EC affects the capabilities of the result of the expression.
E XCEPT is unusual in that it allows dereferencing null .
We use it here simply to ignore the uninteresting (for our
current purposes) behaviour of null .
G LOBAL defines global execution and says that if an actor
can execute, then its stack and next expression to execute
will be updated.

7.

Soundness

A heap χ is well-formed as defined in fig. 12 if all objects in
the heap are well-formed, all actors in the heap are wellformed, and visibility is well-formed. An object is wellformed if all its fields belong to the type defined in the
object’s class. An actor is well-formed if its stack frames and
messages are well-formed. A stack frame is well-formed if
1) its receiver and arguments are well-formed, 2) all local
identifiers are well-formed, 3) if it is the only stack frame,
9

2015/3/25

χ, σ · ϕ, e
χ, σ · ϕ, E[e]

χ0 , σ · ϕ0 , e0
E XPR H OLE
χ0 , σ · ϕ0 , E[e0 ]

t∈
/ϕ

t∈
/ ϕ ϕ0 = ϕ[t 7→ null ]
N ULL
χ, σ · ϕ, null
χ, σ · ϕ0 , t

ι = ϕ(z) ϕ0 = ϕ[t 7→ χ(ι, f)]
F LD
χ, σ · ϕ, z.f
χ, σ · ϕ0 , t

χ, σ, z; e

χ, σ, e

S EQ

t∈
/ ϕ ϕ = ϕ[x 7→ ϕ(z), t 7→ ϕ(x)]
A SN L OCAL
χ, σ · ϕ, x = z
χ, σ · ϕ0 , t

ι = ϕ(z) ϕ0 = ϕ[t 7→ χ(ι, f)]
χ0 = χ[ϕ(z), f 7→ ϕ(y)]
A SN F LD
χ, σ · ϕ, z.f = y
χ0 , σ · ϕ0 , t

ι = ϕ(z) M(χ(ι) ↓1 , m) = (_, x : _, e, _)
ϕ0 = (m, [this 7→ ι, x 7→ ϕ(y)], E[·])
S YNC
χ, σ · ϕ, E[z.m(y)]
χ, σ · ϕ · ϕ0 , e

t∈
/ ϕ ι = ϕ0 (z)
ϕ0 ↓3 = E[·] ϕ00 = ϕ[t 7→ ι]
R ETURN
χ, σ · ϕ · ϕ0 , z
χ, σ · ϕ00 , E[t]

α = ϕ(z) χ(α) ↓3 = µ
A SYNC
χ, σ · ϕ, z.b(y)
χ[α 7→ µ · (b, ϕ(y)], σ · ϕ, z

A = χ(α) ↓1 (n, v) · µ = χ(α) ↓3
M(A, n) = (_, x : _, e, _)
ϕ = (n, [this 7→ α, x 7→ v], ·)
B EHAVE
χ, α, ε
χ[α 7→ µ], α · ϕ, e

ω 6∈ dom(χ) f = Fs(C)
M(C, k) = (_, x : _, e, _)
χ0 = χ[ω 7→ (C, f 7→ null )]
ϕ0 = (k, [this 7→ ω, x 7→ ϕ(y)], E[·])
C TOR
χ, σ · ϕ, E[C.k(y)]
χ0 , σ · ϕ · ϕ0 , e

α 6∈ dom(χ) f = Fs(A)
t∈
/ ϕ ϕ0 = ϕ[t 7→ α]
0
χ = χ[α 7→ (A, f 7→ null , (k, ϕ(y), α, ε)]
ATOR
χ, σ · ϕ, A.k(y)
χ0 , σ · ϕ0 , t

t∈
/ϕ
0

χ, σ, e
χ, σ, recover e

χ0 , σ 0 , e0
R EC 1
χ0 , σ 0 , recover e0

t∈
/ ϕ ϕ0 = ϕ[t 7→ ϕ(z)]
R EC2
χ, σ, recover z
χ, σ, t

ϕ(z) = null ϕ0 = ϕ[t 7→ null ]
E XCEPT
χ, σ · ϕ, z.f
χ, σ · ϕ0 , t
χ, σ · ϕ, z.f = y
χ, σ · ϕ0 , t
χ, σ · ϕ, z.n(y)
χ, σ · ϕ0 , t

χ, χ(α) ↓4 , χ(α) ↓5 χ0 , σ, e
G LOBAL
χ → χ0 [α 7→ (σ, e)]

t∈
/ϕ

Figure 11. Execution.
Definition 3. Well-formed temporaries. WFT (∆, χ, α, i, e)
iff:

it has no continuation and the receiver is the actor, 4) if it
is not the only stack frame, its return value and temporary
identifiers are well-formed wrt. the previous frame, and 5)
if it is the last frame, temporary identifiers are well-formed
and the expression has the expected type.

1. No temporary appears more than once in e.
2. If T (Γ) 6= ∅, then e ≡ E[e0 ], where e0 is a redex of
the form t.f or t.f = y, and T (Γ) = {t}, where Γ =
∆(α, i) and T (Γ) ≡ {t | Γ(t) = S κ ∧ κ ∈ {iso, trn}}.
3. If e = E[recover e0 ] and ∆, χ, α ` ι : _, (i, t) and
∆, χ, α ` ι : κ0 , (i0 , z) · f where t is free in e0 then either
Sendable(∆(α, i0 , z)) or (i, z) = (i0 , t0 ) and z is not free
in E[·].

Treatment of temporaries Temporaries with unique capabilities, iso or trn, are fragile: on the one hand they may
break the encapsulation of other iso or trn objects. For example, because iso . iso = iso, a field read (F LD) may
return a temporary pointing within the encapsulation of iso.
On the other hand, an assignment to another field or variable
might break their encapsulation.
We require that in a frame, no more than one temporary
has an iso or trn capability, and this temporary appears
on a field assignment or a field read. We also require that
any temporaries that appear within a recover expression are
either inaccessible from any frame or are only accessible
through sendable local variables.

The requirements above do not apply to unaliased unique
capabilities, e.g. iso◦, or trn◦. When proving type preservation, we maintain the property
WFT (∆, χ, α, i, e) by turning the types of temporaries with
unique capabilities κ ∈ {iso, trn} into their aliases, A(κ),
as soon as the temporary is no longer involved in field reads
or updates in the current redex. The type of the expression
is preserved despite this change, because the type rules from
10

2015/3/25

• ∆ ` χ iff ∀ι, α ∈ dom(χ), χ ` ι and ∆, χ ` α and

read otherwise introduces. We will provide a full argument
for atomicity and its importance in reasoning about actormodel programming in future work.

WFV (∆, χ)
• χ ` ι iff ∀f, F(χ(ι) ↓1 , f) = S κ implies χ(ι, f) ↓1 = S
• ∆, χ ` α iff χ(α) = (_, _, µ̄, α · ϕ, e) and ∀i, ∆, χ, α `

8.

ϕi , i and ∀j, ∆, χ ` µj , j

Related Work

Linear types [29] provide the basis for uniqueness type systems. The insight that a type that is usable only once allows
for mutation in a pure functional language leads directly to
using linearity for concurrency-safe mutation [5]. A combination of unique pointers and ownership types [14] is used in
PRFJ [7] to accomplish this.
In [10], a set of capabilities and exclusive capabilities, including identity, is used to build a uniqueness and immutability type system. Several important concepts are articulated
in this work, including the notion that exclusive capabilities
deny the existence of capabilities through other aliases, the
use of destructive reads to manage capabilities, and the existence of the null capability (similar but not identical to tag
in our system).
Fractional permissions [9] encode uniqueness and immutability as well as providing implicit static alias tracking
without alias analysis.
Relaxing the notion of uniqueness to external uniqueness
[12] allows for richer and more complex data structures
to be simply encoded while maintaining all of the useful
properties of linear types. In the same work, the concept of
converting an externally unique reference to an immutable
reference is developed.
Using ownership types to express immutability at the
object and reference level in OIGJ [30], rather than at the
class level, allows immutable references to objects of any
type.
In Kilim [27], tree-structured messages are used to combine work on uniqueness with zero-copy messages between
actors. While this is a significant restriction, the combination
of actor-model concurrency, uniqueness, immutability and
destructive read semantics is powerful. External uniqueness
has also been extended to cover actor-model concurrency
[13], providing a richer type system without tree-structure
requirements. In [28], access permissions are combined with
data flow analysis for implicit concurrency, which is in some
sense the inverse of actor-model concurrency.
In [19], capabilities combined with viewpoint adaptation
and recovery build a powerful data race free type system
with significant usability advantages for the programmer.
In addition, external uniqueness is relaxed even further to
isolation, where immutable portions of an isolated object can
be aliased externally.

• ∆, χ, α ` ϕ, i iff given ϕ = (m, _, E[·]) and M(ϕ, χ) =

(T, x : T, _, ET) and ∆(α, i) = Γ then
1. Γ(this) = T and ∀j ∈ 1..|T|.Γ(xj ) = Tj
2. ∀z ∈ ϕ, Γ(z) = S κ φ and χ(ϕ(z)) ↓1 = S
3. If i = 1 then E[·] = · and ϕ(this) = α
4. If i > 1, given χ(α) ↓4 = α · ϕ and Γ0 = ∆(α, i − 1)
and t ∈
/ Γ0 and Γ00 = Γ0 [t 7→ ET] then
(a) Γ00 ` E[t] : M(ϕi−1 , χ) ↓4
(b) WFT (∆[(α, i) 7→ Γ00 ], χ, α, i, E[t])
5. If i = |χ(α) ↓4 | then WFT (∆, χ, α, i, e) and Γ `
e : ET
• ∆, χ, α ` µ, i iff given µ = (b, v) and vj = ι and

M(χ(α) ↓1 , b) = (_, x : S κ, _, _) and ∆(α, −i) = Γ
then
1. χ(ι) ↓1 = Sj
2. Γ(xj ) = S κ
Figure 12. Well-formed heaps.
fig. 6 require the alias of a type (. . . `A . . .) in all such
situations. This is explained further in lemma 10 in the appendix.
Theorem 1. A well-formed heap ensures data race freedom.
∀∆, χ, α1 , α2 , f, g , if
1. ∆ ` χ, and
2. χ(α1 ) = (_, _, σ1 , _, E1 [z1 .f = z3 ]), and
3. χ(α2 ) = (_, _, σ2 , _, E2 [z2 .g])
then χ(α1 , |σ1 | · z1 ) 6= χ(α2 , |σ2 | · z2 ).
Proof. Follows from the type system and the application of
WFV .1 (global consistency).
Theorem 2. Well-formedness is preserved.
∀∆, χ, if ∆ ` χ and χ → χ0 then ∃∆0 .∆0 ` χ0 .
Proof. Follows from lemmas 17-20 in the appendix.
Atomicity Because the type of any entity does not change,
any readable reference is always readable, and so guarantees
no other actor can write to it. This holds not just for methods,
but for behaviours. As a result, theorem 1 guarantees that
behaviours are atomic, a stronger guarantee than data-race
freedom. In the full language, where null is absent, this is
achieved without the null pointer exceptions that destructive

2 Kilim messages are data-race free but the rest of Java is not.
3 The proposed system is data-race free but the rest of Scala is not.
4 Rust uses atomic reference counts and read-writer locks to prevent data

races.
5 Scala has types that are immutable by design, but cannot annotate references to mutable types as immutable.

11

2015/3/25

Zero-copy

Our Work
√

Gordon
√

Æminium
√

DPJ
√

Kilim
√

Haller
√

√

√

√

√

√2

√3

√

√

√

√

√

√

√

√

√

√

√

√

√

√

√

√

√

√

√

Data-race free
Statically data-race free
Non-tree messages
Read unique (iso)
Write unique (trn)
Mutability (ref)
Immutability (val)
Cyclic immutability
Identity (tag)
Destructive read
Recovery
Using uniques (iso . x)
Actors
Formal proof
Native compilation

√
√

√

√

√

Scala
√

Erlang

Rust
√

√

√

√

√

4

√

√

√

√

√

√
5

√
√

√

6

√

√

√

√

√

√

√

√

√

√

√

√
√
√

√

√

√

√

√

√
√

Table 5. Feature comparison.

9.

In [6], a type and effect system for deterministic semantics is provided. This is a powerful system, but does not
provide the unbounded non-deterministic semantics available in the actor-model.
In Rust [23], atomic reference counts, mutexes, allow
properties, and ownership types are combined to achieve
data race freedom. The use of both run-time and compiletime methods, and the addition of an unsafe module that
can violate the type system, is an interesting compromise
approach.
Our work is built on a deny properties [17] model instead
of a permissions or fractional permissions model. We show
that the type annotations used in related work are all expressions of these deny properties, and that additional annotations exist (particularly trn and the use of tag for typing
actors). We extend viewpoint adaptation and add our concept
of safe-to-write, allowing direct manipulation of isolated
types without recovery. Our use of tag with the actor-model
gives us a copy-less, lock-less operational semantics.
In table 5, we summarise some features of our work
and compare with those in Gordon et al. [19], Æminium
[28], Deterministic Parallel Java [6], Kilim [27], Haller and
Odersky [22], Scala, Erlang, and Rust [23].

Implementation and benchmarking

We have implemented a native code compiler using our
type system and a custom actor-model runtime, including
the scheduler, memory allocator, garbage collector, message
queues, etc. We have implemented large portions of a standard library and several real world data analytics programs.
Our experience so far leads us to believe our capabilities
system is expressive and easy to use, and the language is
suitable for any problem that displays non-deterministic concurrency and mutable state. Specific examples include data
analytics, financial systems, and video games.
The language uses carefully chosen default capabilities
to minimise the required annotations. In addition, the compiler guides the programmer as to which annotations should
be used, infers annotations locally, and performs automatic
recovery in some circumstances. As a result, when implementing LINPACK GUPS (in app. F) we require just 8 capability annotations and 3 uses of recover in 249 LOC. In approximately 10k LOC in the standard library, 89.3% of types
required no annotation.
Deny properties are also amenable to a highly efficient
implementation. We have benchmarked our language against
other actor-model languages with the CAF [11] benchmark
suite [2] and against MPI with HPC Challenge LINPACK
GUPS [1]. Benchmarking was done on a 12-core 2.3 GHz

6 A version of identity, none, appears in [25].

12

2015/3/25

Benchmark: LINPACK GUPS
220

**** *****
MPI (clang−3.5.0)

35

**** *****
Erlang OTP 6.1
Scala 2.11.6 (Akka)
CAF 0.13
Charm++ 6.6.1

30
Execution Time (seconds)

Million Updates Per Second

Benchmark: Creating 1,048,576 actors

25
20
15

200
180
160
140
120

10
100

5

2

0
1

2

3

4

5

6
7
8
Physical Cores

9

10

11

12

4
Physical Cores

8

Figure 16. LINPACK GUPS, where **** is our work.

Figure 13. Actor creation, where **** is our work.
Opteron 6338P with 64 GB of memory across 2 NUMA
nodes. The results shown are the average of 100 runs.
In fig. 13, we show actor creation performance. Here,
our implementation is garbage collecting actors themselves
[15] as well as objects, but still outperforms existing systems other than CAF, which is neither garbage collected nor
data-race free. In fig. 14, we show performance of a highly
contended mailbox, where additional cores tend to degrade
performance7 . In fig. 15, we show performance of a mixed
case, where a heavy message load is combined with brute
force factorisation of large integers.
In fig. 16, we show a benchmark that is not tailored for
actors: we take the GUPS benchmark from high-performance
computing, which tests random access memory subsystem
performance, and demonstrate that our implementation is
significantly faster than the highly optimised MPI implementation8 .
The full language as implemented in the compiler includes additional features, such as generic types, traits,
structural types, type expressions (unions, intersections and
tuples), a non-null type system, sound constructors, pattern
matching, exceptions, and garbage collection.
The compiler, a web-based development sandbox, and a
language tutorial are available9 .

Benchmark: Mailbox performance (100,000,000 messages)
***** *****
Erlang OTP 6.1
Scala 2.11.6 (Akka)
CAF 0.13
Charm++ 6.6.1

Execution Time (seconds)

1200
1000
800
600
400
200
0
1

2

3

4

5

6
7
8
Physical Cores

9

10

11

12

Figure 14. Mailbox performance, where **** is our work.

Execution Time (seconds)

Benchmark: Mixed
1050
975
900
825
750
675
600
525
450
375
300
225
150
75
0

**** *****
Erlang OTP 6.1
Scala 2.11.6 (Akka)
CAF 0.13
Charm++ 6.6.1

10.

Conclusions and further work

We have used deny properties to provide a more fundamental
basis for uniqueness and immutability. We have uncovered
a new form of uniqueness, write uniqueness, and have explored the use of an identity capability for asynchronous
method calls. Our extensions to viewpoint adaptation, including safe-to-write semantics, aliasing for non-reflexive
1

2

3

4

5

6
7
8
Physical Cores

9

10

11

12
7 In fig. 13 and 14, Scala performance with fewer than 3 cores has been

Figure 15. Mixed case performance, where **** is our
work.

elided to compress the y axis.
8 We show only power-of-two core counts because the MPI implementation
is optimised for this case.
9 These are supplied in supplementary material.

13

2015/3/25

sub-typing, and unaliased types, allow more operations on
unique types.
In future work, we intend to extend the formalisation in
this paper to cover and prove soundness for these features.
We also intend to formalise our use of the type system to
improve both concurrent and distributed garbage collection.

and encapsulation. In Formal Methods for Components and
Objects, pages 72–112. Springer Berlin Heidelberg, 2008.
[17] M. Dodds, X. Feng, M. Parkinson, and V. Vafeiadis. Denyguarantee reasoning. In Programming Languages and Systems, pages 363–377. Springer, 2009.
[18] C. Flanagan and M. Abadi. Types for safe locking. In Programming Languages and Systems, pages 91–108. Springer
Berlin Heidelberg, 1999.

References

[19] C. S. Gordon, M. J. Parkinson, J. Parsons, A. Bromfield, and
J. Duffy. Uniqueness and reference immutability for safe
parallelism. In ACM SIGPLAN Notices, volume 47, pages 21–
40. ACM, 2012.

[1] http://icl.cs.utk.edu/hpcc/.
[2] https://github.com/actor-framework/benchmarks/.
[3] G. Agha and C. Hewitt. Concurrent programming using actors. In Object-oriented concurrent programming, pages 37–
53. MIT Press, 1987.

[20] W. Gropp, E. Lusk, N. Doss, and A. Skjellum. A highperformance, portable implementation of the mpi message
passing interface standard. Parallel computing, 22(6):789–
828, 1996.

[4] J. Armstrong, R. Virding, C. Wikström, and M. Williams.
Concurrent programming in erlang. 1993.

[21] D. Grossman, G. Morrisett, T. Jim, M. Hicks, Y. Wang, and
J. Cheney. Region-based memory management in cyclone. In
ACM SIGPLAN Notices, volume 37, pages 282–293. ACM,
2002.

[5] H. G. Baker. "use-once" variables and linear objects: storage
management, reflection and multi-threading. ACM Sigplan
Notices, 30(1):45–52, 1995.
[6] R. L. Bocchino Jr, V. S. Adve, D. Dig, S. V. Adve, S. Heumann, R. Komuravelli, J. Overbey, P. Simmons, H. Sung, and
M. Vakilian. A type and effect system for deterministic parallel java. ACM Sigplan Notices, 44(10):97–116, 2009.

[22] P. Haller and M. Odersky. Capabilities for uniqueness and
borrowing. In ECOOP 2010–Object-Oriented Programming,
pages 354–378. Springer, 2010.
[23] N. D. Matsakis and F. S. Klock, II. The rust language. In
Proceedings of the 2014 ACM SIGAda Annual Conference on
High Integrity Language Technology, HILT ’14, pages 103–
104, New York, NY, USA, 2014. ACM.

[7] C. Boyapati and M. Rinard. A parameterized type system
for race-free java programs. In ACM SIGPLAN Notices,
volume 36, pages 56–69. ACM, 2001.
[8] J. Boyland. Alias burying: Unique variables without destructive reads. Software: Practice and Experience, 31(6):533–553,
2001.

[24] M. S. Miller, K.-P. Yee, J. Shapiro, et al. Capability myths
demolished. Technical report, Technical Report SRL200302, Johns Hopkins University Systems Research Laboratory,
2003. http://www. erights. org/elib/capability/duals, 2003.

[9] J. Boyland. Checking interference with fractional permissions. In Static Analysis, pages 55–72. Springer, 2003.

[25] K. Naden, R. Bocchino, J. Aldrich, and K. Bierhoff. A
type system for borrowing permissions. SIGPLAN Not.,
47(1):557–570, Jan. 2012.

[10] J. Boyland, J. Noble, and W. Retert. Capabilities for sharing.
In ECOOP 2001-Object-Oriented Programming, pages 2–27.
Springer, 2001.

[26] J. Östlund, T. Wrigstad, D. Clarke, and B. Åkerblom. Ownership, uniqueness, and immutability. Objects, Components,
Models and Patterns, pages 178–197, 2008.

[11] D. Charousset, T. C. Schmidt, R. Hiesgen, and M. Wählisch.
Native actors: a scalable software platform for distributed, heterogeneous environments. In Proceedings of the 2013 workshop on Programming based on actors, agents, and decentralized control, pages 87–96. ACM, 2013.

[27] S. Srinivasan and A. Mycroft. Kilim: Isolation-typed actors
for java. In ECOOP 2008–Object-Oriented Programming,
pages 104–128. Springer, 2008.

[12] D. Clarke and T. Wrigstad. External uniqueness is unique
enough. ECOOP 2003–Object-Oriented Programming, pages
59–67, 2003.

[28] S. Stork, K. Naden, J. Sunshine, M. Mohr, A. Fonseca,
P. Marques, and J. Aldrich. Æminium: A permission-based
concurrent-by-default programming language approach. ACM
Transactions on Programming Languages and Systems (TOPLAS), 36(1):2, 2014.

[13] D. Clarke, T. Wrigstad, J. Östlund, and E. Johnsen. Minimal
ownership for active objects. Programming Languages and
Systems, pages 139–154, 2008.

[29] P. Wadler. Linear types can change the world. In IFIP TC,
volume 2, pages 347–359. Citeseer, 1990.

[14] D. G. Clarke, J. M. Potter, and J. Noble. Ownership types
for flexible alias protection. In ACM SIGPLAN Notices,
volume 33, pages 48–64. ACM, 1998.

[30] Y. Zibin, A. Potanin, P. Li, M. Ali, and M. D. Ernst. Ownership and immutability in generic java. In ACM Sigplan Notices, volume 45, pages 598–617. ACM, 2010.

[15] S. Clebsch and S. Drossopoulou. Fully concurrent garbage
collection of actors on many-core machines. In Proceedings of
the 2013 ACM SIGPLAN international conference on Object
oriented programming systems languages and applications,
pages 553–570. ACM, 2013.
[16] D. Cunningham, W. Dietl, S. Drossopoulou, A. Francalanza,
P. Müller, and A. J. Summers. Universe types for topology

14

2015/3/25

Appendix
A.

Naming conventions, shorthands and
lookup functions

• ϕ(x) = ϕ ↓2 (x) ↓1
• ϕ[x 7→ v] = (ϕ ↓1 , ϕ ↓2 [x 7→ v], ϕ ↓3 )

We use the naming conventions given in fig.9, and the shorthands defined in fig. 17.
Lookup functions are defined in fig. 18. Function P returns a type definition for a class identifier C or actor identifier A. This contains the fields F, constructors K, functions M,
and behaviours B defined for that type. Since classes have no
asynchronous behaviour, the last entry in P(C) is empty, i.e.
ε. Function Fs returns the identifiers of all fields defined in a
type S, and function F returns the type of field f in S. Function M returns method information for some method in S.
This is overloaded on both the method identifier and the type
identifier in order to handle class constructors, actor constructors, synchronous methods (functions) and asynchronous methods (behaviours). The information returned is a
tuple of four components: the receiver type, the names and
types of the parameters, the body of the method in the form
of a source expression, and the return type. The capability
of the receiver and the return type can vary for synchronous methods, but not for constructors or asynchronous methods. Constructors always operate on a ref receiver, since the
constructor must write to the new object’s fields, and return
a ref◦ result, since the new object is initially mutable but
also unaliased, since the constructor’s reference to the receiver (this) is implicitly discarded when the constructor
returns. This allows a constructor that is passed only sendable references as parameters to be embedded in a recover
expression, giving the capability iso◦, which can be aliased
as iso, which is a subtype of all other capabilities. This allows constructing an object with any capability. Asynchronous methods always operate on a ref receiver. This is because the receiver of an asynchronous method is always an
actor; when the body is executed, a new stack with the receiver as the root actor is created. Since each actor executes
the body of a single behaviour (or asynchronous constructor)
at any given time, every behaviour body can read from and
write to the receiver. Since an asynchronous method cannot,
by definition, perform any operations at the call site before
returning, the only possible return values are the receiver or
null. We have chosen to return the receiver to allow chaining
method calls.

B.

• χ(ι, f) = χ(ι) ↓2 (f)
• χ[ω, f 7→ v] = χ[ω 7→ (χ(ω) ↓1 , χ(ω) ↓2 [f 7→ v]]
• χ[α, f 7→ v] = χ[α 7→ (χ(α) ↓1 , χ(α) ↓2 [f 7→

v], χ(α) ↓3 , χ(α) ↓4 , χ(α) ↓5 )]
• χ[α 7→ (σ, e)] = χ[α 7→ (χ(α) ↓1 , χ(α) ↓2 , χ(α) ↓3

, σ, e]
• χ[α 7→ µ] = χ[α 7→ (χ(α) ↓1 , χ(α) ↓2 , µ, χ(α) ↓4

, χ(α) ↓5 ]
Figure 17. Auxiliary definitions

P = CT AT
class C F K M ∈ CT
P(C) = F K M ε
C∈P
P = CT AT
actor A F K M B ∈ AT
P(A) = F K M B
A∈P
P(S) = F K M B
Fs(S) = {f | var f : T ∈ F}
P(S) = F K M B var f : T ∈ F
F(S, f) = T
P(C) = F K M (new k(x : T) ⇒ e) ∈ K
M(C, k) = (C ref, x : T, e, C ref◦)
P(A) = F K M B (new k(x : T) ⇒ e) ∈ K
M(A, k) = (A var, x : T, e, A tag)
P(S) = F K M B (fun κ m(x : T) : ET ⇒ e) ∈ M
M(S, m) = (S κ, x : T, e, ET)

Operational semantics

Definition 4. We call an expression e a redex if it has one of
the following forms:
e ::= z.f | z.f = y | z.m(y) | z.b(y) | S.k(z)

P(A) = F K M B (be b(x : T) ⇒ e) ∈ B
M(A, b) = (A ref, x : T, e, A tag)
Figure 18. Lookup functions

Lemma 1. Uniqueness of contexts. For any expressions e1 ,
e2 and contexts E1 [·], E2 [·], if E1 [e2 ] ≡ E2 [e2 ] and e1 and e2
are redexes then E1 [·] ≡ E2 [·] and e1 ≡ e2 .
15

2015/3/25

∀S ∈ P. ` S
WF-P ROGRAM
` P

Lemma 3. Properties of capability operators.
∀κ, κ1 , κ2 :
1. If κ1 ∼g κ2 , then κ1 ∼l κ2 .
2. If κ1 ≤ κ2 , then

P(S) = F K M B
∀var f : S κ ∈ F. ` S  ∀K ∈ K.S ` K
∀M ∈ M.S ` M  ∀B ∈ B.S ` B
WF-T YPE
` S

(a) κ1 ∼l κ ⇒ κ2 ∼l κ
(b) κ1 ∼g κ ⇒ κ2 ∼g κ
3. If κ1 ∼l κ2 , and both κ1 . κ and κ2 . κ are defined, then
κ1 . κ ∼l κ2 . κ.
4. If κ1 ∼g κ2 , and both κ1 . κ and κ2 . κ are defined, then
κ1 . κ ∼g κ2 . κ
5. κ2 ≤ κ1 . κ2 or κ1 = val or κ1 . κ2 undefined
6. If A(κ1 ) ≤ κ2 then

[this 7→ C var, x 7→ T] ` e : C var◦
WF-C TOR
C ` new k(x : T) ⇒ e
[this 7→ Sκr , x 7→ T] ` e : ET
WF-S YNC
S ` fun κr m(x : T) : ET ⇒ e
Sendable(Ti )
[this 7→ A var, x 7→ T] ` e : A tag
WF-ATOR
A ` new k(x : T) ⇒ e

(a) κ1 ∼l κ ⇒ κ2 ∼l κ
(b) κ1 ∼g κ ⇒ κ1 ∼g κ
(c) A(κ1 . κ) ≤ κ2 . κ
7. If A(κ1 ) ≤ κ2 and A(κ2 ) ≤ κ4 then

Sendable(Ti )
[this 7→ A var, x 7→ T] ` e : A tag
WF-A SYNC
A ` be b(x : T) ⇒ e

(a) κ1 ∼l κ2 ⇒ κ3 ∼l κ4
(b) κ1 ∼g κ2 ⇒ κ3 ∼g κ4
Proof. By case analysis on κ1 and κ2 .

Figure 19. Well-formed programs

On the other hand, κ1 ≤ κ2 does not imply that κ . κ2 ≤
κ . κ2 . For example, iso ≤ trn, but box . iso = tag 
box . trn = box. Similarly, κ1 ≤ κ2 does not imply that
κ1 . κ ≤ κ2 . κ; take iso . trn = tag  trn . trn = trn.
Finally the .-operator is not associative, i.e. (κ1 . κ2 ) . κ3 6=
κ1 . (κ2 . κ3 ); take (iso . trn) . val = ⊥ 6= iso . (trn .
val) = val.

• z ∈ ϕ iff z ∈ dom(ϕ ↓2 )
• α ∈ χ iff α ∈ dom(χ)
• ∆ ` α ∈ χ iff α ∈ dom(χ)
• ∆ ` ι ∈ χ iff ∃ι0 such that ∆ ` ι0 ∈ χ and ∆, χ, ι0 ` ι :

_
• M(ϕ, χ) = M(χ(ϕ(this) ↓1 , ϕ ↓1 )

C.

D.

Well-formed runtime configurations

Figure 20. Auxiliary well-formedness definitions

Lemma 4. Properties of deep viewpoint adaptation.
∀κ, κ1 ..., κn :

Type system and well-formed programs

1. If κ1 ≤ κ2 then κ1 I κ ≤ κ2 . κ, or κ2 = val.
2. κ1 I κ2 = val iff κ1 . κ2 = val.
3. κ1 I κ2 ≤ κ1 . κ2
4. (...(κ1 I κ2 ) I κ3 ...) I κn ≤ (...(κ1 . κ2 ) . κ3 ...) . κn
5. (...(κ1 I κ2 ) I κ3 ...) I κn = val iff (...(κ1 . κ2 ) .
κ3 ...) . κn = val
6. If κ1 ∼l κ2 and κ1 , κ2 6= tag, then κ1 I κ ∼l κ2 I κ
or κ1 = κ2 = ref
7. If κ1 ∼g κ2 and κ1 , κ2 6= tag then κ1 I κ ∼g κ2 I κ
8. If A(κ1 ) ≤ κ2 and κ1 6= κ2 6= tag then A(κ1 I κ) ≤
κ2 I κ

The rules for a well-formed program are presented in fig.
19. The WF-P ROGRAM rule indicates a program is wellformed if all types in the program are well-formed. The WFT YPE rule indicates that a type is well-formed if the types of
all of its fields are well-formed, its constructors are wellformed, and its synchronous and asynchronous methods are
well-formed. The WF-C TOR , WF-S YNC , and WF-A SYNC
rules indicate that a method is well-formed when the body
of the method in results in a subtype of the return type
of the method. The body of the method is evaluated using
an environment composed of the receiver and the method
parameters, each mapped to their type, as shown in fig. 6.

Lemma 5. Capabilities are preserved along paths.
If ∆, χ, α ` ι : κ, p and ∆, χ, α ` ι : κ0 , p then κ = κ0 .

Lemma 2. Context lemma.
Proof. By induction over the structure of p.

1. Γ ` E[e] : ET ⇒ ∃ET0 and Γ, y 7→ ET0 ` E[y] : ET and
Γ ` e : ET0 and y ∈
/ dom(Γ)
2. Γ, y 7→ ET0 ` E[y] : ET and Γ ` e : ET0 and y free in
E[·] ⇒ Γ ` E[e] : ET

E.

Soundness

The property central to any soundness argument is the preservation of the well-formed visibility property, WFV (∆, χ),
16

2015/3/25

M(S0 , m) = (S0 κ00 , x : T, _, ET0 ) and
Γ ` ei : ETi and A(ETi ) ≤ Ti and ET0 v ET
8. If e ≡ e0 .b(e) then ∃A, κ0 , κ00 , φ, T such that
Γ ` e0 : A κ0 φ and A(κ0 φ) ≤ κ00 and
M(A, b) = (A ref, x : T, _, A tag) and
sendable(Ti ) and Γ ` ei : ETi and A(ETi ) ≤ Ti and
A tag = ET
9. If e ≡ C.k(e)then ∃ET, T such that
M(C, k) = (C ref, x : T, _, C ref◦) and
Γ ` ei : ETi and A(ETi ) ≤ Ti and C ref◦ v ET
10. If e ≡ A.k(e)then ∃ET, T such that
M(A, k) = (A ref, x : T, _, A tag) and
sendable(Ti ) and Γ ` ei : ETi and A(ETi ) ≤ Ti and
A tag = ET
11. If e ≡ recover e0 then ∃ET0 such that
Γ0 = Γ\{x | ¬sendable(Γ(x))} and
Γ0 ` e0 : ET0 and R(ET0 ) v ET

and the well-formed temporaries property WFT (∆, χ, α, i, e)
for all expressions and continuations. To study the former,
we need properties about the creation of new paths, while
for the latter, we need to control the types we assign to the
temporaries in each step.
E.1

New paths

Lemma 6. Simplification.
If
1. A(κ1 φ) ≤ κ2
2. κ2 ≤ κ3
3. κ4 / κ2 or κ4 / κ3
Then
4. A(κ1 φ) ≤ κ3
5. κ4 / A(κ1 φ) or κ4 / κ3
Proof. (4) follows from (1) and (2). For (5), if κ4 / κ3 , done.
Otherwise, κ02 = A(κ1 φ). If κ4 = ref, then for all κ1 φ,
κ4 / κ02 . If κ4 = trn, then κ2 ∈ {iso, trn, val, tag} 63 κ3 .
If κ02 ∈ {iso, trn, val} then κ1 φ ∈ {iso◦, trn◦, val}
and trn / κ02 . If κ02 = tag then κ3 = tag, which contradicts
κ4 6 /κ3 . If κ4 = iso, the same holds, except κ2 cannot be
trn.

Proof. By induction on the typing of Γ ` e : ET. For case 6
(field assignment), apply lemma 6.
Lemma 8. Temporaries and variables with unique capabilities are unique.
If
1. WFV (∆, χ)
2. χ(α, i, z) = χ(α0 , i0 , z0 ) = ι
3. ∆(α, i, z) = S κ φ
4. κ ∈ {iso, trn}
5. ∆, χ, α0 ` ι : κ0 , (i0 , z0 )

Definition 5. Unaliased types can be treated as base types.
ET0 v ET iff ET0 = ET, or ET0 = S κ◦ and ET = S κ
Definition 6. An identifier z is aliased in a runtime expression e iff
∃E[·], e0 , f, y, e, n, S such that

Then α = α0 and either κ ∼` κ0 or (i, z) = (i0 , z0 ).

• e ≡ E[x = z] or
• e ≡ E[e0 .f = z] or
• e ≡ E[e0 .n(y, z, e)] or
• e ≡ E[z.n(y)] or
• e ≡ E[S.k(y, z, e)]

Proof. Assume that α 6= α0 . Then, by WFV .1 , κ ∼g κ0 .
This implies κ0 = tag, which contradicts 5. Therefore, α =
α0 and ∆, χ, α0 ` ι : κ, (i, z). If Stable(∆, α, (i, z)) then
by WFV .2 , either κ ∼` κ0 (done) or χ, α ` (i, z) ∼ (i0 , z0 ),
which requires (i, z) = (i0 , z0 ) (done). If ¬Stable(∆, α, (i, z))
then z = t and by WFV .4 either (i, z) = (i0 , z0 ) (done)
or ∃ι0 , κ00 , p0 , f such that κ ≤ κ00 and κ00 ∈ {iso, trn}
and (i0 , z0 ) = p0 · f and ∆, χ, α ` ι0 : κ00 , p0 and
∆, χ, ι0 ` ι : κ, (0, this) · f, so f =  and p0 = (i0 , z0 )
and ι = ι0 . This gives us ∆, χ, ι ` ι : κ, (0, this), which by
the definition of visibility gives us κ = ref, which contradicts (4) (done).

Lemma 7. Inversion.
If Γ ` e : ET then
1. If e ≡ x then Γ(x) v ET
2. If e ≡ e1 .f then ∃S, S0 , κ, κ0 such that Γ ` e1 : S κ and
F(S, f) = S0 κ0 and ET = S0 κ . κ0 .
3. If e ≡ null then ∃S such that S iso◦ v ET
4. If e ≡ e1 ; e2 then ∃ET1 such that Γ ` e1 : ET1 and
Γ ` e2 : ET
5. If e ≡ x = e1 then ∃S, κ, κ0 , φ such that Γ(x) = S κ and
Γ ` e1 : S κ0 φ and A(κ0 φ) ≤ κ and U(S κ) v ET
6. If e ≡ e1 .f = e2 then ∃S1 , S2 , κ1 , κ2 , φ such that
Γ ` e1 : S1 κ1 and Γ ` e2 : S2 κ2 φ and
F(S1 , f) = S2 κ3 and A(κ2 φ) ≤ κ3 ,
either κ1 / κ3 or κ1 / A(κ2 φ),
and U(S2 κ1 . κ3 ) v ET
7. If e ≡ e0 .m(e) then ∃S0 , κ0 , κ00 , φ, T, ET, ET0 such that
Γ ` e0 : S0 κ0 φ and A(κ0 φ) ≤ κ00 and

Lemma 9. Isolation in well-formed visibility.
If
1. WFV (∆, χ)
2. ∆(α, i, t) = S κ φ and χ(α, i, t) = ι and κ ∈ {iso, trn}
3. ∆, χ, α0 ` ι : κ0 , p
Then
4. If κ φ = iso◦ then α = α0 and p = (i, t).
5. If κ φ = trn◦ then α = α0 and either p = (i, t) or
κ0 = box.
17

2015/3/25

6. If κ φ = iso then α = α0 and either p = (i, t) or
∃ι0 , κ00 , p0 , f such that κ ≤ κ00 and κ00 ∈ {iso, trn}
and p = p0 · f and ∆, χ, α ` ι0 : κ00 , p0 and ∆, χ, ι0 ` ι :
iso, f.
7. If κ φ = trn then α = α0 and either p = (i, t)
or κ0 = box or ∃ι0 , p0 , f such that p = p0 · f and
∆, χ, α ` ι0 : trn, p0 and ∆, χ, ι0 ` ι : trn, f.

4. e ≡ E0 [z.f = e0 ], or
5. e ≡ E0 [recover z], or
Proof. By application of definition 6.
Lemma 12. If Γ, x : T1 ` e : ET1 and A(T2 ) ≤ T1 then
∃ET2 .Γ, x : T2 ` e : ET2 and ET1 = ET2 or A(ET2 ) ≤ ET1
Proof. By structural induction on the typing and lemma 3.

Proof. (4) and (5) follow from lemma 8. (5) and (6) follow
from lemma 8 and WFV .4 .

Lemma 13. New paths through field read.
If

Lemma 10. Aliasing and replaceability.
If

1. χ(α, i, z) = ι
2. ∆(α, i, z) = S κ φ
3. χ(ι, f) = ι0 and F(S, f) = S0 κ0
4. T = ⊥ if z = t0 , S κ otherwise
5. ∆0 = ∆[(α, i, z) 7→ T, (α, i, t) 7→ S0 κ . κ0 )]
6. T (∆(α, i)) ⊆ {z}

1. Γ ` e : ET and z is aliased in e
2. z does not appear more than once in e
3. Γ(z) is not unaliased
4. Γ0 = Γ[z 7→ A(Γ(z))]
Then Γ0 ` e : ET

Then

Proof. By induction over the structure of e. We apply lemma
7. Moreover, we use the fact that ∀κ.A(A(κ)) = A(κ). The
base cases are expressions that can alias z.

7. ∀α0 , ι00 , κ00 , p0 if ∆0 , χ, α0 ` ι00 , κ00 , p0 then
(a) ∆, χ, α0 ` ι00 : κ00 , p0 or
(b) α0 = α and ∃f, κ such that

• If e ≡ x = z then, by lemma 7, we obtain Γ(x) = S κ

and Γ(z) = S κ0 φ and φ 6= ◦ and A(κ0 ) ≤ κ. Therefore,
we have A(A(κ0 )) ≤ κ and so Γ0 ` x = z : ET.
• If e ≡ e0 .f = z then, by lemma 7, we obtain Γ ` e0 : S κ
and F(S, f) = S0 κ0 and Γ(z) = S0 κ00 φ and φ 6= ◦ and
A(κ00 ) ≤ κ0 . Therefore, we have A(A(κ00 )) ≤ κ0 and so
Γ0 ` e0 .f = z : ET.
• If e ≡ e0 .n(y, z, e) then, by lemma 7, we obtain Γ `
e0 : S κ and M(S, n) = (_, x : S κ, _, _) and Γ(z) =
Si κ0i φ and and φ 6= ◦ and A(κ0i ) ≤ κi . Therefore, we
have A(A(κ0i )) ≤ κi and so Γ0 ` e0 .n(y, z, e) : ET.
• If e ≡ z.n(y) then, by lemma 7, we obtain Γ(z) =
S κ φ and φ 6= ◦ and M(S, n) = (S κ0 ) and A(κ) ≤
(κ0 ). Therefore, we have A(A(κ)) ≤ κ0 and so Γ0 `
z.n(y) : ET.
• If e ≡ S.k(y, z, e)then, by lemma 7, we obtain M(S, k) =
(_, x : S κ, _, _) and Γ(z) = Si κ0i φ and and φ 6= ◦ and
A(κ0i ) ≤ κi . Therefore, we have A(A(κ0i )) ≤ κi and so
Γ0 ` S.k(y, z, e) : ET.

i. p0 = (i, t) · f
ii. κ00 = κ . κ0 I κ
iii. ∆, χ, α ` ι00 : κ I κ0 I κ, (i, z) · f · f
8. If WFV (∆, χ) then WFV (∆0 , χ) and T (∆0 (α, i)) ⊆
{t}
Lemma 14. New paths through local assignment.
If
1. χ(α, i, z) = ι and χ(α, i, x) = ι0 and t ∈
/ χ(α, i)
2. ∆(α, i, z) = S κ φ and ∆(α, i, x) = S κ0
3. χ0 = χ[(α, i, x) 7→ ι, (α, i, t) 7→ ι0 ]
4. T = ⊥ if z = t0 , S κ otherwise
5. ∆0 = ∆[(α, i, z) 7→ T, (α, i, t) 7→ U(S κ0 )]
6. T (∆(α, i)) ⊆ {z}
Then
7. ∀α0 , ι00 , κ00 , p if ∆0 , χ0 , α0 ` ι00 : κ00 , p then
(a) ∆, χ, α0 ` ι00 : κ00 , p or
(b) α = α0 and ∃f, κ such that

For the inductive step, if e ≡ E[e0 ]and z is aliased in e,
then, by lemma 2, we obtain that ∃ET0 , y ∈
/ Γ such that Γ `
e0 : ET0 and Γ[y 7→ ET0 ] ` E[y] : ET, and so Γ0 ` e0 : ET0 .
Therefore, by lemma 2, we obtain Γ0 ` E[e0 ] : ET.

i. p = (i, x) · f and κ00 = κ0 I κ and
∆, χ, α ` ι00 : κI κ, (i, z) · f, or
ii. p = (i · t) · f and κ00 = κ0 I κ and
∆, χ, α ` ι00 : κ0 I κ, (i, x) · f

Lemma 11. Origins of temporary identifiers.
If

8. If A(κ φ) ≤ κ0 and WFV (∆, χ) then WFV (∆0 , χ0 ) and
T (∆0 (α, i)) ⊆ {t}

1. z appears once in expression e
2. z is not aliased in e
Then ∃E0 such that

Lemma 15. New paths through field assignment.
If

3. e ≡ E0 [z.f], or

1. χ(α, i, z) = ι and χ(α, i, z0 ) = ι0
18

2015/3/25

2. ∆(α, i, z) = S κ φ and ∆(α, i, z0 ) = S0 κ0 φ0
3. χ(ι, f) = ι00 and F(S, f) = S0 κ00
4. χ0 = χ[(ι, f) 7→ ι0 , (α, i, t) 7→ ι00 ]
5. T = ⊥ if z = t0 , S κ otherwise
6. T0 = ⊥ if z0 = t00 , S0 κ0 otherwise
7. ∆0 = ∆[(α, i, z) 7→ T, (α, i, z0 ) 7→ T0 , (α, i, t) 7→
U(S0 κ . κ00 )]
8. T (∆(α, i)) ⊆ {z, z0 }

2. ∆0 ` χ0 
Lemma 18. Type preservation for method call.
For all heaps χ and actors α, if
1. χ(α) = (_, _, _, σ · ϕ, E[e])
2. χ, σ · ϕ, e
χ00 , σ · ϕ · ϕ0 , e0
0
00
3. χ = χ [α 7→ (σ · ϕ · ϕ0 , E[e0 ])]
4. ∆ ` χ

Then

Then ∃∆0 such that ∆0 ` χ0 

9. ∀α0 , ι000 , κ000 , p0 if ∆0 , χ0 , α0 ` ι000 : κ000 , p0 then
(a) ∆, χ, α0 ` ι000 : κ000 , p0 or
(b) α0 = α and ∃f, κ such that
i. κ000 = κ I κ00 I κ and p0 = (i, z) · f · f and
∆, χ, α ` ι000 : κ0 I κ, (i, z0 ) · f, or
ii. κ000 = U(κ . κ00 )I κ and p0 = (i, t) · f and
∆, χ, α ` ι000 : κ I κ00 I κ, (i, z) · f · f, or
iii. ∃κ0000 , p 6= (i, z) such that κ000 = κ0000 I κ00 I κ
and p0 = p · f · f and ∆, χ, α ` ι : κ0000 , p
10. If A(κ0 φ0 ) ≤ κ00 and (κ / κ0 or κ / κ00 ) and WFV (∆, χ)
then WFV (∆0 , χ0 ) and T (∆0 (α, i)) = ∅

Lemma 19. Type preservation upon method return
For all heaps χ and actors α, if

Lemma 16. New paths through message passing.
If

1. χ(α) = (A, fs, (n · v̄) · µ, α, )
2. M(A, n) = (_, x : T, e, _)
3. ϕ = (n, [this 7→ α, x̄ 7→ v̄], ·)
4. χ0 = χ[α 7→ (A, fs, µ, (α · ϕ), e)]
5. ∆ ` χ

1. χ(α) = (_, _, _, σ · ϕ · ϕ0 , z)
2. t ∈
/ ϕ and ϕ00 = ϕ[t 7→ ϕ0 (z)]
0
3. ϕ = (_, _, E[·])
4. χ0 = χ[α 7→ (σ · ϕ00 , E[t])]
5. ∆ ` χ
Then ∃∆0 such that ∆0 ` χ0 
Lemma 20. Type preservation upon message handling.
For all heaps χ and actors α, if

1. χ(α, i, z) = ι and ∆(α, i, z) = S κ φ
2. χ0 = χ[(α0 , −j, x) 7→ ι]
3. T = ⊥ if z = t, S κ otherwise
4. ∆0 = ∆[(α, i, z) 7→ T, (α0 , −j, x) 7→ S κ0 ]
5. T (∆(α, i)) ⊆ {z}

Then ∃∆0 such that ∆0 ` χ0 

F.

Then
6. ∀α00 , ι00 , κ00 , p if ∆0 , χ0 , α00 ` ι00 : κ00 , p then
1
2
(a) ∆, χ, α00 ` ι00 : κ00 , p or
3
4
(b) α00 = α0 and ∃f, κ such that
5
6
i. p = (−j, x) · f
7
ii. κ00 = κ0 I κ
8
9
iii. ∆, χ, α ` ι00 : κI κ, (i, z) · f
10
0
0
7. If A(κ φ) ≤ κ and sendable(κ ) and WFV (∆, χ) then 11
12
WFV (∆0 , χ0 ) and T (∆0 (α, i)) = ∅
13
E.2

Preservation of well-formedness

Lemma 17. Type preservation on same frame.
For all heaps χ, actors α, global type environments ∆,
frames ϕ, stacks σ and expressions e, if
1. χ(α) = (_, _, _, α · ϕ · ϕ, E[e]) and |ϕ̄| = i − 1
2. χ, α · ϕ · ϕ, e
χ00 , α · ϕ · ϕ0 , e0
3. χ0 = χ00 [α 7→ (α · ϕ · ϕ, E[e0 ])]
4. ∆(α, i) ` e : ET
5. ∆ ` χ
Then ∃∆0 such that
1. ∆0 (α, i) ` e0 : ET

14
15
16
17
18
19
20
21
22
23
24
25
26
27
28
29
30
31

19

GUPS benchmark source code

use "options"
use "time"
use "collections"
class Config
var logtable: U64 = 20
var iterate: U64 = 10000
var logchunk: U64 = 10
var logactors: U64 = 2
fun ref apply(env: Env): Bool =>
var options = Options(env)
options
.add("logtable", "l", None, I64Argument)
.add("iterate", "i", None, I64Argument)
.add("chunk", "c", None, I64Argument)
.add("actors", "a", None, I64Argument)
for option in options do
match option
| ("table", var arg: I64) => logtable = arg.u64()
| ("iterate", var arg: I64) => iterate = arg.u64()
| ("chunk", var arg: I64) => logchunk = arg.u64()
| ("actors", var arg: I64) => logactors = arg.u64()
| ParseError =>
env.out.print(
"""
gups_opt [OPTIONS]
--table
N
log2 of the total table size.
Defaults to 20.
--iterate
N
number of iterations.
Defaults to 10000.

2015/3/25

32
33
34
35
36
37
38
39
40
41
42
43
44
45
46
47
48
49
50
51
52
53
54
55
56
57
58
59
60
61
62
63
64
65
66
67
68
69
70
71
72
73
74
75
76
77
78
79
80
81
82
83
84
85
86
87
88
89
90
91
92
93
94
95
96
97
98
99
100
101
102
103
104
105
106
107
108

--chunk
N
log2 of the chunk size.
Defaults to 10.
--actors
N
log2 of the actor count.
Defaults to 2.
"""
)
return false
end
end
env.out.print(
"logtable: " + logtable.string() +
"\niterate: " + iterate.string() +
"\nlogchunk: " + logchunk.string() +
"\nlogactors: " + logactors.string()
)
true

109
110
111
112
113
114
115
116
117
118
119
120
121
122
123
124
125

126
127
128
129
var _updates: U64 = 0
130
var _confirm: U64 = 0
131
let _start: U64
132
var _actors: Array[Updater] val
133
134
new create(env: Env) =>
135
_env = env
136
137
if _config(env) then
138
let actor_count = 1 << _config.logactors
139
let loglocal = _config.logtable - _config.logactors 140
let chunk_size = 1 << _config.logchunk
141
let chunk_iterate = chunk_size * _config.iterate
142
143
_updates = chunk_iterate * actor_count
144
_confirm = actor_count
145
146
var updaters = recover Array[Updater](actor_count) 147
end
148
149
for i in Range[U64](0, actor_count) do
150
updaters.push(Updater(this, actor_count, i,
151
loglocal, chunk_size,
152
chunk_iterate * i))
153
end
154
155
_actors = consume updaters
156
_start = Time.nanos()
157
158
try
159
for a in _actors.values() do
160
a.start(_actors, _config.iterate)
161
end
162
end
163
else
164
_start = 0
165
_actors = recover Array[Updater] end
166
end
167
168
be done() =>
169
if (_confirm = _confirm - 1) == 1 then
170
try
171
for a in _actors.values() do
172
a.done()
173
end
174
end
175
end
176
177
be confirm() =>
178
_confirm = _confirm + 1
179
180
if _confirm == _actors.size() then
181
let elapsed = (Time.nanos() - _start).f64()
182
let gups = _updates.f64() / elapsed
183
184
_env.out.print(
185
"Time: " + (elapsed / 1e9).string() +
186
"\nGUPS: " + gups.string()
187
)
188

actor Main
let _env: Env
let _config: Config = Config

20

end
actor Updater
let _main: Main
let _index: U64
let _updaters: U64
let _chunk: U64
let _mask: U64
let _loglocal: U64
let _output: Array[Array[U64] iso]
let _reuse: List[Array[U64] iso] = List[Array[U64] iso]
var _others: (Array[Updater] val | None) = None
var _table: Array[U64]
var _rand: U64
new create(main:Main, updaters: U64, index: U64,
loglocal: U64, chunk: U64,
seed: U64)
=>
_main = main
_index = index
_updaters = updaters
_chunk = chunk
_mask = updaters - 1
_loglocal = loglocal
_rand = PolyRand.seed(seed)
_output = _output.create(updaters)
let size = 1 << loglocal
_table = Array[U64].undefined(size)
var offset = index * size
try
for i in Range[U64](0, size) do
_table(i) = i + offset
end
end
be start(others: Array[Updater] val, iterate: U64) =>
_others = others
iteration(iterate)
be apply(iterate: U64) =>
iteration(iterate)
fun ref iteration(iterate: U64) =>
let chk = _chunk
for i in Range(0, _updaters) do
_output.push(
try
_reuse.pop()
else
recover Array[U64](chk) end
end
)
end
for i in Range(0, _chunk) do
var datum = _rand = PolyRand(_rand)
var updater = (datum >> _loglocal) and _mask
try
if updater == _index then
_table(i) = _table(i) xor datum
else
_output(updater).push(datum)
end
end
end
try
let to = _others as Array[Updater] val
repeat
let data = _output.pop()
if data.size() > 0 then

2015/3/25

189
190
191
192
193
194
195
196
197
198
199
200
201
202
203
204
205
206
207
208
209
210
211
212
213
214
215
216
217
218
219
220
221
222
223
224
225
226
227
228
229
230
231
232
233
234
235
236
237
238
239
240
241
242
243
244
245
246
247
248
249
250
251
252
253
254
255
256
257
258
259
260
261
262
263
264

to(_output.size()).receive(consume data)
else
_reuse.push(consume data)
end
until _output.size() == 0 end
end
if iterate > 1 then
apply(iterate - 1)
else
_main.done()
end
be receive(data: Array[U64] iso) =>
try
for i in Range(0, data.size()) do
let datum = data(i)
var j = (datum >> _loglocal) and _mask
_table(j) = _table(j) xor datum
end
data.clear()
_reuse.push(consume data)
end
be done() =>
_main.confirm()
primitive PolyRand
fun apply(prev: U64): U64 =>
(prev << 1) xor if prev.i64() < 0 then _poly() else 0
end
fun seed(from: U64): U64 =>
var n = from % _period()
if n == 0 then
return 1
end
var m2 = Array[U64].undefined(64)
var temp = U64(1)
try
for i in Range(0, 64) do
m2(i) = temp
temp = this(temp)
temp = this(temp)
end
end
var i: U64 = 64 - n.clz()
var r = U64(2)
try
while i > 0 do
temp = 0
for j in Range(0, 64) do
if ((r >> j) and 1) != 0 then
temp = temp xor m2(j)
end
end
r = temp
i = i - 1
if ((n >> i) and 1) != 0 then
r = this(r)
end
end
end
r
fun _poly(): U64 => 7
fun _period(): U64 => 1317624576693539401

21

2015/3/25

