# Variables in Go

## Ways to declare variables in Go

1. **`var` with explicit type**

   ```go
   var age int = 30
   ```

2. **`var` with type inference** (type is inferred from the value)

   ```go
   var age = 30
   ```

3. **Short variable declaration** (`:=`) — only inside functions, not at package level

   ```go
   age := 30
   ```

4. **`var` with no value** — gets the type's zero value

   ```go
   var age int // age == 0
   ```

5. **Multiple variables in one line**

   ```go
   var x, y int = 1, 2
   x, y := 1, 2          // short form
   var x, y = 1, "hi"    // mixed types, inferred
   ```

6. **Grouped declarations** — useful for declaring several related variables together

   ```go
   var (
       host string = "localhost"
       port int    = 8080
       debug bool  = false
   )
   ```

7. **Constants** (`const`) — value fixed at compile time, cannot change

   ```go
   const pi = 3.14159
   ```

## Zero values

A variable declared without an explicit value is set to its type's **zero value**, not `nil`/garbage like some languages:

| Type      | Zero value |
|-----------|------------|
| int/float | `0`        |
| string    | `""`       |
| bool      | `false`    |
| pointer, slice, map, channel, func, interface | `nil` |

## Scope and shadowing

- A variable declared inside a block (`{ }`) is only visible in that block.
- Go allows **shadowing**: a variable in an inner scope with the same name hides the outer one for that scope.

  ```go
  x := 10
  if true {
      x := 20       // shadows outer x
      fmt.Println(x) // 20
  }
  fmt.Println(x) // 10
  ```
- `go vet` / linters will often warn about unused shadowed variables — Go requires every declared local variable to be used, or it's a compile error.

## `iota` — auto-incrementing constants

Used inside a `const` block to generate related constant values without typing each one out:

```go
const (
    Sunday = iota // 0
    Monday        // 1
    Tuesday       // 2
    Wednesday     // 3
)
```

## Type conversions

Go does **not** do implicit/automatic type conversion between different types, even between numeric types — it must be explicit:

```go
var i int = 42
var f float64 = float64(i) // destinationType(variable)
var u uint = uint(f)
```

For converting to/from strings, use the **`strconv`** package:

```go
import "strconv"

n, err := strconv.Atoi("42")       // string -> int
s := strconv.Itoa(42)              // int -> string
f, err := strconv.ParseFloat("3.14", 64) // string -> float64
b, err := strconv.ParseBool("true")      // string -> bool
```

> `string(65)` does **not** give `"65"` — it converts the number as a Unicode code point, giving `"A"`. Always use `strconv` for number↔string conversions, not a raw type conversion.

## Naming conventions

- Use **PascalCase** (exported, visible outside the package) or **camelCase** (unexported, package-private) — Go has no `private`/`public` keywords; capitalization of the first letter controls visibility.
- Capitalize acronyms consistently: `HTTPServer`, `userURL` — not `HttpServer`, `userUrl`.
- Keep names **as short as reasonable**: `i` in a tight loop is fine, but give longer-lived variables (package-level vars, function returns used far from their declaration) more descriptive names — *longer names for longer lives*.
- Avoid repeating the package name in the identifier (`http.Server`, not `http.HTTPServer`).

---

## Summary

- **Naming conventions**
  - Pascal or camelCase
    - Capitalize acronyms (HTTP, URL)
  - As short as reasonable
    - longer names for longer lives
- **Type conversions**
  - `destinationType(variable)`
  - use `strconv` package for strings
