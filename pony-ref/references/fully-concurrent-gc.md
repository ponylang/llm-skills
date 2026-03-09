Fully Concurrent Garbage Collection
of Actors on Many-Core Machines
Sylvan Clebsch and Sophia Drossopoulou
Department of Computing, Imperial College, London
{sc5511, scd}@doc.ic.ac.uk

Abstract
Disposal of dead actors in actor-model languages is as important as disposal of unreachable objects in object-oriented
languages. In current practice, programmers are required
to either manually terminate actors, or they have to rely
on garbage collection systems that monitor actor mutation
through write barriers, thread coordination through locks etc.
These techniques, however, prevent the collector from being
fully concurrent.
We developed a protocol that allows garbage collection to
run fully concurrently with all actors. The main challenges
in concurrent garbage collection is the detection of cycles of
sleeping actors in the actors graph, in the presence of concurrent mutation of this graph. Our protocol is solely built
on message passing: it uses deferred direct reference counting, a dedicated actor for the detection of (cyclic) garbage,
and a confirmation protocol (to deal with the mutation of the
actor graph).
We present our ideas informally through an example, and
then present a formal model, prove soundness and argue
completeness. We have implemented the protocol as part of
a runtime library. As a preliminary performance evaluation,
we discuss the performance of our approach as currently
used at a financial institution, and use four benchmarks from
the literature to compare our approach with other actormodel systems. These preliminary results indicate that the
overhead of our approach is small.
Categories and Subject Descriptors D.3.2 [Programming
Languages]: Language Classifications - concurrent, distributed, and parallel languages; D.3.4 [Programming LanPermission to make digital or hard copies of all or part of this work for personal or
classroom use is granted without fee provided that copies are not made or distributed
for profit or commercial advantage and that copies bear this notice and the full citation
on the first page. Copyrights for components of this work owned by others than the
author(s) must be honored. Abstracting with credit is permitted. To copy otherwise, or
republish, to post on servers or to redistribute to lists, requires prior specific permission
and/or a fee. Request permissions from permissions@acm.org.
OOPSLA ’13, October 29–31, 2013, Indianapolis, Indiana, USA.
Copyright is held by the owner/author(s). Publication rights licensed to ACM.
ACM 978-1-4503-2374-1/13/10. . . $15.00.
http://dx.doi.org/10.1145/2509136.2509557

guages]: Processors - Memory management (garbage collection).
Keywords actors; message passing; concurrency; manycore; garbage collection

1.

Introduction

The actor-model uses actors as the unit of computation. Actors encapsulate messaging, memory, and a thread of execution into a single entity, providing a powerful model for concurrent computation [1, 2].
Actor-model languages must know when an actor has
terminated in order to free resources dedicated to the actor.
Most existing actor-model languages and libraries do not attempt to solve this problem, instead requiring the programmer to explicitly manage every actor’s lifetime [3–7]. The
languages that do garbage collect actors require hardware
features that adversely impact performance, such as cache
coherency, expensive software techniques that may require
hardware support, such as mutation monitoring through
write barriers, and use approaches that are not based on the
message passing paradigm at the heart of the actor-model
[14, 15]. The very problems that actor-model programming
excels at addressing (including concurrency, scalability, and
simplicity) have made actor garbage collection problematic,
due to the difficulty of observing the global state of a program. As a result, actor-model systems in applications which
create many short-lived actors become either more difficult
to program (when they require manually terminating actors)
or encounter performance problems (when they have actor
garbage collection that is not fully concurrent).
A language which does not provide garbage collection of
actors will require a facility to explicitly terminate actors.
This will also require the language to provide a default
behaviour when a message is sent to a terminated actor, the
ability to distinguish at runtime between terminated and nonterminated actors, and possibly notification mechanisms for
actor termination.
In this paper, we present a technique for garbage collection of actors, which we call Message-based Actor Collection (MAC), that satisfies the following goals:

1. Soundness: the technique collects only dead actors.
2. Completeness: the technique collects all dead actors
eventually.
3. Concurrency: the technique does not require a stopthe-world step, thread coordination, actor introspection,
shared memory, read/write barriers or cache coherency.
When an actor has completed local execution and has no
pending messages on its queue, it is blocked. An actor is
dead if it is blocked and all actors that have a reference to it
are blocked, transitively. Collection of dead actors depends
on being able to collect closed cycles of blocked actors.
Our approach is inspired by previous work on distributed
garbage collection of passive objects using distributed reference counting and a secondary mechanism to collect cyclic
garbage [22–25]. Detection of cycles of objects is based on
their topology, which is essentially the number of incoming
references and the identities of all outgoing references. We
adopt this approach so that the topology of an actor consists of the number of incoming references from actors, the
set of outgoing references to actors, and a flag indicating
whether the actor is blocked. A dedicated actor, called the
cycle detector, keeps track of the actor topology and detects
any cycles.
The challenge we face is that the true topology of an actor
is a concept distributed across all of the actors: it changes
not only when the actor mutates, but also when other actors
mutate. An actor’s view of its topology may be out of sync
with the true topology, and the cycle detector’s view of an
actor’s topology may be out of sync with the actor’s view
of its topology. This differs radically from previous work on
distributed object cycle detection, where objects must either
be immutable or cycle detection must monitor mutation [26–
28].
Our technique uses the message passing paradigm at the
heart of the actor-model: when an actor blocks, it sends a
snapshot of its view of its topology to the cycle detector.
The cycle detector in turn detects cycles based on its view of
the topology of blocked actors. Because the cycle detector
operates on its own view of the blocked actor topology rather
than stopping execution or monitoring mutation, cycles may
be detected based on a view of the topology that is out of
date. This is overcome with a confirmation protocol that
allows the cycle detector to determine whether or not its
view of the blocked actor topology is the same as the true
topology, without stopping execution, monitoring mutation,
or examining any actor’s heap.
Contributions The key contribution of this paper is a system for efficient concurrent garbage collection of actors.
More specifically, we present:
• An informal explanation of Message-based Actor Collec-

tion (MAC).

• A formal model of garbage collection with MAC ex-

pressed through an operational semantics.
• A proof of soundness for MAC.
• Preliminary performance results which indicate MAC has

a small overhead over manual collection - if any.
Garbage collection systems are often presented without
soundness proofs [8, 9, 16, 18, 26–28]. Where proofs are
provided, they often do not address cyclic garbage [24] or
mutation [22, 23], or require synchronous collection [10].
We developed suitable abstractions to be able to make our
soundness proof. These abstractions also helped us develop
a simpler presentation of protocol based on the consistency
of the perceived topologies.
Outline We discuss the background on garbage collection
of actors in section 3. We present the design of our system informally in section 4, formalise it in section 5, and
provide a proof of soundness in section 6. We report on our
implementation in section 7, and conclude and discuss further work in section 8.

2.

Motivation

Even though actors are extensively used in the distributed
setting, they can address massively concurrent programming, a major challenge currently, attracting a significant
amount of research. Moreover, actors are often used without
distribution. For example, in [11] the software from repository [12] is studied. From around 750 programs, 16 are
isolated as representative of "real-world actor programs". Of
these, only 7 are distributed applications. Of these 7, only 3
use remote actors for distributed computation.
Within the concurrent setting, our work is best applicable
to the style of concurrency where a multitude of lightweight
actors are continuously created and discarded, rather than
where actors are a few large entities that logically persist
during program execution (e.g. vats). Applications of the
latter style have less need for actor GC. Applications of the
former style of concurrency are encountered in, for example,
trading applications, social simulations, and network traffic
analysis, and motivate the need to reclaim actors. Our system
is currently in use in such an application (cf. section 7).
Moreover, such a style of concurrency will be supported by
the many cores forecast in hardware development [13].

3.

Background on Garbage Collection of
Actors

Actor Collection Existing actor-model languages and libraries use three approaches to garbage collection of actors.
The first approach is to require the programmer to manually terminate actors. Many existing actor-model languages
and libraries, such as Erlang [3], Scala [4], AmbientTalk [5],
SALSA 2.0 [6], Kilim [7], and Akka, do not garbage collect actors at all. All of these except Kilim support actors on

distributed nodes, although only SALSA supports manual
migration of actors to new nodes. None support distributed
scheduling or automatic migration.
The second approach is to transform the actor graph into
an object graph and use a tracing garbage collector to collect
actors [8–10], as done in ActorFoundry [14]. This requires
shared memory, cache coherency, and a stop-the-world step.
This approach allows actors to be collected using the same
collector used for passive objects, but cannot be used across
distributed nodes.
The third approach, used in SALSA 1.0 [15], uses reference listing (whereby an actor keeps a complete list of
every other actor that references it) and monitoring of actor
mutation to build conservative local snapshots which are assembled into a global snapshot. This requires write barriers
for actor mutation (which requires shared memory and cache
coherency), a global synchronisation agent, and coordination of local snapshots within an overlapping time range.
These snapshots are used with the pseudo-root algorithm,
which additionally requires acknowledgement messages for
all asynchronous messages, inverse reference listing, and
a multiple-message protocol for reference passing [16–18].
Like SALSA 2.0, SALSA 1.0 supports distributed nodes and
manual actor migration.
None of these approaches provides a fully concurrent
method for garbage collection of actors.
Distributed Passive Object Collection The literature on
distributed passive object collection is vast, and so we will
only briefly mention key differences. Our approach has been
inspired not just by previous work in actor collection, but
also by work in concurrent cycle detection [23] and distributed reference counting [22, 24–28] for passive object
collection. Some of these approaches do not address cyclic
garbage [24, 25]. Others require either immutable passive
objects or a synchronisation mechanism between the cycle
detector and the mutator, which makes them inapplicable to
actor collection [22, 23, 26–28].
MAC differs significantly from previous work. Unlike
distributed passive object collection, no restrictions on actor
mutation or monitoring of mutation are required in order to
detect cyclic garbage, and no reference listing, indirection
cells, or diffusion trees (a technique whereby nodes keep a
trail of object references they have passed, which can lead
to zombie nodes) are required. Unlike the pseudo-root approach, acknowledgement messages are only required when
actors are actually collected, no reference listing is required,
no message round-trips are required, and no snapshot integration or time ranges are required. As a result, MAC requires
significantly less overhead. Because MAC does not require
thread coordination or cache coherency, it does not become
less efficient as core count increases.
Some approaches to distributed passive object collection
are fault-tolerant [21]. In order to make distributed garbage
collection fault-tolerant, it is necessary to detect and handle

failure and often also to track a global view of time. Our
work is targeted at the many-core environment rather than
the distributed environment and relies on guaranteed message delivery, which obviates the need for failure detection.
In addition, our reliance on causal messaging (cf. section 4)
obviates the need for a global view of time.

4.

Message-based Actor Collection

In this section we explain Message-based Actor Collection
(MAC) informally. We introduce our additions on top of the
actor-model, including causal messaging, external sets for
tracking potentially reachable actors, and the reference count
invariant and the protocol for maintaining it. We also introduce our cycle detector, including perceived cycles for detecting possible cycles, and the conf-ack protocol for confirming perceived cycles. The operational semantics of MAC
are formalised in section 5, and a proof of soundness is
provided in section 6.
Actors The actor-model stipulates that an actor can [1, 2]:
1. Send a finite number of asynchronous, buffered messages
to other actors, with guaranteed delivery but no ordering
or fairness guarantees.
2. Select a behaviour to be executed in response to the next
message.
3. Create a finite number of new actors.
We additionally require that an actor’s message queue is
FIFO ordered, and message delivery is causal (defined below). Moreover, each actor has a local heap. In this paper,
we are only concerned with actor references, but in general
the heap would also contain passive objects, and an actor
would have a stack while performing local execution.
Application Messages We model application-level messages as a single message type (APP) that allows an actor
ι1 to send a set of actors ιs to another actor ι2 . In general,
there would be multiple application message types, which
could contain passive objects as well as actors.
Topology The true topology of the system is the directed
graph of actor reachability. Because actors execute concurrently, it is not possible to efficiently track the true topology.
Instead, each actor maintains a view of its own topology,
consisting of a reference count (indicating the number of incoming graph edges) and an external set of potentially reachable actors (the outgoing edges).
The actor’s view can disagree with the true topology.
When an actor ι1 sends a reference to itself to another actor
ι2 , it can immediately update its reference count, maintaining agreement with the true topology. However, if ι2 drops
its reference to ι1 , ι2 cannot directly mutate ι1 ’s reference
count. Now ι1 ’s reference count is out of sync. To correct
this, ι2 sends a reference count decrement message (DEC)
to ι1 . When ι1 processes that message, it updates its view to
restore agreement with the true topology.

Similarly, if ι2 sends a reference to ι1 to a third actor ι3 , it
first sends a reference count increment message (INC) to ι1 .
This INC represents the reference to ι1 held by the message.
These INC and DEC messages allow the actor’s view
of its topology to be eventually consistent with the true
topology.
Deferred Reference Counting The external set is an overapproximation of the set of actor references contained in
some actor’s heap. It differs from the heap in order to allow
reference counting to be lazy. Rather than tracking all references from ι1 to ι2 , a single reference exists if ι2 appears
one or more times in ι1 ’s heap. The external set contains
all actors that have been in the actor’s heap or received in a
message since the last local garbage collection cycle. When
an actor performs local garbage collection, the external set
is compacted so as to contain only the actors remaining in
the heap. Actors removed from the external set when it is
compacted represent dropped references, and are sent DEC.
Similarly, when an actor ι1 receives another actor ι2 in a
message, ι1 adds ι2 to its external set. If ι2 is not present
in ι1 ’s external set, the reference held by the message is
transferred to ι1 and ι2 ’s view of its topology remains in
agreement with the true topology. If ι2 is already present in
ι1 ’s external set, ι1 already has an outgoing edge to ι2 . To
maintain the reference count invariant of ι2 , ι1 sends DEC
to ι2 , which allows ι2 to eventually update its view of its
own topology.
Our approach is based on, but differs from, deferred increments [19], where ephemeral reference count updates can
be skipped, and update coalescing, where redundant reference count updates are combined for efficiency [20]. In
our work, reference counts are not updated when references
are created or destroyed on the stack or in the heap, but
only when references are sent in messages and when local
garbage collection indicates no references to an actor remain
in a heap. The messages act as the mechanism for deferring
increments and the external set in combination with local
garbage collection acts as the mechanism for coalescing updates.
Cycle Detection As in any reference counting system, cyclic garbage cannot be collected by reference counting alone.
Our system uses a cycle detector that has a message queue
like an actor, and can both send and receive messages.
When an actor has no pending messages on its queue, it
is blocked. When an actor blocks, it sends a block message
(BLK) to the cycle detector containing the actor’s view of its
topology, i.e. its reference count and its external set. When
a blocked actor processes a message, it becomes unblocked
and sends an unblock message (UNB) to the cycle detector,
informing the cycle detector that its view of that actor’s
topology is invalid and that actor is no longer blocked.
This allows the cycle detector to maintain a view of the
topology of all blocked actors that is eventually consistent

with each actor’s view of its topology, which is in turn
eventually consistent with the true topology.
It would be possible but not efficient for application
actors to perform cycle detection when no messages are
pending on their queue (i.e. just before blocking): this would
require every actor in the system to maintain a view of every
other actor’s topology, which for n actors would require n
messages upon each block and unblock and duplication of
blocked actor topology in every actor. A separate cycle detector reduces this to one message upon block or unblock
regardless of the number of actors.
Dead Actors An actor is dead if it is blocked and all
actors that have a reference to it are blocked, transitively.
Because messaging is required to be causal (defined below),
a blocked actor with a reference count of zero is unreachable
by any other actor and is therefore dead (acyclic garbage).
For cyclic garbage, the cycle detector uses a standard
cycle detection algorithm to find isolated cycles in its view of
the topology of blocked actors. However, the cycle detector’s
view of the topology may disagree with an actor’s view of
its topology (when a BLK or UNB message is on the cycle
detector’s queue but as yet unprocessed), and the actor’s
view of its topology may in turn disagree with the true
topology (when an INC or DEC message is on the actor’s
queue but as yet unprocessed). If cyclic garbage is detected
on the basis of a view of the topology that disagrees with
the true topology, that cycle must not be collected. We call a
cycle that has been detected a perceived cycle and a cycle
that has been detected using a view of the topology that
agrees with the true topology a true cycle.
Example 1. A perceived cycle that is not a true cycle. This
is shown in figure 1.
1. Given three actors (ι1 , ι2 and ι3 ), ι1 and ι2 reference each
other and ι2 and ι3 reference each other.
2. ι1 blocks, sending BLK (ι1 , 1, {ι2 }) to the cycle detector.
When the cycle detector processes this, its view of the
topology becomes [ι1 7→ (1, {ι2 })].
3. ι2 wishes to send a reference to ι1 to ι3 . It sends INC to
ι1 and then AP P (ι1 ) to ι3 . ι2 then drops its reference to
ι3 , collects garbage locally, and sends DEC to ι3 . The
cycle detector’s view of the topology does not change.
4. ι3 processes AP P (ι1 ), adding ι1 to its external set. ι3
then drops its reference to ι2 , collects garbage locally,
and sends DEC to ι2 .The cycle detector’s view of the
topology does not change.
5. ι2 processes DEC , then blocks, sending BLK (ι2 , 1, {ι1 })
to the cycle detector. When the cycle detector processes this, its view of the topology becomes [ι1 7→
(1, {ι2 }), ι2 7→ (1, {ι1 })].
6. The cycle detector perceives a cycle {ι1 , ι2 }, even though
ι1 is reachable from ι3 . This is because ι1 has a pending
INC that it has not processed.

(a) Initial state, as in step 1

(c) ι2 sends ι3 ← AP P (ι1 ) and drops ι3 ,
as in step 3

(b) ι1 blocks, as in step 2

(d) ι3 processes AP P (ι1 ) and drops
ι2 , as in step 5

(e) ι2 blocks, as in step 5. The perceived cycle is incorrect due to ι1 ’s
pending INC.

Figure 1: Diagram of example 1. Boxes display the reference count (ρ), and queue (Q) of actors, with round corners indicating
unblocked and square corners indicating blocked. The arrows indicate references, eg. ι1 references ι2 , which implicitly shows
the external set.
Conf-Ack Protocol When a perceived cycle is detected,
the cycle detector must determine whether or not the view
of the topology used to detect the cycle agrees with the
true topology. To do so, we introduce a conf-ack step to our
protocol. When the cycle detector detects a perceived cycle,
it sends a confirm message (CNF) with a token uniquely
identifying the perceived cycle to each actor in the cycle.
When an actor receives CNF, it sends an acknowledgement
message (ACK) with the token to the cycle detector without
regard to the actor’s view of its topology.
If the cycle detector receives ACK from an actor in a perceived cycle without receiving UNB, then that actor did not
unblock between blocking and the detection of the perceived
cycle, which tells us that the actor’s view of its topology
when the perceived cycle was detected was the same as the
cycle detector’s view of that actor’s topology used to detect
the perceived cycle. Such an actor is confirmed. Conversely,

if an actor in a cycle changes state, it will send UNB before it
sends ACK. Because messaging is causal, the cycle detector
will receive the UNB before it receives the ACK. When the
cycle detector receives UNB for an actor, it cancels all perceived cycles containing the newly unblocked actor, since
they were detected with an incorrect view of that actor’s topology.
Further, if all actors in a perceived cycle are confirmed,
then, at the time the cycle was detected, each actor in the
cycle had a view of its topology that agreed with the true
topology. As a result, the perceived cycle is a true cycle and
can be collected.
Example 2. Expanding example 1 with the conf-ack protocol. This is shown in figure 2.
7. The cycle detector sends CNF (τ ) to ι1 and ι2 , where τ
is a token uniquely identifying this perceived cycle.

ates forward: the causes of an effect are also causes for any
secondary effect.
Example 3. Causal messaging.
1. ι1 sends msg1 to ι2 .
2. ι1 sends msg2 to ι3 .
3. After receiving msg2 , ι3 sends msg3 to ι2 .
(a) Cycle detector sends CNF, as in step
6.

4. To preserve causality, ι2 must receive msg1 before msg3 .
Causality is easy to achieve in a many-core setting. Sending
a message and enqueuing it at the destination can be done
with a single atomic operation. As a result, causality is a
natural consequence of lock-free, wait-free FIFO message
queues, and has no overhead.

(b) ι1 unblocks, as in step 8. The perceived cycle is correctly cancelled, as in
step 9.

Figure 2: Diagram of example 2. Boxes display the reference count (ρ), and queue (Q) of actors, with round corners
indicating unblocked and square corners indicating blocked.
The arrows indicate references, eg. ι1 references ι2 , which
implicitly shows the external set.
8. ι1 processes the pending INC from example 1 before
CNF (τ ), due to causal messaging, and sends UNB (ι1 )
to κ.
9. ι1 processes CNF (τ ) and sends ACK (ι1 , τ ) to the cycle
detector.
10. κ processes UNB (ι1 ) before ACK (ι1 , τ ), due to causal
messaging, and correctly cancels the perceived cycle.
Explanation The conf-ack protocol works by providing
the cycle detector with confirmation that the view of the topology used to detect a cycle (which was sent to the cycle
detector as a snapshot of each actor’s view of its topology)
agreed with the true topology when the cycle was detected. This approach allows the cycle detector to work concurrently with other actors, without shared memory, locks,
read/write barriers, cache coherency, or any other form of
thread-coordination.
Causal Messaging In order to maintain the actor’s reference count invariant, message delivery must be causal.
When an actor ι1 sends INC to an actor ι2 before including it in a message to an actor ι3 , ι2 must process that INC
before any DEC message sent by ι3 . Each message is an effect, and every message the sending actor has previously sent
or received is a cause of that effect. Messaging is causal if
every cause is enqueued before the effect. Causality propag-

Consistency Model Our approach requires only weak
memory consistency. In particular, when a message is sent,
all writes to the contents of the message must be visible to
the receiver of the message. This can be implemented with
a release barrier on message send. On the x86 architecture,
this release barrier is implicit on all writes, so no fence is required. Moreover, because MAC requires no shared memory
other than the contents of messages, no consistency model
is necessary for other writes, e.g. when the cycle detector
updates its view of blocked actor topology.

5.

Formal Model

In this section we present a formal model, expressed as an
operational semantics for MAC. Types and identifier conventions are presented in figure 3, and the steps that rewrite the
configuration are presented in figures 4 to 7.
A configuration contains a queue, a cycle detector and a
set of actors. While an actor logically contains its own queue,
we represent the queue as a global entity that maps an actor
ID to a message sequence.
The cycle detector is composed of the cycle detector’s
view of the blocked actor topology (PT), the set of perceived
cycles that are awaiting confirmation (PC), and the next
token that will be used to identify a perceived cycle (τ ). The
cycle detector’s identifier is κ.
Each actor is composed of its identifier, a view of its
topology (ρ and ξ), its heap, and a flag indicating whether
or not it is blocked. We treat an actor’s heap as a set of actor
IDs for convenience, but it stands in for a normal heap.
Messages can be sent and received by actors and the
cycle detector. Each message is composed of a message
identifier and arguments. The APP message represents all
application level messages that are sent by actors, and its
parameter represents the set of actor identifiers included in
the message. All of the other messages are internal. They are
used to describe the protocol, but would not be exposed in a
programming language that used MAC.

cf g ∈
Q ∈

CD
κ
PT
PC
as
a
ι
ιs
ξ
h
ρ
β
τ

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

Conf iguration
Queue
M essage
CycleDetector
CycleDetectorID
P erceivedT opo
P erceivedCycles
Actors
Actor
ID
IDs
ExSet
Heap
Ref Count
Blocked
T oken

= Queue × CycleDetector × Actors
= (ID ∪ {κ}) → (M essage)∗
= AP P (ιs)|IN C|DEC|
BLK(ι, ρ, ξ)|U N B(ι)|CN F (τ )|ACK(ι, τ )
= P erceivedT opo × P erceivedCycles × T oken
=
=
=
=

ID → (Ref Count × ExSet)
T oken → (ID → Boolean)
P(Actor)
ID × Ref Count × ExSet × Heap × Blocked

=
=
=
=
=
=

P(ID)
P(ID)
P(ID)
Integer
Boolean
Integer

Figure 3: Types and identifier conventions
In example 1, the initial configuration looks like this:
cf g1
Q1
CD1
a1
a2
a3

=
=
=
=
=
=

(Q1 , CD1 , {a1 , a2 , a3 }) where
ε
(ε, ε, 0)
(ι1 , 1, {ι2 }, {ι2 }, f alse)
(ι2 , 2, {ι1 , ι3 }, {ι1 , ι3 }, f alse)
(ι3 , 1, {ι2 }, {ι2 }, f alse)

Notation In this paper, we make use of some additional
notation for convenience.
• We treat values in the context of sets as singleton sets, eg.

ξ ∪ ι, ιs \ ι have the expected meaning.
• We use set operations on the domains of mappings.

x ∈ map ⇔ x ∈ dom(map)
map \ {x1 ..xn } , map[x1 7→ ⊥, ..xn 7→ ⊥]
• We use set operations between actors and actor identifi-

ers.
as \ ιs , as \ {a|a = (ι, _, _, _, _) ∧ ι ∈ ιs}
ι ∈ as ⇔ (ι, _, _, _, _) ∈ as
• We use an index operation to examine a queue and an

append operation to modify a queue.
Q(ι)[k] is the k th message on Q(ι).
Q(ι)++msg appends msg to the end of Q(ι).
• We use P ush, P op, and Unblock to manipulate the

queue.
P ush(Q, {ι1 ..ιn }, msg) ,
Q[ι1 7→ Q(ι1 )++msg, ..ιn 7→ Q(ιn )++msg]

P op(Q, ι) , Q0 , msg where Q(ι) = msg : rest and
Q0 = Q[ι 7→ rest]
(
P ush(Q, κ, UNB (ι)) if β
Unblock (Q, ι, β) ,
Q
if ¬β
• We use Closed to refer to a closed cycle of blocked actors

in a perceived topology.



∀ι ∈ ιs :
 ∀ι0 .ι ∈ P T (ι0 ) ↓2 → ι0 ∈ ιs∧ 

Closed(ιs, P T ) ⇔ 


P T (ι) ↓1 =
|{ι0 |ι0 ∈ ιs, ι ∈ P T (ι0 ) ↓2 }|

We guarantee causality with FIFO message queues that
provide both guaranteed and atomic delivery. This is expressed in the operational semantics by using a single operation on the queue (P ush) to both send and enqueue a
message. Using an intermediate container of messages that
have been sent by an actor but not yet enqueued by the receiving actor would make delivery non-atomic, even though
messages would still be FIFO ordered.
We will now discuss the operational semantics.
Actor Local Execution Rather than present a programming language for actors, the rules in figure 4 describe the
effects of local execution on the entities of our protocol. As
usual in concurrency, execution is non-deterministic. In each
rule, the active actor is indicated by (ι, ρ, ξ, h, f alse).
C REATE Create a new actor. The newly created actor a0
has identifier ι0 , a reference count of one (because the
creating actor ι has a reference to it), an empty external
set and heap, and is unblocked. The new actor a0 is added
to the set of actors, and its identifier ι0 is added to the
external set of the active actor.

S END Send an APP message, possibly containing actor IDs,
to another actor ι0 . The active actor first sends an INC
message each actor (other than the sender and the receiver) in ιs, and then sends APP (ιs) to ι0 . If the sender
includes itself in a message, it increments its own reference count.
A DD R EF,D EL R EF Add and delete references to actors in
its local heap, representing heap changes during program
execution.
GC Garbage collect locally, compacting its external set.
Actors that are removed from the external set (i.e. ιs) are
sent DEC.
B LOCK When an actor finishes responding to a message
and has no pending messages, it sends BLK to the cycle
detector with a snapshot of the its topology and sets its
blocked flag to true.
In example 1, step 2 applies rule B LOCK, rewriting the
configuration to:
cf g2
Q2
a01

= (Q2 , CD1 , {a01 , a2 , a3 }) where
= [κ 7→ (BLK(ι1 , 1, {ι2 }))]
= (ι1 , 1, {ι2 }, {ι2 }, true)

It then applies rule R ECV B LK (defined below), rewriting
the configuration to:
cf g3
Q3
CD2

(Q3 , CD2 , {a01 , a2 , a3 }) where

=
= ε
= ([ι1 7→ (1, {ι2 })], ε, 0)

Step 3 then applies rules S END, D EL R EF and GC, rewriting to:
cf g4
Q4
a02

= (Q4 , CD2 , {a01 , a02 , a3 }) where
= [ι1 7→ (IN C), ι3 7→ (AP P (ι1 ), DEC)]
= (ι2 , 2, {ι1 }, {ι1 }, f alse)

Actor Message Receipt As shown in figure 5, an actor can
receive messages regardless of whether or not it is blocked.
An actor can receive four types of message:
R ECVA PP When an actor receives an application message
APP, each actor contained in the message (i.e. ιs) other
than the receiver (i.e. ιs \ ι) that is already present in
the receiving actor’s external set (i.e. (ιs \ ι) ∩ ξ) is sent
DEC. Those not present in the external set are added to
it. A blocked actor that receives APP unblocks.
R ECV I NC When an actor receives INC, it increments its
reference count by one. A blocked actor that receives INC
unblocks.
R ECV D EC When an actor receives DEC, it decrements its
reference count by one. A blocked actor that receives
DEC unblocks.
R ECV C NF When an actor receives CNF, it echoes the token
in the message back to the cycle detector in an ACK

message. A blocked actor that receives CNF does not
unblock.
In example 1, step 4 applies rules R ECVA PP, R ECV D EC,
D EL R EF and GC, rewriting to:
cf g5
Q5
a03

= (Q5 , CD2 , {a01 , a02 , a03 }) where
= [ι1 7→ (IN C), ι2 7→ (DEC)]
= (ι3 , 0, {ι1 }, {ι1 }, f alse)

Step 5 then applies rules R ECV D Ec and B LOCK , rewriting to:
= (Q6 , CD2 {a01 , a002 , a03 }) where
= [ι1 7→ (IN C), κ 7→ (BLK(ι2 , 1, {ι1 }))]
= (ι2 , 1, {ι1 }, {ι1 }, true)

cf g6
Q6
a02

It then applies rule R ECV B LK (defined below), rewriting
to:
cf g7
Q7
CD3

= (Q7 , CD3 , {a01 , a002 , a03 }) where
= [ι1 7→ (IN C)]
= ([ι1 7→ (1, {ι2 }), ι2 7→ (1, {ι1 })], ε, 0)

Cycle Detector Local Execution We now consider the actions of the cycle detector. As shown in figure 6, the cycle
detector can:
D ETECT An isolated cycle of blocked actors is detected and
mapped to a unique token. The actors in the newly detected perceived cycle are initially unconfirmed (mapped to
f alse), and are therefore sent a CNF request.
C OLLECT A dead cycle of confirmed actors is garbage collected. They are removed from the set of actors.
In example 1, step 6 applies part of rule D ETECT, rewriting
to:
cf g8
CD3

= (Q7 , CD3 , {a01 , a002 , a03 }) where
= ([ι1 7→ (1, {ι2 }), ι2 7→ (1, {ι1 })],
[0 7→ [ι1 7→ f alse, ι2 7→ f alse]], 1)

And in example 2, step 7 applies the remainder of rule
D ETECT, rewriting to:
cf g9
Q8

= (Q8 , CD3 , {a01 , a002 , a03 }) where
= [ι1 7→ (IN C, CN F (0)), ι2 7→ (CN F (0))]

Cycle Detector Message Receipt As shown in figure 7, the
cycle detector can receive three types of message:
R ECV B LK The cycle detector maps the actor (ι) to the
topology snapshot (ρ, ξ) in the message.
R ECV U NB The cycle detector removes the actor (ι) from
the map of perceived topology and removes all perceived
cycles that contain the newly unblocked actor.
R ECVACK If the perceived cycle identified by the token
in the message still exists, the acknowledging actor is
confirmed (mapped to true) in that perceived cycle.

ι0 6∈ as
a0 = (ι0 , 1, ∅, ∅, f alse)
(C REATE)
Q, CD, (ι, ρ, ξ, h, f alse) ∪ as → Q, CD, {(ι, ρ, ξ ∪ ι0 , h, f alse), a0 } ∪ as
(
ρ + 1 if ι ∈ ιs
0
0
ι ∈ξ
ιs ⊆ (ξ ∪ ι)
ρ =
ρ
if ι 6∈ ιs
(S END)
Q0 = P ush(Q, ιs \ {ι, ι0 }, IN C)
Q00 = P ush(Q0 , ι0 , AP P (ιs))
Q, CD, (ι, ρ, ξ, h, f alse) ∪ as → Q00 , CD, (ι, ρ0 , ξ, h, f alse) ∪ as
ι0 ∈ ξ ∪ ι
(A DD R EF)
Q, CD, (ι, ρ, ξ, h, f alse) ∪ as → Q, CD, (ι, ρ, ξ, h ∪ ι0 , f alse) ∪ as
ι0 ∈ h
(D EL R EF)
Q, CD, (ι, ρ, ξ, h, f alse) ∪ as → Q, CD, (ι, ρ, ξ, h \ ι0 , f alse) ∪ as
ιs ⊆ {ι0 |ι0 ∈ ξ ∧ ι0 6∈ h}
Q0 = P ush(Q, ιs, DEC)
(GC)
0
Q, CD, (ι, ρ, ξ, h, f alse) ∪ as → Q , CD, (ι, ρ, ξ \ ιs, h, f alse) ∪ as
Q(ι) = ()
Q0 = P ush(Q, κ, BLK(ι, ρ, ξ))
(B LOCK)
Q, CD, (ι, ρ, ξ, h, f alse) ∪ as → Q0 , CD, (ι, ρ, ξ, h, true) ∪ as
Figure 4: Operational semantics of actor local execution

Q0 , AP P (ιs) = P op(Q, ι)
Q = P ush(Q , (ιs \ ι) ∩ ξ, DEC)
Q000 = U nblock(Q00 , ι, β)
(R ECVA PP)
000
0
Q, CD, (ι, ρ, ξ, h, β) ∪ as → Q , CD, (ι, ρ, ξ ∪ (ιs \ ι), h , f alse) ∪ as
00

0

Q0 , IN C = P op(Q, ι)
Q00 = U nblock(Q0 , ι, β)
(R ECV I NC)
Q, CD, (ι, ρ, ξ, h, β) ∪ as → Q00 , CD, (ι, ρ + 1, ξ, h, f alse) ∪ as
Q0 , DEC = P op(Q, ι)
Q00 = U nblock(Q0 , ι, β)
(R ECV D EC)
Q, CD, (ι, ρ, ξ, h, β) ∪ as → Q00 , CD, (ι, ρ − 1, ξ, h, f alse) ∪ as
Q0 , CN F (τ ) = P op(Q, ι)
Q = P ush(Q0 , κ, ACK(ι, τ ))
(R ECV C NF)
Q, CD, (ι, ρ, ξ, h, β) ∪ as → Q00 , CD, (ι, ρ, ξ, h, β) ∪ as
00

Figure 5: Operational semantics of actor message receipt

Closed({ι1 ..ιn }, P T )
P C 0 = P C[τ 7→ [ι1 7→ f alse, ..ιn 7→ f alse]]
(D ETECT)
Q0 = P ush(Q, {ι1 ..ιn }, CN F (τ ))
Q, (P T, P C, τ ), as → Q0 , (P T, P C 0 , τ + 1), as
ιs = {ι1 ..ιn } = dom(P C(τ 0 ))
Q1 = Q
∀i ∈ 1..n.P C(τ 0 )(ιi ) ∧ Qi+1 = P ush(Qi , P T (ιi ) ↓2 \ιs, DEC) (C OLLECT)
Q, (P T, P C, τ ), as → Qi+1 , (P T \ ιs, P C \ τ 0 , τ ), as \ ιs
Figure 6: Operational semantics of cycle detector local execution

Q0 , BLK(ι, ρ, ξ) = P op(Q, κ)
(R ECV B LK)
Q, (P T, P C, τ ), as → Q0 , (P T [ι 7→ (ρ, ξ)], P C, τ ), as
Q0 , U N B(ι) = P op(Q, κ)
P C 0 = P C \ {τ 0 |ι ∈ P C(τ 0 )}
(R ECV U NB)
Q, (P T, P C, τ ), as → Q0 , (P T \ ι, P C 0 , τ ), as
0
0
( Q , ACK(ι, τ ) = P op(Q, κ)
0
P C[τ 7→ P C(τ 0 )[ι 7→ true]] if τ 0 ∈ P C
P C0 =
(R ECVACK)
PC
if τ 06 ∈ P C

Q, (P T, P C, τ ), as → Q0 , (P T, P C 0 , τ ), as
Figure 7: Operational semantics of cycle detector message receipt
In example 2, step 8 applies step R ECV I NC, rewriting to:
= (Q9 , CD3 , {a001 , a002 , a03 }) where
= [ι1 7→ (CN F (0)), ι2 7→ (CN F (0)),
κ 7→ (U N B(ι1 ))]
= (ι1 , 2, {ι2 }, {ι2 }, f alse)

cf g10
Q9
a001

Step 9 applies step R ECV C NF, rewriting to:
cf g11
Q10

= (Q10 , CD3 , {a001 , a002 , a03 }) where
= [ι2 7→ (CN F (0)),
κ 7→ (U N B(ι1 ), ACK(ι1 , 0))]

Step 10 applies step R ECV U NB, rewriting to:
cf g12
Q11
CD4

= (Q11 , CD4 , {a001 , a002 , a03 }) where
= [ι2 7→ (CN F (0)), κ 7→ (ACK(ι1 , 0))]
= ([ι2 7→ (1, {ι1 })], ε, 1)

Completeness If a cycle of blocked actors exists, each
actor will have sent BLK to the cycle detector. The cycle
detector will eventually execute R ECV B LK for each blocked
actor, and will eventually execute D ETECT and begin a confirmation process that will result in executing C OLLECT.
This process is non-deterministic, but it is theoretically possible to detect a cycle as soon as it appears. If all actors are
blocked, the system will find all cycles.
The program terminates when it is not possible to apply
any rule. This occurs when no actors are executing (preventing any actor local execution rules from being applied), the
queue is empty (preventing any actor or cycle detector message receipt rules from being applied), and no cycles are detected (preventing any cycle detector local execution rules
from being applied).
Robustness As presented, MAC is sound and does not have
exceptional conditions. However, the protocol is robust even
if failure is introduced. If the cycle detector fails, cycles of
dead actors will not be collected, but no live actor will be
collected.
If an actor fails, the result depends on whether or not
the cycle detector’s view of the failed actor’s topology is in
agreement with the failed actor’s view of its own topology.

If it is, the failed actor can be considered blocked, and the
system will function normally. If the cycle detector’s view of
the failed actor’s topology is not in sync, then there is no way
to determine what other actors the failed actor referenced.
As a result, actors the failed actor held a reference to will
not receive DEC messages for those references and will not
be collected. However, it remains the case that the cycle
detector will continue to collect other dead cycles, and no
live actor will be collected.
Moreover, failure of actors or the cycle detector does
not jeopardise termination of the overall system. Namely,
collection of all actors is not required in order to reach a
quiescent state where no rules can be applied. This allows
the program to terminate even when some dead actors have
not been collected. As a result, failure results in uncollected
dead actors but does not impact soundness or robustness.
Failure of individual messages, where a message is sent
but not received while future messages from the same sender
are successful, impacts the system differently depending on
the message type. A failed DEC results in an actor with an
excess reference count that will not be collected. A failed
CNF or ACK message that pertains to a dead cycle results
in the failure to collect that dead cycle, but if the message
pertains to a live cycle, there is no impact on the system. A
failed BLK message results in an actor never being collected
if the actor is blocked from that point on, but has no impact
on the system if the actor ever unblocks. A failed APP
message will result in excess reference counts for actors in
the message, with the result that those actors will not be
collected.
The two messages that can impact soundness on failure
are INC and UNB. A failed INC message results in an actor
that has a reference count that is too low. As a result, the
cycle detector may find perceived cycles that are smaller
than the true cycle. If the actors in the perceived cycle are
all blocked, the cycle may be collected while an unblocked
actor retains a reference to a collected actor. A failed UNB
message for an actor in a perceived cycle can cause the
cycle to be incorrectly collected if all other actors in the
cycle are blocked. The sender of the failed UNB message

will now respond with an ACK without having unblocked,
and the cycle detector will incorrectly perceive it as having
confirmed.
However, the actor-model requires guaranteed message
delivery [2]. Failure of an individual message that cannot
be corrected with buffering, retries, or other techniques, can
thus be treated as failure of the sending actor. If a failed message results in all future messages from the sender also failing, no form of failure impacts either soundness or robustness.

6.

Proof of Soundness

Outline To prove soundness, we will show that when every
actor in a perceived cycle has confirmed, the perceived cycle
is a true cycle. To do so, we will show in theorem 1 that if
the cycle detector’s view of the topology of actors in the perceived cycle is the true topology, the perceived cycle is a true
cycle. Then we will show in theorem 2 that when a single
actor confirms, the cycle detector’s view of its topology, the
actor’s view of its topology, and the actor’s true topology
agreed at the time when the perceived cycle was detected.
Finally, we will show in theorem 3 that when every actor
has confirmed, the perceived cycle is a true cycle. We will
present each with an informal proof here. Formal proofs are
presented in the appendix.
As we already said in the introduction, the development
of the soundness proof helped us better understand the algorithm itself and the central role of the relation between the
different views of the topology. Moreover, our initial intuition about the reason the algorithm was correct was slightly
wrong. Namely, instead of the property outlined in theorem
2 above, we thought that only after all actors had confirmed
would we know that the cycle detector’s view coincided with
the true topology. The property from theorem 2 is stronger,
and easier to prove. We believe that the concepts we developed for the proof of MAC will be useful to prove other
protocols as well.
Detailed Arguments In order to express these theorems,
we define T opo as the actor’s view of its topology, T rueT opo
as the true topology based on inspecting the heaps and
queues of all actors, and T rulyClosed as a property of a set
of actors which holds when these actors form a closed cycle
in the true topology. T rueT opo allows only CNF messages
in ι’s queue because all other messages cause an actor to
unblock when they are received. Because a T rulyClosed
cycle encompasses all references to all actors in the cycle, it
is not possible for actors in a T rulyClosed cycle to receive
messages in the future.
Definition 1 (Topology, true topology, and true cycles).
Given cf g = (Q, _, as), we define:
• Heap(ι) , h ⇔ (ι, _, _, h, _) ∈ as
• T opo(ι, cf g) , (ρ, ξ, β) ⇔ (ι, ρ, ξ, _, β) ∈ as


|{ι0 |ι0 ∈ as, ι ∈ Heap(ι0 )}|+
 |{(ι0 , k)|Q(ι0 )[k] = APP (ιs), 



• T rueT opo(ι, cf g) , 
ι ∈ ιs, ι0 ∈ as\ι}|,




Heap(ι) \ ι,
Q(ι) = CNF (_)∗


•

T rulyClosed(ιs, cf g) ⇔
∀ι ∈ ιs : ∀ι0 .ι ∈ Heap(ι0 ) → ι0 ∈ ιs ∧ Q(ι) = ε

For example, after step 3 of example 1, T opo(ι1 , cf g) =
(1, {ι2 }, true), but T rueT opo(ι1 , cf g) = (2, {ι2 }, f alse).
This is because Q(ι1 ) = INC , which both indicates an
additional reference (in this case, from ι3 ) and that ι1 has
pending messages other than CNF, and so will unblock.
We require three things from a well-formed configuration. First, it maintains the reference count invariant that an
actor’s true reference count is equal to the actor’s view of its
own reference count, adjusted for INC and DEC messages
in the actor’s queue. Second, an actor identifier appears only
once in the set of actors. Third, an actor in a perceived cycle
(P C(τ )) is also in the cycle detector’s view of blocked actor
topology (PT).
Definition 2 (A well-formed configuration). We say that a
configuration cf g = (Q, (P T, P C, _), as) is well-formed,
formally W F (cf g), if:


T opo(ι, cf g) ↓1 +
1. T rueT opo(ι, cf g) ↓1 =  |{k | Q(ι)[k] = INC }|− 
|{k | Q(ι)[k] = DEC }|
2. ∀ι.|{a | a ∈ as, a = (ι, _, _, _, _)}| ≤ 1
3. ∀τ ∈ P C.P C(τ ) ⊆ P T
We now define a history of configurations. The history of
configurations is ghost state that we use to denote the times
at which various events took place. A history maps time 0 to
a configuration that contains a single actor.
Definition 3 (History). We define H, a history of configurations.
• H ∈ History = T ime → Conf iguration
• H(0) = (∅, (∅, ∅, 0), {(ι, 0, ∅, ∅, f alse)})
• H(t) → H(t + 1)

Definition 4. We expect every configuration to be wellformed implicitly. The initial configuration is well-formed,
and from lemma 1 in the appendix we know that execution
preserves well-formedness.
With these definitions, we can present our first theorem.
We establish that, for a given perceived cycle, if the cycle
detector’s view of the topology of the actors in the cycle is
the same as their true topology, the perceived cycle is a true
cycle.
Theorem 1 (A PC is truly closed if the CD’s view of the
topology is the true topology). Given a configuration cf g =
(_, (P C, P T, _), _):

∀ι ∈ P C(τ ).(P T (ι), true) = T rueT opo(ι, cf g) ⇒
T rulyClosed(dom(P C(τ ), cf g))
Proof. When the cycle detector detects a perceived cycle
(P C(τ )) based on the cycle detector’s view of the blocked
actor topology (PT), that cycle is closed
(Closed(dom(P C(τ )), P T )). If the cycle detector’s view
of a blocked actor’s topology (P T (ι)) is the same as the
actors true topology (T rueT opo(ι)), then we can substitute
the true topology of the actor for the cycle detector’s view of
the actor’s topology in the definition of Closed. If we do this
for all actors in a perceived cycle, we arrive at the definition
of T rulyClosed for the perceived cycle.
In order to be able to describe at which time certain events
took place, we now define the elements of a configuration,
topology, and events in the configuration history. The queue
at time t in history H is referred to as QtH , and the same
t
t
t
, and astH . An actor ι’s
, τH
, P CH
notation is used for P TH
view of its topology at time t in history H is referred to as
T opotH (ι), and the same notation is used for T rueT opotH ,
ClosedtH and T rulyClosedtH . Similarly, P osttH (ι, msg)
denotes the time at which message msg was posted to actor
ι, ConsumetH (ι, msg) denotes the time at which message
t
(τ ) denotes
msg was consumed by actor ι, and N ewP CH
the time at which the perceived cycle identified by τ was
detected.
Definition 5 (Configuration, topology and events in the history). Given H and t, if H(t) = (Q, (P T, P C, τ ), as) we
define:
• The elements of a configuration at time t: QtH , Q,
t
t
, P C, τ tH , τ , astH , as
, P T , P CH
P TH

• Actor and cycle topology at time t:

T opotH (ι) , T opo(ι, H(t))
T rueT opotH (ι) , T rueT opo(ι, H(t))
t
)
ClosedtH (ιs) , Closed(ιs, P TH

T rulyClosedtH (ιs) , T rulyClosed(ιs, H(t))
• Predicates denoting the times at which events occurred.
t
P osttH (ι, msg) ⇔ Qt−1
H (ι) = q ∧ QH (ι) = q.msg
t
ConsumetH (ι, msg) ⇔ Qt−1
H (ι) = msg.q∧QH (ι) =
q
t−1
t
t
N ewP CH
(τ ) ⇔ τ ∈
/ P CH
∧ τ ∈ P CH
∧
t
t
ClosedH (dom(P CH (τ )))

For example, in example 1, P osttH (ι1 , INC ) indicates the
time when ι2 sends INC to ι1 , and
ConsumetH (ι3 , APP (ιs)) indicates the time when ι3 ret
ceives APP (ιs) from ι2 . Similarly, N ewP CH
(0) indicates
the time when the cycle detector detects the cycle {ι1 , ι2 }.
In the appendix we present a series of short lemmas that
establish the underlying behaviour of the system, revolving

around FIFO message queues and the resultant ordering of
events. Using these definitions and lemmas, we can present
the remaining two theorems. First, we establish that confirmation from a single actor indicates that the confirmed actor’s
view of the its topology was the same as the cycle detector’s
view of that actor’s topology when the perceived cycle was
detected.
Theorem 2 (A confirmed actor implies the CD’s view of
its topology, the actor’s view of its topology, and its true
t
topology agreed when the PC was detected). P CH
(τ )(ι) ⇒
t3
t3
∃t3 ≤ t.N ewP CH (τ ) ∧ (P TH (ι), true) = T opotH3 (ι) =
T rueT opotH3 (ι)
t
Proof. Because actor ι is confirmed (P CH
(τ )(ι)), we know
the cycle detector consumed an acknowledgement message
from ι (∃t5 ≤ t.ConsumetH5 (κ, ACK (ι, τ ))), and therefore
ι consumed a confirmation message from the cycle detector
(∃t4 ≤ t5 .ConsumetH4 (ι, CNF (τ ))) and sent an acknowledgement message in response (P osttH4 (κ, ACK (ι, τ ))).
This in turn means the cycle detector sent the confirmation
message (∃t3 ≤ t4 ∧ P osttH3 (ι, CNF (τ ))), which means the
t3
perceived cycle containing ι was detected (N ewP CH
(τ )).
This implies ι is in the cycle detector’s view of the blocked
t3
), which means the cycle detector contopology (ι ∈ P TH
sumed a block message from ι
(∃t2 ≤ t3 .ConsumetH2 (κ, BLK (ι, ρ, ξ))) and has not consumed an unblock message from ι
0
(∀t0 .t2 ≤ t0 ≤ t.¬ConsumetH (κ, UNB (ι))). This in turn
indicates that ι sent a block message
(∃t1 ≤ t2 .P osttH1 (κ, BLK (ι, ρ, ξ))) and did not send an
unblock message before sending an acknowledgement mes0
sage (∀t0 .t1 ≤ t0 ≤ t4 .¬P osttH (κ, UNB (ι))), which means
ι’s view of its own topology did not change during that
0
time (∀t0 .t1 ≤ t0 ≤ t4 .T opotH1 (ι) = T opotH (ι)). Since
the perceived cycle was detected on the basis of the topology in the block message and was detected before the
acknowledgement message was sent, we know ι’s view of
its topology at the time the perceived cycle was detected
was the same as the cycle detector’s view of ι’s topology
0
t0
(∀t0 .t2 ≤ t0 ≤ t4 .(P TH
(ι), true) = T opotH (ι)).
If ι’s view of its reference count was not the same as its
true reference count (T opotH3 (ι) ↓1 6= T rueT opotH3 (ι) ↓1 ),
then, given the reference count invariant, ι’s queue must
contain either INC or DEC (QtH3 (ι) 3 (INC ∨ DEC ) ).
If that were true, we know that ι would consume INC or
DEC before CNF (τ ), which would mean ι would send an
unblock message before sending an acknowledgement message, which we know to be untrue because ι is confirmed.
Therefore, ι’s view of its reference count is its true reference
count.
If ι’s view of its external set was not the same as its
true external set (T opotH3 (ι) ↓2 6= T rueT opotH3 (ι) ↓2 ), then
ι must have taken a step that rewrites its external set. By
case analysis, ι must unblock to change its external set,

which would mean ι would send an unblock message before
sending an acknowledgement message, which we know to
be untrue because ι is confirmed. Therefore, ι’s view of its
external set is its true external set.
If ι’s view of its blocked state was not the same as its true
blocked state (T opotH3 (ι) ↓3 6= T rueT opotH3 (ι) ↓3 ), the ι’s
queue must contain a message other than CNF (QtH3 (ι) 6=
CNF (_)∗). If this were true, we know that ι would consume
a message other than CNF before CNF (τ ), which would
mean ι would send an unblock message before sending an
acknowledgement message, which we know to be untrue
because ι is confirmed. Therefore, ι’s view of its blocked
state is its true blocked state.
Therefore, for each actor ι in the perceived cycle, the
cycle detector’s view of ι’s topology, ι’s view of its topology
and ι’s true topology agree when the perceived cycle was
t3
t0
detected (∀ι ∈ P CH
(τ ).(P TH
(ι), true) = T opotH3 (ι) =
t3
T rueT opoH (ι)).
We now establish that confirmation from all actors indicates, for every actor in the cycle, that the actor’s view of its
topology is the same as the true topology of the actor. In
combination with theorem 2, this tells us that the cycle detector’s view of the topology of the actors in the cycle is also
the same as the true topology. In combination with theorem
1, this tells us that the perceived cycle is a true cycle and can
be safely collected.
Theorem 3 (A fully confirmed cycle is a true cycle). ∀ι ∈
t
t
t
(τ )))
(τ )(ι) ⇒ T rulyClosedtH (dom(P CH
(τ ).P CH
P CH
Proof. Since every actor in the perceived cycle is confirmed,
we know from theorem 2 that when the perceived cycle
t3
(τ )) every for actor ι in
was detected (∃t3 ≤ t.N ewP CH
the perceived cycle, the cycle detector’s view of the topology of ι, ι’s view of its topology, and ι’s true topology
t3
t3
agreed (∀ι ∈ P CH
(τ ).(P TH
(ι), true) = T opotH3 (ι) =
t3
T rueT opoH (ι)). We know from theorem 1 that P C(τ ) was
therefore truly closed at time t3
t3
(T rulyClosedtH3 (dom(P CH
(τ )))), and a truly closed cycle
can be collected.

7.

Implementation

In this section we discuss the practical implications of implementing MAC. We first report on its current deployment in an
actor runtime deployed at a large financial institution, where
the good performance (linear speedup with the number of
cores) indicates that MAC imposed a negligible performance
overhead. We then discuss implementation considerations
affecting the overhead of MAC, and some implementation
details. Finally, we compare with four benchmarks proposed
for Erlang, Scala, Akka, and libcppa, and find that MAC’s
performance is competitive.
We have implemented message-based actor collection as
part of a runtime library written in C. The library also includes asynchronous messaging, work-stealing scheduling,

memory allocation from per-actor heaps, precise passive object garbage collection, and an extension of the system described in this paper for collecting passive objects that have
been passed or shared across actor heaps.
Actors are currently written in C on top of the runtime.
We do not have a full actor-model programming language
yet. Programming using our library does not offer full type
safety and is thus error prone. However, the library and programs written in C are sufficient to investigate the performance of our approach.
Current deployment The library is currently in use at a
large financial institution as the concurrency core of a highthroughput, low-latency application. The application processes thousands of requests per second under peak usage
and each request potentially creates dozens of new actors.
These actors are short-lived, surviving only for the duration
of the request, which results in regular garbage collection of
actors. The application is relatively long-lived, running for
a week at a time. Performance has been nearly linear with
core count for this application, resulting in approximately a
31.5x speed-up on a 32-core machine. These numbers indicate that hundreds of thousands of actors is a realistic number
for some classes of production software, that short-lived actors are a useful approach to concurrency, and that our implementation of actor collection does not impede performance.
Implementation considerations Causal messaging is guaranteed on a single host (multi- or many-core) using FIFO
ordered message queues with guaranteed atomic delivery, implemented as lock-free wait-free multiple-producer
single-consumer queues. Sending a message requires approximately 10 nanoseconds. Because the only message that
requires an acknowledgement is the confirmation message
from the cycle detector, no message round trips are required
during normal execution. During collection, a round trip is
only required if the actor is indeed ready to be collected,
in which case the CNF message requiring acknowledgment
is the only message on the actor’s queue, resulting in the
fastest possible response. Otherwise, an UNB message associated with an earlier rule execution will be received by the
cycle detector, short circuiting the round trip. As a result, the
overhead of the Conf-Ack protocol is very low.
The overhead of BLK and UNB messages is similarly low,
introducing only an additional 10 nanoseconds of latency
when an actor unblocks and another 10 nanoseconds when
an actor blocks. This cost is only paid when an actor has no
other pending work. An optimisation we have made in the
implementation allows an actor to notify the cycle detector
of a reference count change when it processes INC or DEC
without unblocking, accomplishing with one message what
would otherwise take two.
The formalisation and proof lead directly to an additional optimisation in the implementation: as specified in the
GC rule in the operational semantics, the subset of actors
checked for cycles and the timing of those checks is non-

deterministic. This allows the cycle detector to defer detection, performing orders of magnitude less work. This can be
seen in Table 5, where cycle detection attempts are significantly less common than BLK messages.
Weighted reference counting We have implemented a limited form of weighted reference counting to eliminate some
of the INC and DEC messages required when sending and
receiving APP. This requires the external set to become an
external map. The external map associates actors with numbers, such that each actor can keep a reference weight for
any other actor.
When an actor ι0 receives an APP message containing an
actor ι1 , the reference weight of ι1 in the external map of ι0
is incremented. As a result, when an actor receives an APP
message, it no longer needs to send DEC messages to actors
contained in the message that are already in the receiver’s
external map.
On the other hand, when ι0 sends a reference to ι1 to some
actor ι2 and the reference weight of ι1 in the external map of
ι0 is greater than one, the reference weight is decremented
and no INC message is sent. In that case, we say that a reference to ι1 is split across ι0 and ι2 . However, when ι0 sends a
reference to ι1 to some actor ι2 and the reference weight of
ι1 in the external map of ι0 is one, then an INC message has
to be sent to ι1 , because the single reference cannot be split.
In this case, an INC message with an arbitrary additional reference weight is sent from ι0 to ι1 . This additional reference
weight is added to the reference weight of ι1 in the external
map of ι0 . When ι1 receives the INC message, the additional
reference weight is also added to the reference count of ι1 .
In this way, the number of INC messages required is significantly reduced.
When the heap of ι0 no longer contains a reference to ι1 ,
ι0 sends a DEC message to ι1 that includes the reference
weight of ι1 in the external map of ι0 . When ι1 receives the
DEC message, the reference weight is subtracted from the
reference count of ι1 .
Finally, when an actor blocks, it includes its reference
count and its external map in the BLK message sent to the
cycle detector. The definitions of Closed and T rueT opo are
changed to account for the reference weight in the external
map, and cycle detection proceeds as before.
Benchmarks and preliminary comparisons with Erlang,
Scala, Akka, and libccpa Currently, MAC can collect hundreds of thousands to millions of actors (in various cyclic
topologies) per second on current x64 hardware (2.5 to 3.5
ghz, 4 to 32 cores). In comparison, the pseudo-root approach
used in SALSA 1.0 collects thousands of actors per second
on a dual-processor Solaris machine [16].
We have evaluated programs written against our runtime
library with both manual actor termination and MAC. We
present a summary of preliminary experimental results in
Tables 1 to 4. A break down of cycle detector attempts

Language

Time (s)

Throughput (msg/s)

Erlang OTP

~9

~333,333

Erlang

~7

~428,571

Scala (react)

~9

~333,333

libcppa

~5.5

~545,454

MAC, disable CD

0.24

12,500,000

MAC, normal CD

0.24

12,500,000

MAC, force CD

0.24

12,500,000

Table 1: Message handling: 3 million messages, 2 cores

Language

Time (s)

Throughput (actors/s)

Erlang

~10

~52,429

Scala (react)

~10

~52,429

Scala (Akka)

~18

~29,127

libcppa

~18

~29,127

MAC, disable CD

2.9

180,788

MAC, normal CD

7.5

69,905

MAC, force CD

9.5

55,188

Table 2: Actor creation: 219 actors, 4 cores

Language

Time (s)

Throughput (msgs/s)

Erlang

~16

~1,250,000

Scala (react)

~45

~444,444

Scala (Akka)

~30

~666,666

libcppa

~15

~1,333,333

MAC, disable CD

5.2

3,846,153

MAC, normal CD

5.2

3,846,153

MAC, force CD

5.2

3,846,153

Table 3: Mailbox performance: 20 million messages, 4 cores

Language

Time (s)

Throughput (msgs/s)

Erlang

~125

~400,000

Scala (react)

~120

~416,666

Scala (Akka)

~60

~833,333

libcppa

~80

~625,000

MAC, disable CD

45.7

1,094,091

MAC, normal CD

77.3

646,830

MAC, force CD

78.4

637,755

Table 4: Mixed scenario: 50 million messages plus factorisation, 4 cores

and successes and message counts for each test scenario is
presented in Table 5.
These tests are taken from a series of benchmarks made
available for a collection of existing actor languages and
libraries [29] with publicly available source code [30]. The
benchmarks are designed to stress specific aspects of actormodel languages such as message performance and actor
creation performance. To match the hardware and methodology of the existing benchmark results, we executed the first
test on a 2 core 2.67 GHz i7 and the other three tests on a
4 core 2.27 GHz Xeon, with the average of five runs being
presented. In Tables 1 to 4, we present the results previously
reported in the existing benchmarks [29] and add the results
we obtained for MAC.
For MAC, we present results in three configurations: with
cycle detection disabled, with cycle detection enabled (detecting termination via quiescence), and forcing cycle detection (detecting termination via all actors in the system having been collected). We include test results for forced cycle
detection in order to evaluate worst-case behaviour.
The message handling benchmark spawns a counter actor
and a worker actor. The worker actor sends three million
messages to the counter actor asking it to increment its
counter, followed by a single get-and-reset message retrieving the counter. This tests raw message performance, but not
actor creation or concurrency.
The actor creation benchmark spawns 219 actors, arranged in a doubly-linked tree, forming a single cyclic graph.
This is a good stress test for the cycle detector.
The mailbox performance benchmark spawns a single
receiver and twenty senders, each of which send one million messages to the receiver. This tests concurrent message
performance, as the senders are scheduled simultaneously
across cores.
The mixed scenario spawns twenty rings of fifty actors
each. Each ring sends 500,000 messages around the ring
while a worker actor performs expensive factorisation. This
is repeated five times, resulting in fifty million messages

and 100 factorisation runs. This tests combining expensive
calculation with a heavy message load.
Discussion of preliminary implementation results We
note that all MAC versions perform the same in message
handling and in mailbox performance. This may be so because in both these tests the actors involved are constantly
sending or receiving messages, and as a result they only
block at the end of the test.
The preliminary results are highly encouraging. We chose
to reuse existing benchmarks rather than design new ones
in order to both provide a direct comparison between our
work and existing actor-model languages and libraries and
to avoid inadvertently tailoring benchmarks to our own approach. On the other hand, an aspect that might be underrepresented in these benchmarks is passing references to actors
in messages. We plan to investigate more in future work.

8.

Conclusion and Further Work

We have presented Message-based Actor Collection (MAC),
a system for fully concurrent garbage collection of actors,
including an operational semantics in section 5 and a proof
of soundness in section 6. Specifically, we have addressed
our goals:
1. Soundness: our three theorems show that after completing the conf-ack protocol, a perceived cycle is a true cycle
and can be safely collected.
2. Completeness: our operational semantics show that all
dead actors are eventually collected, allowing the system
to terminate when all actors have been collected.
3. Concurrency: our technique is entirely message-based,
and does not require clocks, timestamps, shared memory,
locking, read/write barriers, or any particular threading
or scheduling system.
The soundness result has been proven for MAC in the manycore setting. To transfer to the distributed setting, we will
need to address the following issues: 1) causal messaging
across distributed nodes, 2) potential message loss, 3) potential node failure.
We plan to fully address these issues in further work,
but we argue here that MAC can be adapted to this setting.
Namely, for (1) nodes can be structured as a tree, which
can efficiently provide communication paths that are always
causal. For (2), we can use a guaranteed delivery network
protocol paired with a buffer of sent messages that can be
used to replay messages when a connection is dropped and
reestablished. This buffer can be reset by lazy, asynchronous acknowledgement of receipt of a batch of messages by
a node. For (3), Erlang-like actor monitors can be coupled
with periodic reference renewal to allow notification of failure and eventual consistency of actor reference counts.
We plan to investigate the application of MAC in a distributed environment. Specifically, we are interested in effi-

Test

CD Attempts

Cycles Collected

APP Msgs

BLK Msgs

UNBLK Msgs

Other MAC Msgs

Message handling

1

1

3,000,000

3

1

11

Actor creation

9

1

1,048,575

707,492

183,205

524,288

Mailbox performance

1

1

20,000,000

21

0

66

Mixed scenario

49

20

50,005,124

50,004,818

49,999,898

10,372

Table 5: Cycle detector and message statistics for tests for MAC, force CD
cient causal messaging across distributed nodes, improving
distributed cycle detection by using multiple local cycle detectors, and robustness in the presence of message, actor, or
node failure.
We also plan to extend this work to collect passive objects that are shared across actor heaps as well as separate
collection of each heap. When an actor finishes handling an
application message (whether or not additional messages are
pending on the queue), that actor has no stack. By extending
MAC so that it uses a message-based system for passive object collection, the point at which an actor finishes handling
an application message establishes a safe-point without instrumentation. This will allow local and distributed passive
object garbage collection without read or write barriers.

Acknowledgements
We are grateful to the anonymous referees for their pertinent
and helpful feedback. We would like to thank the SLURP
reading group at Imperial College London for their extensive
feedback, as well as the anonymous referees at ECOOP and
ESOP for their constructive comments on earlier versions of
this paper. We would also like to thank Harry Richardson
and Andrew McNeil for their helpful discussions of implementation considerations.

References
[1] G. Agha and C. Hewitt. Concurrent programming
using actors: Exploiting large-scale parallelism. In
LNCS 1985.
[2] G. Agha. Actors: A Model of Concurrent Computation in Distributed Systems. MIT Press, 1986.

[7] S. Srinivasan and A. Mycroft. Kilim: Isolation-Typed
Actors for Java (A Million Actors, Safe Zero-Copy
Communication). In ECOOP 2008.
[8] D. Kafura, D. Washabaugh, J. Nelson. Garbage collection of actors. In OOPSLA 1990.
[9] A. Vardhan, G. Agha. Using passive object garbage
collection algorithms for garbage collection of active
objects. In ISMM 2002
[10] Wei-Jen Wang, et al. Actor Garbage Collection Using
Vertex-Preserving Actor-to-Object Graph Transformations. In GPC 2010.
[11] S. Tasharofi, P. Dinges, R. Johnson. Why Do Scala
Developers Mix the Actor Model with Other Concurrency Models? In ECOOP 2013.
[12] http://actor-applications.cs.illinois.
edu/
[13] http://www.gotw.ca/publications/
concurrency-ddj.htm
[14] http://osl.cs.uiuc.edu/af/
[15] C. Varela and G. Agha. Programming Dynamically Reconfigurable Open Systems with SALSA. In
OOPSLA 2001.
[16] Wei-Jen Wang and C. Varela. Distributed Garbage
Collection for Mobile Actor Systems: The Pseudo
Root Approach. In GPC 2006.
[17] Wei-Jen Wang. Distributed Garbage Collection for
Large-Scale Mobile Actor Systems. PhD thesis,
Rensselaer Polytechnic Institute, 2006.
[18] Wei-Jen Wang. Conservative snapshot-based actor
garbage collection for distributed mobile actor systems. In Telecommunication Systems, 2011.

[3] J. Armstrong. A history of Erlang. In HOPL III, 2007.

[19] H. Baker. Minimizing reference count updating with
deferred and anchored pointers for functional data
structures. In ACM SIGPLAN, Sept. 1994.

[4] P. Haller and M. Odersky. Scala actors: Unifying
thread-based and event-based programming. In TCS
2008.

[20] Y. Levanoni, E. Petrank. An On-the-Fly ReferenceCounting Garbage Collector for Java. In OOPSLA
2001.

[5] T. Van Cutsem. Ambient References: Object Designation in Mobile Ad hoc Networks. PhD thesis, Vrije
Universiteit Brussel, 2008.

[21] M. Shapiro, D. Plainfossé. A Survey of Distributed
Garbage Collection Techniques. In IWMM 1995.

[6] C. Varela, G. Agha, Wei-Jen Wang, et al. The SALSA
Programming Language 2.0.0alpha Release Tutorial.
Rensselaer Polytechnic Institute, 2009.

[22] F. Dehne and R. Lins. Distributed Cyclic Reference
Counting. In LNCS 1994.
[23] D. Bacon and V.T. Rajan. Concurrent Cycle Collection in Reference Counted Systems. In ECOOP 2001.

[24] L. Moreau and J. Duprat. A Construction of Distributed Reference Counting. In Acta Informatica 2001.
[25] L. Moreau, P. Dickman, and R. Jones. Birrell’s Distributed Reference Listing Revisited. In TOPLAS
2005.
[26] R. Jones and R. Lins. Cyclic Weighted Reference
Counting Without Delay. In PARLE 1993.
[27] R. Lins. Lazy Cyclic Reference Counting. In JUCS
2003.
[28] A. Formiga and R. Lins. A New Architecture for
Concurrent Lazy Cyclic Reference Counting on
Multi-Processor Systems. In JUCS 2007.
[29] http://libcppa.blogspot.co.uk/search/
label/benchmark
[30] https://github.com/Neverlord/
cppa-benchmarks

A.

Lemmas

Lemma 1. A well-formed configuration progresses to a
well-formed configuration.
• cf g0 → cf g 0 ⇒ W F (cf g 0 )
• W F (cf g) ∧ cf g → cf g 0 ⇒ W F (cf g 0 )

Proof. By case analysis on the rewrite steps that can be applied to a configuration. Applying any step results in another
well-formed configuration.
Lemma 2. A message in a queue implies the message was
posted.
0
QtH (ι) = q.msg.q 0 ⇒ ∃t0 ≤ t.P osttH (ι, msg)
Proof. By induction on t. The last step either appended msg
to the queue, establishing the property, or msg was already
present in the queue, in which case we apply the inductive
hypothesis.
Lemma 3. Consuming a message implies the message was
posted.
0
ConsumetH (ι, msg) ⇒ ∃t0 < t.P osttH (ι, msg)
Proof. Consuming a message at time t requires that QtH (ι) =
0
msg.q, and thus by lemma 2, ∃t0 ≤ t.P osttH (ι, msg).
Lemma 4. Messages are consumed in FIFO order.
0
P osttH (ι, msg) ∧ P ostt+k
H (ι, msg )∧
t0
0
ConsumeH (ι, msg ) ⇒
00
00
∃t .t < t00 < t0 .ConsumetH (ι, msg)
Proof. By induction on t. Given that msg was posted before msg 0 , and, using lemma 3, msg 0 was consumed after
msg 0 was posted, we begin with the configuration at time t,
when msg was posted. The last step consumed msg 0 . The
previous step either consumed msg or msg was not on the
queue. If msg was not on the queue, we apply the inductive
hypothesis.

Lemma 5. Actors that are blocked and have not posted
unblock have not changed their view of their topology.
0
T opotH (ι) ↓3 ∧∀t0 ≥ t.¬P osttH (κ, UNB (ι)) ⇒
0
T opotH (ι) = T opotH (ι)
Proof. By case analysis. We begin with a blocked actor at
time t. No step can be made in which UNB is sent, and the
actor’s view of its topology does not change in any step in
which UNB is not sent.
Lemma 6. Actors that have posted block and have not posted unblock have not changed their view of their topology.
P osttH (κ, BLK (ι, ρ, ξ))∧
0
0
∀t ≥ t.¬P osttH (κ, UNB (ι)) ⇒
00
∀t00 .t ≤ t00 ≤ t0 .T opotH (ι) = T opotH (ι)
Proof. By case analysis. Given lemma 5, only one step (unblocked actors with empty queues) sets an actor’s blocked
state to true, and that step sends BLK .
Lemma 7. Actors in P T have blocked and have not unblocked.
t
ι ∈ P TH
⇒
0
0
t
∃t ≤ t.ConsumeH (κ, BLK (ι, ρ, ξ))∧
00
∀t00 .t0 ≤ t00 ≤ t.¬ConsumetH (κ, UNB (ι))∧
00
t
P TH
(ι) = (ρ, ξ)
Proof. By induction on t. The last step could have consumed
BLK for the actor, establishing the property. It could not
have consumed UNB , since that would remove the actor
from P T . Any other step leaves P T unchanged, and we
apply the inductive hypothesis.
Lemma 8. Actors that are sent CNF must be members of a
perceived cycle that has just been detected and vice versa.
t
t
(τ )
(τ ) ∧ N ewP CH
P osttH (ι, CNF (τ )) ⇔ ι ∈ P CH
Proof. By case analysis. Only one step sends CNF , and that
step detects a new perceived cycle and sends CNF only to
the members of that cycle.
Lemma 9. Actors that send ACK must have consumed
CNF and vice versa.
P osttH (κ, ACK (ι, τ )) ⇔ ConsumetH (ι, CNF (τ ))
Proof. By case analysis. Only one step posts ACK , and that
step consumes CNF for the same token.
Lemma 10. Confirming actors consumed CNF earlier.
ConsumetH (κ, ACK (ι, τ )) ⇒
0
∃t0 ≤ t.ConsumetH (ι, CNF (τ ))
Proof. If ConsumetH (κ, ACK (ι, τ )) then by lemma 3
0
∃t0 .P osttH (κ, ACK (ι, τ )), and thus by lemma 9
00
∃t00 ≤ t.ConsumetH (ι, CNF (τ )).
Lemma 11. The CD consumed ACK for every confirmed
actor in a P C.
0
t
P CH
(τ )(ι) ⇒ ∃t0 ≤ t.ConsumetH (κ, ACK (ι, τ ))

Proof. By case analysis. Only one step maps ι to true in
P C(τ ), and that step consumes ACK (ι, τ ).
Lemma 12. A P C is uniquely identified by its token.
t
t0
N ewP CH
(τ ) ∧ N ewP CH
(τ ) ⇒ t = t0
Proof. By case analysis. Only one step creates a new PC, and
that step uses a unique token. Any PC identified by a given
token is the same PC, created in the same step.

B.

Theorems

Theorem 1 (A PC is truly closed if the CD’s view of the
topology is the true topology). Given a configuration cf g =
(_, (P C, P T, _), _):
∀ι ∈ P C(τ ).(P T (ι), true) = T rueT opo(ι, cf g) ⇒
T rulyClosed(dom(P C(τ ), cf g))
Proof. Assume that:
(A) Closed(dom(P C(τ )), P T )
Expanding the definition of closed, we get:
∀ι ∈ P C(τ ) : ∀ι0 .ι ∈ P T (ι0 ) ↓2 → ι0 ∈ P C(τ )∧
(B)
P T (ι) ↓1 = |{ι0 | ι0 ∈ P C(τ ), ι ∈ P T (ι0 ) ↓2 }|
Given ∀ι ∈ P T (τ ).(P T (ι), true) = T rueT opo(ι, cf g),
we substitute T rueT opo(ι, cf g) for P T (ι) in (B), and get:
(C) ∀ι ∈ P C(τ ) : ∀ι0 .ι ∈ T rueT opo(ι0 , cf g) ↓2 → ι0 ∈
P C(τ ) ∧ T rueT opo(ι, cf g) ↓1 = |{ι0 | ι0 ∈ P C(τ ) ∧ ι ∈
T rueT opo(ι0 , cf g) ↓2 }|
Given (A) and (C), we arrive at the definition of
T rulyClosed(dom(P C(τ )), cf g).
Theorem 2 (A confirmed actor implies the CD’s view of
its topology, the actor’s view of its topology, and its true
t
topology agreed when the PC was detected). P CH
(τ )(ι) ⇒
t3
t3
∃t3 ≤ t.N ewP CH (τ ) ∧ (P TH (ι), true) = T opotH3 (ι) =
T rueT opotH3 (ι)
t
Proof. Given P CH
(τ )(ι) and lemma 11, we get:
(A) ∃t5 ≤ t.ConsumetH5 (κ, ACK (ι, τ ))
From (A) and lemma 10, we get:
(B) ∃t4 ≤ t5 .ConsumetH4 (ι, CNF (τ ))
From (A) and (B) and lemma 3, we get:
(C) ∃t3 ≤ t4 .P osttH3 (ι, CNF (τ ))
From (C) and lemma 8, we get:
t3
t3
(D) ι ∈ P CH
(τ ) ∧ N ewP CH
(τ )
From (D) we get:
t3
(E) ι ∈ P TH
From (E) and lemma 7 we get:
(F1) ∃t2 ≤ t3 .ConsumetH2 (κ, BLK (ι, ρ, ξ))

0

(F2) ∀t0 .t2 ≤ t0 ≤ t.¬ConsumetH (κ, UNB (ι))
t0
(F3) ∀t0 .t2 ≤ t0 ≤ t.P TH
(ι) = (ρ, ξ)
From (F1), (F2) and lemma 3, we get:
(G1) ∃t1 ≤ t2 .P osttH1 (κ, BLK (ι, ρ, ξ))
0
(G2) ∀t0 .t1 ≤ t0 ≤ t4 .¬P osttH (κ, UNB (ι))
From (G1), (G2) and lemma 6, we get:
0
(H) ∀t0 .t1 ≤ t0 ≤ t4 .T opotH1 (ι) = T opotH (ι)
From (F3), (G1) and (H), we get:
0
t0
(I) ∀t0 .t2 ≤ t0 ≤ t4 .(P TH
(ι), true) = T opotH (ι)
t3
t3
If T opoH (ι) 6= T rueT opoH (ι), one of the following
must be true:
(J1) T opotH3 (ι) ↓1 6= T rueT opotH3 (ι) ↓1
Given the reference count invariant, this is only possible
if QtH3 (ι) 3 INC or QtH3 (ι) 3 DEC . If either of these were
true, by lemma 8 and lemma 4, INC or DEC would be
consumed by ι before CNF (τ ), which would mean ∃t0 .t1 ≤
0
t0 ≤ t4 .P osttH (κ, UNB (ι)), which we know from to be
untrue from (G2). Therefore (J1) cannot be true.
(J2) T opotH3 (ι) ↓2 6= T rueT opotH3 (ι) ↓2
By case analysis, ι must unblock to change T opotH3 (ι) ↓2 ,
0
which would mean ∃t0 .t1 ≤ t0 ≤ t4,ι .P osttH (κ, UNB (ι)),
which we know to be untrue from (G2). Therefore (J2)
cannot be true.
(J3) T opotH3 (ι) ↓3 6= T rueT opotH3 (ι) ↓3
From theorem 2, we know
T opotH3 (ι) ↓3 . If ¬T rueT opotH3 (ι) ↓3 , then QtH3 (ι) 6=
CNF (_)∗. If this were true, by lemma 8 and lemma 4, messages other than CNF (_) would be consumed by ι before
0
CNF (τ ), which would mean ∃t0 .t1 ≤ t0 ≤ t4,ι .P osttH (κ, UNB (ι)),
which we know from to be untrue from (G2). Therefore (J3)
cannot be true.
From (J1), (J2) and (J3) we get:
(K) T opotH3 (ι) = T rueT opotH3 (ι)
From (C), (D), (I) and (K), we establish
t3
t3
∃t3 ≤ t.N ewP CH
(τ ) ∧ (P TH
(ι), true) = T opotH3 (ι) =
t3
T rueT opoH (ι).
Theorem 3 (A fully confirmed cycle is a true cycle). ∀ι ∈
t
t
t
P CH
(τ ).P CH
(τ )(ι) ⇒ T rulyClosedtH (dom(P CH
(τ )))
Proof. From theorem 2 and lemma 12, we get:
t3
(A1) ∃t3 .N ewP CH
(τ )
t3
t3
(A2) ∀ι ∈ P CH (τ ).(P TH
(ι), true) = T opotH3 (ι) =
t3
T rueT opoH (ι)
From (A1), (A2) and theorem 1, we establish
t
T rulyClosedtH (dom(P CH
(τ ))).

