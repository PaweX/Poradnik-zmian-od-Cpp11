# Dodatek - moje FAQ

## `std::move` - czy mogę przenieść obiekt lokalny do globalnego?

Krótka odpowiedź: **tak, możesz przenieść obiekt lokalny do globalnego**, ale **tylko wtedy, gdy globalny obiekt ma gdzie ten zasób przyjąć** (np. przez konstruktor przenoszący lub operator przenoszący).
Natomiast **nie możesz „przenieść życia” obiektu** — jego _czas życia_ pozostaje lokalny.

To jest kluczowa różnica.

***

### 🧩 Co to znaczy w praktyce?

#### ✔️ Możesz przenieść _zasoby_ obiektu lokalnego do globalnego

Przykład:

```cpp
std::string global_s;

void foo() {
    std::string local = "tekst";
    global_s = std::move(local);  // OK — zasób (bufor) przechodzi do global_s
}
```

To działa, bo:

* `global_s` istnieje przez cały czas działania programu,
* `local` istnieje tylko w `foo()`,
* ale **zasób** (np. bufor stringa) może zostać zabrany z `local` i przekazany do `global_s`.

***

#### ❌ Czego NIE możesz zrobić?

Nie możesz „przenieść obiektu lokalnego tak, żeby stał się globalny”.

To nie zadziała:

```cpp
std::string& global_ref;

void foo() {
    std::string local = "tekst";
    global_ref = std::move(local);  // NIE — global_ref nie może wskazywać na lokalny obiekt
}
```

Dlaczego?

Bo **czas życia obiektu się nie zmienia**.\
`local` umrze po wyjściu z funkcji, więc globalny wskaźnik/referencja byłby martwy.

***

#### 🧠 Najważniejsze zasady

**✔️ Możesz przenosić **zasoby** między obiektami o różnych czasach życia**

(np. lokalny → globalny, lokalny → statyczny, lokalny → element kontenera).

**❌ Nie możesz przenosić **czasu życia** obiektu**

Obiekt lokalny zawsze umrze po wyjściu z funkcji.

**✔️ Przenoszenie działa tylko wtedy, gdy globalny obiekt ma odpowiedni operator/konstruktor przenoszący.**

***

#### 🔥 Przykład poprawny i praktyczny

```cpp
#include <string>

std::string global;

void init() {
    std::string tmp = "duży tekst";
    global = std::move(tmp);  // przeniesienie zasobu
}
```

Po wyjściu z `init()`:

* `tmp` jest „valid but unspecified”,
* `global` ma przejęty bufor,
* wszystko jest bezpieczne.

***

#### 🎯 Podsumowanie

> **Tak — możesz przenieść zasoby obiektu lokalnego do globalnego.
> Nie — nie możesz sprawić, żeby lokalny obiekt stał się globalny.**

***

### 🧠 **Co się dzieje w pamięci podczas przenoszenia?**

Załóżmy:

```cpp
std::string local = "bardzo duży tekst";
global = std::move(local);
```

#### **1. Przed przeniesieniem**

W pamięci mamy coś takiego:

```
local:
    +-----------------------+
    | ptr ---> [bufor]     |
    | size = 17            |
    | capacity = 32        |
    +-----------------------+

global:
    +-----------------------+
    | ptr = nullptr         |
    | size = 0              |
    | capacity = 0          |
    +-----------------------+
```

`local` posiada bufor na stercie (heap).\
`global` jest pusty.

***

#### 🚚 **2. Przeniesienie (`std::move`)**

`std::move` robi tylko:

```
static_cast<std::string&&>(local)
```

Czyli mówi kompilatorowi:\
**„traktuj `local` jak rvalue, możesz zabrać jego zasoby”**.

Jeszcze nic nie zmienia w pamięci.

***

#### 🔧 **3. Konstruktor/ operator przenoszący wykonuje właściwą operację**

Dla `std::string` wygląda to mniej więcej tak:

```
global.ptr = local.ptr;
global.size = local.size;
global.capacity = local.capacity;

local.ptr = nullptr;     // lub "" albo coś innego — unspecified
local.size = 0;
local.capacity = 0;      // lub zostaje — unspecified
```

##### **Efekt w pamięci:**

```
global:
    +-----------------------+
    | ptr ---> [bufor]     |  <-- przejęty z local
    | size = 17            |
    | capacity = 32        |
    +-----------------------+

local:
    +-----------------------+
    | ptr = nullptr         |  <-- valid but unspecified
    | size = 0              |
    | capacity = 0          |
    +-----------------------+
```

**Bufor nie został skopiowany.**
**Tylko wskaźnik został przeniesiony.**

***

#### 🧨 **4. Po wyjściu z funkcji `local` jest niszczony**

Ale to już nie ma znaczenia, bo:

* `local` nie ma już bufora,
* destruktor `local` nie zwolni pamięci, bo `ptr == nullptr`,
* bufor jest teraz własnością `global`.

***

#### 🎯 **Najważniejsze: co się dzieje w pamięci?**

##### ✔️ Zasób (np. bufor, uchwyt, plik, mutex, socket) **zmienia właściciela**

Z obiektu źródłowego → do obiektu docelowego.

##### ✔️ Obiekt źródłowy jest „wyczyszczony” do stanu minimalnego

Ale nadal legalnego.

##### ✔️ Nie ma kopiowania danych

Tylko przeniesienie wskaźników lub uchwytów.

##### ✔️ Czas życia obiektu się nie zmienia

Tylko zasoby zmieniają właściciela.

***

#### 🔥 **Dlaczego to jest takie ważne?**

Bo przenoszenie:

* jest **ekstremalnie szybkie** (kilka instrukcji),
* pozwala uniknąć kopiowania dużych danych,
* umożliwia działanie nowoczesnych kontenerów,
* jest fundamentem RAII i `unique_ptr`.

Bez przenoszenia C++ byłby 10× wolniejszy.

***

## Czy `decltype` zastąpiło `typeof`?

W praktyce **tak**, ale z ważnym zastrzeżeniem:

### `typeof` nie było częścią standardu C++03

`typeof` było **niestandardowym rozszerzeniem kompilatorów** (np. GCC, Clang).

Działało tak:

```cpp
typeof(wyrazenie) zmienna;
```

czyli bardzo podobnie do `decltype(wyrazenie)`.

Przykład (GCC, nie C++03 standard):

```cpp
int x = 5;
typeof(x) y = x; // y jest typu int
```

To było wygodne, ale:

* nie działało w MSVC,
* nie działało w standardowym C++03,
* nie miało gwarancji przenośności,
* nie miało precyzyjnych reguł typu jak `decltype`.

***

### Czym różni się `decltype` od `typeof`?

#### 1. **`decltype` jest standardowe (od C++11)**

`typeof` nigdy nie było częścią standardu.

#### 2. **`decltype` ma precyzyjne reguły określania typu**

`decltype` zachowuje:

* referencje,
* const/volatile,
* lvalue/rvalue,
* typ wyrażenia _bez jego wykonywania_.

Przykład:
```cpp
int x = 0;
int& r = x;

decltype(r) a = x; // a jest int&
```

`typeof` w GCC **nie rozróżniał** tak dokładnie kategorii wartości.

#### 3. `decltype` nie wykonuje wyrażenia

To kluczowe dla bezpieczeństwa:

```cpp
int f();

decltype(f()) a; // OK, nie wywołuje f()
```

`typeof` w niektórych implementacjach _mógł_ mieć inne zachowanie.

#### 4. `decltype` działa z wyrażeniami złożonymi

Przykład:
```cpp
decltype((x))  // lvalue → int&
decltype(x)    // int
```

`typeof` nie miało takich subtelnych reguł.

***

### Czy w C++03 dało się jakoś obejść brak `decltype`?

Tak, ale tylko częściowo — za pomocą **szablonów i `sizeof`**:

```cpp
template<typename T>
T& declval();

typedef typeof(sizeof(declval<T>())) wynik;
```

To były bardzo skomplikowane triki metaprogramistyczne, stosowane w bibliotekach typu Boost.TypeOf.

***

### Podsumowanie

> **W C++03 nie istniało `decltype`.**
> Jedynym zbliżonym mechanizmem było niestandardowe rozszerzenie kompilatora `typeof` (np. w GCC), które pozwalało pobrać typ wyrażenia, ale nie było częścią standardu i nie miało precyzyjnych reguł takich jak `decltype` w C++11.

