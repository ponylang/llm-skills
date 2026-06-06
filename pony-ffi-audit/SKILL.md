---
name: pony-ffi-audit
description: Audit Pony FFI code for capability violations — C functions mutating through non-mutable refcaps. Load before auditing FFI safety.
disable-model-invocation: false
---

# Pony FFI Safety Audit

## The FFI Trust Boundary

Pony's reference capabilities enforce memory safety at compile time, but FFI declarations are trusted. The programmer specifies refcaps in FFI declarations and the compiler takes them at face value. If a C function mutates data through a pointer declared as `tag` or `val` in Pony, the type system's guarantees are silently violated. The compiler won't catch it. The code will compile, run, and corrupt memory safety invariants without warning.

An FFI safety audit finds these violations by examining every FFI call site, determining what C actually does with each argument, and checking whether the Pony refcap permits it.

This audit covers one specific class of FFI hazard: C mutating Pony data through a non-mutable refcap. It does not cover other FFI risks (lifetime and ownership of foreign memory, null handling, ABI or type-width mismatches). And it can't be done from the Pony side alone — determining what a C function writes requires reading the C side of every call, so plan on having that source available before you start.

## Refcap Mutation Rules

| Cap   | Mutation | Safe for C to write through? |
|-------|----------|------------------------------|
| `iso` | yes      | yes |
| `trn` | yes      | yes |
| `ref` | yes      | yes |
| `val` | no       | **no — violation** |
| `box` | no       | **no — violation** |
| `tag` | no       | **no — violation** |

Any FFI call where C mutates data through a `val`, `box`, or `tag` reference is a finding.

## Audit Methodology

The methodology is pattern-agnostic. It catches any violation, not just known patterns.

### Step 1: Find all FFI call sites

Search for `@` prefixed function calls in `.pony` files. These are FFI calls:

```pony
@read(fd, buffer.cpointer(), buffer.size())
@pony_os_sockname(_fd, ip)
```

Also find FFI declarations to understand declared parameter caps:

```pony
use @read[ISize](fd: I32, buffer: Pointer[U8] tag, size: USize)
```

### Step 2: Determine what C mutates

For each FFI call, identify which arguments the C function writes to. This requires knowing the C function's semantics (see "Identifying Mutated Arguments" below).

### Step 3: Check the refcap

For each mutated argument, determine the Pony refcap at the call site. If the refcap is `val`, `box`, or `tag`, it's a violation.

The refcap comes from two places:
- The **call site expression** — what cap does the argument actually have?
- The **FFI declaration** — what cap does the declaration allow?

Both matter. Flag both kinds of problems:
- A specific call site passing a non-mutable cap to a mutating function
- A declaration that *allows* non-mutable caps even when current call sites happen to pass mutable ones (future call sites could pass `tag`)

Also check the **return type of allocation FFI calls**. If an FFI function that allocates a buffer declares its return type as `val` (e.g., `@ponyint_pool_alloc_size[Pointer[U8] val]`), the buffer is born with the wrong cap — C writes into it immediately after allocation, but Pony thinks it's immutable from the start.

### Step 4: Check for escape hatches

Two mechanisms bypass refcap checking entirely:

**`addressof` on a `var`** — `addressof` on a `var` field or `var` local always produces `Pointer[FieldType] ref`, regardless of the enclosing receiver's cap. (It's only legal on a `var` target; `addressof` on a `let` field, a `let` local, or a parameter is a compile error.) A `fun box` method can therefore forge a `ref` pointer to a `var` field via `addressof` and pass it to C for mutation, even though the receiver is `box`:

```pony
fun box get_token(handle: Pointer[None] tag): Bool =>
  // _token is a var field; addressof yields Pointer[Pointer[None]] ref
  // even though the receiver is box
  @OpenProcessToken(handle, rights, addressof _token)
```

**`USize` coercion** — calling `.usize()` on a Pointer converts it to a plain integer, completely bypassing refcap tracking. The FFI system treats `USize` as an integer, not a capability-tracked reference:

```pony
// _ptr is Pointer[U8] — its cap is irrelevant after .usize()
@memmove(_ptr.usize(), src.usize(), count)
```

### Step 5: Classify and report

Report each finding with enough context to understand and fix it:

| Line | FFI Call | Problematic Arg | Refcap | Why |
|------|----------|-----------------|--------|-----|

Group findings by file and project. Summarize with a pattern breakdown table showing how many findings fall into each category.

## Identifying Mutated Arguments

Knowing which arguments a C function writes to is the core skill. Several heuristics help, but none substitute for actually understanding the C function.

**Check C headers for `const` qualifiers.** A `const` pointer parameter is read-only. A non-const pointer parameter *may* be written to (not all are, but it's the first signal).

**Look for `out` parameter naming conventions.** Many C APIs name output parameters `out`, `result`, `buf`, `dst`, or `dest`.

**Know the common C functions:**

| C function | Mutated argument | What it writes |
|------------|------------------|----------------|
| `read` / `_read` | buffer (2nd arg) | file data |
| `recv` / `recvfrom` | buffer (2nd arg) | network data |
| `snprintf` / `_snprintf` | buffer (1st arg) | formatted string |
| `memcpy` / `memmove` | dest (1st arg) | copied bytes |
| `getsockopt` | value buffer (4th arg) | socket option value |
| `WideCharToMultiByte` | output buffer (5th arg) | converted string |

**Know common library functions:**

| Library | Functions | Mutated argument |
|---------|-----------|------------------|
| OpenSSL | `EVP_DigestFinal_ex`, `RAND_bytes`, `SSL_read`, `BIO_read`, `HMAC`, `PKCS5_PBKDF2_HMAC` | output buffer param |
| PCRE2 | `pcre2_substring_copy_*`, `pcre2_substitute_*` | output buffer param |
| Windows | `ReadFile`, `OpenProcessToken` | output buffer / handle param |

**For custom FFI functions**, read the C source. There is no shortcut.

**For Pony runtime functions** (`pony_os_*`, `pony_asio_*`), check the runtime C source in the ponyc repo under `src/libponyrt/` and `src/common/`.

## Known Patterns

These are recurring patterns found across Pony codebases. They're not an exhaustive taxonomy — any mutation through a non-mutable cap is a violation regardless of whether it fits one of these. But these are especially prevalent and worth recognizing.

### `.cpointer()` / `.cstring()` returning `Pointer tag`

The most common pattern. `Array.cpointer()` and `String.cstring()` always return `Pointer[X] tag` regardless of the receiver's refcap. Even when the underlying Array or String is `iso` or `ref` (mutable and exclusively owned), the extracted pointer loses that information. Every FFI call that writes into a Pony-managed buffer goes through a `tag` pointer.

```pony
// data is Array[U8] ref — mutable, writable
// but data.cpointer() returns Pointer[U8] tag — "identity only, no read/write"
// and C writes into this buffer via read()
@read(fd, data.cpointer(), data.size())
```

### Structs declared `tag` in FFI but C writes their fields

FFI declarations use `tag` for struct parameters that C mutates. The Pony object is `ref` at the call site (inside a constructor or `ref` method), but the FFI declaration's `tag` cap means nothing prevents passing a `val` or `tag` reference from another call site.

```pony
// FFI declaration allows tag — too permissive
use @pony_os_sockname[Bool](fd: U32, ip: NetAddress tag)

// Call site passes ref (this is inside a constructor) — actually safe here
// But the declaration would also accept val or tag
@pony_os_sockname(_fd, ip)
```

### Runtime event handles (intentional)

`AsioEventID` is `Pointer[AsioEvent] tag` by design — it's an opaque handle. C mutates internal fields through these handles (`pony_asio_event_set_readable`, `pony_asio_event_destroy`, etc.). This is intentional and internal to the runtime. Auditors should recognize these and classify them separately, not flag them as bugs to fix.

### FFI-allocated buffers returned with wrong refcap

When an FFI function allocates a buffer, its declared return type sets the refcap. If declared as `val`, the buffer is immutable from Pony's perspective even though C immediately writes into it.

```pony
// Returns val — but the buffer gets written to by @get_compiler_exe_directory
use @ponyint_pool_alloc_size[Pointer[U8] val](size: USize)
let buf = @ponyint_pool_alloc_size(path_size)
@get_compiler_exe_directory(buf, path_size)  // writes into a val buffer
```

### FFI declarations using `box` for mutating C functions

Pony finalizers receive `box` receivers, but finalizers often need to free C memory, which requires mutation. The FFI declarations use `box` as a compromise. This is an inherent tension with the Pony runtime.

```pony
// box because this is called from a finalizer
use @ast_free[None](ast: Pointer[_AST] box)
```

## Fix Strategies

**For `.cpointer()` / `.cstring()`**: The proposed fix (not yet implemented) is to change the return type to use viewpoint adaptation (`this->Pointer[A]`), so the pointer carries the receiver's cap. FFI declarations would also need updating to require `ref` for mutated parameters. With both changes, passing a `val` Array's `.cpointer()` to a mutating FFI function becomes a compile-time error. Until that lands there's no per-call-site fix — record these as known, tracked findings rather than reaching for local workarounds that would only obscure them.

**For struct `tag` declarations**: Change the FFI declaration to use the appropriate mutable cap (`ref`) for parameters that C writes to.

**For runtime event handles**: These are intentional. Document but don't change.

**For finalizer `box`**: Inherent runtime tension. Document the compromise. The comment pattern "box is needed as this is called in a finalizer" makes the intent clear.

**General principle**: Fix both the source side (where the pointer/reference is produced) and the sink side (the FFI declaration that accepts it). Fixing only one side doesn't give you compile-time enforcement.

## Reference Material

For a concrete example of what a completed audit looks like (reporting format, classification, summary structure), see `references/audit-example.md`.
