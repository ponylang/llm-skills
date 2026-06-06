# Example FFI Safety Audit

This is a condensed example showing the structure and reporting format of a completed FFI safety audit. The findings are drawn from real Pony codebases across the ponylang organization.

## Summary

**42 distinct FFI call sites** across **8 projects** pass arguments with `val`, `box`, or `tag` refcaps to C functions that mutate through them. A further category — runtime event-handle mutations through `AsioEventID` — is intentional and counted separately, not as a violation.

| Pattern | Count | Root Cause |
|---------|-------|------------|
| `.cpointer()`/`.cstring()` returns `Pointer tag` for writable buffers | 25 | `Array.cpointer()` and `String.cstring()` always return `tag` regardless of receiver cap |
| Pony objects/structs declared `tag` in FFI but C writes to their fields | 13 | FFI declarations use `tag` for struct parameters that C mutates |
| FFI declarations use `box` for mutating C functions | 4 | Finalizer pattern requires `box`, but the C functions mutate |
| Runtime event handles mutated through `AsioEventID` (`Pointer[AsioEvent] tag`) — *intentional, not counted above* | 5 categories | Intentional — `AsioEventID` is an opaque handle by design |

### Escape hatches discovered

- **`addressof` on a `var`**: Always produces `Pointer[FieldType] ref` regardless of receiver cap. A `fun box` method can forge a mutable-looking pointer to a `var` field via `addressof`.
- **`USize` coercion**: Passing `_ptr.usize()` instead of `_ptr` to FFI, bypassing Pointer refcap checking entirely.

---

## Findings

### `.cpointer()` / `.cstring()` Pattern

#### format/_format_float.pony

| Line | FFI Call | Problematic Arg | Refcap | Why |
|------|----------|-----------------|--------|-----|
| 42 | `@_snprintf(s.cstring(), ...)` | `s.cstring()` (1st arg) | `Pointer[U8] tag` | `snprintf` writes formatted float into buffer |
| 44 | `@snprintf(s.cstring(), ...)` | `s.cstring()` (1st arg) | `Pointer[U8] tag` | Same, non-Windows path |

#### files/file.pony

| Line | FFI Call | Problematic Arg | Refcap | Why |
|------|----------|-----------------|--------|-----|
| 233 | `@_read(_fd, result.cpointer(), ...)` | `result.cpointer()` (2nd arg) | `Pointer[U8] tag` | Windows `_read` writes file data into buffer |
| 235 | `@read(_fd, result.cpointer(), ...)` | `result.cpointer()` (2nd arg) | `Pointer[U8] tag` | POSIX `read` writes file data into buffer |

#### net/tcp_connection.pony

| Line | FFI Call | Problematic Arg | Refcap | Why |
|------|----------|-----------------|--------|-----|
| 921 | `@pony_os_recv(_event, _read_buf.cpointer(...), ...)` | `_read_buf.cpointer(...)` (2nd arg) | `Pointer[U8] tag` | `recv` writes network data into buffer |

#### crypto/digest.pony (ssl project)

| Line | FFI Call | Problematic Arg | Refcap | Why |
|------|----------|-----------------|--------|-----|
| 194 | `@EVP_DigestFinal_ex(_ctx, digest.cpointer(), ...)` | `digest.cpointer()` (2nd arg) | `Pointer[U8] tag` | Writes hash output into buffer |
| 197 | `@EVP_DigestFinalXOF(_ctx, digest.cpointer(), ...)` | `digest.cpointer()` (2nd arg) | `Pointer[U8] tag` | Writes XOF hash output into buffer |
| 199 | `@EVP_DigestFinal_ex(_ctx, digest.cpointer(), ...)` | `digest.cpointer()` (2nd arg) | `Pointer[U8] tag` | Same as line 194, else branch |

#### regex/match.pony (regex project)

| Line | FFI Call | Problematic Arg | Refcap | Why |
|------|----------|-----------------|--------|-----|
| 65-66 | `@pcre2_substring_copy_bynumber_8(_match, i, out.cpointer(), ...)` | `out.cpointer()` (3rd arg) | `Pointer[U8] tag` | Copies captured substring into buffer |

---

### Struct `tag` Pattern

#### files/file_info.pony

| Line | FFI Call | Problematic Arg | Refcap | Why |
|------|----------|-----------------|--------|-----|
| 101 | `@pony_os_stat(from.path.cstring(), this)` | `this` (2nd arg) | `FileInfo tag` (decl) | C writes all file metadata fields into struct |
| 117 | `@pony_os_fstat(fd, path.path.cstring(), this)` | `this` (3rd arg) | `FileInfo tag` (decl) | Same |

Note: `this` is `ref` at the call sites (inside constructors), but the FFI declaration accepts `tag`/`val`.

#### net/tcp_connection.pony

| Line | FFI Call | Problematic Arg | Refcap | Why |
|------|----------|-----------------|--------|-----|
| 539 | `@pony_os_sockname(_fd, ip)` | `ip` (2nd arg) | `NetAddress tag` (decl) | C writes socket address into struct |
| 548 | `@pony_os_peername(_fd, ip)` | `ip` (2nd arg) | `NetAddress tag` (decl) | C writes peer address into struct |

---

### Runtime Event Handles (Intentional)

These are classified separately because `AsioEventID` is `Pointer[AsioEvent] tag` by design — it's an opaque runtime handle.

#### net/tcp_connection.pony

| Lines | FFI Call | Why |
|-------|----------|-----|
| 425, 1095, 1126 | `@pony_asio_event_set_writeable(_event, ...)` | Writes `ev->writeable` |
| 991, 1094 | `@pony_asio_event_set_readable(_event, ...)` | Writes `ev->readable` |
| 624, 637, 1091 | `@pony_asio_event_unsubscribe(event)` | Writes `ev->flags` |
| 645, 668 | `@pony_asio_event_destroy(event)` | Writes fields, frees memory |

---

### FFI-Allocated Buffer with Wrong Refcap

#### tools/pony-doc/main.pony

| Line | FFI Call | Problematic Arg | Refcap | Why |
|------|----------|-----------------|--------|-----|
| 155-156 | `@get_compiler_exe_directory(buf, ...)` | `buf` (1st arg) | `Pointer[U8] val` (from `ponyint_pool_alloc_size` returning `val`) | C writes exe directory path into buffer |

The buffer is allocated by `@ponyint_pool_alloc_size` which is declared as returning `Pointer[U8] val`. The buffer is `val` from birth, but C writes into it immediately after allocation.

Same pattern in `tools/pony-lint/main.pony` and `tools/pony-lsp/pony_compiler.pony`.

---

### Finalizer `box` Pattern

#### pony_compiler/ast.pony

| Line | FFI Declaration | Problematic Param | Refcap | Why |
|------|-----------------|-------------------|--------|-----|
| 17 | `@ast_free(ast: Pointer[_AST] box)` | `ast` | `box` | Writes `ast->frozen`, frees children |

#### pony_compiler/_symtab.pony

| Line | FFI Declaration | Problematic Param | Refcap | Why |
|------|-----------------|-------------------|--------|-----|
| 2 | `@symtab_free(symtab: Pointer[_Symtab] box)` | `symtab` | `box` | Destroys hash table, frees memory |

Comment in source: "box is needed as this is called in a finalizer" — intentional compromise.

---

### Escape Hatches

#### `addressof` bypass

##### files/file_path.pony

| Line | FFI Call | Problematic Arg | Refcap | Why |
|------|----------|-----------------|--------|-----|
| 327 | `@OpenProcessToken(handle, rights, addressof token)` | `addressof token` (3rd arg) | `Pointer[None] tag` (decl) | C writes token handle through pointer |

#### `USize` coercion bypass

##### builtin/string.pony

`_ptr.usize()` is passed to `@memmove` instead of `_ptr`, converting the Pointer to a plain integer and bypassing all refcap checking. All current uses happen to be in `fun ref` methods so the mutation is authorized, but this pattern could mask violations in `box` or `val` contexts.

---

## Observations

The most impactful root cause is `.cpointer()` / `.cstring()` always returning `tag`. Fixing the return type to use viewpoint adaptation (`this->Pointer[A]`) would address 25 of 42 findings at the source, though FFI declarations also need updating to enforce the correct cap at the sink side.
