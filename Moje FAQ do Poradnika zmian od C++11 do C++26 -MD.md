# Poradnik zmian po C++03

Niniejszy poradnik ma na celu przedstawienie i wyjaśnienie wszystkich istotnych zmian,
jakie zaszły w języku C++ od czasów standardu C++03. Obecnie obejmuje on zmiany
wprowadzone w C++11, C++14, C++17, C++20 oraz C++23.

## Cele projektowe C++11:

**Komitet projektowy starał się trzymać kilku kluczowych założeń:**

* Zachowanie stabilności i kompatybilności ze starszym kodem
* Wprowadzanie nowych możliwości przede wszystkim przez bibliotekę standardową, a nie przez rozszerzanie samego języka
* Usprawnianie C++ tak, by lepiej nadawał się do projektowania systemów i bibliotek, a nie tylko do konkretnych aplikacji
* Zwiększenie bezpieczeństwa typów poprzez bezpieczniejsze alternatywy dla wcześniejszych niebezpiecznych idiomów
* Zwiększenie wydajności i możliwości bezpośredniej pracy z hardware’em
* Dostarczanie właściwych rozwiązań dla realnych problemów
* Ułatwienie nauczania i nauki C++ bez odbierania zaawansowanym programistom potrzebnych im mechanizmów

Duża uwaga poświęcona została początkującym, ponieważ większość programistów zawsze będzie na poziomie „średnio-zaawansowanym / początkującym”, a wielu nigdy nie poszerza swojej wiedzy poza wąski wycinek języka, w którym się specjalizują.

***

## Rozszerzenia rdzenia języka C++ (core language)

Jednym z głównych zadań komitetu standaryzacyjnego C++ jest rozwój **rdzenia języka**. W standardach od C++11 wzwyż znacząco ulepszono m.in.:

* wsparcie dla **wielowątkowości**,
* wsparcie dla **programowania generycznego**,
* **jednolitą inicjalizację**,
* oraz **wydajność wykonania**.

### Poprawki wydajności w czasie wykonywania (runtime)

Poniższe funkcje językowe powstały głównie po to, aby poprawić **wydajność czasu wykonania** — zarówno pod względem zużycia pamięci, jak i szybkości obliczeń.

#### Referencje do r‑wartości (rvalue references) i konstruktory przenoszące (move constructors)

##### Tło: jak było w C++03

W C++03 (i wcześniejszych standardach) obiekty tymczasowe — czyli tzw. **r‑wartości** (_rvalues_, bo zwykle pojawiają się po prawej stronie przypisania) — były traktowane tak, jakby miały typ `const T&`.

W praktyce oznaczało to:

* **nie można było ich modyfikować** (przynajmniej w założeniach języka),
* kompilator **nie rozróżniał** ich od zwykłych referencji do stałych (`const T&`),
* w pewnych sytuacjach **dało się je jednak modyfikować** — co było niezamierzoną, ale czasem wykorzystywaną „furtką” językową.

Największy problem: **kosztowne i niepotrzebne głębokie kopiowanie**, które mogło zdarzyć się automatycznie przy przekazywaniu obiektów przez wartość.

***

##### Dlaczego kopiowanie było problemem?

Weźmy `std::vector<T>`. Wewnątrz przechowuje on:

* wskaźnik do tablicy dynamicznej,
* rozmiar,
* pojemność.

W C++03, jeśli funkcja zwracała `std::vector<T>` **przez wartość**, to wyglądało to tak:

1. tworzony był obiekt tymczasowy (r‑wartość),
2. następnie tworzono nowy `std::vector<T>` w miejscu docelowym,
3. **kopiowano wszystkie elementy** z tymczasowego wektora,
4. niszczono obiekt tymczasowy i jego pamięć.

To oznaczało:

* **dużo alokacji**,
* **dużo kopiowania**,
* **dużo czasu straconego na operacje, które nie były potrzebne**.

> **Uwaga:** w C++03 istniała optymalizacja RVO/NRVO (Return Value Optimization), która czasem usuwała to kopiowanie — ale **nie zawsze działała** i nie można było na niej polegać.

***

##### C++11: referencja do r-wartości (`T&&`) i semantyka przenoszenia (move semantics)

C++11 wprowadza nowy typ referencji: **rvalue reference**, zapisywany jako `T&&`.

Pozwala on:

* rozpoznać obiekty tymczasowe,
* **przenosić** zasoby zamiast je kopiować.

***

##### Jak działa przenoszenie?

Dla `std::vector<T>` konstruktor przenoszący:

* przejmuje wskaźnik do tablicy z obiektu tymczasowego,

* ustawia wskaźnik w obiekcie źródłowym na `nullptr`,

* dzięki temu:

  * nie ma kopiowania elementów,
  * tymczasowy obiekt nie zwolni pamięci (bo ma `nullptr`),
  * operacja jest szybka i bezpieczna.

***

##### Automatyczne użycie move

Jeśli funkcja zwraca `std::vector<T>` przez wartość:
```cpp
std::vector<int> makeVec()
{
    return {1, 2, 3};
}
```

to:

* obiekt tymczasowy jest **rvalue**,
* kompilator automatycznie użyje **konstruktora przenoszącego**,
* nie trzeba zmieniać sygnatury funkcji na `std::vector<T>&&` ani pisać dodatkowego kodu.

**Co dokładnie robi konstruktor przenoszący?**
Konstruktor przenoszący `std::vector<T>` może **przenieść** wskaźnik do wewnętrznej tablicy (C‑style array) z obiektu tymczasowego do nowego obiektu docelowego, a następnie ustawić wskaźnik w obiekcie tymczasowym na `nullptr`. Ponieważ obiekt tymczasowy nie będzie już używany, nikt nie spróbuje odczytać tego `nullptr`, a pamięć nie zostanie zwolniona przy jego zniszczeniu. Dzięki temu operacja **omija kosztowne głębokie kopiowanie** i jest bezpieczna oraz niewidoczna dla użytkownika.

> **Uwaga praktyczna:** jeśli używasz starej wersji biblioteki (implementacji zgodnej tylko z C++03), która nie ma konstruktorów przenoszących, wtedy zamiast przeniesienia nastąpi **kopiowanie** (wywołanie konstruktora kopiującego na `const std::vector<T>`), co wiąże się z alokacją pamięci i kopiowaniem elementów.

***

##### `std::move`

* **Nazwane zmienne nigdy nie są rvalue**, nawet jeśli zadeklarowano je jako `T&&`.
* Aby wymusić traktowanie nazwanej zmiennej jak rvalue (czyli umożliwić przeniesienie jej zasobów), używamy:
```cpp
std::move(x);
```

* `std::move` **nie wykonuje przeniesienia** — ono tylko **konwertuje** (poprzez `static_cast`) obiekt do rvalue, co pozwala wywołać konstruktor przenoszący lub operator przenoszący.

**Dodatkowe uwagi o bezpieczeństwie:**

* Po przeniesieniu obiekt źródłowy pozostaje w stanie **określonym, ale nieokreślonym co do wartości** (ang. _valid but unspecified_). Oznacza to, że można go bezpiecznie zniszczyć lub przypisać do niego nową wartość, ale nie należy polegać na jego zawartości.
* Rvalue references są projektowane głównie do obsługi konstruktorów i operatorów przenoszących; modyfikowanie obiektu po przeniesieniu wymaga ostrożności.

Przykład praktyczny:
```cpp
std::string s = "Hello";
std::string t = std::move(s);

// Co jest w s?
// Nie wiadomo. Może być "", może być "Hello", może być coś innego.
// Ale s musi być valid — możesz zrobić:
s = "Nowa wartość";  // OK
```
Najkrótsza możliwa definicja:

> **Obiekt po przeniesieniu jest w stanie poprawnym, ale jego wartości nie wolno używać do żadnych założeń. Możesz go zniszczyć lub nadpisać, ale nie polegać na tym, co w nim zostało.**

***

##### Podsumowanie

###### Po co w ogóle przenosić?

Żeby **uniknąć kosztownego kopiowania dużych zasobów**.

Kopiowanie:

* alokuje nową pamięć,
* kopiuje dane bajt po bajcie,
* jest wolne.

Przenoszenie:

* **zabiera** zasób z obiektu źródłowego,
* **nie kopiuje** danych,
* jest ekstremalnie szybkie (często tylko kilka instrukcji).

To jest różnica między:

* kopiowaniem 1 GB danych,
* a przestawieniem jednego wskaźnika.

***

###### Skąd dokąd się przenosi?

Z **obiektu źródłowego** → do **obiektu docelowego**, zwykle:

* z tymczasowego obiektu (rvalue)

np. `std::string("duży tekst")`

* z obiektu, którego już nie potrzebujesz

np. `std::move(x)`

* z elementu kontenera do innego miejsca

np. podczas `std::vector::push_back`, `emplace_back`, `resize`, `reserve`

**Najprostszy przykład:**
```cpp
std::string s = "bardzo duży tekst...";
std::string t = std::move(s);
```

Co się dzieje?

* `t` **przejmuje** wskaźnik do bufora `s`.
* `s` zostaje w stanie „valid but unspecified”.
* **Nie skopiowano ani jednego znaku**.

To jest powód, dla którego przenoszenie istnieje.

***

###### Dlaczego nie kopiować?

Wyobraź sobie kontener:
```cpp
std::vector<std::string> v;
v.push_back("bardzo duży tekst...");
```

Gdy `vector` się powiększa, musi przenieść wszystkie elementy do nowej pamięci.

Gdyby robił to kopiowaniem:

* każdy element byłby kopiowany,
* każda kopia to alokacja + kopiowanie danych,
* byłoby to _koszmarnie wolne_.

Dzięki przenoszeniu:

* `vector` tylko **przesuwa wskaźniki**,
* operacje są szybkie,
* nie ma zbędnych kopii.

***

###### Przenoszenie jest fundamentem nowoczesnego C++

Bez przenoszenia:

* `std::vector` byłby wolny,
* `std::string` byłby wolny,
* `std::unique_ptr` nie mógłby istnieć,
* `std::optional`, `std::variant`, `std::function` byłyby niepraktyczne,
* biblioteka standardowa byłaby 10× wolniejsza.

Przenoszenie umożliwia:

* RAII,
* zero-cost abstractions,
* nowoczesne API,
* bezpieczne zarządzanie zasobami.

**Najkrótsza odpowiedź**:

> **Przenoszenie pozwala przekazać zasoby z jednego obiektu do drugiego bez kopiowania.
> Jest używane wszędzie tam, gdzie kopiowanie byłoby zbyt wolne lub niemożliwe.

***
_Zobacz też:_
* **`std::move` - czy mogę przenieść obiekt lokalny do globalnego?**
***

##### Perfect forwarding

Połączenie **referencji do r‑wartości** z pewnymi zmianami w semantyce referencji w kontekście szablonów umożliwiło tzw. **perfect forwarding** (**doskonałe przekierowywanie**).

* W praktyce oznacza to, że funkcja szablonowa może **przekazać dalej** otrzymane argumenty do innej funkcji **bez utraty ich kategorii wartości** (czyli bez „zgniecenia” R-value do L-value lub odwrotnie).

* Mechanizm ten wykorzystuje:

  * **forwarding references** (dawniej nazywane _universal references_): parametry szablonowe zadeklarowane jako `T&&` w kontekście dedukcji typu,
  * `std::forward<T>(arg)` do zachowania oryginalnej kategorii wartości przy przekazywaniu.

**Dlaczego to jest przydatne?**
Umożliwia tworzenie funkcji fabrycznych i konstruktorów pomocniczych, które wywołują właściwy konstruktor docelowego typu bez niepotrzebnych kopii. Przykłady w bibliotece standardowej: `emplace_back`, `std::make_unique`, `std::make_shared` — wszystkie korzystają z perfect forwarding, aby przekazać argumenty bezpośrednio do odpowiedniego konstruktora elementu.

***

##### Podsumowanie techniczne (ważne fakty)

* **Temporaries (tymczasowe obiekty)** są automatycznie rvalue — nie trzeba zmieniać typu zwracanego funkcji na `&&`, aby wywołać konstruktor przenoszący.
* **Konstruktor przenoszący** może „ukraść” zasoby (np. wskaźnik do bufora) i ustawić źródło w stanie bezpiecznym (np. `nullptr`), co eliminuje kosztowną alokację i kopiowanie.
* **`std::move`** to narzędzie do konwersji nazwanej zmiennej na rvalue; samo w sobie nie przenosi zasobów.
* **Perfect forwarding** (w połączeniu z szablonami wariadycznymi) pozwala pisać ogólne funkcje, które przekazują argumenty dalej bez strat wydajnościowych.

***

#### `constexpr` – uogólnione wyrażenia stałe

C++ od zawsze rozróżniał **wyrażenia stałe** — wyrażenia, których wartość jest znana i może być obliczona w czasie kompilacji i w czasie wykonywania, np. `3 + 4`. Wyrażenia stałe są okazją do optymalizacji: kompilatory często **wykonują je podczas kompilacji** i **wstawiają wynik na stałe** do wygenerowanego kodu. Ponadto specyfikacja C++ wymaga użycia wyrażeń stałych w niektórych kontekstach (np. przy określaniu rozmiaru tablicy statycznej czy przy wartościach enumeratorów).

##### Problem w C++03

W C++03 nie można było używać wywołań funkcji ani konstruktorów w wyrażeniach stałych, ponieważ kompilator nie miał gwarancji, że funkcja jest rzeczywiście stała:
```cpp
int pobierzTrzy() { return 3; }

int jakasTablica[pobierzTrzy() + 7]; // Utwórz tablicę 10 elementów typu int. Niepoprawny C++ (ill-formed)
```

To nie było poprawne w C++03, ponieważ `pobierzTrzy() + 7` nie jest wyrażeniem stałym. Kompilator C++03 nie miał sposobu, by stwierdzić, czy `pobierzTrzy()` jest rzeczywiście stałe w czasie kompilacji — w teorii taka funkcja mogłaby modyfikować zmienną globalną, wywoływać inne funkcje zależne od stanu programu lub wykonywać operacje niedozwolone w kontekście kompilacyjnym.

***

##### C++11: słowo kluczowe `constexpr`

C++11 wprowadził `constexpr`, które pozwala oznaczyć funkcję, konstruktor lub zmienną jako **możliwą do ewaluacji w czasie kompilacji**:
```cpp
constexpr int pobierzTrzy() { return 3; }

int jakasTablica[pobierzTrzy() + 7]; // Utwórz tablicę 10 elementów typu int. Poprawny C++11
```

Dzięki `constexpr` kompilator może zrozumieć i zweryfikować, że `pobierzTrzy()` jest stałą w czasie kompilacji, i obliczyć jej wynik wtedy, gdy kontekst tego wymaga.

***

##### Co narzuca `constexpr` (wersja C++11) i jak to się rozwinęło

**C++11** — ograniczenia dla funkcji `constexpr`:

* Funkcja `constexpr` **musi** mieć typ zwracany inny niż `void`.
* Ciało funkcji `constexpr` **nie może** deklarować zmiennych lokalnych ani definiować nowych typów; może zawierać tylko deklaracje, puste instrukcje i **jedną** instrukcję `return`.
* Musi istnieć zestaw argumentów, dla których po podstawieniu argumentów wyrażenie w instrukcji `return` daje wyrażenie stałe.

**Przed C++11** wartości zmiennych mogły być używane w wyrażeniach stałych tylko wtedy, gdy były zadeklarowane jako `const`, miały inicjalizator będący wyrażeniem stałym i były typu całkowitego lub wyliczeniowego. **C++11** usunął ograniczenie dotyczące typu — jeśli zmienna jest zadeklarowana jako `constexpr`, nie musi być typu całkowitego ani wyliczeniowego.

**Ewolucja w kolejnych standardach:**

* **C++14** — reguły zostały znacznie poluzowane: `constexpr` może zawierać zmienne lokalne, pętle i instrukcje warunkowe, co pozwala pisać bardziej „normalne” funkcje, które nadal mogą być ewaluowane w czasie kompilacji.
* **C++17** — dodano `if constexpr`, ułatwiające warunkowe generowanie kodu w szablonach (kompilacyjny branching).
* **C++20** — `constexpr` stało się jeszcze bardziej elastyczne; wprowadzono dodatkowo **`consteval`** (funkcja, która **musi** być wykonana w czasie kompilacji) oraz **`constinit`** (zapewnia inicjalizację statyczną bez ukrytej dynamicznej inicjalizacji).

***

##### (C++14): poluzowane ograniczenia `constexpr`

W C++11 funkcje oznaczone jako `constexpr` mogły zawierać jedynie pojedyncze wyrażenie zwracane (`return expression;`), a także `static_assert` i kilka prostych deklaracji.  
C++14 znacząco rozszerza możliwości funkcji `constexpr`, pozwalając wykonywać w czasie kompilacji znacznie bardziej złożone operacje.

Od C++14 funkcje `constexpr` mogą zawierać:

* **Dowolne deklaracje**, z wyjątkiem:
  * zmiennych `static` lub `thread_local`,
  * deklaracji zmiennych bez inicjalizatora.

* **Instrukcje warunkowe**: `if`, `switch`.

* **Pętle**, w tym pętle `for`, `while`, a także pętlę po zakresie (`range‑based for`).

* **Instrukcje modyfikujące obiekty**, pod warunkiem że:
  * obiekt powstał w trakcie ewaluacji stałej (`constexpr`),
  * oraz jego czas życia rozpoczął się w obrębie funkcji `constexpr`.

  Obejmuje to również wywołania nie‑`const` metod oznaczonych jako `constexpr`.

Instrukcja `goto` pozostaje zabroniona w funkcjach `constexpr`.

W C++11 wszystkie niestatyczne metody oznaczone jako `constexpr` były **implicitnie `const`** względem `this`.  
C++14 usuwa to ograniczenie — metody `constexpr` mogą być nie‑`const`.  
Jednak zgodnie z powyższymi zasadami, mogą modyfikować tylko te obiekty, których czas życia rozpoczął się w trakcie ewaluacji stałej.

Poluzowanie ograniczeń `constexpr` w C++14 umożliwia tworzenie bardziej złożonych algorytmów wykonywanych w czasie kompilacji, co stanowi fundament dla dalszych rozszerzeń w C++17 i C++20.

***

##### Różnica między `constexpr` i `consteval` oraz `constinit`

* **`constexpr`** — funkcja, konstruktor lub zmienna **może** być ewaluowana w czasie kompilacji, ale nie jest to obowiązkowe. Jeśli wywołanie ma nie‑stałe argumenty lub kontekst nie wymaga ewaluacji w czasie kompilacji, zachowuje się jak zwykła funkcja wykonywana w czasie działania programu (runtime).  
* **`consteval`** — wywołanie **zawsze** musi być obliczone w czasie kompilacji; wywołanie w kontekście runtime powoduje błąd kompilacji. 
* **`constinit`** — specyfikator dla zmiennych statycznych/plikowych, który **gwarantuje** inicjalizację w czasie kompilacji (statyczną) i zapobiega ukrytej, późnej inicjalizacji dynamicznej; `constinit` nie czyni zmiennej `const`.

Przykład `consteval`:
```cpp
// funkcja musi być ewaluowana w czasie kompilacji
consteval int kwadrat(int x) { return x * x; }

constexpr int a = kwadrat(3); // OK — wywołanie wykonane w czasie kompilacji
int b = kwadrat(4); // Błąd kompilacji: kwadrat() musi być wywołane w czasie kompilacji
```

Przykład `constexpr`:
```cpp
// może być ewaluowane w czasie kompilacji, ale nie musi
constexpr int dodaj(int x, int y) { return x + y; }

int main()
{
    constexpr int c = dodaj(2, 3); // ewaluacja w czasie kompilacji — c == 5
    int p = 10, q = 20;
    int d = dodaj(p, q); // wywołanie w czasie wykonywania — d obliczone w runtime
}
```

Przykład `constinit`:
```cpp
// gwarantuje inicjalizację statyczną, ale nie czyni zmiennej const
constinit int licznik_globalny = 0; // musi być zainicjalizowane statycznie
licznik_globalny = 5; // dozwolone — constinit nie oznacza const
```

**Dodatkowe uwagi praktyczne**

- `constexpr` jest elastyczne i przydatne, gdy chcemy, aby funkcja lub wartość była użyteczna zarówno w kontekstach kompilacyjnych, jak i w runtime.  
- `consteval` stosujemy, gdy wynik **zawsze** musi być znany na etapie kompilacji (np. generowanie stałych parametrów szablonów, walidacje kompilacyjne).  
- `constinit` używamy dla zmiennych statycznych, które muszą być zainicjalizowane w fazie inicjalizacji statycznej programu (bardzo wczesny etap uruchamiania programu w C++, zanim jeszcze zacznie się wykonywanie funkcji main() ), aby uniknąć problemów z kolejnością inicjalizacji (static initialization order fiasco), ale gdy chcemy móc je modyfikować później.  
- `constinit` nie zastępuje `constexpr` — można użyć obu razem tylko wtedy, gdy sens ma jednoczesna statyczna inicjalizacja i stałość (choć `constexpr` zmienna jest już `const`, więc `constinit` z `constexpr` zwykle nie ma sensu).

**Kiedy kompilator wykona ewaluację w czasie kompilacji?**

- Kontekst wymuszający ewaluację: inicjalizacja `constexpr`, rozmiar tablicy wymagający wyrażenia stałego, wartość parametru szablonu nie‑typowego (non-type template parameter), lub inne miejsca, gdzie specyfikacja wymaga wyrażenia stałego.  
- Jeśli kontekst nie wymaga ewaluacji, `constexpr` funkcja może zostać wykonana w runtime; `consteval` nigdy nie — każde wywołanie musi być skompilowane.

**Błędy i diagnostyka**

- Wywołanie `consteval` poza kontekstem kompilacyjnym generuje błąd kompilacji.  
- Wywołanie `constexpr` z argumentami, które nie dają wyrażenia stałego, nie jest błędem — po prostu wynik nie będzie wyrażeniem stałym i obliczenie nastąpi w runtime.  
- `constinit` spowoduje błąd, jeśli inicjalizacja nie jest statyczna (tj. nie może być wykonana w fazie inicjalizacji statycznej).

***

##### Zmienne constexpr

Przed C++11 tylko stałe integralne mogły być używane w stałych wyrażeniach.

C++11 pozwala:
```cpp
constexpr double PRZYSPIESZENIE_GRAWITACYJNE_ZIEMI = 9.8;
constexpr double PRZYSPIESZENIE_GRAWITACYJNE_KSIEZYCA = PRZYSPIESZENIE_GRAWITACYJNE_ZIEMI / 6.0;
```

Zmienne `constexpr`:

* Zmienne oznaczone `constexpr` są **zawsze `const`** i muszą mieć inicjalizator będący stałym wyrażeniem.
* Dzięki C++11 można definiować `constexpr` zmienne nie tylko całkowite.

***

##### `constexpr` dla typów użytkownika i dodatkowe wymagania

* Konstruktory mogą być oznaczone jako `constexpr`, co pozwala tworzyć obiekty typu użytkownika w czasie kompilacji — pod warunkiem, że spełniają wszystkie wymagania `constexpr` obowiązujące w danym standardzie.
* W C11 ciało konstruktora `constexpr` mogło zawierać **wyłącznie deklaracje i puste instrukcje** (czyli nie mogło zawierać instrukcji wykonawczych, deklaracji zmiennych lokalnych ani definicji typów). Od C14/C++20 ograniczenia te zostały znacząco poluzowane.
* Destruktory typów, które mają być używane w kontekście wyrażeń stałych, **muszą być trywialne** — czyli takie, które **nie mają własnego ciała**, **nie wykonują żadnego kodu**, **nie zwalniają zasobów**, **nie są zdefiniowane przez użytkownika**, a ich implementację generuje automatycznie kompilator. Trywialny destruktor jest „pusty” i może zostać całkowicie pominięty podczas ewaluacji kompilacyjnej.
* **Konstruktor kopiujący**, a także inne funkcje członkowskie (np. operatory), w typie posiadającym konstruktory `constexpr` **zwykle również powinny być oznaczone jako `constexpr`**, aby umożliwić zwracanie obiektów przez wartość z funkcji `constexpr` oraz wykonywanie operacji na tych obiektach w czasie kompilacji. Bez tego obiekt mógłby „stracić constexpr‑owość” podczas kopiowania lub operacji.

Przykład:
```cpp
struct Wektor2
{
    double x, y;

    // Konstruktor constexpr — może być używany w czasie kompilacji
    constexpr Wektor2(double x, double y)
        : x(x), y(y)
    {
        // W C++11 ciało konstruktora constexpr nie mogło zawierać
        // żadnych instrukcji wykonawczych — tylko inicjalizator i puste instrukcje.
    }

    // Funkcja członkowska constexpr — może być ewaluowana w czasie kompilacji
    constexpr double norma2() const
    {
        return x * x + y * y;
    }
};
```

**Ograniczenia (C++11):**

* ciało konstruktora `constexpr` może zawierać tylko deklaracje i puste instrukcje,
* destruktor musi być trywialny (czyli generowany automatycznie, bez kodu wykonywalnego).

> Od C14 i C20 zasady są znacznie luźniejsze — można używać zmiennych lokalnych, pętli, instrukcji warunkowych, a destruktory nie muszą już być trywialne, o ile spełniają wymagania ewaluacji kompilacyjnej.

**Zachowanie wywołań `constexpr` z nie‑stałymi argumentami**

Jeżeli funkcja lub konstruktor `constexpr` zostanie wywołany z argumentami, które **nie są** wyrażeniami stałymi, to wywołanie zachowuje się tak, jakby funkcja nie była `constexpr` — jest wykonywane w czasie wykonywania programu, a wynik **nie** jest wyrażeniem stałym. Podobnie, jeśli po podstawieniu argumentów wyrażenie w instrukcji `return` nie daje wyrażenia stałego, wynik nie jest stały.

**Praktyczne przykłady:**

**C++14 pętla w `constexpr`:**
```cpp
constexpr int factorial(int n)
{
    int r = 1;
    for (int i = 2; i <= n; ++i) r *= i;
    return r;
}
constexpr int f6 = factorial(6); // OK w C++14+
```

**C++17 if constexpr:**
```cpp
template<typename T>
constexpr auto id(T x)
{
    if constexpr (std::is_integral_v<T>) return x + 1;
    else return x;
}
```

**C++20 consteval:**
```cpp
consteval int sq(int x) { return x * x; }
constexpr int a = sq(3); // OK
// int b = sq(4); // błąd: sq musi być wywołane w czasie kompilacji
```

**Uwaga o rzeczywistej ewaluacji**

Nawet jeśli funkcja jest oznaczona `constexpr`, kompilator wykona jej obliczenie w czasie kompilacji **tylko wtedy, gdy kontekst tego wymaga** (np. inicjalizacja `constexpr`, rozmiar tablicy, wartość non-type template parameter). `consteval` natomiast wymusza kompilacyjną ewaluację.

**Krótkie podsumowanie**

* **`constexpr`** umożliwia definiowanie funkcji, konstruktorów i zmiennych, które **mogą** być obliczane w czasie kompilacji; reguły były stopniowo poluzowywane od C11 do C20.
* **`consteval`** (C++20) wymusza kompilacyjną ewaluację.
* Mechanizmy `constexpr` i pokrewne są fundamentem wydajnego metaprogramowania, bezpiecznej inicjalizacji statycznej i optymalizacji w nowoczesnym C++.

***

#### Modyfikacja definicji typu POD (plain old data)

W C++03 klasa, struktura lub `union` musiały spełniać wiele sztywnych zasad, aby zostać uznane za **POD** (plain old data).

Typy POD:

* **miały układ pamięci zgodny z językiem C**,
* mogły być **statycznie inicjalizowane**,
* mogły być bezpiecznie kopiowane za pomocą `memcpy`.

Problem polegał na tym, że zasady były **zbyt restrykcyjne**.
Przykład:

Jeśli ktoś miał poprawny typ POD w C++03 i dodał do niego **jedną funkcję wirtualną**, to:

* typ przestawał być POD,
* nie mógł być statycznie inicjalizowany,
* tracił zgodność z C,

mimo że **układ pamięci wcale się nie zmieniał**.

***

C++11 rozwiązał ten problem, dzieląc pojęcie POD na dwa osobne pojęcia:

* **trivial** (typ trywialny),
* **standard-layout** (typ o standardowym układzie pamięci).

Dzięki temu można mieć typ zgodny z C, ale niekoniecznie trywialny — albo odwrotnie.

##### Typ _trivial_ (trywialny)

Typ trywialny:

* może być **statycznie inicjalizowany**,
* można go kopiować przez `memcpy`,
* jego „czas życia” zaczyna się, gdy tylko pamięć zostanie przydzielona (nie czeka na wykonanie konstruktora).

Aby klasa/struct/union była **trivial**, musi:

1. Mieć trywialny konstruktor domyślny (może być `= default;`).
2. Mieć trywialne konstruktory kopiujące i przenoszące.
3. Mieć trywialne operatory przypisania (kopiujące i przenoszące).
4. Mieć trywialny destruktor (nie może być wirtualny).

Dodatkowe zasady:

* konstruktor jest trywialny tylko wtedy, gdy klasa **nie ma funkcji wirtualnych** i **nie ma wirtualnych klas bazowych**,
* operacje kopiowania/przenoszenia są trywialne tylko wtedy, gdy **wszystkie pola niestatyczne** są trywialne.

***

##### Typ _standard-layout_ (standardowy układ pamięci)

Typ standard-layout ma układ pamięci zgodny z językiem C.
Klasa/struct/union jest standard-layout, jeśli:

1. Nie ma funkcji wirtualnych.
2. Nie ma wirtualnych klas bazowych.
3. Wszystkie jej pola niestatyczne mają **ten sam poziom dostępu** (wszystkie publiczne, albo wszystkie prywatne itd.).
4. Wszystkie pola niestatyczne, włącznie z odziedziczonymi, znajdują się w **tej samej klasie** w hierarchii (tzn. nie są rozproszone po różnych poziomach w sposób łamiący regułę).
5. Te zasady muszą być spełnione również przez wszystkie klasy bazowe.
6. Nie ma klasy bazowej tego samego typu, co pierwsze zdefiniowane pole niestatyczne.

***

##### Kiedy typ jest POD?

W C++11 typ (class/struct/union) jest POD, jeśli:

* jest **trivial**,
* jest **standard-layout**,
* wszystkie jego pola niestatyczne i klasy bazowe również są POD.

***

##### Dlaczego to rozdzielono?

Dzięki temu można mieć:

* typ **standard-layout**, ale nie trywialny
  (np. ma skomplikowany konstruktor, ale układ pamięci zgodny z C),

* typ **trivial**, ale nie standard-layout
  (np. ma pola publiczne i prywatne, ale nadal można go kopiować `memcpy`).

To daje programiście dużo większą elastyczność niż w C++03.

***

##### Krótkie przykłady: różnica między typem _trivial_ a _standard-layout_

Poniższe przykłady pokazują, że:

* typ może być **trywialny**, ale **nie** mieć standardowego układu pamięci,
* typ może mieć **standardowy układ pamięci**, ale **nie** być trywialny.

**Przykład 1 — typ trywialny **i** standard-layout**
```cpp
struct Punkt
{
    int wspolrzednaX;
    int wspolrzednaY;
};
// Konstruktor domyślny, kopiujący, przenoszący i destruktor są generowane
// automatycznie i są trywialne. Układ pamięci jest zgodny z C.
```

**Przykład 2 — typ standard-layout, ale _nietrywialny_**
```cpp
struct TypStandardLayoutAleNietrywialny
{
    int poleA;
    int poleB;

    ~TypStandardLayoutAleNietrywialny()
    {
        // Użytkownik zdefiniował destruktor → destruktor nie jest trywialny.
    }
};
// Układ pamięci nadal jest zgodny z C, ale typ nie jest trywialny.
```

**Przykład 3 — typ trywialny, ale **nie** standard-layout**
```cpp
struct TypTrywialnyAleNieStandardLayout
{
public:
    int polePubliczne;

private:
    int polePrywatne;
};
// Wszystkie specjalne funkcje są trywialne, ale różne poziomy dostępu pól
// łamią zasady standard-layout.
```

***

### Ulepszenia wydajności kompilacji w rdzeniu języka

#### `extern template`

W C++03 kompilator **musi** instancjonować szablon za każdym razem, gdy w danej jednostce kompilacji pojawia się jego pełna specjalizacja.
Jeśli ten sam szablon jest używany w wielu plikach `.cpp`, to:

> kompilator generuje jego kod **w każdym pliku osobno**, co może **drastycznie wydłużyć czas kompilacji**.

W C++03 nie dało się temu zapobiec.

C++11 wprowadził rozwiązanie: **`extern template`**, działające podobnie jak `extern` przy zmiennych.

W C++03 wymuszenie instancjonowania wyglądało tak:
```cpp
template class std::vector<MyClass>;
```

W C++11 można napisać:
```cpp
extern template class std::vector<MyClass>;
```

co mówi kompilatorowi:

> „Nie instancjonuj tego szablonu w tym pliku — instancjonacja będzie gdzie indziej”.

To pozwala znacząco skrócić czas kompilacji dużych projektów.

***

### Ulepszenia użyteczności rdzenia języka

Te funkcje mają przede wszystkim **ułatwić korzystanie z języka** — poprawić czytelność, bezpieczeństwo typów i zmniejszyć powtarzalność kodu.

#### Listy inicjalizacyjne

##### Listy inicjalizacyjne w C++03

C++03 odziedziczył listy inicjalizacyjne z języka C.
Struktura lub tablica otrzymuje listę wartości w nawiasach klamrowych `{}`, w kolejności zgodnej z definicją pól w strukturze.
Listy inicjalizacyjne są rekurencyjne — więc tablica struktur lub struktura zawierająca inne struktury może z nich korzystać.

Przykład:
```cpp
struct FloatOrazInt
{
    float pierwsza;
    int druga;
};

FloatOrazInt skalar = { 0.43f, 10 }; // Jeden obiekt, z pierwsza = 0.43f i druga = 10

FloatOrazInt tablicaObiektow[] =
{
    { 13.4f, 3 }, { 43.28f, 29 }, { 5.934f, 17 } // Tablica trzech obiektów
};
```

To jest bardzo przydatne do statycznych list lub inicjalizacji struktury do pewnej wartości.
C++ oferuje też konstruktory do inicjalizacji obiektów, ale często nie są one tak wygodne jak listy inicjalizacyjne.

Jednak w C++03 listy inicjalizacyjne działały **tylko** dla struktur/klas zgodnych z definicją POD (plain old data).

***

##### C++11: listy inicjalizacyjne dla wszystkich klas

W C++11 listy inicjalizacyjne zostały rozszerzone i mogą być używane dla **wszystkich typów**, w tym:

* klas z konstruktorami,
* kontenerów standardowej biblioteki (`std::vector`, `std::map`, …),
* typów użytkownika.

Mechanizm opiera się na szablonie:
```cpp
std::initializer_list<T>
```

Można go użyć w konstruktorze:
```cpp
using std::initializer_list;

class KlasaSekwencji
{
public:
    KlasaSekwencji(initializer_list<int> lista);
};
```

Dzięki temu można tworzyć obiekty w prosty sposób:
```cpp
KlasaSekwencji jakasSekwencja = { 1, 4, 5, 6 };
```

Taki konstruktor nazywa się **konstruktorem listy inicjalizacyjnej** (initializer-list constructor)
i ma specjalne znaczenie podczas tzw. **jednolitej inicjalizacji** (uniform initialization).

***

##### Czym jest `std::initializer_list`?

`std::initializer_list` to pełnoprawny typ biblioteczny w C++11.

Cechy:

* kompilator potrafi tworzyć go automatycznie z `{}` bez podawania typu,
* można go tworzyć jawnie:
```cpp
std::initializer_list<int> lista { 1, 2, 3 };
```

* kopiowanie jest tanie — zwykle implementacja to para wskaźników (`begin`, `end`),
* elementy są **stałe** — nie można ich modyfikować ani przenosić.

***

##### Użycie w zwykłych funkcjach

Nie tylko konstruktory mogą przyjmować `initializer_list`.
Zwykłe funkcje również:
```cpp
using std::initializer_list;

void nazwaFunkcji(initializer_list<float> lista); // Kopiowanie jest tanie; patrz wyżej

nazwaFunkcji({ 1.0f, -3.45f, -0.4f });
```

Standardowe funkcje `std::min` i `std::max` mają wersje przyjmujące `initializer_list`.

***

##### Inicjalizacja kontenerów STL

Od C++11 można wygodnie inicjalizować kontenery standardowe:
```cpp
using std::string;
using std::vector;

vector<string> wektor1 = { "xyzzy", "blabla", "abrakadabra" };
vector<string> wektor2 = vector<string>({ "xyzzy", "blabla", "abrakadabra" });
vector<string> wektor3{ "xyzzy", "blabla", "abrakadabra" }; // zobacz „Ujednolicona inicjalizacja”
```

To ogromne ułatwienie w porównaniu z C++03, gdzie trzeba było ręcznie wywoływać `push_back`.

***

#### Ujednolicona inicjalizacja (Uniform initialization)

C++03 miał wiele problemów związanych z inicjalizacją typów. Istnieje kilka sposobów, aby to zrobić, a niektóre z nich dają różne rezultaty, jeśli zamieni się je miejscami. Tradycyjna składnia konstruktora, na przykład, może wyglądać jak deklaracja funkcji, i trzeba podejmować dodatkowe kroki, aby kompilator — zgodnie z zasadą **most vexing parse** — nie pomylił jej z taką deklaracją.

W C++03 tylko typy \*\*POD\*\* i agregaty mogły być inicjalizowane listami `{ ... }`:
```cpp
JakisTyp zmienna = { /* wartości */ };
```

C++11 wprowadza **ujednoliconą inicjalizację**, która działa dla każdego typu — zarówno struktur, jak i klas z konstruktorami. Rozszerza ona składnię list inicjalizacyjnych i eliminuje wiele niejednoznaczności związanych z wcześniejszymi formami inicjalizacji.

Przykład:
```cpp
struct FloatOrazInt1
{
    int x;
    double y;
};

struct FloatOrazInt2
{
private:
    int x;
    double y;

public:
    FloatOrazInt2(int xParam, double yParam)
        : x{ xParam }, y{ yParam } // inicjalizacja pól za pomocą list inicjalizacyjnych
    {
    }
};

FloatOrazInt1 var1{ 5, 3.2 }; // inicjalizacja jak agregat — każde pole dostaje wartość z listy
FloatOrazInt2 var2{ 2, 4.3 }; // wywołanie konstruktora klasy
```

Inicjalizacja `var1` zachowuje się dokładnie tak, jak gdyby była to inicjalizacja agregatu. Oznacza to, że każdy element danych obiektu będzie po kolei inicjalizowany przez kopiowanie z odpowiadającej mu wartości z listy inicjalizacyjnej. Tam, gdzie to potrzebne, zostanie użyta niejawna konwersja typów. Jeśli taka konwersja nie istnieje albo istnieje tylko konwersja zawężająca, program jest niepoprawny. Inicjalizacja `var2` wywołuje konstruktor.

Jeśli potrzebna jest konwersja typu, kompilator ją wykona — ale **niedozwolone są konwersje zawężające** (np. `double → int` bez jawnego rzutowania).

***

Można też zwracać obiekty za pomocą `{}` bez podawania typu:
```cpp
using std::string;

struct IdString
{
    string nazwa;
    int identyfikator;
};

IdString pobierzString()
{
    return { "foo", 42 }; // kompilator sam dopasowuje typ i tworzy tymczasowy IdString
}
```

##### Uwaga o konstruktorach list inicjalizacyjnych

Jeśli klasa ma konstruktor:
```cpp
TypeName(initializer_list<T>);
```

to **ma on pierwszeństwo** przed innymi konstruktorami, jeśli tylko lista `{}` pasuje typem. Przykład:
```cpp
std::vector<int> vec{ 4 };
```

To **nie** tworzy wektora o rozmiarze 4. Zamiast tego wywoływany jest konstruktor:
```cpp
vector(initializer_list<int>); // tworzy wektor z jednym elementem: 4
```

Aby utworzyć wektor o rozmiarze 4, trzeba użyć klasycznej składni:
```cpp
std::vector<int> vec(4); // poprawnie: wektor o rozmiarze 4
```

***

##### Dodatkowe uwagi i doprecyzowania (ważne dla początkującego)

* **Uniform initialization** ujednolica składnię i pomaga uniknąć „most vexing parse”, ponieważ zapis z nawiasami klamrowymi `{}` nie jest interpretowany jako deklaracja funkcji.
* **Konstruktor listy inicjalizacyjnej** (`initializer_list` constructor) ma priorytet przy dopasowaniu przeciążeń, co może czasem prowadzić do zaskakających wyborów przeciążeń — warto o tym pamiętać przy projektowaniu klas.
* **Narrowing conversions** są zabronione w kontekście list inicjalizacyjnych (np. `double` → `int` bez jawnego rzutowania), co pomaga wykrywać potencjalne błędy utraty informacji już na etapie kompilacji.
* Zwracanie `{ ... }` bez jawnego typu (jak w `return { "foo", 42 };`) działa, ponieważ kompilator wie, jaki typ ma zostać zwrócony i dopasowuje listę do konstruktora docelowego typu.

***

#### Wnioskowanie typów (Type inference)

W C++03 (i w języku C) każda zmienna musiała mieć **jawnie zapisany typ**.
Bywało to problematyczne, szczególnie gdy:

* typ był bardzo złożony (np. tworzony przez szablony),
* typ zwracany przez funkcję był trudny do zapisania,
* używano metaprogramowania szablonowego.

C++11 łagodzi ten problem na dwa sposoby:

* poprzez słowo kluczowe **`auto`**,
* poprzez słowo kluczowe **`decltype`**.

##### `auto`

`auto` pozwala kompilatorowi **wywnioskować typ zmiennej z inicjalizatora**:
```cpp
auto jakisWywolywalnyTyp = std::bind(&jakasFunkcja, _2, _1, jakisObiekt);
// typ jest bardzo złożony — kompilator go zna, ale człowiek nie musi

auto innaZmienna = 5; // typ to int
```

Typ `jakisWywolywalnyTyp` jest dokładnie tym, co zwraca odpowiednia instancja `std::bind` dla podanych argumentów. Kompilator zna ten typ bez problemu, ale użytkownik nie musi.

**Uwaga dla początkującego**

> `auto` **nie oznacza „dowolnego typu”**,
> oznacza: **„kompilator sam wpisze właściwy typ”**.

**Uwaga historyczna**

> W języku **B** (poprzedniku C) słowo `auto` oznaczało _zmienną automatyczną_ (lokalną).
> C++11 **zmienia jego znaczenie** — teraz służy do _wnioskowania typu_.

###### Uzupełnienie (C++17): nowe reguły dedukcji `auto` z listy inicjalizacyjnej

W C++11/14 zapis:
```cpp
auto x = {1, 2, 3};
```

dedukowało typ `std::initializer_list<int>`, co było zaskakujące i prowadziło do błędów.
C++17 rozdziela dwa przypadki:
```cpp
auto a = {1, 2, 3};  // nadal std::initializer_list<int>
auto b{1};           // teraz int (nie initializer_list<int>)
auto c{1, 2};        // błąd kompilacji — niedozwolone od C++17
```

Czyli `auto x{val}` od C++17 deduuje typ bezpośrednio jak `val`, a nie jako listę jednoelementową.

***

##### `decltype`

`decltype(expr)` zwraca **dokładny typ wyrażenia**:
```cpp
int jakasLiczba;
decltype(jakasLiczba) innaLiczba = 5; // typ to int
```

`decltype` jest szczególnie przydatne, gdy:

* typ jest trudny do zapisania,
* używamy przeciążonych operatorów,
* pracujemy z typami specjalizowanymi,
* pracujemy z szablonami,
* chcemy pobrać typ zmiennej, pola lub wyrażenia bez zgadywania.

***

##### `auto` i `decltype` mogą dawać różne typy

Poniższy przykład pokazuje różnicę między typem wywnioskowanym przez `auto`, a typem zwróconym przez `decltype`:
```cpp
#include <vector>

using std::vector;

int main()
{
    const vector<int> wektor(1);

    auto a = wektor[0];        // a ma typ int (kopiowanie wartości)
    decltype(wektor[0]) b = 1; // b ma typ const int& (operator[] zwraca referencję)

    auto c = 0;                // c ma typ int
    auto d = c;                // d ma typ int

    decltype(c) e;             // e ma typ int (typ zmiennej c)
    decltype((c)) f = c;       // f ma typ int& (nawiasy → lvalue → referencja)

    decltype(0) g;             // g ma typ int (0 to rvalue)
}
```

**Dodatkowa uwaga**

Im bardziej zagnieżdżone są kontenery (`vector<map<string, vector<...>>>`), tym większą różnicę robi `auto`.
W C++03 często stosowano `typedef`, aby skrócić kod — `auto` eliminuje tę potrzebę.

Komentarz dla początkującego:

* `decltype(x)` → typ zmiennej `x`
* `decltype((x))` → **zawsze referencja**, bo `(x)` jest lvalue (to jedna z najczęstszych pułapek!)

***
_Zobacz też:_
* **Czy `decltype` zastąpiło `typeof`?**
***

##### `auto` w pętlach

Zamiast długiego:
```cpp
for (std::vector<int>::const_iterator iterator = mojWektor.cbegin();
     iterator != mojWektor.cend();
     ++iterator)
{
}
```

można napisać:
```cpp
for (auto iterator = mojWektor.cbegin(); iterator != mojWektor.cend(); ++iterator)
{
}
```

A najczęściej stosowana i najczytelniejsza forma (od C++11):
```cpp
for (const auto& element : mojWektor) // pętla po zakresie (range-based for)
{
    // element jest referencją do elementu kontenera
}
```

***

##### (C++14): dedukcja typu zwracanego funkcji

C++11 pozwalał na dedukcję typu zwracanego jedynie w **funkcjach lambda**, i to tylko wtedy, gdy ciało lambdy składało się z pojedynczego wyrażenia `return expression;`.
C++14 rozszerza tę możliwość na **wszystkie funkcje**, niezależnie od tego, czy są to lambdy, funkcje wolnostojące, metody klas czy funkcje szablonowe.

Aby włączyć dedukcję typu zwracanego, funkcja musi być zadeklarowana z użyciem `auto` jako typu zwracanego, **bez trailing return type**:
```cpp
auto policz(); // typ zwracany zostanie wywnioskowany z definicji
```

Typ zwracany jest określany na podstawie wszystkich instrukcji `return` w definicji funkcji.
Jeśli funkcja zawiera wiele instrukcji `return`, **wszystkie muszą zwracać ten sam typ** — w przeciwnym razie kompilacja zakończy się błędem.

Funkcje z dedukcją typu zwracanego mogą mieć deklaracje wstępne, ale **nie mogą być używane przed definicją**, ponieważ kompilator musi znać wszystkie instrukcje `return`, aby ustalić typ.

Dedukcja działa również w funkcjach rekurencyjnych, ale z ograniczeniem:
**pierwsze wywołanie rekurencyjne musi nastąpić po instrukcji `return`, która pozwala ustalić typ zwracany.**

Przykład poprawny:
```cpp
auto poprawna(int i)
{
    if (i == 1)
        return i; // typ zwracany: int

    return poprawna(i - 1) + i; // dopiero teraz można wywołać rekurencyjnie
}
```

Przykład błędny:
```cpp
auto bledna(int i)
{
    if (i != 1)
        return bledna(i - 1) + i; // za wcześnie — typ zwracany nie został jeszcze ustalony

    return i;
}
```

Dedukcja typu zwracanego funkcji w C++14 stanowi fundament późniejszych rozszerzeń, takich jak `decltype(auto)` oraz dedukcja typu zwracanego w kontekstach constexpr.

***

##### **(C++14): `decltype(auto)` i alternatywna dedukcja typu**

C++11 wprowadził dwa mechanizmy dedukcji typu:

* `auto` — tworzy zmienną o typie wywnioskowanym z wyrażenia, ale **zawsze usuwa referencje** (zachowuje się jak `std::decay`).
* `decltype` — oblicza typ wyrażenia zgodnie z jego kategorią wartości (l‑wartość, r‑wartość), dzięki czemu może zwrócić typ referencyjny.

Przykład różnic:
```cpp
int i;
int&& f();

auto x3a = i;            // typ: int
decltype(i) x3d = i;     // typ: int

auto x4a = (i);          // typ: int
decltype((i)) x4d = (i); // typ: int&

auto x5a = f();          // typ: int
decltype(f()) x5d = f(); // typ: int&&
```

C++14 dodaje nową konstrukcję:

**`decltype(auto)`**

Pozwala ona użyć reguł `decltype` w deklaracjach `auto`.
Oznacza to, że typ jest dedukowany **dokładnie tak**, jak zrobiłby to `decltype(expr)`.

Przykłady:
```cpp
int i = 10;
int& ref = i;

auto a = ref;           // typ: int  (kopiowanie)
decltype(auto) b = ref; // typ: int& (zachowanie referencji)
```

`decltype(auto)` może być również użyte jako **typ zwracany funkcji**, co pozwala zachować referencje i kwalifikatory:
```cpp
decltype(auto) zwroc(int& x)
{
    return (x); // zwraca int&
}
```

W przeciwieństwie do zwykłego `auto`, które zawsze zwraca typ niererefencyjny, `decltype(auto)` umożliwia precyzyjne odwzorowanie typu wyrażenia, w tym:

* referencji l‑wartości (`T&`),
* referencji r‑wartości (`T&&`),
* kwalifikatorów `const` i `volatile`.

Mechanizm ten jest szczególnie przydatny w szablonach oraz funkcjach przekazujących argumenty dalej (perfect forwarding).

***

#### Pętla po zakresie (range-based `for`)

C++11 rozszerza składnię instrukcji `for`, aby umożliwić łatwe iterowanie po zakresie elementów.

```cpp
int a[5] = { 1, 2, 3, 4, 5 };

// podwajamy wartość każdego elementu tablicy
for (int& x : a)
{
    x *= 2;
}

// to samo, ale z użyciem auto (wnioskowanie typu)
for (auto& x : a)
{
    x *= 2;
}
```

Ta forma `for`, nazywana **range-based for** (**pętla po zakresie**), iteruje po każdym elemencie:

* tablic C‑stylowych (o znanym rozmiarze w czasie kompilacji),
* list inicjalizacyjnych,
* dowolnego typu, który ma funkcje `begin()` i `end()` zwracające iteratory.

Wszystkie kontenery standardowej biblioteki (`std::vector`, `std::array`, `std::list`, itd.) działają z tą pętlą.

##### Uzupełnienie (C++20): inicjalizator w pętli po zakresie

C++20 pozwala umieścić inicjalizator bezpośrednio w pętli `for` po zakresie,
analogicznie do inicjalizatorów w `if` i `switch` z C++17:
```cpp
for (auto kontener = pobierzKontener(); auto& element : kontener)
{
    std::cout << element << "\n";
}
```

Zmienna zadeklarowana w inicjalizatorze żyje przez cały czas trwania pętli
i nie jest widoczna poza nią. Przydatne gdy chcemy uniknąć tworzenia zmiennej
pomocniczej w zewnętrznym zakresie.

***

#### Funkcje lambda

C++11 wprowadza możliwość tworzenia **funkcji anonimowych** (_lambda functions_ — funkcje lambda).

Przykład:
```cpp
[](int x, int y) -> int
{
    return x + y;
};
```

* `-> int` określa typ zwracany (można go pominąć, jeśli wszystkie `return` zwracają ten sam typ).
* Lambda może być **domknięciem** (_closure_ — funkcja zapamiętująca zmienne z otoczenia).

To bardzo przydatne w programowaniu funkcyjnym, algorytmach STL i callbackach.

##### (C++14): lambdy generyczne (generic lambdas)

W C++11 parametry funkcji lambda musiały mieć **konkretne typy** — nie można było używać `auto`.
C++14 wprowadza **lambdy generyczne**, pozwalając deklarować parametry lambdy z użyciem `auto`, co czyni lambdę funkcjonalnie odpowiednikiem szablonu.

Przykład:
```cpp
auto lambda = [](auto x, auto y) -> auto
{
    return x + y;
};
```

Taka lambda może być wywoływana z argumentami różnych typów:
```cpp
auto a = lambda(2, 3);                 // int
auto b = lambda(1.5, 2.5);             // double
auto c = lambda(std::string("a"), "b"); // std::string
```

Lambdy generyczne stosują **reguły dedukcji szablonów**, co oznacza, że ich działanie jest równoważne funktorowi z szablonowym `operator()`:
```cpp
struct
{
    template <typename T, typename U>
    auto operator()(T x, U y) const
    {
        return x + y;
    }
} lambda {};
```

Lambdy generyczne są więc w praktyce **szablonowymi funktorami zapisanymi w postaci lambdy**, co znacząco zwiększa ich elastyczność i przydatność w kodzie generycznym.

***

##### (C++14): wyrażenia przechwytywania (lambda capture expressions)

W C++11 lambda może przechwytywać zmienne z otaczającego zakresu **przez wartość** lub **przez referencję**.
Powoduje to jednak ograniczenie:
**przechwytywanie przez wartość nie pozwala na przechwytywanie typów przenoszalnych (move‑only), takich jak `std::unique_ptr`.**

C++14 wprowadza **wyrażenia przechwytywania**, które pozwalają inicjalizować przechwycone pola lambdy **dowolnym wyrażeniem**, a nie tylko nazwą zmiennej z zewnętrznego zakresu.

Przykład prostego przechwytywania z inicjalizatorem:
```cpp
auto lambda = [wartosc = 1] -> int
{
    return wartosc;
};
```

Lambda zwraca `1`, ponieważ `wartosc` została zainicjalizowana wartością `1`.
Typ `wartosc` jest dedukowany tak, jak przy użyciu `auto`.

Wyrażenia przechwytywania umożliwiają również **przechwytywanie przez przeniesienie**:
```cpp
using std::unique_ptr;

unique_ptr<int> wskaznik(new int(10));

auto lambda = [wartosc = std::move(wskaznik)] -> int
{
    return *wartosc;
};
```

Dzięki temu:

* można przechwytywać obiekty **move‑only**,
* można tworzyć **własne pola lambdy**, nawet jeśli nie istnieją w zewnętrznym zakresie,
* przechwytywanie staje się bardziej elastyczne i przypomina inicjalizację pól w konstruktorze.

Mechanizm ten jest kluczowy dla nowoczesnego stylu programowania funkcyjnego w C++ i stanowi fundament dla późniejszych rozszerzeń (np. init‑captures w structured bindings).

###### Uzupełnienie (C++17): przechwytywanie `*this` przez wartość

W C++11/14 lambda mogła przechwycić `this` (wskaźnik do obiektu), ale nie mogła
przechwycić **kopii całego obiektu**. Przy pracy asynchronicznej było to ryzykowne
— jeśli obiekt został zniszczony przed wykonaniem lambdy, wskaźnik `this` stawał się
nieprawidłowy.

C++17 dodaje składnię `[*this]`, która przechwytuje **kopię całego obiektu**:
```cpp
struct Zadanie
{
    int wartosc = 42;

    auto przygotuj()
    {
        return [*this]()     // kopia całego obiektu Zadanie
        {
            return wartosc;  // bezpieczne — używa kopii, nie wskaźnika
        };
    }
};

Zadanie z;
auto lambda = z.przygotuj();
// z może być zniszczone — lambda nadal działa poprawnie
```

Przed C++17 jedynym sposobem było ręczne kopiowanie potrzebnych pól przez
wyrażenia przechwytywania (`[wartosc = this->wartosc]`).

***

###### Uzupełnienie (C++20): `[=, this]` — jawne przechwytywanie `this` przy `[=]`

W C++17 i wcześniej zapis `[=]` niejawnie przechwytywał `this` przez wskaźnik,
co było zaskakujące — programista mógł myśleć, że wszystko jest przechwycone
przez wartość, podczas gdy `this` nadal było wskaźnikiem.

C++20 **zakazuje** niejawnego przechwytywania `this` przez `[=]`.
Jeśli potrzebujemy zarówno domyślnego przechwytywania przez wartość, jak i `this`,
musimy napisać to jawnie:
```cpp
// C++17: [=] niejawnie przechwytywał też this — dozwolone, ale mylące
// C++20: [=] bez this — this nie jest przechwycone
// C++20: [=, this] — jawne przechwycenie this przez wskaźnik
// C++20: [=, *this] — jawne przechwycenie kopii obiektu (jak w C++17)

struct Zadanie
{
    int wartosc = 42;

    auto przygotuj()
    {
        return [=, this]() { return wartosc; }; // C++20: jawne
    }
};
```

***

#### Alternatywna składnia funkcji (trailing return type — typ zwracany po parametrze)

Składnia deklaracji funkcji odziedziczona z języka C była wystarczająca dla C, ale w C++ zaczęła być problematyczna — szczególnie przy szablonach.

W C++03 taki kod jest niepoprawny:
```cpp
template <class L, class R>
Ret dodaj(const L& lhs, const R& rhs)
{
    return lhs + rhs; // Ret powinien być typem wyniku lhs + rhs
}
```

Nawet z `decltype` w C++11 nie da się tego zapisać w klasycznej formie:
```cpp
// Niepoprawne w C++11
template <class L, class R>
decltype(lhs + rhs) dodaj(const L& lhs, const R& rhs)
{
    return lhs + rhs;
}
```

Dlaczego?
Bo `lhs` i `rhs` **nie istnieją jeszcze** w momencie, gdy parser czyta nagłówek funkcji.

##### Trailing return type (typ zwracany po parametrze)

C++11 wprowadza nową składnię:
```cpp
template <class L, class R>
auto add(const L& lhs, const R& rhs) -> decltype(lhs + rhs)
{
    return lhs + rhs;
}
```

Tutaj:

* `auto` jest tylko częścią składni (nie oznacza wnioskowania typu),
* `decltype(lhs + rhs)` może używać parametrów, bo są już znane parserowi.

***

##### Zwykłe funkcje też mogą używać tej składni
```cpp
struct JakasStruktura
{
    auto dodaj(int x, int y) -> int
    {
        return x + y;
    }
};
```

***

##### C++14 upraszcza to jeszcze bardziej

Od C++14 można pominąć trailing return type:
```cpp
auto add(const L& lhs, const R& rhs)
{
    return lhs + rhs; // kompilator sam wywnioskuje typ
}
```

To działa, jeśli typ zwracany można jednoznacznie ustalić.

***

#### Ulepszenia konstrukcji obiektów

W C++03 konstruktor klasy **nie mógł wywołać innego konstruktora tej samej klasy**.
Każdy konstruktor musiał samodzielnie inicjalizować wszystkie pola albo wywoływać wspólną funkcję składową:
```cpp
class LiczbaCalkowita
{
private:
    int wartosc;

    // Wspólna funkcja pomocnicza używana przez oba konstruktory.
    // W C++03 konstruktor NIE mógł wywołać innego konstruktora tej samej klasy,
    // więc wszystkie wspólne operacje inicjalizacyjne trzeba było umieszczać
    // w osobnej funkcji składowej.
    void ustawWartosc(int liczba)
    {
        wartosc = liczba;
    }

public:
    // Konstruktor przyjmujący wartość początkową.
    // Musi samodzielnie wywołać funkcję ustawWartosc(),
    // ponieważ w C++03 nie można było delegować do innego konstruktora.
    LiczbaCalkowita(int liczba)
    {
        ustawWartosc(liczba);
    }

    // Konstruktor domyślny.
    // Również musi samodzielnie wywołać funkcję ustawWartosc(),
    // mimo że logika jest taka sama jak w konstruktorze powyżej.
    // W C++11 można by napisać: LiczbaCalkowita() : LiczbaCalkowita(42) {}
    // ale w C++03 było to niedozwolone.
    LiczbaCalkowita()
    {
        ustawWartosc(42);
    }
};
```

Dodatkowe ograniczenia C++03:

* konstruktory klas bazowych **nie były dziedziczone**,
* każda klasa pochodna musiała pisać własne konstruktory, nawet jeśli konstruktor bazowy był idealny,
* **pól niestatycznych nie można było inicjalizować przy deklaracji**, tylko w konstruktorze.

C++11 rozwiązuje wszystkie te problemy.

##### Delegowanie konstruktorów (konstruktor wywołujący inny konstruktor)

C++11 pozwala, aby konstruktor wywołał inny konstruktor tej samej klasy.
Nazywa się to **delegowaniem konstruktora** (constructor delegation).

Delegowanie było wcześniej stosowane w innych językach, takich jak **Java** czy **Objective‑C**.

Przykład:
```cpp
class LiczbaCalkowita
{
private:
    int wartosc;

public:
    LiczbaCalkowita(int liczba)
        : wartosc(liczba)
    {
    }

    LiczbaCalkowita()
        : LiczbaCalkowita(42) // delegowanie do innego konstruktora
    {
    }
};
```

W tym przypadku ten sam efekt można by osiągnąć, używając parametru domyślnego.
Jednak delegowanie ma ważną zaletę: **domyślna wartość (np. 42) znajduje się w implementacji, a nie w interfejsie**.
To ułatwia utrzymanie bibliotek — zmiana wartości domyślnej nie wymaga rekompilacji kodu użytkownika.

**Uwaga dla początkującego:**
W C03 obiekt uznawano za skonstruowany dopiero po zakończeniu działania konstruktora.
W C11 obiekt uznaje się za skonstruowany, gdy **jakikolwiek konstruktor** zakończy działanie.
Ponieważ delegowanie pozwala wykonać kilka konstruktorów po kolei, oznacza to, że konstruktor delegujący działa już na **w pełni skonstruowanym obiekcie**.

Konstruktory klas pochodnych wykonują się **dopiero po zakończeniu całego delegowania** w klasach bazowych.

***

##### Dziedziczenie konstruktorów

C++11 pozwala klasie pochodnej **odziedziczyć wszystkie konstruktory** klasy bazowej.
```cpp
class KlasaBazowa
{
public:
    KlasaBazowa(int wartosc);
};

class KlasaPochodna : public KlasaBazowa
{
public:
    using KlasaBazowa::KlasaBazowa; // dziedziczenie konstruktorów
};
```

Ograniczenia:

* to mechanizm **„wszystko albo nic”** — dziedziczymy wszystkie konstruktory bazowe,
* jeśli konstruktor klasy pochodnej ma taką samą sygnaturę, to **zacienia** konstruktor bazowy,
* przy wielodziedziczeniu nie można dziedziczyć konstruktorów z dwóch klas, jeśli mają identyczne sygnatury (problem diamentu).

***

##### Inicjalizacja pól przy deklaracji (in‑class member initializers)

C++11 pozwala inicjalizować pola **bezpośrednio w miejscu deklaracji**:
```cpp
class LiczbaCalkowita
{
private:
    int wartosc = 5; // inicjalizacja domyślna

public:
    LiczbaCalkowita()
    {
    }

    // konstruktor jawny 'explicit'
    explicit LiczbaCalkowita(int wartoscParam)
        : wartosc(wartoscParam) // nadpisanie wartości domyślnej
    {
    }
};
```

Zasady:

* jeśli konstruktor **nie** inicjalizuje pola, używana jest wartość domyślna,
* jeśli konstruktor inicjalizuje pole, wartość domyślna jest ignorowana.

Można używać:

* przypisania (`= 5`),
* list inicjalizacyjnych (`{5}`),
* konstruktorów (`int wartosc(5)`),
* jednolitej inicjalizacji (`int wartosc{5}`).

***

##### (C++14): inicjalizacja agregatów z polami posiadającymi wartości domyślne

C++11 wprowadził możliwość nadawania polom wartości domyślnych bezpośrednio w klasie (tzw. _in‑class member initializers_).
Jednocześnie zmieniono definicję agregatu tak, aby **każda klasa posiadająca takie inicjalizatory przestawała być agregatem**.
W efekcie nie można było używać inicjalizacji agregatowej (`{ ... }`) dla takich typów.

C++14 **luzuje to ograniczenie**:
klasy posiadające domyślne inicjalizatory pól **mogą ponownie być agregatami**, o ile spełniają pozostałe warunki agregatu.

Jeśli lista inicjalizacyjna nie dostarcza wartości dla danego pola, używany jest jego inicjalizator domyślny:
```cpp
struct Punkt
{
    int x = 1;
    int y = 2;
};

// Od C++14: dozwolone
Punkt p1{ };      // p1.x = 1, p1.y = 2
Punkt p2{ 10 };   // p2.x = 10, p2.y = 2
Punkt p3{ 10, 20 }; // p3.x = 10, p3.y = 20
```

Zasady szablonów i specjalizacji pozostają bez zmian — agregatowość zależy wyłącznie od cech typu, nie od tego, czy jest szablonem.

Mechanizm ten przywraca spójność między inicjalizacją agregatową a inicjalizatorami pól, czyniąc kod bardziej przewidywalnym i wygodnym.

***

#### Jawne nadpisania (`override`) i ostateczne (`final`)

W C++03 łatwo było **przez pomyłkę stworzyć nową funkcję wirtualną**, zamiast nadpisać istniejącą.

Przykład błędu:
```cpp
struct KlasaBazowa
{
    virtual void wykonajOperacje(float wartosc);
};

struct KlasaPochodna : public KlasaBazowa
{
    virtual void wykonajOperacje(int wartosc); // to NIE jest nadpisanie!
};
```

Ponieważ sygnatura jest inna, powstaje **nowa** funkcja wirtualna.
To częsty błąd, szczególnie gdy ktoś modyfikuje klasę bazową i nie zauważa zmiany sygnatury.

##### `override` — wymuszenie poprawnego nadpisania

C++11 wprowadza słowo kluczowe (a właściwie _atrybut deklaratora_) `override`:
```cpp
struct KlasaBazowa
{
    virtual void wykonajOperacje(float wartosc);
};

struct KlasaPochodna : public KlasaBazowa
{
    virtual void wykonajOperacje(int wartosc) override; // błąd — nie nadpisuje funkcji bazowej
};
```

Jeśli metoda **nie nadpisuje** żadnej metody z klasy bazowej, kompilator zgłosi błąd.

To chroni przed literówkami, pomyłkami w typach parametrów i przypadkowym tworzeniem nowych funkcji wirtualnych.

***

##### `final` — zakaz dziedziczenia lub nadpisywania

C++11 pozwala:

* oznaczyć klasę jako **niedziedziczącą** (`final`),
* oznaczyć metodę jako **nienadpisywalną** (`final`).

Przykład klasy `final`:
```cpp
struct KlasaBazowa final
{
    // ...
};

// błąd — nie można dziedziczyć po klasie oznaczonej final
struct KlasaPochodna : public KlasaBazowa
{
};
```

Przykład metody `final`:
```cpp
struct KlasaBazowa
{
    virtual void wykonajOperacje() final; // metoda wirtualna oznaczona jako final — nie wolno jej nadpisywać
};

struct KlasaPochodna : public KlasaBazowa
{
    void wykonajOperacje(); // błąd: metoda KlasaBazowa::wykonajOperacje została oznaczona jako final
};
```

W tym przykładzie deklaracja:
```cpp
virtual void wykonajOperacje() final;
```

tworzy nową metodę wirtualną, ale jednocześnie **zabrania klasom pochodnym jej nadpisywania**.
Dodatkowo oznaczenie `final` sprawia, że **żadna klasa pochodna nie może zdefiniować metody o tej samej nazwie i tej samej liście parametrów** — nawet jeśli nie próbowałaby jej „tylko” ukryć lub zdefiniować jako nowej metody.
Dzieje się tak dlatego, że taka deklaracja byłaby traktowana jako próba nadpisania — a to jest zabronione.

***

##### `override` i `final` — ważna uwaga

Ani `override`, ani `final` **nie są słowami kluczowymi języka C++**.
Technicznie są to **identyfikatory używane jako atrybuty deklaratora** (_declarator attributes_).

Oznacza to, że:

* zyskują specjalne znaczenie **tylko w konkretnym miejscu**, czyli:

  * po wszystkich specyfikatorach typu,
  * po specyfikatorach dostępu (`public`, `private`, `protected`),
  * po słowach takich jak `virtual`,
  * ale **przed** inicjalizacją lub implementacją funkcji;

* **nie zmieniają typu funkcji**,

* **nie tworzą nowych identyfikatorów**,

* **nie wpływają na przeciążanie funkcji** — jedynie informują kompilator o zamiarze programisty.

***

##### Rozszerzalność atrybutów deklaratora

Standard C++ dopuszcza możliwość dodawania nowych atrybutów deklaratora w przyszłych wersjach języka.
Już dziś niektóre kompilatory mają własne rozszerzenia, które:

* podpowiadają optymalizacje,
* dodają metadane dla debuggera lub linkera,
* wprowadzają atrybuty bezpieczeństwa,
* wspierają _reflection_ (programowanie refleksyjne),
* dodają informacje potrzebne do współpracy z innymi językami.

Takie rozszerzenia mogą przyjmować parametry w nawiasach, np.:
```cpp
[[gnu::hot]]
[[clang::annotate("info")]]
```

Zgodnie z konwencją ANSI, rozszerzenia specyficzne dla kompilatora powinny używać prefiksu `__` (podwójny podkreślnik).

***

##### Ostatnia ważna rzecz

Poza kontekstem deklaracji funkcji `override` i `final` **mogą być używane jako zwykłe identyfikatory**, np.:
```cpp
int final = 10; // poprawne, choć to bardzo zły pomysł
```

Kompilator nada im specjalne znaczenie **tylko wtedy**, gdy pojawią się w miejscu, gdzie mogą pełnić rolę atrybutu deklaratora.

***

#### Stała pustego wskaźnika i jej typ (null pointer constant and type)

W tym fragmencie, gdy pojawia się zapis „`0`”, oznacza on:

> „stałe wyrażenie o wartości `0` i typie `int`”.

W praktyce taka stała może mieć dowolny typ całkowitoliczbowy.

Od początku istnienia języka C (1972) stała `0` pełniła **podwójną rolę**:

* była liczbą całkowitą,

* była **stałą pustego wskaźnika** (null pointer constant — wartość reprezentująca „brak adresu”).

W języku C problem ten łagodzono makrem `NULL`, które zwykle rozwijało się do:

* `((void*)0)` albo

* `0`.

W C++ nie wolno niejawnie konwertować `void*` do innych typów wskaźnikowych, więc rzutowanie `0` na `void*` **nie daje żadnej korzyści**. W efekcie w C++ jedyną poprawną stałą pustego wskaźnika był **sam&#x20;**`0`.

To prowadziło do problemów z przeciążaniem funkcji:
```cpp
void foo(char*);
void foo(int);
```

Jeśli `NULL` jest zdefiniowane jako `0` (co w C++ jest normą), to:
```cpp
foo(NULL); // wywoła foo(int), co jest prawie na pewno błędem
```

##### `nullptr` — nowe, jednoznaczne źródło pustego wskaźnika

C++11 wprowadza nową stałą pustego wskaźnika: `nullptr`.

* ma typ `nullptr_t`,

* konwertuje się niejawnie i porównuje do **dowolnego typu wskaźnikowego**,

* konwertuje się niejawnie i porównuje do **wskaźnika do składowej** (pointer‑to‑member),

* **nie** konwertuje się ani nie porównuje do typów całkowitych (poza `bool`).

Konwersja do `bool` daje `false` — tak samo jak w przypadku zwykłych wskaźników.

**Uwaga historyczna:** Pierwotnie planowano, że r‑value typu `nullptr_t` **nie** będzie konwertowalne do `bool`. Jednak grupa robocza uznała, że taka konwersja jest pożądana dla spójności z zachowaniem zwykłych wskaźników. Zmiana została jednogłośnie przyjęta w czerwcu 2008 roku.

**Uwaga dodatkowa:** Podobna propozycja została przyjęta również do standardu **C23**.

Dla kompatybilności wstecznej `0` nadal jest poprawną stałą pustego wskaźnika.

Przykłady:
```cpp
char* pc = nullptr; // OK
int* pi = nullptr;  // OK
bool b = nullptr;   // OK. b == false
int i = nullptr;    // błąd — nullptr nie konwertuje się do int
```

***

##### `nullptr` a przeciążanie funkcji

```cpp
foo(nullptr); // wywoła foo(nullptr_t), a nie foo(int)
```

Pełny komentarz (bez uproszczeń):
```cpp
/*
  Uwaga: w praktyce foo(nullptr_t) wywoła foo(char*) w powyższym przykładzie,
  używając niejawnej konwersji do wskaźnika, ale tylko wtedy, gdy w zasięgu
  nie ma innych przeciążeń przyjmujących kompatybilne typy wskaźników.

  Jeśli istnieje wiele przeciążeń przyjmujących różne typy wskaźników,
  rozstrzyganie przeciążeń zakończy się błędem niejednoznaczności,
  chyba że istnieje dokładne przeciążenie foo(nullptr_t).

  W standardowych nagłówkach C++11 typ nullptr_t powinien być zdefiniowany jako:
      typedef decltype(nullptr) nullptr_t;

  A NIE jako:
      typedef int nullptr_t;      // starsze wersje C++, gdzie NULL musiało być równe 0
      typedef void* nullptr_t;    // ANSI C, gdzie NULL definiowano jako ((void*)0)
*/
```

***

#### Silnie typowane wyliczenia (strongly typed enumerations)

W C++03 typy wyliczeniowe (`enum`) **nie były bezpieczne typowo**:

* enum zachowywał się jak liczba całkowita,
* można było porównywać wartości z różnych enumów,
* można było porównywać wartości enum z liczbami całkowitymi,
* typ bazowy (rozmiar) był zależny od implementacji,
* wszystkie nazwy elementów enum trafiały do **tego samego zakresu**,
  co oznaczało, że **nie można było mieć dwóch różnych enumów z tymi samymi nazwami elementów**.

C++11 wprowadza nowy rodzaj wyliczeń: **`enum class`** (również `enum struct`, które jest synonimem).

```cpp
enum class KolorKarty
{
    TREFL = 1,
    KIER = 2,
    KARO = 4,
    PIK = 8
};
```

Zalety:

* wartości **nie konwertują się niejawnie do liczb**,
  więc wyrażenie typu `KolorKarty::PIK == 8` powoduje błąd kompilacji,
* wartości **nie konwertują się** do innych enumów,
* nazwy są umieszczone w zakresie `KolorKarty::`,
* typ bazowy jest zawsze znany (domyślnie `int`).

Można jawnie określić typ bazowy:
```cpp
enum class Kierunek : char
{
    GORA,
    DOL,
    LEWO,
    PRAWO
};
```

##### Stare wyliczenia z nowym zakresem

Można użyć starej składni, ale z określonym typem bazowym:
```cpp
enum Kierunek : char
{
    GORA,
    DOL,
    LEWO,
    PRAWO
};
```

W tym przypadku:

* `Kierunek::GORA` jest poprawne,
* ale dla zgodności wstecznej **`GORA` również istnieje w zakresie zewnętrznym**.

Oznacza to, że enumeratory są dostępne **jednocześnie**:

* w zakresie `Kierunek::`,
* oraz w zakresie otaczającym.

***

##### Deklaracje wstępne enumów

W C++03 nie można było deklarować enumów wstępnie, ponieważ kompilator nie znał ich rozmiaru.

W C++11 można to zrobić, jeśli rozmiar jest znany — jawnie lub domyślnie:
```cpp
enum Enum1;
// Niepoprawne w C++03 i C++11: nie można określić typu bazowego,
// więc kompilator nie zna rozmiaru wyliczenia.

enum Enum2 : unsigned int;
// Poprawne w C++11: typ bazowy został jawnie określony jako unsigned int,
// więc kompilator zna rozmiar wyliczenia i może przyjąć deklarację wstępną.

enum class Enum3;
// Poprawne w C++11: dla enum class domyślnym typem bazowym jest int,
// więc rozmiar jest znany i deklaracja wstępna jest dozwolona.

enum class Enum4 : unsigned int;
// Poprawne w C++11: typ bazowy określony jawnie, więc deklaracja wstępna jest poprawna.

enum Enum2 : unsigned short;
// Niepoprawne w C++11: Enum2 zostało wcześniej zadeklarowane z typem bazowym unsigned int,
// więc nie można później zmienić typu bazowego na unsigned short.
```

***

##### Uzupełnienie (C++20): `using enum` — import elementów wyliczenia do zakresu

W C++11/17 każde odwołanie do elementu `enum class` wymagało pełnej kwalifikacji:
```cpp
enum class Kierunek { Gora, Dol, Lewo, Prawo };

void idz(Kierunek k)
{
    if (k == Kierunek::Gora) { ... }   // za każdym razem pełna kwalifikacja
}
```

C++20 wprowadza `using enum`, które importuje elementy wyliczenia do bieżącego zakresu:
```cpp
void idz(Kierunek k)
{
    using enum Kierunek;
    if (k == Gora) { ... }   // bez kwalifikacji
}
```

Szczególnie przydatne w instrukcjach `switch`:
```cpp
switch (k)
{
    using enum Kierunek;
    case Gora:  /* ... */ break;
    case Dol:   /* ... */ break;
    case Lewo:  /* ... */ break;
    case Prawo: /* ... */ break;
}
```

`using enum` działa zarówno dla `enum class`, jak i zwykłych `enum`.

***

#### Podwójny nawias ostry

W C++03 parser zawsze interpretował `>>` jako:

* operator przesunięcia bitowego w prawo, albo
* operator ekstrakcji strumienia (`std::cin >> x`).

To powodowało problemy przy zagnieżdżonych szablonach:
```cpp
vector<vector<int>> v; // w C++03 błąd — parser widzi operator >>
```

**C++11 usprawnia specyfikację parsera** w taki sposób, że wielokrotne nawiasy ostre zamykające (`>>`, `>>>`, itd.) są interpretowane jako zamykanie listy argumentów szablonu — tam, gdzie ma to sens.

Można to obejść, stosując nawiasy okrągłe wokół wyrażeń parametrów, które zawierają operatory binarne `>`, `>=` lub `>>`:
```cpp
using std::vector;

template <bool Test>
class JakisTyp;

vector<JakisTyp<1> 2>> x1;
// Interpretacja:
//   Kompilator widzi JakisTyp<1> → wartość 1 jest traktowana jako true,
//   więc jest to JakisTyp<true>.
//   Następnie parser interpretuje "2 >> x1" jako operator przesunięcia bitowego
//   lub operator ekstrakcji strumienia, co NIE jest poprawną składnią deklaratora.
//   W efekcie cały zapis jest niepoprawny. (1 jest true).

vector<JakisTyp<(1>2)>> x1;
// Interpretacja:
//   Nawiasy wymuszają ocenę wyrażenia (1 > 2), które jest false,
//   więc otrzymujemy JakisTyp<false>.
//   Następnie parser widzi poprawny deklarator "x1".
//   Całość jest poprawną deklaracją w C++11.
//   (1 > 2) jest false.
```

***

#### (C++17): Zagnieżdżone przestrzenie nazw

W C++03 i C++11 zagnieżdżone przestrzenie nazw wymagały osobnych definicji
dla każdego poziomu:
```cpp
namespace Firma
{
    namespace Modul
    {
        namespace Szczegoly
        {
            void funkcja();
        }
    }
}
```

C++17 wprowadza skróconą składnię z operatorem `::`:
```cpp
namespace Firma::Modul::Szczegoly
{
    void funkcja();
}
```

Obie formy są równoważne. Skrócona składnia poprawia czytelność w dużych projektach,
gdzie głęboko zagnieżdżone przestrzenie nazw są powszechne.

> **Uwaga:** skrócona składnia służy wyłącznie do **definiowania** przestrzeni nazw.
> Dostęp do elementów nadal używa `::`, np. `Firma::Modul::Szczegoly::funkcja()`.

##### Uzupełnienie (C++20): **`inline`** w zagnieżdżonych przestrzeniach nazw

C++20 rozszerza składnię z C++17, pozwalając używać `inline` również w skróconej formie zagnieżdżonych przestrzeni nazw:
```cpp
namespace Firma::inline V2::Szczegoly
{
    void funkcja();
}
```
To zachowuje wszystkie właściwości `inline namespace` (m.in. automatyczne „eksportowanie” nazw z przestrzeni `V2`), a jednocześnie pozwala korzystać z czytelnej składni wprowadzonej w C++17.

***

#### (C++17): `if constexpr` — kompilacyjne rozgałęzianie kodu

W szablonach często chcemy wykonać różny kod w zależności od właściwości typu.
Przed C++17 wymagało to specjalizacji szablonów lub techniki SFINAE (Substitution Failure Is Not An Error — mechanizm, w którym nieudana podstawienie typu powoduje odrzucenie przeciążenia, a nie błąd kompilacji) — obu skomplikowanych.

Przykład problemu w C++11/14 — funkcja wypisująca wartość, inaczej dla liczb i napisów:
```cpp
// C++11: trzeba pisać dwie specjalizacje
template <typename T>
void wypisz(T val) { std::cout << val; }

template <>
void wypisz(std::string val) { std::cout << '"' << val << '"'; }
```

C++17 wprowadza `if constexpr` — instrukcję warunkową ewaluowaną **w czasie kompilacji**.
Gałąź, której warunek jest fałszywy, **nie jest kompilowana** dla danej instancji szablonu:
```cpp
#include <type_traits>

template <typename T>
void wypisz(T val)
{
    if constexpr (std::is_same_v<T, std::string>)
    {
        std::cout << '"' << val << '"'; // kompilowane tylko dla T = std::string
    }
    else
    {
        std::cout << val;               // kompilowane dla pozostałych typów
    }
}
```

Kluczowa różnica względem zwykłego `if`: odrzucona gałąź **nie musi być poprawna**
dla danego typu — kompilator jej nie sprawdza. Dzięki temu można w jednej funkcji
używać operacji dostępnych tylko dla niektórych typów:
```cpp
template <typename T>
auto pobierzWartosc(T t)
{
    if constexpr (std::is_pointer_v<T>)
        return *t;  // dereferencja — poprawna tylko dla wskaźników
    else
        return t;
}
```

Bez `if constexpr` kompilator próbowałby skompilować `*t` nawet dla typów
niebędących wskaźnikami i zgłaszał błąd.

> **Uwaga:** `if constexpr` działa tylko w szablonach. Poza szablonem zachowuje się
> jak zwykły `if` — obie gałęzie muszą być poprawne składniowo i typowo.

***

#### (C++17): Structured bindings — destrukturyzacja obiektów

C++17 wprowadza składnię pozwalającą rozłożyć strukturę, krotkę lub tablicę
na nazwane zmienne w jednej deklaracji:
```cpp
auto [a, b] = pobierzDwieWartosci();
```

**Dla struktur i klas:**
```cpp
struct Punkt { int x; int y; };

Punkt p = {3, 7};
auto [x, y] = p;  // x == 3, y == 7
```

**Dla krotek i par:**
```cpp
std::pair<int, std::string> para = {42, "ala"};
auto [liczba, tekst] = para;  // liczba == 42, tekst == "ala"
```

**Dla tablic:**
```cpp
int tab[3] = {1, 2, 3};
auto [a, b, c] = tab;  // a == 1, b == 2, c == 3
```

**Najczęstsze zastosowanie — iteracja po mapie:**
```cpp
std::map<std::string, int> mapa = {{"ala", 1}, {"ola", 2}};

for (const auto& [klucz, wartosc] : mapa)
{
    std::cout << klucz << ": " << wartosc << "\n";
}
```

Przed C++17 trzeba było pisać:
```cpp
for (const auto& para : mapa)
{
    std::cout << para.first << ": " << para.second << "\n";
}
```

**Wiązanie przez referencję:**
```cpp
auto& [x, y] = p;  // x i y są referencjami do pól p
x = 10;            // modyfikuje p.x
```

Structured bindings działają dla:

* agregatów (struktury bez konstruktorów użytkownika),
* typów z `std::tuple_size` i `std::get` (krotki, pary),
* tablic C-stylowych o znanym rozmiarze.

***

#### (C++17): Inicjalizatory w `if` i `switch`

C++17 pozwala umieścić instrukcję inicjalizującą bezpośrednio w warunku `if` i `switch`,
analogicznie do inicjalizatora w pętli `for`:
```cpp
if (inicjalizator; warunek)
{
    // ...
}
```

**Przykład z mapą — szukanie elementu:**
```cpp
// Przed C++17:
auto it = mapa.find("klucz");
if (it != mapa.end())
{
    uzyj(it->second);
}
// it jest widoczne poza blokiem if — zanieczyszcza zakres

// C++17:
if (auto it = mapa.find("klucz"); it != mapa.end())
{
    uzyj(it->second);
}
// it istnieje tylko wewnątrz bloku if
```

Zmienna zadeklarowana w inicjalizatorze jest widoczna **w obu gałęziach** `if`
(zarówno `if`, jak i `else`), ale nie poza blokiem:
```cpp
if (auto wynik = oblicz(); wynik > 0)
{
    std::cout << "dodatni: " << wynik;
}
else
{
    std::cout << "niedodatni: " << wynik; // wynik dostępny też tutaj
}
// wynik niedostępny tutaj
```

**Dla `switch`:**
```cpp
switch (auto status = pobierzStatus(); status)
{
    case 0: /* ... */ break;
    case 1: /* ... */ break;
}
```

Główna zaleta: ograniczenie zasięgu zmiennych pomocniczych do bloku,
w którym są potrzebne, bez konieczności tworzenia sztucznych zakresów przez `{}`.

***

#### (C++17): `typename` w parametrach szablonu szablonu

Przed C++17 parametr szablonu szablonu (_template template parameter_) wymagał
użycia słowa kluczowego `class`, nawet jeśli w innych kontekstach dopuszczalne było `typename`:
```cpp
// C++11/14: tylko class — typename niedozwolone
template <template <class> class Kontener>
void funkcja();

// C++17: typename również dozwolone
template <template <typename> typename Kontener>
void funkcja();
```

Obie formy są równoważne — zmiana ma charakter czysto kosmetyczny, ujednolicając
składnię z resztą języka, gdzie `typename` i `class` w parametrach szablonu
są wymienne.

***

#### (C++17): Dedukcja argumentów szablonu klasy (CTAD)

Przed C++17 kompilator potrafił dedukować typy dla **funkcji** szablonowych,
ale nie dla **klas** szablonowych. Przy tworzeniu obiektów trzeba było podawać
typy jawnie lub używać funkcji pomocniczych (`make_pair`, `make_tuple` itd.):
```cpp
// C++11/14 — typy trzeba podać jawnie
std::pair<int, double> p(42, 3.14);

// ...lub użyć funkcji pomocniczej
auto p = std::make_pair(42, 3.14);
```

C++17 wprowadza **dedukcję argumentów szablonu klasy** (CTAD — _Class Template
Argument Deduction_): kompilator może wywnioskować parametry szablonu klasy
z argumentów konstruktora:
```cpp
std::pair p(42, 3.14);        // deduuje std::pair<int, double>
std::vector v{1, 2, 3};       // deduuje std::vector<int>
std::tuple t(1, 2.5, "ala");  // deduuje std::tuple<int, double, const char*>
```

**Przewodniki dedukcji (deduction guides)**

Czasem kompilator nie może wywnioskować typów automatycznie — wtedy autor klasy
może dostarczyć jawny **przewodnik dedukcji**:
```cpp
template <typename T>
struct Opakowanie
{
    T wartosc;
    Opakowanie(T v) : wartosc(v) {}
};

// Przewodnik dedukcji — nie jest konieczny tutaj, ale pokazuje składnię:
template <typename T>
Opakowanie(T) -> Opakowanie<T>;

Opakowanie o(42);  // deduuje Opakowanie<int>
```

Standardowa biblioteka C++17 dostarcza przewodniki dedukcji dla wszystkich
swoich szablonów (`std::vector`, `std::map`, `std::pair` itd.), dzięki czemu
funkcje pomocnicze jak `std::make_pair` stają się w większości przypadków zbędne.

##### Uzupełnienie (C++20): CTAD dla klas dziedziczących i aliasów szablonów

C++20 rozszerza CTAD, umożliwiając dedukcję typów również dla:
* **klas dziedziczących po szablonach**, np.:
```cpp
template <typename T>
struct Baza { T x; };

struct Pochodna : Baza<int> {};

Pochodna p{42};   // C++20: dedukcja działa poprawnie
```

* **aliasów szablonów**, np.:
```cpp
template <typename T>
using Vec = std::vector<T>;

Vec v{1, 2, 3};   // C++20: dedukuje Vec<int> → std::vector<int>
```

Dzięki temu CTAD obejmuje więcej konstrukcji języka i eliminuje kolejne przypadki, w których wcześniej trzeba było podawać typy jawnie.

***

#### (C++20): Koncepty (`concept`, `requires`)

Szablony w C++ od początku miały poważną wadę: błędy wynikające z użycia
nieodpowiedniego typu ujawniają się dopiero przy instancjacji szablonu
i generują często kilkadziesiąt linii nieczytelnych komunikatów kompilatora.

Przykład w C++17 — funkcja sumująca elementy:
```cpp
template <typename T>
T suma(T a, T b)
{
    return a + b;
}

suma("ala", "ola"); // błąd kompilacji — ale komunikat jest trudny do zrozumienia
```

Kompilator zgłosi błąd gdzieś wewnątrz szablonu, nie w miejscu wywołania.
Nie ma też żadnej informacji o tym, jakiego typu oczekuje funkcja.

C++20 wprowadza **koncepty** — nazwane zestawy wymagań na typy i wartości,
sprawdzane w czasie kompilacji. Pozwalają one:

* jasno określić jakie typy są akceptowane przez szablon,
* generować czytelne komunikaty błędów w miejscu wywołania,
* przeciążać szablony na podstawie właściwości typów.

##### Definiowanie konceptu

```cpp
#include <concepts>

// Koncept: typ T musi obsługiwać operator+ i zwracać T
template <typename T>
concept Dodawalny = requires(T a, T b)
{
    { a + b } -> std::convertible_to<T>;
};
```

Składnia `requires(T a, T b) { wyrażenie; }` to **wyrażenie requires** —
sprawdza czy dane wyrażenie jest poprawne dla podanych typów.
`{ a + b } -> std::convertible_to<T>` oznacza dodatkowo, że wynik
musi być konwertowalny do `T`.

***

##### Używanie konceptu

Trzy równoważne sposoby zastosowania konceptu:
```cpp
// Sposób 1: requires po liście parametrów szablonu
template <typename T>
    requires Dodawalny<T>
T suma(T a, T b) { return a + b; }

// Sposób 2: koncept zamiast typename
template <Dodawalny T>
T suma(T a, T b) { return a + b; }

// Sposób 3: skrócona składnia (abbreviated function template)
auto suma(Dodawalny auto a, Dodawalny auto b) { return a + b; }
```

Teraz wywołanie z nieprawidłowym typem daje czytelny błąd:
```cpp
suma("ala", "ola"); // błąd: typ 'const char*' nie spełnia konceptu Dodawalny
```

Komunikat wskazuje miejsce wywołania i podaje nazwę niespełnionego konceptu.

***

##### Standardowe koncepty (`<concepts>`)

C++20 dostarcza bogaty zestaw gotowych konceptów w nagłówku `<concepts>`:

**Koncepty typów:**
```cpp
std::integral<T>          // typ całkowity (int, long, char...)
std::floating_point<T>    // typ zmiennoprzecinkowy
std::signed_integral<T>   // całkowity ze znakiem
std::unsigned_integral<T> // całkowity bez znaku
std::arithmetic<T>        // całkowity lub zmiennoprzecinkowy
```

**Koncepty relacji między typami:**
```cpp
std::same_as<T, U>        // T i U to ten sam typ
std::convertible_to<T, U> // T jest konwertowalny do U
std::derived_from<T, B>   // T dziedziczy po B
std::common_with<T, U>    // T i U mają wspólny typ
```

**Koncepty operacji:**
```cpp
std::equality_comparable<T>      // T obsługuje == i !=
std::totally_ordered<T>          // T obsługuje pełne porównanie
std::copyable<T>                 // T można kopiować
std::movable<T>                  // T można przenosić
std::regular<T>                  // T jest kopiowalne, przenoszalne i equality_comparable
std::invocable<F, Args...>       // F można wywołać z argumentami Args
std::predicate<F, Args...>       // F zwraca bool dla Args
```

***

##### Wyrażenia `requires` — szczegóły

Wyrażenie `requires` może zawierać cztery rodzaje wymagań:
```cpp
template <typename T>
concept Kontener = requires(T c)
{
    // Wymaganie proste: wyrażenie musi być poprawne
    c.begin();
    c.end();

    // Wymaganie typowe: typ musi istnieć
    typename T::value_type;
    typename T::iterator;

    // Wymaganie złożone: wyrażenie musi być poprawne i mieć określony typ
    { c.size() } -> std::convertible_to<std::size_t>;

    // Wymaganie noexcept: wyrażenie musi być noexcept
    { c.empty() } noexcept -> std::convertible_to<bool>;
};
```

***

##### Klauzula `requires` vs wyrażenie `requires`

Warto odróżnić dwa użycia słowa `requires`:
```cpp
// Klauzula requires — ogranicza szablon (przyjmuje bool)
template <typename T>
    requires std::integral<T>    // klauzula: bool
void f(T x);

// Wyrażenie requires — sprawdza poprawność wyrażeń (zwraca bool)
template <typename T>
    requires requires(T x) { x + x; }  // wyrażenie: sprawdza czy x+x działa
void g(T x);
```

Podwójne `requires requires` jest poprawną składnią — pierwsze to klauzula,
drugie to wyrażenie.

***

##### Porównanie z SFINAE

Przed C++20 podobne efekty osiągano przez SFINAE z `std::enable_if`:
```cpp
// C++17 — SFINAE: trudne do czytania i pisania
template <typename T,
          std::enable_if_t<std::is_integral_v<T>, int> = 0>
void f(T x);

// C++20 — koncepty: czytelne i jasne
template <std::integral T>
void f(T x);
```

Koncepty są preferowanym sposobem ograniczania szablonów w C++20 i nowszych.
SFINAE nadal działa, ale jest uważane za przestarzały idiom w nowym kodzie.

***

#### (C++20): Moduły (`import`, `module`)

Od początku C++ kod był organizowany przy pomocy **nagłówków** (pliki `.h`/`.hpp`)
dołączanych przez `#include`. System ten ma poważne wady:

* każdy plik `.cpp` dołączający nagłówek **kompiluje go od nowa**,
* symbole z nagłówka trafiają do **globalnej przestrzeni nazw** pliku,
* kolejność dołączania nagłówków może mieć znaczenie,
* makra z jednego nagłówka mogą wpływać na inny,
* czas kompilacji dużych projektów jest bardzo długi.

C++20 wprowadza **moduły** — nowy mechanizm organizacji kodu, który rozwiązuje
te problemy.

##### Tworzenie modułu

```cpp
// plik: matematyka.cpp (lub matematyka.ixx na MSVC)

export module matematyka;  // deklaracja modułu

export int dodaj(int a, int b)  // eksportowana funkcja
{
    return a + b;
}

int pomocnicza(int x)  // nieeksportowana — widoczna tylko wewnątrz modułu
{
    return x * 2;
}
```

Słowo `export` przed `module` deklaruje moduł.
Słowo `export` przed funkcją lub typem udostępnia go użytkownikom modułu.

***

##### Importowanie modułu

```cpp
// plik: main.cpp

import matematyka;  // importuje moduł — nie #include

int main()
{
    int wynik = dodaj(2, 3);    // 5
    // pomocnicza(5);           // błąd — nie jest eksportowana
}
```

***

##### Eksportowanie bloków i przestrzeni nazw

```cpp
export module geometria;

// Eksportowanie bloku — wygodne dla wielu deklaracji
export
{
    struct Punkt { int x, y; };
    double odleglosc(Punkt a, Punkt b);
}

// Eksportowanie całej przestrzeni nazw
export namespace geo
{
    struct Wektor { double x, y, z; };
    double dlugosc(Wektor v);
}
```

***

##### Podmoduły i partycje

Duże moduły można dzielić na **partycje**:
```cpp
// plik: matematyka-podstawy.cpp
export module matematyka:podstawy;  // partycja 'podstawy' modułu 'matematyka'

export int dodaj(int a, int b) { return a + b; }
```

```cpp
// plik: matematyka.cpp
export module matematyka;

export import :podstawy;  // re-eksportuje partycję
```

***

##### Nagłówkowe jednostki (header units)

Dla stopniowej migracji C++20 pozwala importować tradycyjne nagłówki
jako moduły (wsparcie zależne od kompilatora):
```cpp
import <vector>;    // importuje nagłówek standardowy jako moduł
import "moj.h";     // importuje lokalny nagłówek jako moduł
```

***

##### Zalety modułów względem nagłówków

* **Szybsza kompilacja** — moduł jest kompilowany raz, wynik jest buforowany,
* **Izolacja makr** — makra zdefiniowane w module nie przeciekają do importujących,
* **Brak problemów z kolejnością** — moduły nie zależą od kolejności importu,
* **Jawna kontrola eksportu** — dokładnie wiadomo co jest publicznym API modułu.

> **Uwaga praktyczna:** wsparcie kompilatorów dla modułów w C++20 jest wciąż
> niekompletne lub wymaga specjalnej konfiguracji systemu budowania.
> GCC 11+, Clang 16+ i MSVC 2019+ mają podstawowe wsparcie.
> Pełne wsparcie narzędzi budowania (CMake, Make) pojawiło się stopniowo
> po 2022 roku. W nowych projektach warto już używać modułów,
> ale migracja istniejących dużych projektów wymaga czasu.

***

#### (C++20): Korutyny (`co_await`, `co_return`, `co_yield`)

**Korutyna** to funkcja, która może **zawiesić swoje wykonanie** w połowie
i **wznowić je później** — bez blokowania wątku i bez tworzenia nowego wątku.

Zwykła funkcja działa sekwencyjnie: wchodzi, wykonuje się, wychodzi.
Korutyna może wyjść tymczasowo (zawiesić się), a potem wrócić do miejsca
zawieszenia i kontynuować.

##### Trzy nowe słowa kluczowe

* `co_return` — kończy korutynę i opcjonalnie zwraca wartość,
* `co_yield` — zawiesza korutynę i zwraca wartość pośrednią (jak iterator),
* `co_await` — zawiesza korutynę i czeka na zakończenie operacji asynchronicznej.

Każda funkcja zawierająca którekolwiek z tych słów kluczowych
jest automatycznie korutyną.

***

##### Przykład 1 — generator (co_yield)

Korutyna jako generator nieskończonej sekwencji liczb:
```cpp
#include <generator> // C++23 — w C++20 wymaga własnej implementacji

std::generator<int> liczby_naturalne()
{
    int n = 0;
    while (true)
    {
        co_yield n++;  // zawieś i zwróć n, potem kontynuuj
    }
}

int main()
{
    for (int x : liczby_naturalne() | std::views::take(5))
        std::cout << x << " "; // 0 1 2 3 4
}
```

Korutyna `liczby_naturalne` nie oblicza wszystkich liczb z góry —
generuje kolejną dopiero gdy jest potrzebna (**lazy evaluation**).

***

##### Przykład 2 — operacja asynchroniczna (co_await)

Typowe zastosowanie: kod asynchroniczny pisany w stylu sekwencyjnym:
```cpp
// Przykład konceptualny — wymaga frameworka asynchronicznego
Task<std::string> pobierzDane(std::string url)
{
    // zawieś korutynę i czekaj na wynik operacji sieciowej
    // wątek jest wolny w tym czasie — może obsługiwać inne zadania
    auto odpowiedz = co_await klient.get(url);
    auto tresc     = co_await odpowiedz.tekst();
    co_return tresc;
}

Task<void> main_task()
{
    std::string dane = co_await pobierzDane("https://przyklad.pl/api");
    std::cout << dane;
}
```

Kod wygląda sekwencyjnie, ale nie blokuje wątku podczas oczekiwania —
wątek może w tym czasie wykonywać inne korutyny.

***

##### Jak działają korutyny wewnętrznie

Kompilator przekształca korutynę w obiekt zawierający:

* **ramkę korutyny** (_coroutine frame_) — stan lokalnych zmiennych
  i miejsce zawieszenia,
* obiekt **promise** — kontroluje zachowanie korutyny
  (co zwraca, jak się zawiesza, jak obsługuje wyjątki),
* obiekt **handle** (`std::coroutine_handle`) — pozwala wznowić
  lub zniszczyć zawieszoną korutynę.

C++20 dostarcza tylko **niskopoziomowe mechanizmy** (`co_await`, `co_yield`,
`co_return`, `std::coroutine_handle`, `std::suspend_always`, `std::suspend_never`).
Wysokopoziomowe typy jak `Task<T>` czy `Generator<T>` muszą być
dostarczone przez bibliotekę lub napisane przez programistę.

> `std::generator<T>` jest dostępny dopiero od C++23
> W C++20 można używać np. cppcoro lub własnej implementacji

***

##### Kiedy używać korutyn

* **Generatory** — leniwa generacja sekwencji danych bez buforowania wszystkiego,
* **Kod asynchroniczny** — operacje I/O, sieciowe, bez blokowania wątków,
* **Potoki przetwarzania danych** — korutyny jako etapy pipeline,
* **Maszyny stanów** — zawieszenie w konkretnym stanie, wznowienie po zdarzeniu.

> **Uwaga praktyczna:** korutyny w C++20 to mechanizm niskopoziomowy.
> W praktyce używa się ich przez biblioteki wyższego poziomu:
> **cppcoro**, **Asio** (Boost/standalone), **libcoro**, lub frameworki
> jak Qt (od wersji 6.5) i POCO. Bezpośrednie pisanie własnych typów
> promise jest skomplikowane i zazwyczaj niepotrzebne.

***

#### (C++17): `auto` jako typ parametru szablonu niebędącego typem

Szablony mogą przyjmować nie tylko typy, ale też **wartości** jako parametry
(tzw. _non-type template parameters_). Przed C++17 typ takiej wartości trzeba
było podać jawnie:
```cpp
// C++11/14 — typ parametru musi być jawny
template <int N>
struct Tablica { int dane[N]; };

template <std::size_t N>
struct InnaStruktura { /* ... */ };
```

C++17 pozwala użyć `auto`, żeby kompilator sam wywnioskował typ parametru:
```cpp
template <auto N>
struct Tablica { int dane[N]; };

Tablica<42>  t1; // N ma typ int
Tablica<42u> t2; // N ma typ unsigned int
```

Przydatne gdy chcemy napisać szablon działający dla różnych typów całkowitych
bez powielania kodu:
```cpp
template <auto Wartosc>
constexpr auto podwoj()
{
    return Wartosc * 2;
}

podwoj<21>();    // zwraca int 42
podwoj<21u>();   // zwraca unsigned int 42
podwoj<21ll>();  // zwraca long long 42
```

***

#### (C++17): Zmienne `inline`

W C++ obowiązuje **reguła jednej definicji** (ODR — _One Definition Rule_):
zmienna globalna lub statyczna może być **zdefiniowana tylko raz** w całym programie.
Funkcje można oznaczać jako `inline`, co pozwala umieszczać ich definicje
w nagłówkach — kompilator zapewnia, że mimo wielokrotnego dołączenia nagłówka
powstanie tylko jedna definicja. Zmienne nie miały analogicznego mechanizmu.

Przed C++17 umieszczenie definicji zmiennej w nagłówku i dołączenie go
w wielu plikach `.cpp` powodowało błąd linkera:
```cpp
// naglowek.h
int licznik = 0; // błąd: wielokrotna definicja przy dołączeniu w wielu plikach
```

Standardowe obejście: deklaracja `extern` w nagłówku i definicja w jednym pliku `.cpp`:
```cpp
// naglowek.h
extern int licznik;

// naglowek.cpp
int licznik = 0;
```

C++17 wprowadza zmienne `inline` — działają analogicznie do funkcji `inline`:
```cpp
// naglowek.h
inline int licznik = 0; // można dołączyć w wielu plikach — linker scala w jedną definicję
```

Jest to szczególnie przydatne dla **stałych i zmiennych statycznych w klasach**,
które przed C++17 wymagały osobnej definicji w pliku `.cpp`:
```cpp
// C++11/14
struct Konfiguracja
{
    static const int MAX = 100;      // deklaracja w klasie
};
const int Konfiguracja::MAX;         // definicja wymagana w .cpp

// C++17
struct Konfiguracja
{
    static inline int MAX = 100;     // definicja bezpośrednio w klasie
};
```

Zmienne `constexpr` na poziomie klasy są od C++17 **niejawnie `inline`**,
więc ten konkretny przypadek nie wymaga jawnego `inline`.

***

#### (C++17): Gwarantowane pominięcie kopiowania (copy elision)

Gdy funkcja zwraca obiekt przez wartość, C++ teoretycznie tworzy obiekt tymczasowy
i kopiuje go (lub przenosi) do miejsca docelowego. W praktyce kompilatory
od dawna stosowały optymalizację **RVO** (_Return Value Optimization_),
która eliminowała to kopiowanie — ale była **opcjonalna**. Kompilator mógł,
ale nie musiał jej zastosować. Oznaczało to, że typ zwracany musiał mieć
dostępny konstruktor kopiujący lub przenoszący, nawet jeśli w praktyce
nigdy nie był wywoływany.

C++17 **gwarantuje** pominięcie kopiowania w konkretnym przypadku:
gdy prvalue (obiekt tymczasowy bez nazwy) jest używane do inicjalizacji
obiektu tego samego typu. Obiekt tymczasowy jest konstruowany **bezpośrednio**
w miejscu docelowym — nie ma żadnego pośredniego kopiowania ani przenoszenia:
```cpp
struct NieKopiowalny
{
    NieKopiowalny() = default;
    NieKopiowalny(const NieKopiowalny&) = delete;
    NieKopiowalny(NieKopiowalny&&) = delete;
};

NieKopiowalny stworz()
{
    return NieKopiowalny(); // C++17: OK — obiekt konstruowany bezpośrednio w miejscu docelowym
}

NieKopiowalny obj = stworz(); // C++17: OK — żadne kopiowanie ani przenoszenie nie ma miejsca
```

W C++11/14 powyższy kod był błędem kompilacji — mimo że kompilator i tak
nie kopiowałby obiektu, standard wymagał **dostępności** konstruktora kopiującego
lub przenoszącego.

**Co jest gwarantowane, a co nie:**

* **Gwarantowane** (C++17): inicjalizacja z prvalue tego samego typu —
  `T obj = T(args)` lub zwracanie prvalue z funkcji.
* **Niegwarantowane** (nadal opcjonalne): NRVO (_Named_ RVO) — gdy funkcja
  zwraca **nazwaną** zmienną lokalną. Kompilatory niemal zawsze to robią,
  ale standard nadal tego nie wymaga.

```cpp
NieKopiowalny stworz2()
{
    NieKopiowalny lokalny; // nazwana zmienna
    return lokalny;        // NRVO — opcjonalne, zależne od kompilatora
}
```

***

#### (C++20): Inicjalizatory oznaczone (designated initializers)

C++20 wprowadza składnię pozwalającą inicjalizować pola struktury **po nazwie**,
analogiczną do mechanizmu z języka C99:
```cpp
struct Punkt
{
    int x;
    int y;
    int z = 0;
};

Punkt p = { .x = 1, .y = 2 };       // z == 0 (wartość domyślna)
Punkt q = { .x = 1, .y = 2, .z = 3 };
```

Zalety względem zwykłej inicjalizacji agregatowej:

* kod jest samodokumentujący — widać które pole otrzymuje którą wartość,
* zmiana kolejności pól w strukturze nie psuje istniejącego kodu
  (kompilator zgłosi błąd jeśli nazwy się nie zgadzają),
* pola pominięte otrzymują wartość domyślną.

**Ważne ograniczenia:**

* pola muszą być inicjalizowane **w kolejności deklaracji** w strukturze,
* nie można mieszać inicjalizatorów oznaczonych ze zwykłymi,
* działa tylko dla **agregatów** (struktury bez konstruktorów użytkownika,
  bez dziedziczenia z klas nieagregatowych).

```cpp
Punkt r = { .y = 2, .x = 1 }; // błąd — kolejność odwrotna niż w definicji
Punkt s = { .x = 1, 2 };      // błąd — mieszanie stylów
```

> **Uwaga:** C99 pozwala na inicjalizatory w dowolnej kolejności i z pominięciem
> pól między oznaczonymi. C++20 jest tu bardziej restrykcyjny.

***

#### (C++20): Operator trójstronnego porównania (`<=>`)

Przed C++20 implementacja pełnego zestawu operatorów porównania dla klasy
wymagała pisania sześciu osobnych operatorów: `==`, `!=`, `<`, `>`, `<=`, `>=`.
Było to żmudne i podatne na błędy — szczególnie gdy logika porównania była złożona.

C++20 wprowadza **operator trójstronnego porównania** `<=>`,
zwany też operatorem statku kosmicznego (_spaceship operator_).
Zwraca on nie `bool`, lecz wartość opisującą **relację** między porównywanymi obiektami.

**Typ wyniku zależy od kategorii porównania:**

* `std::strong_ordering` — dla typów z pełnym porządkiem liniowym
  (np. liczby całkowite): `less`, `equal`, `greater`,
* `std::weak_ordering` — dla typów gdzie równoważność nie oznacza identyczności
  (np. porównanie case-insensitive napisów): `less`, `equivalent`, `greater`,
* `std::partial_ordering` — dla typów gdzie niektóre pary są nieporównywalne
  (np. liczby zmiennoprzecinkowe — `NaN` nie jest ani mniejszy, ani większy,
  ani równy): `less`, `equivalent`, `greater`, `unordered`.

**Użycie:**
```cpp
#include <compare> // definicje std::strong_ordering / weak_ordering / partial_ordering

int a = 3, b = 5;

auto wynik = a <=> b;
// wynik NIE jest liczbą typu int.
// wynik ma typ std::strong_ordering (bo int ma pełny porządek liniowy).
// std::strong_ordering to typ "enum‑like", który może przyjąć jedną z wartości:
//   - std::strong_ordering::less
//   - std::strong_ordering::equal
//   - std::strong_ordering::greater
//
// UWAGA: to NIE są wartości liczbowe (-1, 0, 1)!
// To symboliczne stany opisujące relację między obiektami.

if (wynik < 0)  std::cout << "a < b";
    // Porównanie z 0 działa, bo std::strong_ordering ma przeciążone operatory
    // <, ==, > względem liczby 0.
    // wynik < 0 jest równoważne:
    // wynik == std::strong_ordering::less
    
if (wynik == 0) std::cout << "a == b"; // wynik == std::strong_ordering::equal
if (wynik > 0)  std::cout << "a > b"; // wynik == std::strong_ordering::greater
```

**Automatyczne generowanie operatorów porównania:**

Najważniejsza praktyczna zaleta: zdefiniowanie `operator<=>` w klasie
automatycznie generuje wszystkie sześć operatorów porównania.
Dodanie `= default` pozwala kompilatorowi wygenerować porównanie
pole po polu:
```cpp
struct Punkt
{
    int x;
    int y;

    auto operator<=>(const Punkt&) const = default;
    // kompilator generuje: ==, !=, <, >, <=, >=
    // porównując kolejno x, potem y
};

Punkt p1{1, 2}, p2{1, 3};

p1 < p2;   // true — x równe, y mniejsze
p1 == p2;  // false
```

**Kiedy `= default` nie wystarczy:**

Jeśli chcemy niestandardowej logiki porównania, definiujemy `operator<=>`
ręcznie. Wystarczy zdefiniować `<=>` i `==` — reszta jest generowana automatycznie:
```cpp
struct NapisCI // porównanie case-insensitive
{
    std::string dane;

    std::weak_ordering operator<=>(const NapisCI& inny) const
    {
        // porównanie ignorujące wielkość liter
        return /* ... */;
    }

    bool operator==(const NapisCI& inny) const
    {
        return (*this <=> inny) == std::weak_ordering::equivalent;
    }
};
```

> **Uwaga:** `operator<=>` z `= default` generuje też `operator==` z `= default`.
> Jeśli definiujesz `<=>` ręcznie, musisz też zdefiniować `==` osobno — kompilator go nie wygeneruje.

***

#### Jawne operatory konwersji (explicit conversion operators)

W C++98 słowo kluczowe `explicit` można było stosować tylko do konstruktorów, aby zapobiec **niejawnym konwersjom typu** wykonywanym przez konstruktory jednoargumentowe.
Nie działało to jednak dla **operatorów konwersji**.

Przykład problemu:

* inteligentny wskaźnik może mieć `operator bool()`,
* dzięki temu można go używać w instrukcjach warunkowych:
```cpp
if (inteligentnyWskaznik) { ... }
```

* ale `bool` w C++ jest **typem arytmetycznym**,
* więc może konwertować się niejawnie do `int`, `double`, itd.,
* co pozwala na niezamierzone operacje matematyczne.

To klasyczny problem znany jako **idiom bezpiecznego boola** (_safe bool idiom_).

##### C++11: `explicit` dla operatorów konwersji

C++11 pozwala oznaczać operatory konwersji jako `explicit`, np.:
```cpp
explicit operator bool() const;
```

Efekt:

* operator **nie może być użyty w konwersjach niejawnych**,

* ale **może być użyty w kontekstach wymagających wartości logicznej**, takich jak:

  * warunek `if`,
  * warunek pętli `while` / `for`,
  * operatory logiczne (`&&`, `||`, `!`).

Czyli:

* `if (obj)` → **dozwolone**,
* `int x = obj;` → **błąd**,
* `double y = obj;` → **błąd**.

To elegancko rozwiązuje problem **safe bool**.

***

#### `noexcept` — specyfikacja i operator braku wyjątków

W C++03 istniał mechanizm **dynamicznych specyfikacji wyjątków** (`throw(...)`),
pozwalający deklarować, jakie wyjątki funkcja może rzucić:
```cpp
void funkcja() throw(std::runtime_error); // może rzucić tylko runtime_error
void inna()    throw();                   // nie rzuca żadnych wyjątków
```

W praktyce mechanizm ten okazał się nieudany:

* sprawdzanie odbywało się **w czasie wykonywania**, nie kompilacji,
* naruszenie specyfikacji powodowało wywołanie `std::unexpected()`, a nie błąd kompilacji,
* kompilatory nie mogły na tej podstawie robić optymalizacji,
* kod obsługi był kosztowny nawet gdy wyjątki nie były rzucane.

C++11 zastępuje go słowem kluczowym `noexcept`.

##### `noexcept` jako specyfikator

Oznacza, że funkcja **nie rzuca wyjątków**:
```cpp
void funkcja() noexcept;          // nie rzuca wyjątków
void inna()    noexcept(true);    // równoważne — nie rzuca
void jeszcze() noexcept(false);   // może rzucać (domyślne zachowanie)
```

Jeśli funkcja oznaczona `noexcept` rzuci wyjątek, program wywołuje `std::terminate()`
natychmiast — bez rozwijania stosu. To gwarancja silniejsza niż w C++03.

Kompilator może wykorzystać `noexcept` do **optymalizacji** — np. `std::vector`
użyje konstruktora przenoszącego zamiast kopiującego tylko wtedy, gdy przenoszenie
jest `noexcept`. Bez tej gwarancji musi kopiować, żeby zachować silną gwarancję wyjątków
przy realokacji.

Dlatego konstruktory przenoszące i operatory przenoszące powinny być oznaczone `noexcept`
wszędzie tam, gdzie to możliwe:
```cpp
class Bufor
{
    int* dane;
    std::size_t rozmiar;

public:
    Bufor(Bufor&& inny) noexcept  // bez noexcept vector będzie kopiował zamiast przenosić
        : dane(inny.dane), rozmiar(inny.rozmiar)
    {
        inny.dane = nullptr;
        inny.rozmiar = 0;
    }
};
```

***

##### `noexcept` jako operator

`noexcept(wyrażenie)` użyte jako **operator** (nie specyfikator) zwraca `bool`
w czasie kompilacji — `true` jeśli wyrażenie nie może rzucić wyjątku:
```cpp
int x = 5;
constexpr bool a = noexcept(x + 1);      // true — dodawanie int nie rzuca
constexpr bool b = noexcept(new int(1)); // false — new może rzucić bad_alloc
```

Pozwala to warunkowo oznaczać funkcje jako `noexcept` na podstawie właściwości
używanych przez nie typów:
```cpp
template <typename T>
void zamien(T& a, T& b) noexcept(noexcept(T(std::move(a))))
{
    T tmp = std::move(a);
    a = std::move(b);
    b = std::move(tmp);
}
```

Funkcja `zamien` jest `noexcept` dokładnie wtedy, gdy przenoszenie `T` jest `noexcept`.

***

##### Uzupełnienie (C++17): `noexcept` jako część typu funkcji

Od C++17 `noexcept` jest częścią **typu** funkcji, a nie tylko jej deklaracji.
Wskaźnik do funkcji `noexcept` i wskaźnik do zwykłej funkcji to różne typy:
```cpp
void f() noexcept;
void g();

void (*pf)() noexcept = &f; // OK
void (*pg)() noexcept = &g; // błąd — g() nie jest noexcept
```

Przed C++17 obie deklaracje miały ten sam typ wskaźnika, co uniemożliwiało
kompilatorowi i narzędziom statycznej analizy dokładniejsze sprawdzanie gwarancji wyjątków.

***

#### Aliasowanie szablonów (template aliases)

W C++03 można było tworzyć `typedef`, ale tylko jako alias **konkretnego typu**, np.:

* alias typu zwykłego,
* alias konkretnej specjalizacji szablonu.

Nie można było tworzyć aliasów **samych szablonów**.

Przykład niepoprawny w C++03:
```cpp
template <typename Pierwszy, typename Drugi, int Trzeci>
class JakisTyp;

template <typename Drugi>
typedef JakisTyp<InnyTyp, Drugi, 5> NazwaTypedefu; // Niepoprawne w C++03
```

##### C++11: aliasy szablonów przez `using`

C++11 wprowadza składnię:
```cpp
template <typename Pierwszy, typename Drugi, int Trzeci>
class JakisTyp;

template <typename Drugi>
using NazwaTypu = JakisTyp<InnyTyp, Drugi, 5>;
```

To jest **pełnoprawny alias szablonu**.

***

##### `using` jako nowoczesny zamiennik `typedef`

```cpp
typedef void (*TypFunkcji)(double); // stary styl
using TypFunkcji = void (*)(double); // nowy styl
```

Zalety `using`:

* czytelniejszy,
* działa z aliasami szablonów,
* lepiej współpracuje z `template <...>`.

***

##### (C++14): zmienne szablonowe (variable templates)

W poprzednich wersjach C++ szablonami mogły być jedynie funkcje, klasy oraz aliasy typów.
C++14 rozszerza ten mechanizm, pozwalając tworzyć **szablonowe zmienne** — czyli zmienne, których typ i wartość zależą od parametru szablonu.

Przykładowo, można zdefiniować stałą `PI` zależną od typu:
```cpp
template <typename T>
constexpr T PI = T(3.141592653589793238462643383);
```

Dzięki temu:
```cpp
double d = PI<double>;       // 3.1415926535897931...
float  f = PI<float>;        // 3.1415927f
int    i = PI<int>;          // 3
```

Zmienne szablonowe podlegają **tym samym zasadom specjalizacji**, co funkcje i klasy szablonowe:
```cpp
template <>
constexpr const char* PI<const char*> = "pi";
```

Mechanizm ten jest szczególnie przydatny do definiowania:

* stałych zależnych od typu (np. `epsilon<T>`, `zero<T>`, `identity<T>`),
* parametrów konfiguracyjnych w metaprogramowaniu,
* wartości używanych w kontekstach `constexpr`.

Zmienne szablonowe stanowią naturalne uzupełnienie aliasów szablonów z C++11 i są ważnym elementem nowoczesnego stylu programowania szablonowego.

***

#### Unia bez ograniczeń (unrestricted unions)

W C++03 unie (`union`) miały poważne ograniczenia:

* nie mogły zawierać obiektów z **nietrywialnym konstruktorem** lub **destruktorem**,
* nie mogły zawierać typów z nietrywialnymi funkcjami specjalnymi.

C++11 **znosi część tych ograniczeń**.

Jeśli unia zawiera typ z nietrywialnymi funkcjami specjalnymi, to:

* kompilator **nie wygeneruje automatycznie** odpowiednich funkcji specjalnych dla unii,
* trzeba je zdefiniować ręcznie.

Przykład unii dozwolonej w C++11:
```cpp
#include <new> // Potrzebne do użycia placement 'new'.

struct Punkt
{
    int a;
    int b;

    Punkt() {}

    Punkt(int x, int y)
        : a(x), b(y) {} // ← "poprawiony błąd 'x(a), y(b)' z przykładu z wikipedii."
};

union MojaUnia
{
    int z;
    double w;
    Punkt p; // Niepoprawne w C++03; poprawne w C++11.

    // Z powodu składowej Punkt, teraz potrzebna jest definicja konstruktora.
    MojaUnia() {}

    MojaUnia(const Punkt& punktParam)
        : p(punktParam) {} // Konstruuje obiekt Punkt z użyciem listy inicjalizacyjnej.

    MojaUnia& operator=(const Punkt& punktParam)
    {
        // Przypisuje obiekt Punkt z użyciem placement 'new'.
        new (&p) Punkt(punktParam);
        return *this;
    }
};
```

Zmiany te **nie psują istniejącego kodu**, ponieważ jedynie **luzują wcześniejsze ograniczenia**.

***

### Ulepszenia funkcjonalności języka

Te funkcje pozwalają językowi robić rzeczy, które wcześniej były niemożliwe, bardzo rozwlekłe lub wymagały nieprzenośnych bibliotek.

#### Szablony wariadyczne (Variadic templates)

W C++03 jedynym sposobem na napisanie funkcji przyjmującej dowolną liczbę argumentów były **funkcje wariadyczne w stylu C** (`...` + `va_list`, `va_arg`, `va_start`). Były one bardzo niebezpieczne – brak sprawdzania typów, łatwe błędy, problemy z alignmentem i niezdefiniowane zachowanie przy złym użyciu.

C++11 wprowadza **szablony wariadyczne** – mechanizm, który pozwala szablonom (zarówno klasom, jak i funkcjom) przyjmować **zmienną liczbę parametrów** w sposób **w pełni bezpieczny typowo**.

##### Podstawowa składnia

```cpp
template <typename... Args>        // Args...  – "parameter pack" (paczka parametrów)
void mojaFunkcja(Args... args)     // args...  – paczka argumentów
{
    // ...
}
```

`typename... Args` oznacza „dowolna liczba dowolnych typów”.

***

##### Prosty przykład – bezpieczna funkcja wypisująca dowolną liczbę argumentów

```cpp
#include <iostream>

void print() 
{
    std::cout << std::endl;                    // przypadek bazowy (0 argumentów)
}

template <typename T, typename... Args>
void print(T first, Args... rest)
{
    std::cout << first << " ";
    print(rest...);                            // rekurencyjne wywołanie z resztą argumentów
}

int main()
{
    print(42, 3.14, "C++11", 'x', "jest super"); // działa z różnymi typami
}
```

**Uwaga:** Funkcja _print_ używa **rekurencji szablonów** (kompilator tworzy kolejne wersje funkcji, za każdym razem z jednym argumentem mniej – aż dojdzie do wersji z zeroma argumentami).

Dzięki temu mechanizmowi kompilator w czasie kompilacji generuje kod dla każdej kombinacji typów i liczby argumentów. Wszystko jest sprawdzane typowo, w czasie kompilacji, a programista nie musi ręcznie wyciągać argumentów za pomocą niebezpiecznych makr (`va_arg`).

To jedna z najważniejszych zmian w C++11, która ogromnie ułatwiła pisanie elastycznych i bezpiecznych bibliotek.

***

##### Dlaczego to jest duża zmiana?

- **Bezpieczeństwo typów** – kompilator wie dokładnie, jakie typy przekazujesz.
- **Brak rzutowań** i ręcznego wyciągania argumentów przez `va_arg`.
- Umożliwia tworzenie bardzo elastycznych bibliotek (np. `std::tuple`, `std::make_shared`, `std::thread`, formatowanie tekstu itp.).
- Działa zarówno dla funkcji, jak i dla klas szablonowych (`std::tuple<int, double, std::string>` to właśnie szablon wariadyczny).

W praktyce w C++11 najczęściej spotykasz je w **formie rekurencyjnej** (jak powyżej), czyli takiej, w której funkcja szablonowa wywołuje samą siebie, stopniowo rozpakowując parameter pack — to podstawowy wzorzec, który warto zrozumieć na początku.

Przykład:
```cpp
// Przypadek bazowy: funkcja przyjmuje tylko JEDEN argument.
// Gdy rekurencja "zje" wszystkie pozostałe parametry, trafiamy tutaj.
template<typename T>
void print(const T& t)
{
    std::cout << t << "\n";   // wypisz ostatni element i zakończ
}

// Wersja rekurencyjna: funkcja przyjmuje CO NAJMNIEJ dwa argumenty.
// T = pierwszy argument
// Ts... = pozostałe argumenty (parameter pack)
template<typename T, typename... Ts>
void print(const T& t, const Ts&... ts)
{
    std::cout << t << "\n";   // wypisz pierwszy element

    // Wywołanie rekurencyjne:
    // - pierwszy element został wypisany,
    // - więc przekazujemy dalej TYLKO pozostałe argumenty (ts...)
    //
    // Za każdym wywołaniem parameter pack staje się coraz krótszy:
    //   print(1, 2, 3)
    //     → print(2, 3)
    //         → print(3)
    //             → przypadek bazowy
    
    print(ts...); // rekurencja na reszcie
}
```

***

##### Uzupełnienie (C++17): wyrażenia składane (fold expressions)

W C++11/14 rozwijanie paczki parametrów wymagało rekurencji szablonów
(jak w przykładzie z `print` powyżej). C++17 wprowadza **wyrażenia fold**,
które pozwalają zastosować operator do całej paczki bez rekurencji:
```cpp
template <typename... Args>
auto suma(Args... args)
{
    return (args + ...); // fold po operatorze +
}

suma(1, 2, 3, 4); // 10
```

Cztery formy wyrażeń fold (`op` to dowolny operator binarny, `e` to wartość początkowa):

* `(pack op ...)` — prawostronne fold bez wartości początkowej,
* `(... op pack)` — lewostronne fold bez wartości początkowej,
* `(pack op ... op e)` — prawostronne fold z wartością początkową,
* `(e op ... op pack)` — lewostronne fold z wartością początkową.

Przykład z wartością początkową (bezpieczny dla pustej paczki):
```cpp
template <typename... Args>
auto suma(Args... args)
{
    return (0 + ... + args); // lewostronne fold, wartość początkowa 0
}

suma(); // 0 — działa dla pustej paczki
```

Wyrażenia fold eliminują potrzebę pisania przypadku bazowego dla wielu
prostych operacji na paczkach parametrów.

***

#### Nowe literały napisowe

W C++03 istniały tylko dwa rodzaje literałów napisowych:

1. `"tekst"` → tablica zakończona znakiem null typu `const char[]`,
2. `L"tekst"` → tablica zakończona znakiem null typu `const wchar_t[]`,
   gdzie `wchar_t` jest znakiem szerokim o **niezdefiniowanym rozmiarze i semantyce**.

Żaden z tych literałów **nie obsługiwał**:

* UTF‑8,
* UTF‑16,
* UTF‑32,
* ani żadnego innego kodowania Unicode.

***

C++11 wprowadza obsługę trzech kodowań Unicode:

* UTF‑8,
* UTF‑16,
* UTF‑32.

Dodatkowo:

* definicja typu `char` została zmieniona tak, aby **gwarantować**, że ma co najmniej rozmiar potrzebny do przechowywania ośmiobitowego kodowania UTF‑8,

* dodano typy:

  * `char16_t` — przeznaczony do przechowywania UTF‑16,
  * `char32_t` — przeznaczony do przechowywania UTF‑32.

***

Tworzenie literałów napisowych dla każdego kodowania:
```cpp
u8"Jestem napisem UTF-8."
u"To jest napis UTF-16."
U"To jest napis UTF-32."
```

Typy:

* `u8"..."` → `const char[]`,
* `u"..."` → `const char16_t[]`,
* `U"..."` → `const char32_t[]`.

***

Wstawianie punktów kodowych Unicode:
```cpp
u8"To jest znak Unicode: \u2018."
u"To jest większy znak Unicode: \u2018."
U"To jest znak Unicode: \U00002018."
```

Zasady:

* liczba po `\u` to **16‑bitowy** punkt kodowy Unicode (hex, bez `0x`),
* liczba po `\U` to **32‑bitowy** punkt kodowy Unicode,
* można wstawiać tylko **poprawne** punkty kodowe,
* zakres U+D800–U+DFFF jest **zabroniony**, ponieważ jest zarezerwowany dla par surogatów UTF‑16.

##### Uzupełnienie (C++17): literały znakowe UTF-8

C++11 wprowadził literały napisowe UTF-8 (`u8"..."`), ale nie miał odpowiednika
dla pojedynczych znaków. C++17 dodaje literały znakowe UTF-8:
```cpp
char c = u8'a'; // znak ASCII / Basic Latin w kodowaniu UTF-8
```

Ze względu na to, że `char` ma jeden bajt, literały `u8'x'` mogą przechowywać
wyłącznie znaki z zakresu **Basic Latin** (ASCII, U+0000–U+007F) oraz kody sterujące C0.
Próba użycia znaku spoza tego zakresu jest błędem kompilacji.

Głównym celem jest spójność z literałami napisowymi: skoro istnieje `u8"tekst"`,
powinno istnieć też `u8'x'`.

***

##### Uzupełnienie (C++17): szestnastkowe literały zmiennoprzecinkowe

C++17 dodaje możliwość zapisu liczb zmiennoprzecinkowych w systemie szesnastkowym,
analogicznie do składni z języka C99:
```cpp
double d = 0x1.8p+1; // 1.5 × 2¹ = 3.0
float  f = 0x0.4p-2; // 0.25 × 2⁻² = 0.0625
```

Format: `0x<mantysa_hex>p<wykładnik_dziesiętny>`, gdzie:

* `p` oddziela mantysę od wykładnika (potęga dwójki, nie dziesiątki),
* wykładnik jest zawsze dziesiętny i obowiązkowy.

Zalety: zapis heksadecymalny (szestnastkowy) pozwala zapisać dokładną reprezentację binarną
liczby zmiennoprzecinkowej bez zaokrągleń wynikających z konwersji dziesiętno-binarnej.
Przydatne w kodzie niskopoziomowym i przy pracy z IEEE 754.

***

##### Surowe literały napisowe (raw string literals)

C++11 dodaje surowe literały napisowe:
```cpp
R"(Dane napisu \ Różne rzeczy " )"
R"delimiter(Dane napisu \ Różne rzeczy " )delimiter"
```

Zasady:

* wszystko między `"( ... )"` jest częścią napisu,

* znaki `"` i `\` **nie wymagają uciekania** („Uciekanie” ang. _escaping_ - to poprzedzenie znaku backslashem '\\', aby kompilator nie potraktował go jako elementu składni),

* w wersji z delimiterem:

  * napis zaczyna się od `R"delimiter(`,
  * kończy się na `)delimiter"`,
  * `delimiter` może mieć do 16 znaków,
  * nie może zawierać spacji, znaków sterujących, `(`, `)` ani `\`,
  * dzięki delimiterowi można mieć w napisie sekwencję `)"`.

Przykład z oryginału:
```cpp
R"delimiter("(a-z)")delimiter"
```

jest równoważne:
```cpp
"\"(a-z)\""
```
***

Surowe literały można łączyć z Unicode:
```cpp
u8R"XXX(Jestem „surowym UTF-8” napisem.)XXX"
uR"*(To jest „surowy UTF-16” napis.)*"
UR"(To jest „surowy UTF-32” napis.)"
```

***

#### Literały definiowane przez użytkownika (user‑defined literals)

C++03 udostępniał pewną liczbę literałów.
Na przykład zapis `12.5` jest literałem typu `double` o wartości 12.5.
Dodanie sufiksu `f`, jak w `12.5f`, tworzy wartość typu `float` o tej samej wartości.

Sufiksy literałów w C++03 są **sztywno określone przez standard** — programista **nie może** tworzyć własnych modyfikatorów literałów.

C++11 to zmienia: pozwala użytkownikowi definiować **własne sufiksy literałów**, które tworzą obiekty na podstawie znaków występujących w literałach.

##### Surowe i przetworzone literały (raw vs cooked literals)

C++11 rozdziela przetwarzanie literałów na dwa etapy:

* **raw literal** — surowa sekwencja znaków określonego typu,
* **cooked literal** — wartość po interpretacji przez kompilator.

Przykłady:

* literał `1234`
  raw → `'1','2','3','4'`
  cooked → liczba całkowita `1234`

* literał `0xA`
  raw → `'0','x','A'`
  cooked → liczba `10`

Literały mogą być rozszerzane zarówno w formie raw, jak i cooked —
**z wyjątkiem literałów napisowych**, które mogą być przetwarzane tylko w formie cooked,
ponieważ prefiksy (`u8`, `u`, `U`, `L`) zmieniają znaczenie i typ znaków.

***

##### Zasady dotyczące sufiksów użytkownika

* wszystkie literały definiowane przez użytkownika są **sufiksami**,
* **nie można** definiować prefiksów,
* wszystkie sufiksy zaczynające się od czegokolwiek poza `_` są **zarezerwowane przez standard**,
* dlatego każdy sufiks użytkownika **musi zaczynać się od `_`**.

***

##### Literały użytkownika w formie raw (`operator""`)

Literały przetwarzające surową formę definiuje się przez `operator""`.

Przykład:
```cpp
OutputType operator""_mysuffix(const char* literal_string)
{
    // zakładamy, że OutputType ma konstruktor przyjmujący const char*
    OutputType ret(literal_string);
    return ret;
}

OutputType some_variable = 1234_mysuffix;
// zakładamy, że OutputType ma metodę get_value() zwracającą double
assert(some_variable.get_value() == 1234.0);
```

Instrukcja:
```cpp
OutputType some_variable = 1234_mysuffix;
```

wywołuje funkcję literału użytkownika.
Przekazywany jest do niej C‑string `"1234"` — czyli z terminatorem `\0`.

***

##### Alternatywny mechanizm: szablony wariadyczne dla raw literals

Można też przetwarzać literały raw za pomocą **szablonów wariadycznych**:
```cpp
template <char...>
OutputType operator""_tuffix();

OutputType some_variable = 1234_tuffix;
OutputType another_variable = 2.17_tuffix;
```

To instancjuje funkcję jako:
```cpp
operator""_tuffix<'1','2','3','4'>()
```

W tej formie:

* **nie ma** znaku `\0` na końcu,

* celem jest umożliwienie użycia `constexpr`,

* dzięki temu kompilator może przetworzyć literał **w całości w czasie kompilacji**,
  pod warunkiem, że:

  * `OutputType` jest `constexpr`‑konstruktywny i kopiowalny,
  * funkcja literału jest `constexpr`.

***

##### Literały cooked dla liczb

Dla literałów liczbowych cooked literal ma typ:

* `unsigned long long` — dla literałów całkowitych,
* `long double` — dla literałów zmiennoprzecinkowych.

Uwaga:
Nie ma potrzeby obsługi typów całkowitych ze znakiem,
bo znak `-` jest operatorem unarnym, a nie częścią literału.

Przykład:
```cpp
OutputType operator""_suffix(unsigned long long);
OutputType operator""_suffix(long double);

OutputType some_variable = 1234_suffix;      // Używa przeciążenia 'unsigned long long'.
OutputType another_variable = 3.1416_suffix; // Używa przeciążenia 'long double'.
```

***

##### Literały użytkownika dla napisów

Dla literałów napisowych używa się przeciążeń:
```cpp
OutputType operator""_ssuffix(const char* string_values, size_t num_chars);
OutputType operator""_ssuffix(const wchar_t* string_values, size_t num_chars);
OutputType operator""_ssuffix(const char16_t* string_values, size_t num_chars);
OutputType operator""_ssuffix(const char32_t* string_values, size_t num_chars);

OutputType some_variable = "1234"_ssuffix;   // const char*
OutputType some_variable = u8"1234"_ssuffix; // const char*
OutputType some_variable = L"1234"_ssuffix;  // const wchar_t*
OutputType some_variable = u"1234"_ssuffix;  // const char16_t*
OutputType some_variable = U"1234"_ssuffix;  // const char32_t*
```

Nie istnieje alternatywna forma szablonowa dla literałów napisowych.
Literały znakowe działają analogicznie.

***

##### (C++14): standardowe literały użytkownika

C++11 zdefiniował mechanizm literałów użytkownika, ale sama biblioteka standardowa nie dostarczała żadnych gotowych sufiksów.
C++14 wprowadza pierwsze **standardowe literały**, dostępne bez dodatkowych definicji:

**1. Literały napisowe (`"s"`)**

Tworzą odpowiednie typy `std::basic_string`:
```cpp
using namespace std::string_literals;

auto napis = "hello world"s; // std::string
```

**2. Literały czasu (`h`, `min`, `s`, `ms`, `us`, `ns`)**

Tworzą obiekty `std::chrono::duration`:
```cpp
using namespace std::chrono_literals;

auto czas = 60s; // std::chrono::seconds
```

**3. Literały liczb zespolonych (`if`, `i`, `il`)**

Tworzą obiekty `std::complex<float>`, `std::complex<double>`, `std::complex<long double>`:
```cpp
using namespace std::complex_literals;

auto z = 1i; // std::complex<double>
```

Literały `"s"` nie kolidują ze sobą, ponieważ:

* `"tekst"s` działa tylko dla **literałów napisowych**,
* `10s` działa tylko dla **liczb**, tworząc `std::chrono::seconds`.

***

#### Model pamięci dla wielowątkowości

C++11 standaryzuje wsparcie dla programowania wielowątkowego.

Składa się to z dwóch części:

* modelu pamięci, który pozwala na współistnienie wielu wątków w programie,
* wsparcia bibliotecznego dla interakcji między wątkami (zob. sekcję o mechanizmach wątkowych w artykule).

Model pamięci definiuje, kiedy wiele wątków może uzyskiwać dostęp do tego samego miejsca w pamięci oraz określa, kiedy zmiany dokonane przez jeden wątek stają się widoczne dla innych wątków.

##### Pamięć lokalna dla wątku (thread-local storage)

W środowisku wielowątkowym powszechne jest, że każdy wątek ma pewne unikalne zmienne.
Dzieje się tak już dla zmiennych lokalnych funkcji, ale nie dotyczy to zmiennych globalnych i statycznych.

Nowy czas życia obiektu — **thread‑local** (oprócz istniejących: _static_, _dynamic_ i _automatic_) — jest oznaczany specyfikatorem przechowywania `thread_local`.

Każdy obiekt, który mógłby mieć statyczny czas życia (tj. żyć przez cały czas wykonywania programu), może zamiast tego mieć czas życia związany z wątkiem.
Intencją jest to, że podobnie jak inne zmienne o czasie życia statycznego, obiekt thread‑local może być inicjalizowany konstruktorem i niszczony destruktorem.

***

##### Jawnie domyślne funkcje specjalne (explicitly defaulted special member functions)

W C++03 kompilator dostarcza dla klas, które ich nie definiują samodzielnie:

* konstruktor domyślny,
* konstruktor kopiujący,
* operator przypisania kopiującego (`operator=`),
* destruktor.

Programista może nadpisać te domyślne implementacje, definiując własne wersje.
C++ definiuje także kilka globalnych operatorów (np. `operator new`), które działają dla wszystkich klas i które programista może nadpisać.

Jednak kontrola nad tworzeniem tych domyślnych funkcji była ograniczona.
Uczynienie klasy niekopiowalną często osiągano przez zadeklarowanie prywatnego konstruktora kopiującego i operatora przypisania **bez ich definicji**.
Próba użycia takich funkcji narusza Zasadę jednej definicji (One Definition Rule, ODR).
Choć diagnostyka nie jest wymagana, naruszenia mogą skutkować błędem linkera.

W przypadku konstruktora domyślnego kompilator **nie wygeneruje go**, jeśli klasa ma zdefiniowany **jakikolwiek inny konstruktor**.

C++11 pozwala na:

* **jawne zadeklarowanie użycia domyślnych** funkcji specjalnych (`= default`),
* **jawne usunięcie** funkcji (`= delete`).

Przykład:
```cpp
class JakisTyp
{
    JakisTyp() = default; // Konstruktor domyślny jest jawnie zadeklarowany.
    JakisTyp(InnyTyp wartosc);
};
```

***

##### Jawnie usunięte funkcje (explicitly deleted functions)

Funkcję można jawnie wyłączyć.
Jest to przydatne do zapobiegania niejawnych konwersji typów.

Specyfikator `= delete` może być użyty, aby zabronić wywołań funkcji z określonymi typami parametrów:
```cpp
void noInt(double i);
void noInt(int) = delete;
```

Próba wywołania `noInt()` z argumentem typu `int` zostanie odrzucona przez kompilator,
zamiast wykonywać cichą konwersję do `double`.
Wywołanie `noInt()` z `float` nadal działa.

Możliwe jest zabronienie wywołań funkcji dla dowolnego typu innego niż `double` przy użyciu szablonu:
```cpp
double onlyDouble(double d)
{
    return d;
}

template <typename T>
double onlyDouble(T) = delete;
```

Wywołanie `onlyDouble(1.0)` zadziała, natomiast `onlyDouble(1.0f)` spowoduje błąd kompilacji.

Funkcje składowe klas i konstruktory również można usuwać.
Na przykład można zapobiec kopiowaniu obiektów klasy przez usunięcie konstruktora kopiującego i operatora przypisania:
```cpp
class NieKopiowalny
{
    NieKopiowalny();
    NieKopiowalny(const NieKopiowalny&) = delete;
    NieKopiowalny& operator=(const NieKopiowalny&) = delete;
};
```

***

#### Typ `long long int`

W C++03 największym typem całkowitym był `long int`.
Gwarantowano, że ma co najmniej tyle użytecznych bitów, co `int`.
W praktyce powodowało to, że `long int` miał rozmiar **64 bity** w niektórych popularnych implementacjach, a **32 bity** w innych.

C++11 dodaje nowy typ całkowity: **`long long int`**, aby rozwiązać ten problem.

Gwarantuje się, że:

* jest co najmniej tak duży jak `long int`,
* ma **nie mniej niż 64 bity**.

Typ ten został pierwotnie wprowadzony w standardzie **C99**, a większość kompilatorów C++ już wcześniej wspierała go jako rozszerzenie.

##### Uzupełnienie (C++20): gwarantowana reprezentacja two's complement

C++20 gwarantuje, że wszystkie typy całkowite ze znakiem używają reprezentacji
**uzupełnienia do dwóch** (ang. _two's complement_). Przed C++20 standard
dopuszczał inne reprezentacje (uzupełnienie do jedności, znak-moduł),
choć w praktyce wszystkie liczące się platformy używały two's complement.

Oznacza to, że:

* konwersje między typami całkowitymi ze znakiem i bez znaku są teraz
  w pełni zdefiniowane i przewidywalne,
* operacje bitowe na liczbach ze znakiem mają dokładnie zdefiniowane wyniki.

> **Uwaga:** przepełnienie liczb całkowitych ze znakiem (`signed integer overflow`)
> nadal jest **niezdefiniowanym zachowaniem** — gwarancja two's complement
> nie zmienia tego faktu.

***

#### (C++14): literały binarne (`0b`, `0B`)

C++14 wprowadza możliwość zapisu wartości liczbowych w postaci binarnej.
Nowa składnia wykorzystuje przedrostki:

* `0b`
* `0B`

Przykłady:
```cpp
int mask = 0b101010;     // 42
int flags = 0B1100'0011; // 195 (można łączyć z apostrofami)
```

Literały binarne są szczególnie przydatne przy:

* operacjach bitowych,
* programowaniu niskopoziomowym,
* definiowaniu masek i flag,
* pracy z rejestrami sprzętowymi.

Składnia ta jest zgodna z wieloma innymi językami (Java, C#, Swift, Go, Scala, Python, Ruby, OCaml) i była dostępna jako rozszerzenie w niektórych kompilatorach C już od 2007 roku.

***

#### (C++14): separatory cyfr w literałach liczbowych

C++14 pozwala używać apostrofu (`'`) jako **separatora cyfr** w literałach liczbowych.
Separator może być stosowany **dowolnie**, zarówno w literałach całkowitych, jak i zmiennoprzecinkowych, a także w literałach binarnych.

Przykłady:
```cpp
auto literal_calkowity          = 1'000'000;
auto literal_zmiennoprzecinkowy = 0.000'015'3;
auto literal_binarny            = 0b0100'1100'0110;
auto tuzin_krorow              = 12'00'00'000; // format indyjski (12 crore)
```

Separatory cyfr:

* nie wpływają na wartość liczbową,
* służą wyłącznie poprawie czytelności,
* mogą być stosowane w dowolnych miejscach między cyframi,
* są zgodne z podobnymi mechanizmami w innych językach (Java, C#, Swift, Python).

Mechanizm ten ułatwia szybkie rozpoznawanie dużych liczb przez człowieka (tzw. _subitizing_), szczególnie w kodzie niskopoziomowym, obliczeniach finansowych i pracy z dużymi stałymi.

***

#### Asercje statyczne (static assertions)

W C++03 istniały dwie metody testowania asercji:

* makro `assert` — sprawdzane **w czasie wykonywania**,
* dyrektywa preprocesora `#error` — sprawdzana **podczas preprocessingu**, czyli **przed** instancjacją szablonów.

Żadna z nich nie nadaje się do testowania własności zależnych od parametrów szablonu.

C++11 wprowadza nowe narzędzie: **asercje statyczne**, testowane **w czasie kompilacji**, za pomocą słowa kluczowego `static_assert`.

Deklaracja ma postać:
```cpp
static_assert(wyrazenie_stale, komunikat_bledu);
```

Przykłady:
```cpp
static_assert((GREEKPI > 3.14) && (GREEKPI < 3.15),
              "Wartość GREEKPI jest niedokładna!");
```

```cpp
template <class Typ>
struct Sprawdz
{
    static_assert(sizeof(int) <= sizeof(Typ),
                  "Typ T jest zbyt mały!");
};
```

```cpp
using std::is_integral;

template <class Liczbowy>
Liczbowy foo(Liczbowy x, Liczbowy y)
{
    static_assert(is_integral<Liczbowy>::value,
                  "Parametr foo() musi być typem całkowitoliczbowym.");
}
```

Jeśli wyrażenie stałe jest `false`, kompilator generuje komunikat o błędzie.

Pierwszy przykład jest podobny do `#error`, ale preprocesor obsługuje tylko typy całkowite.
W drugim przykładzie asercja jest sprawdzana **przy każdej instancjacji** szablonu `Sprawdz`.

Asercje statyczne są użyteczne także poza szablonami.
Na przykład implementacja algorytmu może zakładać, że `long long` jest większy niż `int` — założenie prawdziwe na większości systemów, ale **niegwarantowane** przez standard.
`static_assert` pozwala wykryć takie niezgodności **w czasie kompilacji**.

##### Uzupełnienie (C++17): komunikat błędu jest opcjonalny

Od C++17 komunikat błędu w `static_assert` stał się **opcjonalny**:
```cpp
static_assert(sizeof(int) == 4);
```

Jeśli warunek jest fałszywy, kompilator generuje domyślny komunikat.

***

##### Uzupełnienie (C++20): `static_assert` w modułach i konceptach

C++20 pozwala używać `static_assert`:

* w modułach (`module`),
* w definicjach konceptów,
* w kontekstach wymagających stałej ewaluacji.

***

#### Pozwolenie na użycie `sizeof` dla składowych klas bez jawnego obiektu

W C++03 operator `sizeof` można stosować do typów i obiektów, ale nie można było zrobić tego:
```cpp
struct JakisTyp
{
    InnyTyp skladowa;
};

sizeof(JakisTyp::skladowa); // Nie działa w C++03. Działa w C++11.
```

To wyrażenie powinno zwrócić rozmiar typu `InnyTyp`.
W C++03 takie użycie jest zabronione i powoduje błąd kompilacji.
C++11 pozwala na to.

To samo dotyczy operatora `alignof` wprowadzonego w C++11 — również może być użyty w analogiczny sposób dla składowych klasy.

> **Uwaga praktyczna:**
> To ułatwia pisanie metaprogramów i szablonów, gdzie chcemy odwołać się do właściwości typu składowej bez potrzeby tworzenia instancji obiektu.

***

#### Kontrola i odpytywanie wyrównania obiektów (Control and query object alignment)

C++11 pozwala odpytywać i kontrolować wyrównanie zmiennych za pomocą operatorów `alignof` i specyfikatora `alignas`.

**`alignof(T)`**:

* zwraca wymagane wyrównanie typu `T` (w bajtach, potęga dwójki),
* zwraca `std::size_t`,
* dla referencji zwraca wyrównanie typu, na który referencja wskazuje,
* dla tablic zwraca wyrównanie typu elementu tablicy.

**`alignas`**:

* kontroluje wyrównanie pamięci dla zmiennej,
* przyjmuje stałą lub typ,
* zapis `alignas(T)` jest równoważny `alignas(alignof(T))`.

Przykład:
```cpp
alignas(float) unsigned char bufor[sizeof(float)];
```

> **Wyjaśnienie dla początkujących:**
> Wyrównanie (alignment) oznacza, że adresy pamięci, pod którymi przechowywane są obiekty danego typu, muszą być wielokrotnością pewnej liczby bajtów.
> Nieprawidłowe wyrównanie może prowadzić do błędów sprzętowych lub spadku wydajności.

##### Uzupełnienie (C++17): interference sizes

C++17 wprowadza stałe:
```cpp
std::hardware_destructive_interference_size
std::hardware_constructive_interference_size
```

Pomagają one unikać _false sharing_ w programach wielowątkowych.

***

##### Uzupełnienie (C++20): alignas w kontekstach constexpr

Od C++20 `alignas` może być używany w obiektach `constexpr`, jeśli wyrównanie jest znane w czasie kompilacji.

***

#### Pozwolenie na implementacje z automatycznym zbieraniem śmieci (Allow garbage collected implementations)

W poprzednich standardach C++ przewidziano mechanizmy sterowane przez programistę (np. `set_new_handler`), ale **nie zdefiniowano pojęcia osiągalności obiektów** w kontekście automatycznego zbierania śmieci.

C++11 definiuje warunki, kiedy wartości wskaźnikowe są **„bezpiecznie pochodne”** od innych wartości.

Implementacja może zadeklarować, że działa w trybie **strict pointer safety**.
W takim przypadku wskaźniki, które nie są pochodne zgodnie z tymi regułami, mogą stać się nieprawidłowe.

> **Nota:**
> Standard **nie wymusza** implementacji garbage collectora,
> ale pozwala implementacjom, które go oferują, działać w sposób zgodny ze standardem.

***

#### Atrybuty (Attributes)

C++11 wprowadza ujednoliconą składnię dla rozszerzeń kompilatora i narzędzi w postaci **atrybutów**, zapisywanych w podwójnych nawiasach kwadratowych `[[...]]`.
Wcześniej rozszerzenia te były realizowane za pomocą dyrektywy `#pragma` lub vendor‑specyficznych słów kluczowych (np. `__attribute__` w GCC, `__declspec` w MSVC).

Atrybut można stosować do różnych elementów kodu źródłowego. Przykład:
```cpp
int [[atrybut1]] zmienna [[atrybut2, atrybut3]];

[[atrybut4(arg1, arg2)]] if (warunek)
{
    [[dostawca::atrybut5]] return zmienna;
}
```

W powyższym przykładzie:

* `atrybut1` odnosi się do **typu** zmiennej `zmienna`,
* `atrybut2` i `atrybut3` odnoszą się do **samej zmiennej**,
* `atrybut4` odnosi się do **instrukcji `if`**,
* `dostawca::atrybut5` odnosi się do **instrukcji `return`**.

Ogólne zasady (z pewnymi wyjątkami):

* atrybut dla **nazwanego bytu** umieszcza się **po nazwie**,
* atrybut dla **nienazwanego bytu** umieszcza się **przed** tym bytem,
* w jednej parze `[[...]]` można wymienić **wiele atrybutów**,
* atrybuty mogą przyjmować **argumenty**,
* atrybuty mogą być zdefiniowane w **przestrzeniach nazw dostawców** (np. `vendor::attr`).

Zalecenie: atrybuty **nie powinny zmieniać semantyki programu** — kod powinien zachowywać ten sam sens nawet wtedy, gdy atrybuty zostaną zignorowane.
Atrybuty służą głównie do przekazywania kompilatorowi dodatkowych informacji (diagnostyka, optymalizacje, analiza kodu).

C++11 definiuje dwa standardowe atrybuty:

* `[[noreturn]]` — informuje, że funkcja **nie zwraca** (np. funkcja kończąca program),
* `[[carries_dependency]]` — pomaga optymalizować kod wielowątkowy, wskazując, że argumenty funkcji lub wartość zwracana **niosą zależność pamięciową**.

> **Ostrzeżenie:** chociaż atrybuty są bezpiecznym mechanizmem rozszerzeń, używanie vendor‑specyficznych atrybutów może zmniejszyć przenośność kodu. Zawsze sprawdź, czy atrybut ma znaczenie w docelowych kompilatorach.

##### Uzupełnienie (C++14): atrybut `[[deprecated]]`

C++14 wprowadza atrybut:
```cpp
[[deprecated("Powód oznaczenia jako przestarzałe")]]
```

Służy do oznaczania elementów programu jako **przestarzałych**, co powoduje generowanie ostrzeżeń kompilatora przy ich użyciu.
Można podać opcjonalny komunikat wyjaśniający powód wycofania i sugerujący alternatywę.

Atrybut `[[deprecated]]` może być stosowany do:

* funkcji,
* metod klas,
* zmiennych,
* pól klas,
* typów,
* przestrzeni nazw,
* szablonów.

Przykład:
```cpp
[[deprecated]]
int funkcja_f();

[[deprecated("funkcja_g() nie jest bezpieczna wątkowo. Użyj funkcja_h()")]]
void funkcja_g(int& x);

void funkcja_h(int& x);

void test()
{
    int a = funkcja_f(); // ostrzeżenie: 'funkcja_f' jest przestarzała
    funkcja_g(a);        // ostrzeżenie: 'funkcja_g' jest przestarzała: funkcja_g() nie jest bezpieczna wątkowo. Użyj funkcja_h()
}
```

Atrybut ten pozwala stopniowo wycofywać stare API, jednocześnie zachowując kompatybilność wsteczną.

C++17 rozszerza też **miejsca**, w których można stosować atrybuty — od tej wersji wolno umieszczać je przy **przestrzeniach nazw** oraz **elementach wyliczenia**:
```cpp
namespace [[deprecated]] stareApi
{
    void funkcja();
}

enum class Kolor
{
    Czerwony,
    Zielony [[deprecated]],  // konkretny element wyliczenia (iterator) oznaczony jako przestarzały
    Niebieski
};
```

Przed C++17 atrybuty przy przestrzeniach nazw i elementach wyliczenia były niedozwolone lub zależne od kompilatora.

***

##### **Uzupełnienie (C++17): atrybuty `[[fallthrough]]`, `[[nodiscard]]`, `[[maybe_unused]]`**

C++17 dodaje trzy ważne atrybuty:

* `[[fallthrough]]` — oznacza zamierzone „przejście” między sekcjami `case` w `switch`,
* `[[nodiscard]]` — oznacza, że wartość zwracana **nie powinna być ignorowana**,
* `[[maybe_unused]]` — oznacza, że element **może nie być używany**, co zapobiega ostrzeżeniom.

Przykład:
```cpp
[[nodiscard]] int policz();
```

***

##### **Uzupełnienie (C++20): atrybut `[[likely]]` i `[[unlikely]]`**

C++20 dodaje atrybuty podpowiadające kompilatorowi przewidywanie gałęzi:
```cpp
if ([[likely]] warunek)
{
    ...
}
else [[unlikely]]
{
    ...
}
```

***

##### Uzupełnienie (C++23): atrybut `[[assume]]`

C++23 wprowadza:
```cpp
[[assume(warunek)]]
```

Informuje kompilator, że dany warunek **zawsze jest prawdziwy**, co może umożliwić dodatkowe optymalizacje.

***

## Zmiany w standardowej bibliotece C++

W standardzie C++11 wprowadzono szereg nowych funkcji do standardowej biblioteki.
Wiele z nich dałoby się zaimplementować w starym standardzie, ale część opiera się — w mniejszym lub większym stopniu — na nowych cechach rdzenia języka C++11.

Duża część nowych bibliotek została wcześniej zdefiniowana w dokumencie znanym jako **TR1 (Library Technical Report)**.
Różne implementacje TR1 były dostępne w przestrzeni nazw `std::tr1`.
W C++11 funkcje te przeniesiono do przestrzeni nazw `std`, a przy okazji niektóre z nich zostały zaktualizowane tak, by wykorzystywać nowe możliwości języka C++11 lub rozszerzone o funkcje, które były możliwe do zaimplementowania już w C++03, ale nie znalazły się w pierwotnym TR1.

### Ulepszenia istniejących komponentów biblioteki

C++11 wprowadza nowe cechy języka, z których mogą korzystać istniejące komponenty biblioteki standardowej.

Przykładowo większość kontenerów standardowych zyskuje na wsparciu dla **konstruktorów przenoszących opartych na rvalue references** — pozwala to szybko przenosić ciężkie obiekty lub przenosić zawartość kontenerów do nowej pamięci bez kosztownego kopiowania.

Komponenty biblioteki zostały tam, gdzie to miało sens, zaktualizowane o następujące cechy C++11 (lista nie jest wyczerpująca):

* rvalue references i związane z nimi wsparcie dla przenoszenia (move),
* wsparcie dla jednostek kodowania UTF‑16 i UTF‑32 (typy znakowe),
* szablony wariadyczne (w połączeniu z rvalue references umożliwiające perfect forwarding),
* wyrażenia stałoczasowe (`constexpr`),
* `decltype`,
* jawne `explicit` dla operatorów konwersji,
* funkcje zadeklarowane jako `= default` lub `= delete`.

Ponadto od czasu poprzedniego standardu powstało dużo kodu korzystającego ze standardowej biblioteki, co ujawniło obszary wymagające poprawy.
Jednym z takich obszarów są **alokatory**.
W C++11 wprowadzono dodatkowy, **zakresowy model alokatorów**, uzupełniający wcześniejszy model.

#### (C++14): heterogeniczne wyszukiwanie w kontenerach asocjacyjnych

C++14 rozszerza kontenery asocjacyjne (`std::map`, `std::set` i ich warianty) o możliwość wyszukiwania za pomocą typu innego niż typ klucza, o ile komparator potrafi porównać oba typy.

Przykładowo w `std::map<std::string, int>` można wywołać:
```cpp
std::map<std::string, int, std::less<>> mapa;

mapa["ala"] = 1;

auto it = mapa.find("ala"); // działa bez tworzenia std::string
```

Mechanizm ten pozwala:

* unikać kosztownych konwersji (np. `const char*` → `std::string`),
* wyszukiwać obiekty złożone po jednym polu bez tworzenia obiektu tymczasowego,
* pisać bardziej naturalny i wydajny kod.

Aby zachować kompatybilność wsteczną, heterogeniczne wyszukiwanie działa tylko wtedy, gdy komparator na to pozwala.
Standardowe `std::less<>` i `std::greater<>` zostały w C++14 odpowiednio rozszerzone.

***

#### Uzupełnienie (C++14): drobne rozszerzenia biblioteki

C++14 wprowadza szereg mniejszych, ale praktycznych rozszerzeń w standardowej bibliotece:

##### `std::make_unique`

Dodano funkcję `std::make_unique`, będącą odpowiednikiem `std::make_shared`, ale tworzącą obiekty zarządzane przez `std::unique_ptr`:
```cpp
auto ptr = std::make_unique<int>(42);
```

Zapobiega to błędom związanym z ręcznym użyciem `new` i poprawia bezpieczeństwo wyjątków.

***

##### `std::integral_constant` — operator wywołania

`std::integral_constant` zyskuje przeciążenie `operator()`, które zwraca wartość stałej:
```cpp
std::integral_constant<int, 7> c;
int x = c(); // x == 7
```

***

##### `std::integer_sequence` i aliasy (`index_sequence`, `make_index_sequence`)

Dodano narzędzia do reprezentowania sekwencji liczb całkowitych w czasie kompilacji — kluczowe dla metaprogramowania i pracy z param packami:
```cpp
template<std::size_t... I>
void foo(std::index_sequence<I...>);
```

***

##### Nowe funkcje globalne: `std::cbegin`, `std::cend`, `std::rbegin`, `std::rend`, `std::crbegin`, `std::crend`

Dodano stałe i odwrotne iteratory w formie funkcji globalnych:
```cpp
for (auto it = std::cbegin(v); it != std::cend(v); ++it) { ... }
```

***

##### Uzupełnienie (C++17): `std::size`, `std::empty`, `std::data`

C++17 dodaje trzy nowe funkcje globalne, analogiczne do istniejących `std::begin`/`std::end`:
```cpp
#include <iterator>

int tab[] = {1, 2, 3, 4, 5};
std::vector<int> v = {1, 2, 3};

std::size(tab);   // 5 — liczba elementów tablicy lub kontenera
std::size(v);     // 3

std::empty(v);    // false — czy kontener jest pusty
std::empty(tab);  // false

std::data(v);     // wskaźnik do pierwszego elementu (jak v.data())
std::data(tab);   // wskaźnik do pierwszego elementu tablicy
```

Pozwalają pisać kod generyczny działający zarówno dla tablic C-stylowych,
jak i kontenerów STL, bez specjalizowania szablonów dla obu przypadków.

***

##### `std::exchange`

Funkcja przypisuje nową wartość i zwraca starą:
```cpp
int x = 5;
int old = std::exchange(x, 10); // old == 5, x == 10
```

***

##### Nowe przeciążenia `std::equal`, `std::mismatch`, `std::is_permutation`

Dodano wersje przyjmujące **dwa zakresy** zamiast jednego zakresu i długości drugiego:
```cpp
std::equal(a.begin(), a.end(), b.begin(), b.end());
```

***

##### `std::is_final`

Nowy trait wykrywający, czy klasa została oznaczona jako `final`.

***

##### `std::quoted`

Manipulator strumieniowy umożliwiający bezpieczne wypisywanie i wczytywanie napisów zawierających spacje lub cudzysłowy:
```cpp
std::cout << std::quoted("ala ma kota");
```

***

#### (C++17): ulepszenia alokatorów i kontenerów

**Polymorphic memory resources (`std::pmr`)**

C++17 wprowadza nowy model zarządzania pamięcią w nagłówku `<memory_resource>`:
**polimorficzne zasoby pamięci** (`std::pmr::*`).

Problem, który rozwiązują: w C++11/14 alokatory były częścią **typu** kontenera
(`std::vector<int, MojAlokator>`). Oznaczało to, że `std::vector<int>` i
`std::vector<int, MojAlokator>` to **dwa różne typy** — niemożliwe do przekazania
do tej samej funkcji bez szablonów.

`std::pmr` oddziela alokator od typu kontenera. Kontener zapamiętuje wskaźnik
do `std::pmr::memory_resource` (interfejs polimorficzny), a nie typ alokatora:
```cpp
#include <memory_resource>
#include <vector>

// Bufor na stosie — żadnych alokacji na stercie
std::byte bufor[1024];
std::pmr::monotonic_buffer_resource zasob(bufor, sizeof(bufor));

// Wektor używający pamięci ze stosu — ale jego typ to nadal std::pmr::vector<int>
std::pmr::vector<int> v(&zasob);
v.push_back(1);
v.push_back(2);
```

`std::pmr::vector<T>` to alias dla `std::vector<T, std::pmr::polymorphic_allocator<T>>`.
Możemy przekazywać takie kontenery do funkcji przyjmujących `std::pmr::vector<int>`
niezależnie od tego, jaki zasób pamięci jest aktualnie używany.

Dostępne standardowe zasoby pamięci:

* `std::pmr::monotonic_buffer_resource` — szybka alokacja z bufora, bez możliwości
  zwalniania pojedynczych obiektów (wszystko zwalniane naraz),
* `std::pmr::unsynchronized_pool_resource` — pula pamięci bez synchronizacji wątków,
* `std::pmr::synchronized_pool_resource` — pula pamięci bezpieczna wątkowo,
* `std::pmr::null_memory_resource()` — zawsze rzuca `std::bad_alloc`
  (przydatne do testowania, czy kontener nie alokuje nieoczekiwanie).

##### Nowe operacje na mapach: `try_emplace` i `insert_or_assign`

C++17 dodaje do `std::map` i `std::unordered_map` dwie nowe metody:

`try_emplace` — wstawia element **tylko jeśli klucz nie istnieje**,
konstruując wartość bezpośrednio w miejscu (bez zbędnych kopii ani przeniesień
w przypadku, gdy klucz już istnieje):
```cpp
std::map<std::string, std::vector<int>> m;

// Jeśli "klucz" nie istnieje — konstruuje vector w miejscu
// Jeśli "klucz" istnieje — nic nie robi, nie niszczy argumentów
m.try_emplace("klucz", std::initializer_list<int>{1, 2, 3});
```

Przed C++17 używano `insert` lub `emplace`, które mogły konstruować obiekt wartości
nawet jeśli klucz już istniał, a następnie go niszczyć.

`insert_or_assign` — wstawia element jeśli klucz nie istnieje,
lub **nadpisuje wartość** jeśli klucz istnieje. Zwraca parę
`{iterator, bool}` (podobnie jak `insert`), gdzie `bool` oznacza
czy nastąpiło wstawienie (`true`) czy nadpisanie (`false`):
```cpp
auto [it, wstawiono] = m.insert_or_assign("klucz", nowaWartosc);
```

Przed C++17 osiągano ten efekt przez `operator[]`, ale `operator[]`
wymaga, żeby typ wartości miał konstruktor domyślny — `insert_or_assign` nie ma tego wymagania.

***

##### Uzupełnienie (C++20): `std::erase` i `std::erase_if`

Usuwanie elementów z kontenerów sekwencyjnych wymagało przed C++20
idiomatycznego zapisu zwanego _erase-remove idiom_:
```cpp
// C++11/17 — usunięcie wszystkich wartości 42 z wektora
v.erase(std::remove(v.begin(), v.end(), 42), v.end());
```

C++20 wprowadza wolnostojące funkcje upraszczające ten wzorzec:
```cpp
#include <vector>

std::vector<int> v = {1, 2, 3, 2, 4, 2};

std::erase(v, 2);           // usuwa wszystkie elementy równe 2
// v == {1, 3, 4}

std::erase_if(v, [](int x) { return x % 2 == 0; }); // usuwa parzyste
```

`std::erase` i `std::erase_if` działają dla większości standardowych kontenerów
sekwencyjnych: `std::vector`, `std::list`, `std::deque`, `std::string`.
Dla kontenerów asocjacyjnych (`std::map`, `std::set`) działa tylko `std::erase_if`.

***

##### Uzupełnienie (C++20): kontenery i algorytmy constexpr

C++20 pozwala używać wielu kontenerów i algorytmów w kontekście `constexpr`, np.:
```cpp
constexpr auto suma = []() {
    std::vector<int> v = {1, 2, 3};
    int s = 0;
    for (int x : v) s += x;
    return s;
}();
// suma == 6, obliczone w czasie kompilacji
```

Dotyczy to m.in. `std::vector`, `std::string`, `std::array` oraz większości algorytmów
z `<algorithm>` — pod warunkiem, że nie wykonują operacji niedozwolonych w `constexpr`
(np. operacji na plikach czy wątkach).

***

#### (C++20/C++23): `std::ranges` i `std::format`

##### `std::ranges` (C++20)

C++20 wprowadza bibliotekę `<ranges>`, która dostarcza nowe podejście do algorytmów:
zamiast par iteratorów (`begin`, `end`) operujemy na **zakresach** (_ranges_) — obiektach,
które wiedzą, gdzie zaczyna się i kończy sekwencja.

Zakresy pozwalają na **leniwe komponowanie operacji** (_lazy composition_) bez tworzenia
kontenerów pośrednich:
```cpp
#include <ranges>
#include <vector>
#include <iostream>

std::vector<int> v = {1, 2, 3, 4, 5, 6, 7, 8};

// Filtruj parzyste, pomnóż przez 2 — żadnych kopii, przetwarzanie leniwe
for (int x : v | std::views::filter([](int n){ return n % 2 == 0; })
               | std::views::transform([](int n){ return n * 2; }))
{
    std::cout << x << " "; // 4 8 12 16
}
```

C++23 rozszerza `std::ranges` o nowe widoki i algorytmy, m.in.:
`std::views::zip`, `std::views::enumerate`, `std::views::chunk`,
`std::views::slide`, `std::views::join_with`, `std::ranges::fold_left`.

***

##### `std::format` (C++20)

C++20 wprowadza `<format>` — bezpieczną typowo alternatywę dla `printf` i wygodniejszą
od budowania napisów przez `std::ostringstream`:
```cpp
#include <format>

std::string s = std::format("Witaj, {}! Masz {} lat.", "Ania", 30);
// s == "Witaj, Ania! Masz 30 lat."

std::string liczba = std::format("{:.2f}", 3.14159);
// liczba == "3.14"
```

Format jest sprawdzany **w czasie kompilacji** — błędna specyfikacja formatu
to błąd kompilacji, a nie błąd wykonania.

**C++23 rozszerza `std::format` o:**
* `std::print` i `std::println` — bezpośrednie wypisywanie sformatowanego tekstu
  bez `std::cout << std::format(...)`,
* formatowanie zakresów i kontenerów (`std::vector`, `std::map` itd.) bez ręcznego iterowania,
* formatowanie krotek i par.

```cpp
// C++23
std::println("Wektor: {}", std::vector<int>{1, 2, 3});
// Wypisze: Wektor: [1, 2, 3]
```

***

#### (C++17): `std::string_view`

Funkcje przyjmujące napisy w C++ miały przed C++17 problem z wydajnością:
przyjmowanie `const std::string&` wymuszało tworzenie obiektu `std::string`
gdy przekazywano literał lub `const char*`, co wiązało się z alokacją pamięci.

```cpp
// C++11/14 — każde wywołanie z literałem alokuje std::string
void wypisz(const std::string& s) { std::cout << s; }

wypisz("hello");        // alokacja: tworzy tymczasowy std::string
wypisz(bufor, dlugosc); // niemożliwe bez konwersji
```

C++17 wprowadza `std::string_view` (nagłówek `<string_view>`) —
**lekki, niewłaścicielski widok** na sekwencję znaków. Wewnętrznie przechowuje
tylko wskaźnik i długość, bez alokacji i bez kopiowania danych:
```cpp
#include <string_view>

void wypisz(std::string_view s)
{
    std::cout << s;
}

std::string str = "hello";
const char* cstr = "world";

wypisz(str);            // brak kopii — widok na dane str
wypisz(cstr);           // brak kopii — widok na literał
wypisz("inline");       // brak kopii — widok na literał
wypisz({"abcdef", 3});  // widok na pierwsze 3 znaki literału
```

`std::string_view` obsługuje większość operacji `std::string` niemodyfikujących danych:
`size()`, `empty()`, `substr()`, `find()`, `starts_with()`, `ends_with()`, operator `[]`, iteratory.

Od C++20 zarówno `std::string_view`, jak i `std::string` zyskują metody
`starts_with()` i `ends_with()`:
```cpp
std::string_view sv = "hello world";

sv.starts_with("hello"); // true
sv.ends_with("world");   // true

std::string s = "plik.txt";
s.ends_with(".txt");     // true
```

**Ważne ograniczenia:**

* `std::string_view` **nie jest właścicielem** danych — musi istnieć oryginalny
  obiekt przez cały czas życia widoku,
* **nie jest null-terminated** — nie można przekazać `string_view.data()`
  do funkcji C oczekujących `const char*` bez sprawdzenia,
* nie nadaje się do przechowywania — tylko do przekazywania jako parametr funkcji.

```cpp
std::string_view niebezpieczne()
{
    std::string s = "hello";
    return s; // błąd: s zostanie zniszczone, widok będzie nieprawidłowy
}
```

**Zalecenie:** używaj `std::string_view` jako typ parametru funkcji wszędzie tam,
gdzie wcześniej używałeś `const std::string&` i nie potrzebujesz własności nad danymi.

***

#### (C++20): `std::span`

`std::span<T>` (nagłówek `<span>`) to **niewłaścicielski widok** na ciągły
obszar pamięci — analogiczny do `std::string_view`, ale dla dowolnych typów,
nie tylko znaków. W przeciwieństwie do `std::string_view`, `std::span` pozwala
**modyfikować** elementy.

Przed C++20 funkcje przyjmujące tablice lub wektory miały problem z ujednoliceniem
interfejsu — trzeba było pisać wiele przeciążeń lub przyjmować parę wskaźnik+rozmiar:
```cpp
// C++11/17 — trzy różne przeciążenia dla tego samego zadania
void przetwarzaj(const std::vector<int>& v);
void przetwarzaj(const int* ptr, std::size_t n);
void przetwarzaj(std::array<int, 5>& arr);
```

C++20 rozwiązuje to przez `std::span`:
```cpp
#include <span>

void przetwarzaj(std::span<int> dane)
{
    for (int& x : dane)
        x *= 2;
}

std::vector<int> v = {1, 2, 3};
int tab[] = {4, 5, 6};
std::array<int, 3> arr = {7, 8, 9};

przetwarzaj(v);    // działa
przetwarzaj(tab);  // działa
przetwarzaj(arr);  // działa
```

**Rozmiar statyczny i dynamiczny:**

`std::span` może mieć rozmiar znany w czasie kompilacji (_static extent_)
lub w czasie wykonywania (_dynamic extent_):
```cpp
std::span<int>       dynamiczny = v;    // rozmiar znany w runtime
std::span<int, 3>    statyczny  = arr;  // rozmiar 3 znany w czasie kompilacji
```

**Podzakresy:**
```cpp
std::span<int> s(v);

s.first(2);        // pierwsze 2 elementy
s.last(2);         // ostatnie 2 elementy
s.subspan(1, 2);   // elementy od indeksu 1, długość 2
```

**Ważne:** `std::span` nie jest właścicielem danych — oryginalny kontener
musi żyć przez cały czas życia `span`. Modyfikacje przez `span` modyfikują
oryginalne dane.

> **Zalecenie:** używaj `std::span<T>` jako parametru funkcji wszędzie tam,
> gdzie wcześniej przyjmowałeś parę `(T*, size_t)` lub gdzie pisałeś
> wielokrotne przeciążenia dla różnych kontenerów ciągłych.

***

#### (C++17): `std::optional`

Funkcje, które mogą nie zwrócić sensownej wartości, miały przed C++17
kilka nieeleganckich rozwiązań:
```cpp
// Zwracanie wartości sentinel (magiczna wartość oznaczająca brak wyniku)
int znajdz(const std::vector<int>& v, int x); // zwraca -1 gdy nie znaleziono

// Zwracanie przez wskaźnik (nullptr = brak wyniku)
const Rekord* znajdz(const Baza& db, int id);

// Parametr wyjściowy + bool
bool znajdz(const std::vector<int>& v, int x, int& wynik);
```

Każde z tych podejść ma wady: wartości sentinel są nieczytelne, wskaźniki
sugerują dynamiczną alokację, parametry wyjściowe zaburzają czytelność kodu.

C++17 wprowadza `std::optional<T>` (nagłówek `<optional>`) —
typ, który **może, ale nie musi** zawierać wartość:
```cpp
#include <optional>

std::optional<int> znajdz(const std::vector<int>& v, int x)
{
    for (int i = 0; i < v.size(); ++i)
        if (v[i] == x) return i;    // zwraca wartość
    return std::nullopt;             // zwraca brak wartości
}

auto wynik = znajdz({1, 2, 3}, 2);

if (wynik)                          // sprawdzenie czy wartość istnieje
    std::cout << *wynik;            // wyłuskanie wartości

// Alternatywnie:
std::cout << wynik.value_or(-1);    // zwraca wartość lub -1 jeśli brak
```

**Podstawowe operacje:**

```cpp
std::optional<int> a = 42;
std::optional<int> b;               // puste — std::nullopt

a.has_value();  // true
b.has_value();  // false

*a;             // 42 — wyłuskanie (niezdefiniowane gdy puste)
a.value();      // 42 — z sprawdzeniem (rzuca std::bad_optional_access gdy puste)
a.value_or(0);  // 42
b.value_or(0);  // 0
```

`std::optional<T>` przechowuje wartość **wewnętrznie** (bez alokacji na stercie)
— jest to tzw. typ z semantyką wartości, bezpieczny i wydajny.

> **Uwaga:** `std::optional<T&>` (opcjonalna referencja) jest niedozwolone.
> Użyj `std::optional<std::reference_wrapper<T>>` jeśli naprawdę potrzebujesz.

***

#### (C++17): `std::variant`

`std::variant<T1, T2, ...>` (nagłówek `<variant>`) to **bezpieczna typowo unia** —
przechowuje dokładnie jedną wartość spośród podanych typów i zawsze wie, który typ
aktualnie przechowuje.

W C++03/11 unie (`union`) pozwalały przechowywać różne typy w tej samej pamięci,
ale nie śledziły który typ jest aktywny — dostęp do złego pola to niezdefiniowane zachowanie.
`std::variant` rozwiązuje ten problem:
```cpp
#include <variant>

std::variant<int, double, std::string> v;

v = 42;                             // przechowuje int
std::get<int>(v);                   // 42

v = 3.14;                           // przechowuje double
std::get<double>(v);                // 3.14

v = std::string("hello");           // przechowuje string
std::get<std::string>(v);           // "hello"

std::get<int>(v);                   // rzuca std::bad_variant_access — aktywny typ to string
```

**Sprawdzanie aktywnego typu:**

```cpp
std::holds_alternative<int>(v);     // false — aktywny typ to string
v.index();                          // 2 — indeks aktywnego typu (string jest trzeci)
```

**`std::visit` — odwiedzanie wartości:**

Najczystszy sposób obsługi wszystkich możliwych typów to `std::visit`
z funktorem lub lambdą:
```cpp
std::visit([](auto&& val)
{
    std::cout << val;
}, v);
```

Można też przekazać obiekt z przeciążonymi `operator()` dla każdego typu:
```cpp
struct Odwiedzajacy
{
    void operator()(int i)         { std::cout << "int: " << i; }
    void operator()(double d)      { std::cout << "double: " << d; }
    void operator()(std::string s) { std::cout << "string: " << s; }
};

std::visit(Odwiedzajacy{}, v);
```

**Typowe zastosowania:**

* wynik funkcji, który może być wartością lub błędem (alternatywa dla wyjątków),
* węzły drzewa AST w kompilatorach i parserach,
* komunikaty protokołu sieciowego różnych typów,
* zastąpienie hierarchii klas wirtualnych gdy typy są znane z góry.

> **Uwaga:** `std::variant` nigdy nie jest pusty — zawsze przechowuje wartość
> jednego z typów. Wyjątkiem jest stan `valueless_by_exception` po nieudanej
> operacji przypisania.

***

#### (C++17): `std::any`

`std::any` (nagłówek `<any>`) przechowuje **pojedynczą wartość dowolnego typu**
z możliwością sprawdzenia typu w czasie wykonywania. W przeciwieństwie do
`std::variant` nie wymaga z góry listy dopuszczalnych typów:
```cpp
#include <any>

std::any a = 42;                    // przechowuje int
std::any b = std::string("hello");  // przechowuje string
std::any c = 3.14;                  // przechowuje double

std::any_cast<int>(a);              // 42
std::any_cast<int>(b);              // rzuca std::bad_any_cast — aktywny typ to string

a.type() == typeid(int);            // true
a.has_value();                      // true

a.reset();                          // czyści wartość
a.has_value();                      // false
```

**Kiedy używać `std::any`, a kiedy `std::variant`:**

* `std::variant` — gdy zestaw możliwych typów jest **znany z góry**; bezpieczniejszy,
  szybszy, sprawdzany w czasie kompilacji. Preferowany wybór.
* `std::any` — gdy zestaw typów jest **nieznany z góry** lub zmienny
  (np. system wtyczek, ogólne kontenery konfiguracji, interfejsy skryptowe).

> **Uwaga o wydajności:** `std::any` może alokować pamięć na stercie dla większych
> obiektów (implementacje zwykle stosują optymalizację małych obiektów dla typów
> do kilkunastu bajtów). `std::variant` nigdy nie alokuje.

***

#### (C++17): `std::byte`

Przed C++17 do reprezentowania surowych danych binarnych używano `char`
lub `unsigned char`. Powodowało to niejednoznaczność — `char` służy zarówno
do przechowywania znaków, jak i surowych bajtów danych:
```cpp
char bufor[1024]; // czy to tekst czy surowe dane?
```

C++17 wprowadza `std::byte` (nagłówek `<cstddef>`) — typ semantycznie
reprezentujący **bajt danych**, nie znak:
```cpp
#include <cstddef>

std::byte b{0xFF};
std::byte bufor[1024]; // jasno: surowe dane, nie tekst
```

`std::byte` obsługuje tylko operacje bitowe — celowo nie obsługuje arytmetyki
ani konwersji do/z typów całkowitych bez jawnego rzutowania:
```cpp
std::byte a{0b1010};
std::byte b{0b1100};

a | b;              // 0b1110 — OR bitowy
a & b;              // 0b1000 — AND bitowy
a ^ b;              // 0b0110 — XOR bitowy
~a;                 // negacja bitowa
a << 1;             // przesunięcie

int x = a;          // błąd — brak niejawnej konwersji
int y = std::to_integer<int>(a); // OK — jawna konwersja
```

Używaj `std::byte` wszędzie tam, gdzie masz do czynienia z surowymi danymi
binarnymi (bufory sieciowe, serializacja, operacje na plikach binarnych) —
zamiast `char*` lub `unsigned char*`. Poprawia to czytelność i eliminuje
przypadkowe traktowanie danych binarnych jako tekstu.

***

#### (C++20): `std::bit_cast`

Reinterpretacja bitowej reprezentacji jednego typu jako innego typu była
przed C++20 możliwa przez `memcpy` lub przez `reinterpret_cast` na wskaźnikach —
obie metody są nieeleganckie, a druga jest technicznie niezdefiniowanym
zachowaniem w wielu przypadkach (naruszenie strict aliasing).

C++20 wprowadza `std::bit_cast<To>(from)` (nagłówek `<bit>`) —
bezpieczną, `constexpr`-kompatybilną reinterpretację bitową:
```cpp
#include <bit>
#include <cstdint>

float f = 1.0f;

// Pobierz bitową reprezentację float jako uint32_t
uint32_t bits = std::bit_cast<uint32_t>(f); // 0x3F800000

// Odwrotnie
float z_powrotem = std::bit_cast<float>(bits); // 1.0f
```

Wymagania:

* `sizeof(To) == sizeof(From)` — typy muszą mieć ten sam rozmiar,
* oba typy muszą być **trivially copyable**,
* wynik jest `constexpr` jeśli oba typy są odpowiednie.

Typowe zastosowania:

* inspekcja reprezentacji IEEE 754 liczb zmiennoprzecinkowych,
* niskopoziomowe protokoły sieciowe i serializacja,
* implementacje algorytmów korzystających z reprezentacji bitowej
  (np. szybki odwrotny pierwiastek kwadratowy).

```cpp
// Klasyczny przykład: sprawdzenie bitu znaku float
float f = -3.14f;
uint32_t bits = std::bit_cast<uint32_t>(f);
bool ujemna = (bits >> 31) & 1; // true
```

***

#### (C++20): Operacje bitowe (`<bit>`)

C++20 dodaje nagłówek `<bit>` z zestawem funkcji do operacji na bitowej
reprezentacji liczb całkowitych bez znaku. Przed C++20 operacje te
wymagały implementacji zależnych od kompilatora (np. `__builtin_popcount` w GCC)
lub ręcznego pisania algorytmów.

**Liczenie bitów:**
```cpp
#include <bit>
#include <cstdint>

uint32_t x = 0b1010'1100u;

std::popcount(x);        // 4 — liczba bitów ustawionych na 1
std::countl_zero(x);     // liczba zer wiodących (od lewej)
std::countl_one(x);      // liczba jedynek wiodących (od lewej)
std::countr_zero(x);     // liczba zer końcowych (od prawej)
std::countr_one(x);      // liczba jedynek końcowych (od prawej)
```

**Potęgi dwójki:**
```cpp
std::has_single_bit(8u);       // true — 8 jest potęgą dwójki
std::has_single_bit(6u);       // false

std::bit_ceil(5u);             // 8 — najmniejsza potęga dwójki >= 5
std::bit_floor(5u);            // 4 — największa potęga dwójki <= 5
std::bit_width(5u);            // 3 — minimalna liczba bitów do reprezentacji 5
```

**Rotacje bitowe:**
```cpp
uint8_t b = 0b1010'0001u;

std::rotl(b, 1);   // 0b0100'0011 — rotacja w lewo o 1
std::rotr(b, 1);   // 0b1101'0000 — rotacja w prawo o 1 (uwaga: przykład poglądowy)
```

Wszystkie funkcje działają tylko dla typów całkowitych **bez znaku**
i są `constexpr`.

***

#### (C++20): Kalendarz i strefy czasowe (`<chrono>`)

C++20 znacząco rozszerza nagłówek `<chrono>` o obsługę kalendarza
i stref czasowych. Przed C++20 `<chrono>` zawierał tylko typy czasu trwania
(`duration`) i punkty w czasie (`time_point`), ale nie miał pojęcia
o datach, godzinach ani strefach czasowych.

**Typy dat:**
```cpp
#include <chrono>
using namespace std::chrono;

// Konstruowanie dat
year_month_day dzisDzien = 2024y / January / 15;
year_month_day innyDzien = {year(2024), month(1), day(15)};

// Dostęp do składowych
dzisDzien.year();   // 2024
dzisDzien.month();  // January
dzisDzien.day();    // 15

// Sprawdzenie poprawności daty
dzisDzien.ok();     // true — data jest poprawna
(2024y / February / 30).ok(); // false — 30 lutego nie istnieje
```

**Arytmetyka na datach:**
```cpp
year_month_day data = 2024y / March / 1;

// Dodawanie miesięcy i lat
auto nastepnyMiesiac = data + months{1};  // 2024/April/1
auto nastepnyRok     = data + years{1};   // 2025/March/1
```

**Strefy czasowe:**
```cpp
// Bieżący czas w UTC
auto teraz = system_clock::now();

// Konwersja do strefy czasowej
auto* strefa = locate_zone("Europe/Warsaw");
auto lokalny = zoned_time{strefa, teraz};

std::cout << lokalny << "\n"; // wypisuje czas lokalny z offsetem
```

**Formatowanie dat:**
```cpp
// C++20 + std::format
auto data = 2024y / January / 15;
std::string s = std::format("{:%Y-%m-%d}", data); // "2024-01-15"
```

> **Nota:** obsługa stref czasowych wymaga dostępu do bazy danych stref
> (IANA Time Zone Database). Na Windows może wymagać dodatkowej konfiguracji.

***

#### (C++17): `std::uncaught_exceptions`

C++03 dostarczał funkcję `std::uncaught_exception()` (liczba pojedyncza),
która zwracała `bool` — `true` jeśli w toku było rozwijanie stosu z powodu wyjątku.
Używano jej głównie w destruktorach, żeby nie rzucać wyjątku podczas obsługi innego
wyjątku (co kończy program przez `std::terminate()`).

Problem pojawia się przy zagnieżdżonych wyjątkach i przy `std::exception_ptr` —
`uncaught_exception()` nie potrafiła odróżnić sytuacji gdy jest jeden wyjątek
od sytuacji gdy jest ich wiele.

C++17 zastępuje ją funkcją `std::uncaught_exceptions()` (liczba mnoga),
która zwraca **liczbę** aktywnych, nieprzechwyconych wyjątków:
```cpp
#include <exception>

struct Straznik
{
    int poziom = std::uncaught_exceptions(); // zapamiętaj liczbę wyjątków przy tworzeniu

    ~Straznik()
    {
        if (std::uncaught_exceptions() > poziom)
        {
            // destruktor wywołany podczas obsługi wyjątku — nie rzucaj
        }
        else
        {
            // destruktor wywołany normalnie — można rzucać
        }
    }
};
```

`std::uncaught_exception()` (stara wersja) została oznaczona jako przestarzała
w C++17 i usunięta w C++20.

***

#### (C++17): Iteratory ciągłe (contiguous iterators)

C++11 definiował kilka kategorii iteratorów: input, forward, bidirectional,
random access. Brakowało jednak formalnej kategorii dla iteratorów gwarantujących,
że elementy leżą **w ciągłym obszarze pamięci** (jak w tablicy lub `std::vector`).

C++17 dodaje kategorię **contiguous iterator** — iterator, dla którego zachodzi:
```cpp
adres(*(it + n)) == adres(*it) + n * sizeof(element)
```

Ciągłość pamięci gwarantują: `std::vector`, `std::array`, `std::string`,
`std::string_view` oraz tablice C-stylowe.

Praktyczne znaczenie: kod może teraz formalnie stwierdzić, że dane leżą
w ciągłym bloku pamięci i bezpiecznie przekazać wskaźnik do API C:
```cpp
std::vector<int> v = {1, 2, 3};

// Bezpieczne — vector gwarantuje ciągłość (contiguous iterator)
int* ptr = v.data();
funkcjaC(ptr, v.size());
```

C++20 sformalizował to jeszcze bardziej, wprowadzając koncepty
`std::contiguous_iterator` i `std::contiguous_range`.

***

#### (C++17): Biblioteka systemu plików (`<filesystem>`)

C++17 wprowadza bibliotekę `<filesystem>` (bazującą na `boost::filesystem`),
która dostarcza przenośne API do operacji na plikach i katalogach.
Przed C++17 operacje na systemie plików wymagały funkcji zależnych od platformy
(`stat`, `opendir` na POSIX lub `FindFirstFile` na Windows).

**Podstawowy typ — `std::filesystem::path`:**
```cpp
#include <filesystem>
namespace fs = std::filesystem;

fs::path p = "/home/user/dokument.txt";

p.filename();       // "dokument.txt"
p.stem();           // "dokument"
p.extension();      // ".txt"
p.parent_path();    // "/home/user"
p.parent_path() / "podkatalog";   // "/home/user/podkatalog" — łączenie ścieżek przez /
```

**Operacje na plikach i katalogach:**
```cpp
fs::exists(p);                          // czy plik/katalog istnieje
fs::is_regular_file(p);                 // czy to zwykły plik
fs::is_directory(p);                    // czy to katalog
fs::file_size(p);                       // rozmiar pliku w bajtach
fs::last_write_time(p);                 // czas ostatniej modyfikacji

fs::create_directory("nowy_katalog");   // utwórz katalog
fs::create_directories("a/b/c");        // utwórz całą ścieżkę
fs::copy(src, dst);                     // kopiuj plik
fs::rename(src, dst);                   // przenieś/zmień nazwę
fs::remove(p);                          // usuń plik
fs::remove_all(p);                      // usuń katalog rekurencyjnie
```

**Iteracja po katalogu:**
```cpp
for (const auto& wpis : fs::directory_iterator("katalog"))
{
    std::cout << wpis.path() << "\n";
}

// Rekurencyjnie:
for (const auto& wpis : fs::recursive_directory_iterator("katalog"))
{
    if (wpis.is_regular_file())
        std::cout << wpis.path() << "\n";
}
```

**Obsługa błędów:**

Funkcje biblioteki mają dwa warianty — rzucający wyjątek i z kodem błędu:
```cpp
std::error_code ec;
fs::exists(p, ec);  // nie rzuca wyjątku — błąd w ec
if (ec) { /* obsłuż błąd */ }
```

***

#### (C++17): Równoległe algorytmy STL

C++17 rozszerza algorytmy z `<algorithm>`, `<numeric>` i `<memory>`
o **polityki wykonania** (_execution policies_), pozwalające uruchamiać je
równolegle bez ręcznego zarządzania wątkami:
```cpp
#include <algorithm>
#include <execution>
#include <vector>

std::vector<int> v(1'000'000);

// Sekwencyjnie (domyślne zachowanie jak dotychczas)
std::sort(std::execution::seq, v.begin(), v.end());

// Równolegle — kompilator/biblioteka zarządza wątkami
std::sort(std::execution::par, v.begin(), v.end());

// Równolegle z wektoryzacją SIMD
std::sort(std::execution::par_unseq, v.begin(), v.end());
```

**Trzy standardowe polityki:**

* `std::execution::seq` — sekwencyjne, bez równoległości (jak przed C++17),
* `std::execution::par` — równoległe wykonanie na wielu wątkach,
* `std::execution::par_unseq` — równoległe i wektoryzowane (SIMD);
  funkcja nie może używać mutexów ani alokować pamięci.

Większość algorytmów STL obsługuje polityki wykonania, m.in.:
`std::sort`, `std::for_each`, `std::transform`, `std::reduce`,
`std::find`, `std::count`, `std::copy`, `std::fill`.

**Ważne uwagi:**

* Przy `par` i `par_unseq` operacje na współdzielonych danych muszą być
  bezpieczne wątkowo — biblioteka nie dodaje synchronizacji automatycznie.
* Rzeczywiste przyspieszenie zależy od implementacji biblioteki standardowej
  i sprzętu. Na małych danych narzut tworzenia wątków może być większy niż zysk.
* Wsparcie kompilatorów: GCC wymaga linkowania z `-ltbb` (Intel TBB),
  MSVC ma wbudowane wsparcie, Clang ma częściowe wsparcie.

***

#### (C++17): Matematyczne funkcje specjalne (`<cmath>`)

C++17 dodaje do nagłówka `<cmath>` zestaw **specjalnych funkcji matematycznych**
używanych w fizyce, inżynierii i statystyce. Przed C++17 były dostępne tylko
przez biblioteki zewnętrzne (Boost.Math) lub funkcje specyficzne dla platformy.

Dodane funkcje (wybór najważniejszych):

**Funkcje Bessela** — rozwiązania równania Bessela, używane w analizie falowej,
elektromagnetyzmie i mechanice kwantowej:
```cpp
std::cyl_bessel_j(n, x);   // funkcja Bessela pierwszego rodzaju
std::cyl_bessel_y(n, x);   // funkcja Bessela drugiego rodzaju
std::cyl_bessel_i(n, x);   // zmodyfikowana funkcja Bessela pierwszego rodzaju
std::cyl_bessel_k(n, x);   // zmodyfikowana funkcja Bessela drugiego rodzaju
std::sph_bessel(n, x);     // sferyczna funkcja Bessela
```

**Całki eliptyczne** — używane w mechanice (ruch wahadła, orbity) i elektrodynamice:
```cpp
std::comp_ellint_1(k);     // pełna całka eliptyczna pierwszego rodzaju
std::comp_ellint_2(k);     // pełna całka eliptyczna drugiego rodzaju
std::ellint_1(k, phi);     // niezupełna całka eliptyczna pierwszego rodzaju
std::ellint_2(k, phi);     // niezupełna całka eliptyczna drugiego rodzaju
```

**Inne funkcje:**
```cpp
std::beta(x, y);           // funkcja beta Eulera
std::legendre(n, x);       // wielomiany Legendre'a
std::hermite(n, x);        // wielomiany Hermite'a
std::laguerre(n, x);       // wielomiany Laguerre'a
std::riemann_zeta(x);      // funkcja dzeta Riemanna
std::expint(x);            // całka wykładnicza
```

> **Nota:** funkcje te są przeznaczone dla kodu naukowego i inżynierskiego.
> W typowych aplikacjach biznesowych lub systemowych rzadko są potrzebne.

***

### Mechanizmy wielowątkowe (threading facilities)

C++03 nie miał **żadnego** wbudowanego wsparcia dla wielowątkowości w standardzie języka.
Programiści musieli korzystać z bibliotek zależnych od platformy:
`pthreads` na systemach POSIX (Linux, macOS) lub `WinAPI` na Windows.
Kod wielowątkowy pisany w C++03 był nieprzenośny i trudny w utrzymaniu.

C++11 zmienia to fundamentalnie — wprowadza model pamięci dla wielu wątków
oraz kompletną bibliotekę do programowania wielowątkowego, przenośną między platformami.

#### Podstawowe pojęcia

##### Czym jest wątek?

Program uruchomiony na komputerze wykonuje instrukcje **sekwencyjnie** — jedna po drugiej.
Taki pojedynczy ciąg wykonania nazywa się **wątkiem** (ang. _thread_).

Nowoczesne procesory mają wiele rdzeni i mogą wykonywać wiele wątków **równocześnie**.
Wielowątkowość pozwala programowi korzystać z tej możliwości.

**Przykład praktyczny — aplikacja okienkowa z pobieraniem pliku:**

Wyobraź sobie aplikację z przyciskiem „Pobierz plik". Bez wielowątkowości:

* użytkownik klika „Pobierz plik",
* program zaczyna pobierać plik — **cały program się zatrzymuje**,
* okno przestaje reagować na kliknięcia, nie można go nawet przesunąć,
* użytkownik widzi „zamrożoną" aplikację i myśli, że się zawiesiła,
* dopiero po zakończeniu pobierania program wraca do normalnego działania.

Z wielowątkowością:

* użytkownik klika „Pobierz plik",
* program uruchamia **drugi wątek**, który pobiera plik w tle,
* **główny wątek** nadal obsługuje interfejs — okno reaguje, można klikać inne przyciski,
* drugi wątek po zakończeniu pobierania powiadamia główny wątek,
* główny wątek wyświetla komunikat „Pobieranie zakończone".

```cpp
#include <thread>
#include <iostream>

void pobierzPlik(const std::string& url)
{
    // ... logika pobierania pliku ...
    std::cout << "Pobieranie zakończone: " << url << "\n";
}

void aplikacja()
{
    std::string url = "https://przyklad.pl/plik.zip";

    // Uruchamia pobieranie w osobnym wątku — główny wątek nie czeka
    std::thread watek(pobierzPlik, url);
    watek.detach(); // wątek działa w tle niezależnie

    // Główny wątek nadal obsługuje interfejs użytkownika
    // ...
}
```

Inne typowe zastosowania wielowątkowości:

* **renderowanie grafiki** — jeden wątek liczy fizykę, drugi rysuje obraz,
* **serwer sieciowy** — każde połączenie obsługiwane w osobnym wątku,
* **przetwarzanie danych** — duży zbiór danych dzielony między wątki
  i przetwarzany równolegle na wielu rdzeniach procesora.

***

##### Wyścig danych (data race)

Gdy wiele wątków jednocześnie korzysta z tych samych danych, może dojść do **wyścigu danych**
(ang. _data race_) — sytuacji, w której co najmniej dwa wątki jednocześnie próbują odczytać
lub zmodyfikować tę samą zmienną, a co najmniej jeden z nich ją modyfikuje.

Wyścig danych to **niezdefiniowane zachowanie** w C++ — program może działać pozornie
poprawnie, dawać błędne wyniki, lub zawieszać się w trudny do przewidzenia sposób.

Przykład wyścigu danych:
```cpp
int licznik = 0;

// Wątek A i wątek B wykonują jednocześnie:
licznik++; // to NIE jest operacja atomowa — składa się z odczytu, dodania i zapisu
```

Jeśli oba wątki odczytają `licznik` w tym samym momencie (np. wartość `5`),
oba dodadzą `1` i oba zapiszą `6` — zamiast oczekiwanego `7`.
To klasyczny przykład wyścigu danych.

***

##### Mutex i sekcja krytyczna

Rozwiązaniem jest **mutex** (ang. _mutual exclusion_ — wzajemne wykluczanie).
Mutex to obiekt synchronizacyjny, który gwarantuje, że w danym momencie
**tylko jeden wątek** może wykonywać wybrany fragment kodu.

Ten chroniony fragment kodu nazywa się **sekcją krytyczną**.

Zasada działania:

* wątek **blokuje** (_lock_) mutex przed wejściem do sekcji krytycznej,
* jeśli mutex jest już zablokowany przez inny wątek — wątek **czeka**,
* po zakończeniu sekcji krytycznej wątek **zwalnia** (_unlock_) mutex,
* dopiero wtedy inny czekający wątek może wejść do sekcji krytycznej.

***

##### Zakleszczenie (deadlock)

**Zakleszczenie** (ang. _deadlock_) to sytuacja, w której dwa lub więcej wątków
czeka na siebie nawzajem — każdy trzyma zasób, którego potrzebuje drugi.

Klasyczny przykład:
```cpp
// Wątek A: blokuje m1, potem czeka na m2
// Wątek B: blokuje m2, potem czeka na m1
// → oba wątki czekają w nieskończoność
```

Unikanie zakleszczeń to jeden z najtrudniejszych problemów programowania wielowątkowego.

***

#### `std::thread` — tworzenie i zarządzanie wątkami

`std::thread` to klasa reprezentująca wątek wykonania.
Przyjmuje obiekt funkcyjny (funkcję, lambdę, funktor) i opcjonalnie argumenty,
a następnie uruchamia go w nowym wątku.

```cpp
#include <thread>
#include <iostream>

void zadanie(int numer)
{
    std::cout << "Wątek " << numer << " działa\n";
}

int main()
{
    std::thread watek1(zadanie, 1); // uruchamia zadanie(1) w nowym wątku
    std::thread watek2(zadanie, 2); // uruchamia zadanie(2) w nowym wątku

    watek1.join(); // czeka na zakończenie wątku 1
    watek2.join(); // czeka na zakończenie wątku 2

    // Program kończy się dopiero po zakończeniu obu wątków
}
```

**`join()`** — wątek wywołujący czeka, aż dany wątek zakończy pracę.
Jeśli obiekt `std::thread` zostanie zniszczony bez wywołania `join()`
lub `detach()`, program wywołuje `std::terminate()`.

**`detach()`** — odłącza wątek; działa w tle niezależnie od obiektu `std::thread`.
Po `detach()` nie można już czekać na zakończenie wątku.

Gdy potrzebny jest dostęp do mechanizmów specyficznych dla platformy
(np. ustawienie priorytetu wątku), `std::thread::native_handle()` zwraca
natywny uchwyt wątku (np. `pthread_t` na POSIX).

***

#### `std::mutex` i `std::lock_guard` — podstawowa synchronizacja

`std::mutex` to podstawowy mutex w C++11.

Bezpieczne użycie mutexa opiera się na zasadzie **RAII** — zamiast ręcznie
wywoływać `lock()` i `unlock()`, używamy obiektów blokujących,
które zwalniają mutex automatycznie przy wyjściu z zakresu
(nawet jeśli wyjście następuje przez wyjątek).

`std::lock_guard` to najprostszy taki obiekt — blokuje mutex w konstruktorze
i zwalnia w destruktorze:
```cpp
#include <mutex>
#include <thread>

int licznik = 0;
std::mutex mutexLicznika;

void zwieksz()
{
    std::lock_guard<std::mutex> blokada(mutexLicznika); // blokuje mutex
    licznik++; // sekcja krytyczna — tylko jeden wątek naraz
} // blokada zwolniona automatycznie

int main()
{
    std::thread w1(zwieksz);
    std::thread w2(zwieksz);

    w1.join();
    w2.join();

    // licznik == 2, gwarantowane
}
```

`std::unique_lock` to bardziej elastyczna wersja `std::lock_guard`:
pozwala na ręczne zwalnianie i ponowne blokowanie mutexa,
odroczenie blokowania oraz próbę blokowania bez czekania (`try_lock`).
Jest wymagany przez zmienne warunkowe.

Dostępne są też inne warianty mutexa:

* `std::recursive_mutex` — pozwala temu samemu wątkowi zablokować mutex wielokrotnie,
* `std::timed_mutex` — pozwala na próbę blokowania z timeoutem (`try_lock_for`, `try_lock_until`),
* `std::recursive_timed_mutex` — łączy obie powyższe właściwości.

***

#### Zmienne warunkowe — oczekiwanie na zdarzenie

`std::condition_variable` pozwala wątkowi **czekać** na spełnienie warunku,
zamiast aktywnie sprawdzać go w pętli (co marnuje czas procesora).

Typowy wzorzec producent–konsument:
```cpp
#include <condition_variable>
#include <mutex>
#include <queue>

std::queue<int> kolejka;
std::mutex m;
std::condition_variable cv;

// Producent — dodaje dane i powiadamia konsumenta
void producent()
{
    {
        std::lock_guard<std::mutex> blokada(m);
        kolejka.push(42);
    }
    cv.notify_one(); // budzi jeden czekający wątek
}

// Konsument — czeka na dane
void konsument()
{
    std::unique_lock<std::mutex> blokada(m);
    cv.wait(blokada, [] { return !kolejka.empty(); }); // czeka aż kolejka nie będzie pusta
    int wartosc = kolejka.front();
    kolejka.pop();
}
```

`std::condition_variable_any` działa z dowolnym typem blokady
(nie tylko z `std::unique_lock<std::mutex>`).

***

#### Operacje atomowe — synchronizacja bez mutexa

Dla prostych operacji na pojedynczych zmiennych mutex bywa nadmiarowy.
C++11 wprowadza **operacje atomowe** — operacje gwarantowane jako niepodzielne,
wykonywane jako całość bez możliwości przerwania przez inny wątek.

```cpp
#include <atomic>

std::atomic<int> licznik(0);

void zwieksz()
{
    licznik++; // atomowe — bezpieczne bez mutexa
}
```

`std::atomic<T>` działa dla typów całkowitych, wskaźników i `bool`.
Dla bardziej złożonych typów nadal potrzebny jest mutex.

Operacje atomowe pozwalają też określić **wymagania widoczności pamięci**
(ang. _memory ordering_) — czyli gwarancje co do kolejności, w jakiej zmiany
w pamięci stają się widoczne dla innych wątków. Domyślne `memory_order_seq_cst`
daje najsilniejsze gwarancje i jest bezpieczne w typowym użyciu.

***

#### `std::future`, `std::promise`, `std::async` — wyniki asynchroniczne

Często chcemy uruchomić zadanie w tle i później pobrać jego wynik.

`std::async` to najprostszy sposób:
```cpp
#include <future>
#include <iostream>

int oblicz()
{
    return 6 * 7;
}

int main()
{
    // Uruchamia oblicz() asynchronicznie (potencjalnie w nowym wątku)
    std::future<int> wynik = std::async(std::launch::async, oblicz);

    // ... można tu robić inne rzeczy ...

    std::cout << wynik.get() << "\n"; // czeka na wynik i go pobiera
}
```

`std::future<T>` reprezentuje wartość, która będzie dostępna w przyszłości.
`get()` blokuje wątek wywołujący, dopóki wynik nie jest gotowy.

`std::promise<T>` i `std::future<T>` pozwalają na ręczne przekazywanie
wartości między wątkami:
```cpp
std::promise<int> obietnica;
std::future<int> wynik = obietnica.get_future();

std::thread watek([&obietnica]()
{
    obietnica.set_value(42); // przekazuje wynik do future
});

std::cout << wynik.get() << "\n"; // odbiera wynik
watek.join();
```

`std::packaged_task<T>` opakowuje obiekt funkcyjny tak, aby jego wynik
był dostępny przez `std::future`. Przydatne przy budowaniu kolejek zadań.

> **Nota praktyczna:** bardziej zaawansowane mechanizmy wysokopoziomowe
> (np. pule wątków) nie zostały ustandaryzowane w C++11.
> Oczekuje się, że będą budowane na podstawie tych podstawowych mechanizmów.

***

#### Uzupełnienie (C++14): drobne poprawki

C++14 nie wprowadza dużych zmian w mechanizmach wielowątkowych, ale przynosi
kilka praktycznych ulepszeń:

* Doprecyzowano zachowanie destruktora `std::future` zwróconego przez `std::async`.
  W C++11 było niezdefiniowane, czy zniszczenie takiego `std::future` blokuje wątek
  czy nie. Prowadziło to do subtelnego błędu:
```cpp
  std::async(std::launch::async, zadanie); // wynik ignorowany — tymczasowy future
                                           // natychmiast zniszczony
```

  Tymczasowy obiekt `std::future` jest tu tworzony i od razu niszczony —
  w C++11 niektóre implementacje nie czekały wtedy na zakończenie wątku,
  co mogło prowadzić do niezdefiniowanego zachowania.
  C++14 precyzuje: destruktor `std::future` zwróconego przez `std::async`
  **zawsze blokuje** aż wątek zakończy pracę.

  Aby uniknąć tego problemu, zawsze przechowuj wynik `std::async`:
```cpp
  auto wynik = std::async(std::launch::async, zadanie); // poprawnie
```

* Dodano **`std::shared_timed_mutex`** — mutex obsługujący wielu czytających
  i jednego zapisującego (tak samo jak `std::shared_mutex` z C++17),
  ale dodatkowo z obsługą timeoutów (`try_lock_for`, `try_lock_until`).
  Pozwala to na próbę zablokowania mutexa przez określony czas,
  zamiast czekania w nieskończoność.

> **Nota:** `std::shared_timed_mutex` zostało wprowadzone w C++14, ale od C++17 preferowanym, lżejszym odpowiednikiem jest `std::shared_mutex`.
>`shared_timed_mutex` pozostaje częścią biblioteki i nie jest oznaczone jako przestarzałe.

***

#### (C++17): `std::shared_mutex` i `std::scoped_lock`

##### `std::shared_mutex` i `std::shared_lock` — wielu czytających, jeden zapisujący

W wielu programach wielowątkowych dane są często **czytane**, a rzadko **modyfikowane**.
W takim przypadku użycie zwykłego `std::mutex` jest zbyt restrykcyjne — blokuje wszystkich,
nawet gdy kilka wątków chce tylko czytać te same dane jednocześnie (co jest bezpieczne).

`std::shared_mutex` rozwiązuje ten problem, rozróżniając dwa tryby dostępu:

* **tryb współdzielony** (_shared_) — wiele wątków może jednocześnie trzymać blokadę
  do **odczytu**; żaden z nich nie może modyfikować danych,
* **tryb wyłączny** (_exclusive_) — tylko jeden wątek trzyma blokadę do **zapisu**;
  żaden inny wątek nie może ani czytać, ani pisać.

Do blokowania w trybie współdzielonym służy `std::shared_lock`,
a do trybu wyłącznego — `std::unique_lock` lub `std::lock_guard`
(tak samo jak przy zwykłym mutexie).

```cpp
#include <shared_mutex>
#include <mutex>
#include <string>

std::shared_mutex mutexDanych;
std::string wspolneDane = "poczatkowa wartosc";

// Wątek czytający — może działać równolegle z innymi czytającymi
void czytaj()
{
    std::shared_lock blokada(mutexDanych); // tryb współdzielony
    auto kopia = wspolneDane;             // bezpieczny odczyt
} // blokada zwolniona automatycznie

// Wątek zapisujący — wymaga wyłącznego dostępu
void zapisz(const std::string& nowaWartosc)
{
    std::unique_lock blokada(mutexDanych); // tryb wyłączny
    wspolneDane = nowaWartosc;
} // blokada zwolniona automatycznie
```

> **Uwaga:** `std::shared_timed_mutex` (C++14) oferuje te same możliwości, ale dodatkowo
> obsługuje timeouty (`try_lock_for`, `try_lock_until`). Jeśli timeouty nie są potrzebne,
> `std::shared_mutex` (C++17) jest lżejszym i preferowanym wyborem.

***

##### `std::scoped_lock` — jednoczesne blokowanie wielu mutexów bez zakleszczenia

Klasyczny problem z wieloma mutexami: jeśli dwa wątki próbują zablokować te same mutexy
w **odwrotnej kolejności**, mogą się wzajemnie zablokować (zakleszczenie, ang. _deadlock_).

```cpp
// Wątek A blokuje najpierw m1, potem m2
// Wątek B blokuje najpierw m2, potem m1
// → oba wątki czekają na siebie nawzajem → deadlock
```

C++17 rozwiązuje ten problem przez `std::scoped_lock`, który blokuje **wszystkie podane
mutexy jednocześnie** przy użyciu algorytmu unikania zakleszczeń:
```cpp
#include <mutex>

std::mutex m1, m2;

void funkcja()
{
    std::scoped_lock blokada(m1, m2); // oba mutexy zablokowane bezpiecznie jednocześnie
    // sekcja krytyczna
} // oba mutexy zwolnione automatycznie
```

`std::scoped_lock` jest uogólnieniem `std::lock_guard` na wiele mutexów.
Dla jednego mutexa zachowuje się identycznie jak `std::lock_guard`.

***

#### (C++20): `std::jthread` i stop tokens

##### `std::jthread` — wątek z automatycznym `join()`

`std::thread` wymaga jawnego wywołania `join()` lub `detach()` przed zniszczeniem
obiektu — pominięcie tego powoduje wywołanie `std::terminate()`.
Jest to częste źródło błędów, szczególnie gdy wyjątek przerwie normalny przepływ programu.

`std::jthread` rozwiązuje ten problem: automatycznie wywołuje `join()` w destruktorze
(analogicznie do RAII w blokadach mutexów):
```cpp
#include <thread>

void zadanie() { /* ... */ }

int main()
{
    std::jthread watek(zadanie);
    // watek.join() wywołane automatycznie na końcu zakresu
    // nawet jeśli wystąpi wyjątek
}
```

***

##### Stop tokens — ustandaryzowane anulowanie wątków

Przed C++20 nie było standardowego sposobu na poproszenie wątku o zakończenie pracy.
Programiści używali zmiennych atomowych lub flag — każdy na swój sposób.

C++20 wprowadza ustandaryzowany mechanizm:

* `std::stop_source` — źródło sygnału zatrzymania; wywołanie `request_stop()`
  wysyła żądanie zatrzymania,
* `std::stop_token` — token przekazywany do wątku; wątek sprawdza
  `token.stop_requested()` i kończy pracę gdy to konieczne.

`std::jthread` automatycznie przekazuje `std::stop_token` do funkcji wątku,
jeśli ta go przyjmuje:
```cpp
#include <thread>
#include <chrono>

void zadanie(std::stop_token token)
{
    while (!token.stop_requested())
    {
        // wykonuj pracę...
    }
    // wątek kończy się grzecznie po otrzymaniu żądania zatrzymania
}

int main()
{
    std::jthread watek(zadanie);
    // ... po jakimś czasie ...
    watek.request_stop(); // wysyła żądanie zatrzymania
    // destruktor jthread czeka na zakończenie wątku
}
```

***

##### Nowe prymitywy synchronizacji

* `std::latch` — jednorazowa bariera: wątki czekają, aż licznik spadnie do zera,
  po czym bariera otwiera się na stałe. Przydatna do synchronizacji startu
  grupy wątków lub oczekiwania na zakończenie zestawu zadań.

* `std::barrier` — bariera wielokrotnego użytku: wszystkie wątki czekają
  aż każdy z nich dotrze do punktu synchronizacji, po czym wszystkie ruszają dalej.
  Przydatna w algorytmach iteracyjnych, gdzie każda iteracja musi być
  ukończona przez wszystkie wątki przed rozpoczęciem następnej.

* `std::semaphore` — uogólniony licznik dostępu: pozwala ograniczyć liczbę wątków
  mogących jednocześnie wykonywać dany fragment kodu.
  `std::binary_semaphore` to uproszczona wersja dla wartości 0/1.

***

#### Uzupełnienie (C++20): ulepszenia atomików i futures

C++20 wprowadza drobne rozszerzenia w obszarze wielowątkowości:

* `std::atomic` zyskuje operacje `wait()`, `notify_one()` i `notify_all()`,
  pozwalające wątkowi czekać na zmianę wartości atomowej bez użycia
  mutexa i zmiennej warunkowej — prostszy i wydajniejszy alternatywny
  wzorzec dla prostych przypadków synchronizacji.

* **Dodano **`std::jthread`** oraz mechanizm zatrzymywania wątków
(**`std::stop_token`**, **`std::stop_source`**)**. `std::jthread` automatycznie
dołącza się w destruktorze i umożliwia bezpieczne anulowanie pracy wątku
poprzez `stop_token`, co znacząco upraszcza zarządzanie cyklem życia wątków.

***

### Typy krotek (Tuple types)

Krotki to kolekcje heterogenicznych obiektów o ustalonej liczbie elementów — można je traktować jako uogólnienie pól struktury.

Wersja krotek w TR1 korzystała z technik wymagających z góry określonego maksymalnego rozmiaru i sporej ilości kodu opartego na makrach.  
Dzięki szablonom wariadycznym w C++11 deklaracja krotki jest prosta i nie wymaga jawnego limitu liczby typów:
```cpp
namespace std
{
    template <class... Typy>
    class tuple;
}
```

Przykład definicji i użycia:
```cpp
typedef std::tuple<int, double, long&, const char*> KrotkaTestowa;

long dlugi = 12;
KrotkaTestowa dowod(18, 6.5, dlugi, "Ciao!");

dlugi = std::get<0>(dowod); // Przypisuje do 'dlugi' wartość 18.
std::get<3>(dowod) = " Pięknie!"; // Modyfikuje czwarty element krotki.
```

Kilka ważnych uwag:

* Można tworzyć krotkę bez podawania wartości elementów tylko wtedy, gdy typy elementów mają konstruktory domyślne.
* Można przypisać jedną krotkę do drugiej:
  - jeśli typy krotek są identyczne, każdy element musi mieć konstruktor kopiujący,
  - jeśli typy różnią się, elementy po prawej stronie muszą być konwertowalne do odpowiadających typów po lewej lub typ po lewej musi mieć odpowiedni konstruktor.

Przykład konwersji elementów:
```cpp
typedef std::tuple<int, double, std::string> Krotka1;
Krotka1 k1;

typedef std::tuple<char, short, const char*> Krotka2;
Krotka2 k2('X', 2, "Hola!");

k1 = k2; // OK: pierwsze dwa elementy da się skonwertować,
         // trzeci można skonstruować z 'const char *'.
```

Dodatkowe narzędzia:

* `std::make_tuple` — tworzy `std::tuple` z dedukcją typów,
* `auto` ułatwia deklarację zmiennych przechowujących krotki,
* `std::tie` tworzy krotki referencji do l‑value, co ułatwia rozpakowywanie krotek,
* `std::ignore` pozwala pominąć elementy podczas rozpakowywania.

Przykład:
```cpp
#include <string>
#include <tuple>

using std::string;

auto rekord = std::make_tuple("Hari Ram", "New Delhi", 3.5, 'A');

string imie;
float gpa;
char ocena;

std::tie(imie, std::ignore, gpa, ocena) = rekord; // std::ignore pomija nazwę miejsca

std::cout << imie << ' ' << gpa << ' ' << ocena << std::endl;
```

Dostępne są operatory relacyjne (dla krotek o tej samej liczbie elementów) oraz dwie metafunkcje kompilacyjne:

* `std::tuple_size<T>::value` — zwraca liczbę elementów w krotce `T`,
* `std::tuple_element<I, T>::type` — zwraca typ elementu o indeksie `I` w krotce `T`.

#### (C++14): pobieranie elementu krotki po typie (`std::get<T>`)

W C++11 elementy `std::tuple` można było pobierać wyłącznie za pomocą indeksu:
```cpp
auto x = std::get<2>(t);
```

C++14 rozszerza `std::get` o możliwość pobierania elementu **po typie**:
```cpp
using std::string;
using std::tuple;

tuple<string, string, int> t("foo", "bar", 7);

int liczba = std::get<int>(t); // OK — jedyny element typu int
int liczba2 = std::get<2>(t);  // nadal działa jak wcześniej
```

Jeśli krotka zawiera **więcej niż jeden element danego typu**, wywołanie `std::get<T>` powoduje **błąd kompilacji**:
```cpp
string s = std::get<string>(t); // błąd: typ string jest niejednoznaczny
```

Mechanizm ten poprawia czytelność kodu i eliminuje konieczność pamiętania indeksów, o ile typy w krotce są unikalne.

***

#### Uzupełnienie (C++14): `std::make_tuple` jako częściowo `constexpr`

W C++11 funkcja `std::make_tuple` nie była funkcją `constexpr`, co uniemożliwiało tworzenie krotek w kontekście stałoczasowym.

C++14 częściowo to zmienia — `std::make_tuple` staje się **`constexpr` tam, gdzie to możliwe**, co pozwala tworzyć proste krotki w czasie kompilacji:
```cpp
constexpr auto t = std::make_tuple(1, 2.5, 'x'); // OK w C++14
```

Ograniczenia wynikają z tego, że `constexpr` zależy od tego, czy wszystkie elementy krotki są `constexpr`‑konstruktywne.

***

#### Uzupełnienie (C++17/20/23)

* **C++17** — krotki stały się w pełni `constexpr`; dodano strukturę wiązań (`auto [a, b] = krotka;`).  
* **C++20** — krotki są kompatybilne z `std::ranges`.  
* **C++23** — usprawniono dedukcję typów i integrację z `std::format`.

***

### Hash tables

Dodanie tablic mieszających (unordered associative containers) było jednym z najczęściej zgłaszanych postulatów.  
Nie trafiły do C++03 wyłącznie z powodu ograniczeń czasowych.

Choć w najgorszym przypadku (przy wielu kolizjach) tablice mieszające są mniej wydajne niż zrównoważone drzewa, w wielu praktycznych zastosowaniach działają szybciej.

Kolizje są obsługiwane wyłącznie przez **łańcuchowanie liniowe**, ponieważ komitet uznał, że standaryzowanie rozwiązań z otwartym adresowaniem wprowadza zbyt wiele problemów (zwłaszcza przy usuwaniu elementów).

Aby uniknąć konfliktów nazw z bibliotekami niestandardowymi, użyto przedrostka **`unordered`** zamiast **`hash`**.

Nowa biblioteka udostępnia cztery typy kontenerów unordered:

| Typ kontenera               | Wartość powiązana | Klucze równoważne |
|-----------------------------|-------------------|--------------------|
| `std::unordered_set`        | Nie               | Nie                |
| `std::unordered_multiset`   | Nie               | Tak                |
| `std::unordered_map`        | Tak               | Nie                |
| `std::unordered_multimap`   | Tak               | Tak                |

Nowe klasy spełniają wszystkie wymagania kontenera i udostępniają metody takie jak `insert`, `erase`, `begin`, `end`.

Ta funkcja nie wymagała rozszerzeń rdzenia języka — jedynie niewielkiego rozszerzenia nagłówka `<functional>` oraz dodania `<unordered_set>` i `<unordered_map>`.

#### Uzupełnienie (C++17/20/23)

* **C++17** — dodano `try_emplace`, `insert_or_assign` w mapach.  
* **C++20** — poprawiono wydajność hashowania i dodano `contains()`.  
* **C++23** — rozszerzono API o nowe operacje i poprawiono integrację z `std::expected`.

***

### std::array i std::forward_list

Poza tablicami mieszającymi do biblioteki dodano jeszcze dwa kontenery:

* **`std::array`** — kontener o stałym rozmiarze, bardziej wydajny niż `std::vector` w scenariuszach, gdzie rozmiar jest znany i stały, a jednocześnie bezpieczniejszy i wygodniejszy w użyciu niż tablica w stylu C.
* **`std::forward_list`** — lista jednokierunkowa, która zajmuje mniej pamięci niż dwukierunkowa `std::list`, gdy nie potrzebujemy iteracji dwukierunkowej.

#### Uzupełnienie (C++17/20)

* **C++17** — `std::array` stał się w pełni `constexpr`.  
* **C++20** — `std::array` i `std::forward_list` współpracują z `std::ranges`.

***

### Wyrażenia regularne (Regular expressions)

Nowa biblioteka, dostępna w nagłówku `<regex>`, wprowadza kilka klas:

* wyrażenia regularne reprezentuje szablon `std::regex`,
* dopasowania reprezentuje `std::match_results`,
* `std::regex_iterator` służy do iterowania po wszystkich dopasowaniach wyrażenia.

Funkcja `std::regex_search` służy do wyszukiwania, a `std::regex_replace` do operacji „znajdź i zamień”, zwracając nowy łańcuch.

Przykład użycia `std::regex_iterator`:
```cpp
#include <regex>

using std::cregex_iterator;
using std::regex;
using std::string;

const char* wzorzec = R"([^ ,.\t\n]+)"; // znajdź słowa oddzielone spacją, przecinkiem, kropką, tabem, nową linią

regex re(wzorzec); // rzuca wyjątek przy niepoprawnym wzorcu

const char* tekst = "Unseen University - Ankh-Morpork";

// Użyj regex_iterator, aby zidentyfikować wszystkie słowa w 'tekst' rozdzielone znakami z 'wzorzec'.
for (cregex_iterator iter(tekst, tekst + strlen(tekst), re); iter != re.end(); ++iter)
{
    string dopasowanie = iter->str();
    std::cout << dopasowanie << std::endl;
}
```

Nagłówek `<regex>` nie wymaga modyfikacji istniejących nagłówków ani rozszerzeń rdzenia języka.
W systemach POSIX wyrażenia regularne są też dostępne przez bibliotekę C (`<regex.h>`), ale implementacje i interfejsy różnią się od C++ `<regex>`.

#### Uzupełnienie (C++17/20/23)

* **C++17** — poprawiono wydajność i stabilność implementacji `<regex>` (wiele kompilatorów dopiero wtedy zaczęło mieć w pełni działające regexy).
* **C++20** — dodano `constexpr` dla części operacji na `std::regex_constants`.
* **C++23** — trwają prace nad ujednoliceniem zachowania `<regex>` między kompilatorami (nie jest to część standardu, ale praktyczna uwaga).

***

### Ogólnego przeznaczenia inteligentne wskaźniki (General-purpose smart pointers)

C++11 dostarcza `std::unique_ptr` oraz ulepszenia dla `std::shared_ptr` i `std::weak_ptr` pochodzących z TR1.
`std::auto_ptr` jest **przestarzały** (deprecated) i nie powinien być używany w nowych programach - usunięty całkowicie w standardzie C++17.

> **Uwaga:** `std::unique_ptr` zastępuje `std::auto_ptr` w większości zastosowań, oferując bezpieczne semantyki przenoszenia bez niejednoznacznych zachowań kopiowania.

#### Uzupełnienie (C++14/17/20)

* **C++14** — dodano `std::make_unique`.
* **C++17** — poprawiono integrację `std::shared_ptr` z tablicami.
* **C++20** — inteligentne wskaźniki mogą być używane w większej liczbie kontekstów `constexpr`.

  C++20 rozszerza `std::make_shared` i `std::allocate_shared` o obsługę tablic:
```cpp
  auto ptr = std::make_shared<int[]>(10);    // tablica 10 int-ów
  auto ptr2 = std::make_shared<int[5]>();    // tablica 5 int-ów (rozmiar w typie)
  ptr[0] = 42;
```

  Przed C++20 `std::shared_ptr` obsługiwał tablice, ale `std::make_shared` nie — trzeba było używać `std::shared_ptr<int[]>(new int[10])`.

***

### Rozszerzalny mechanizm liczb losowych (Extensible random number facility)

Biblioteka standardowa C dostarczała funkcję `rand` do generowania pseudolosowych liczb, ale algorytm był całkowicie zależny od dostawcy biblioteki.
C++11 wprowadza nowy, bardziej elastyczny mechanizm generowania liczb pseudolosowych.

Mechanizm C++11 dzieli się na dwie części:

* **silnik generatora** (engine) — przechowuje stan generatora i produkuje surowe pseudolosowe wartości,
* **rozkład** (distribution) — określa zakres i rozkład matematyczny wyników.

Silnik i rozkład łączy się, tworząc obiekt generatora losowego.

W odróżnieniu od `rand`, C++11 dostarcza trzy podstawowe algorytmy silników:

* `linear_congruential_engine`,
* `subtract_with_carry_engine`,
* `mersenne_twister_engine` (np. `std::mt19937`).

C++11 udostępnia też wiele standardowych rozkładów, m.in.:

* `uniform_int_distribution`,
* `uniform_real_distribution`,
* `bernoulli_distribution`,
* `binomial_distribution`,
* `geometric_distribution`,
* `negative_binomial_distribution`,
* `poisson_distribution`,
* `exponential_distribution`,
* `gamma_distribution`,
* `weibull_distribution`,
* `extreme_value_distribution`,
* `normal_distribution`,
* `lognormal_distribution`,
* `chi_squared_distribution`,
* `cauchy_distribution`,
* `fisher_f_distribution`,
* `student_t_distribution`,
* `discrete_distribution`,
* `piecewise_constant_distribution` oraz
* `piecewise_linear_distribution`.

Przykład łączenia silnika i rozkładu:
```cpp
#include <functional>
#include <random>

using std::mt19937;
using std::uniform_int_distribution;

uniform_int_distribution<int> rozklad(0, 99);
mt19937 silnik; // Mersenne twister MT19937

auto generator = std::bind(rozklad, silnik);

int losowa1 = generator();            // Wygeneruj liczbę 0..99
int losowa2 = rozklad(silnik);        // Alternatywny sposób generowania
```

> **Wskazówka praktyczna:** nowy mechanizm pozwala wybrać odpowiedni silnik i rozkład do konkretnego zastosowania (np. symulacje, gry, statystyka), zamiast polegać na jednej, nieokreślonej implementacji `rand`.

#### Uzupełnienie (C++14/17/20/23)

* **C++14** — dodano `std::shuffle` oparty na silnikach `<random>`.
* **C++17** — poprawiono deterministyczność i stabilność implementacji.
* **C++20** — część rozkładów i silników stała się `constexpr`.
* **C++23** — trwają prace nad rozszerzeniem API generatorów (niektóre kompilatory już implementują propozycje).

***

### Wrapper reference (opakowanie referencji)

**Wrapper reference (opakowanie referencji)** uzyskuje się z instancji szablonu klasy `reference_wrapper`.
Opakowania referencji są podobne do zwykłych referencji języka C++ (`&`).
Aby uzyskać opakowanie referencji z dowolnego obiektu, używa się funkcji szablonowej `ref` (dla referencji stałej — `cref`).

Opakowania referencji są szczególnie przydatne w funkcjach szablonowych, gdy chcemy przekazywać **referencje** do parametrów zamiast ich **kopiować**:
```cpp
#include <functional>
#include <iostream>

// Ta funkcja przyjmie referencję do parametru 'r' i ją zwiększy.
void funkcja(int& r)
{
    r++;
}

// Funkcja szablonowa.
template <class F, class P>
void g(F f, P t)
{
    f(t);
}

int main()
{
    int i = 0;

    g(funkcja, i);
    // Instancjacja: 'g<void(int&), int>'
    // W efekcie 'i' nie zostanie zmodyfikowane.

    std::cout << i << std::endl; // Wyjście -> 0

    g(funkcja, std::ref(i));
    // Instancjacja: 'g<void(int&), reference_wrapper<int>>'
    // W efekcie 'i' zostanie zmodyfikowane.

    std::cout << i << std::endl; // Wyjście -> 1
}
```

Ta funkcjonalność została dodana do istniejącego nagłówka `<functional>` i nie wymagała zmian w rdzeniu języka.

#### Uzupełnienie (C++14/17/20/23)

**C++14**

* `reference_wrapper` zyskał bardziej konsekwentne konwersje do `T&`.
* `std::ref` i `std::cref` stały się częściowo `constexpr`.

**C++17**

* `reference_wrapper` stał się **literalnym typem** (`constexpr`).
* Można go używać w strukturach wiązań (`auto& [a, b] = ...;`).

**C++20**

* Wrappery referencji współpracują z `std::invoke` w kontekstach `constexpr`.
* `std::invoke` stał się centralnym mechanizmem wywoływania obiektów funkcyjnych.

**C++23**

* Wrappery są szerzej akceptowane w algorytmach ranges.
* Trwa integracja z `std::expected` i `std::function_ref`.

***

### Polimorficzne wrappery dla obiektów funkcyjnych

**Polimorficzne wrappery** dla obiektów funkcyjnych działają podobnie do wskaźników na funkcje pod względem semantyki i składni, ale są mniej ściśle związane z konkretnym typem.
Mogą odnosić się do **wszystkiego, co da się wywołać**:

* wskaźników na funkcje,
* wskaźników na metody składowe,
* funktorów,

o ile argumenty są zgodne z sygnaturą wrappera.

Przykład:
```cpp
#include <functional>

using std::function;
using std::plus;

// Tworzenie wrappera przy użyciu szablonu 'function'.
function<int(int, int)> funkcja;

plus<int> dodaj;
// 'plus' zadeklarowano jako 'template <class T> T plus(T, T);'
// więc 'dodaj' ma typ 'int dodaj(int x, int y)'.

funkcja = dodaj; // OK — parametry i typ zwracany są zgodne.

int a = funkcja(1, 2);

// UWAGA: jeśli wrapper 'funkcja' nie odnosi się do żadnej funkcji,
// rzucany jest wyjątek 'std::bad_function_call'.

function<bool(short, short)> funkcja2;

if (!funkcja2)
{
    // Prawda, ponieważ 'funkcja2' nie została jeszcze przypisana.

    bool adjacent(long x, long y);
    funkcja2 = &adjacent; // OK — parametry i typ zwracany są konwertowalne.

    struct Test
    {
        bool operator()(short x, short y);
    };

    Test obiekt;

    // 'std::ref' zwraca wrapper dla obiektu 'obiekt' (jego operator()).
    funkcja = std::ref(obiekt);
}

funkcja = funkcja2; // OK — parametry i typy zwracane są konwertowalne.
```

Szablonowa klasa `function` została zdefiniowana w nagłówku `<functional>` bez potrzeby zmiany języka.

#### Uzupełnienie (C++14/17/20/23)

**C++14**

* W wielu implementacjach pojawiło się `make_function` (nie w standardzie, ale popularne).
* `std::function` lepiej współpracuje z lambdami niekopiowalnymi.

**C++17**

* `std::function` korzysta z `std::invoke`, co ujednoliciło sposób wywoływania funkcji, metod i funktorów.
* Poprawiono wydajność i semantykę przenoszenia.

**C++20**

* `std::function` może być używany w kontekstach `constexpr` (częściowo zależne od implementacji).
* Dodano `std::bind_front`, lżejszą alternatywę dla `std::bind`.

**C++23**

* Wprowadzono `std::function_ref` — lekki, niewłaścicielski wrapper na obiekty wywoływalne.
* `std::function` zyskał lepszą integrację z ranges i `std::expected`.

***

### Cechy typów (type traits) do metaprogramowania

**Metaprogramowanie** polega na tworzeniu programu, który tworzy lub modyfikuje inny program (albo samego siebie).
W C++ wiele tego typu operacji wykonuje się **w czasie kompilacji** za pomocą szablonów.

Komitet standaryzacyjny wprowadził bibliotekę ułatwiającą metaprogramowanie kompilacyjne — zestaw **cech typów (type traits)** dostępny w nagłówku `<type_traits>`.

Przykład metaprogramu w C++03: rekurencyjne obliczanie potęgi całkowitej przy użyciu szablonów:
```cpp
template <int B, int N>
struct Potega
{
    // rekurencyjne wywołanie i rekombinacja
    enum
    {
        WARTOSC = B * Potega<B, N - 1>::WARTOSC
    };
};

template <int B>
struct Potega<B, 0>
{
    // warunek zakończenia: N == 0
    enum
    {
        WARTOSC = 1
    };
};

int wynik = Potega<3, 4>::WARTOSC;
```

Wiele algorytmów działa na różnych typach danych; szablony wspierają programowanie generyczne, ale często algorytm potrzebuje informacji o typie użytym w instancjacji.
Taką informację dostarczają **cechy typów (type traits)** — metafunkcje i struktury, które:

* identyfikują kategorię typu lub jego właściwości,
* umożliwiają transformacje typów,
* pozwalają podejmować decyzje w czasie kompilacji.

Przykład użycia cech typów do wyboru implementacji:
```cpp
#include <type_traits>

using std::is_floating_point;
using std::is_integral;

// Pierwszy sposób działania.
template <bool B>
struct Algorytm
{
    template <class T1, class T2>
    static int wykonaj(T1& a, T2& b)
    {
        // ...
    }
};

// Drugi sposób działania (specjalizacja dla true).
template <>
struct Algorytm<true>
{
    template <class T1, class T2>
    static int wykonaj(T1 a, T2 b)
    {
        // ...
    }
};

// Instancjacja 'opracuj' automatycznie wybierze właściwy sposób działania.
template <class T1, class T2>
int opracuj(T1 a, T2 b)
{
    // Użyj drugiego sposobu tylko jeśli 'T1' jest całkowity, a 'T2' jest zmiennoprzecinkowy.
    return Algorytm<is_integral<T1>::value && is_floating_point<T2>::value>::wykonaj(a, b);
}
```

Dzięki cechom typów można też wykonywać **transformacje typów** (np. usuwanie `const`, dodawanie referencji), co jest niezbędne w zaawansowanych szablonach, gdzie `static_cast` i `const_cast` są niewystarczające.

**Uwaga praktyczna:** metaprogramowanie daje eleganckie i zwarte rozwiązania, ale debugowanie błędów kompilacji może być trudne — komunikaty kompilatora bywają długie i nieintuicyjne.

#### Uzupełnienie (C++14/17/20/23)

**C++14**

* Dodano wiele nowych traitsów, m.in. `std::is_final`, `std::is_null_pointer`.
* Wprowadzono aliasy `_t` i `_v`, np. `std::remove_const_t<T>`, `std::is_integral_v<T>` — ogromne uproszczenie metaprogramowania.

**C++17**

* Wiele traitsów stało się `constexpr`.
* Dodano `std::void_t`, kluczowy element nowoczesnego SFINAE.
* Dodano `std::is_invocable`, `std::invoke_result`, `std::is_swappable`, `std::is_nothrow_swappable`.
* Dodano **logiczne cechy typów**: `std::conjunction<T...>`, `std::disjunction<T...>`,
  `std::negation<T>` — pozwalają łączyć warunki na typach operatorami logicznymi
  bez ręcznego pisania zagnieżdżonych szablonów:
```cpp
  // Czy wszystkie typy są całkowite?
  static_assert(std::conjunction_v<std::is_integral<int>,
                                   std::is_integral<long>>);

  // Czy któryś typ jest wskaźnikiem?
  static_assert(std::disjunction_v<std::is_pointer<int*>,
                                   std::is_pointer<int>>);
```
  `conjunction` i `disjunction` są **leniwe** — przestają sprawdzać kolejne typy
  gdy wynik jest już znany (short-circuit evaluation w czasie kompilacji).

**C++20**

* Wprowadzenie **konceptów** (`std::integral`, `std::floating_point`, `std::regular`…) — w praktyce zastępują wiele klasycznych traitsów.
* Dodano `std::type_identity` i `std::remove_cvref_t`.
* Traitsy stały się szerzej dostępne w kontekstach `constexpr`.

**C++23**

* Rozszerzono `std::is_scoped_enum`.
* Dodano nowe narzędzia do detekcji typów w kontekście ranges i `std::expected`.
* Traitsy są szerzej wykorzystywane w standardowych konceptach.

***

### Jednolita metoda wyznaczania typu zwracanego obiektów funkcyjnych

Określenie typu zwracanego funkcji szablonowej w czasie kompilacji bywa nieintuicyjne, zwłaszcza gdy typ zwracany zależy od parametrów. Przykład:
```cpp
struct Jasny
{
    // Typ parametru jest równy typowi zwracanemu.
    int operator()(int) const;
    double operator()(double) const;
};

template <class Obj>
class Kalkulator
{
private:
    Obj element;
public:
    template <class Arg>
    Arg operator()(Arg& a) const
    {
        return element(a);
    }
};
```

Dla `Kalkulator<Jasny>` zwracany typ będzie zgodny z typem parametru `Arg`.
Jednak dla klasy `Zdezorientowany`:
```cpp
struct Zdezorientowany
{
    // Typ parametru nie jest równy typowi zwracanemu.
    double operator()(int) const;
    int operator()(double) const;
};
```

Instancjacja `Kalkulator<Zdezorientowany>` może prowadzić do niejednoznaczności i konwersji między `int` i `double`, co skutkuje ostrzeżeniami lub błędami.

TR1 wprowadziło, a C++11 przyjęło, szablonową metafunkcję **`std::result_of`**, która pozwala wyznaczyć typ zwracany wywołania obiektu funkcyjnego.
Przykład użycia w poprawionej wersji `Kalkulator`:
```cpp
#include <type_traits>

using std::result_of;

template <class Obj>
class KalkulatorVer2
{
private:
    Obj element;
public:
    template <class Arg>
    typename result_of<Obj(Arg)>::type operator()(Arg& a) const
    {
        return element(a);
    }
};
```

W ten sposób `KalkulatorVer2<Zdezorientowany>` nie wymaga konwersji ani nie generuje ostrzeżeń.

Różnica względem wersji TR1 polega na tym, że TR1 dopuszczał implementacje, które nie były w stanie określić typu wyniku w pewnych przypadkach.
Dzięki wprowadzeniu `decltype` w C++11, wersja `std::result_of` w C++11 **musi** wyznaczać typ wyniku we wszystkich przypadkach.

#### Uzupełnienie (C++14/17/20/23)

**C++14**

* Dodano alias `std::result_of_t<T>`.

**C++17**

* `std::result_of` zostało oznaczone jako **przestarzałe**.
* Zastępuje je **`std::invoke_result`** i alias `std::invoke_result_t`.

**C++20**

* `std::result_of` zostało **usunięte**.
* Jedynym poprawnym sposobem określania typu zwracanego jest `std::invoke_result_t`.

**C++23**

* `invoke_result` jest szeroko stosowane w ranges i nowych algorytmach.

***

## Ulepszona zgodność z C

Standard **C++11** wprowadził zestaw zmian mających na celu poprawę zgodności z językiem **C99**.

### C++11

#### Preprocesor

* makra wariadyczne (_variadic macros_),
* łączenie sąsiednich literałów łańcuchowych (wąskich i szerokich),
* funkcja `_Pragma()` — odpowiednik `#pragma`.

***

#### Typy i makra

* `long long` — typ całkowity gwarantowany co najmniej na 64 bity,
* `__func__` — makro zwracające nazwę bieżącej funkcji.

***

#### Nagłówki

* `cstdbool` (odpowiednik `stdbool.h`),
* `cstdint` (odpowiednik `stdint.h`),
* `cinttypes` (odpowiednik `inttypes.h`).

***

### C++17

#### Preprocesor

* `__has_include(<nagłówek>)` (C++17) — pozwala sprawdzić w preprocesie,
  czy dany nagłówek jest dostępny:
```cpp
  #if __has_include(<optional>)
  #  include <optional>
  #else
  #  include "my_optional.h"
  #endif
```
  Przydatne przy pisaniu kodu przenośnego między kompilatorami i standardami.

***

### C++14 / C++20 / C++23

Brak zmian — żadna z późniejszych wersji standardu nie rozszerzała ani nie modyfikowała tej sekcji.

***

## Funkcje usunięte lub oznaczone jako przestarzałe (C++11 → C++17 → C++20)

Ta sekcja w C++11 obejmowała elementy oznaczone jako **przestarzałe (deprecated)** lub **usunięte**.
Nowsze standardy — szczególnie **C++17** — kontynuowały proces usuwania tych elementów, a **C++20** wprowadził ponownie `export`, ale w zupełnie innym znaczeniu (moduły).

Poniżej znajduje się uporządkowana lista zmian, z zaznaczeniem ewolucji w kolejnych standardach.

### C++11

* Termin **sequence point** został usunięty i zastąpiony precyzyjnym określeniem relacji między operacjami:
  _sequenced before_, _unsequenced_, _indeterminately sequenced_.

* Słowo kluczowe `export` oraz mechanizm eksportowanych szablonów zostały usunięte.
  Pozostało zarezerwowane (powróci dopiero w C++20, ale w innym znaczeniu — moduły).

* Dynamiczne specyfikacje wyjątków (`throw(...)`) zostały oznaczone jako przestarzałe.
  Zastępuje je **`noexcept`**.

* `std::auto_ptr` zostało oznaczone jako przestarzałe — zastępuje je `std::unique_ptr`.

* Klasy bazowe dla obiektów funkcyjnych (`std::unary_function`, `std::binary_function`),
  adaptery wskaźników (`ptr_fun`, `mem_fun`, `mem_fun_ref`) oraz bindery (`bind1st`, `bind2nd`)
  zostały oznaczone jako przestarzałe.

* Słowo kluczowe `register` zostało oznaczone jako przestarzałe.

***

### C++14

Standard C++14 **nie wprowadził żadnych zmian** dotyczących elementów przestarzałych lub usuniętych w tej sekcji.
Wszystkie pozycje z C++11 pozostały w tym samym stanie.

***

### C++17 (usunięcia elementów przestarzałych)

C++17 usuwa większość elementów oznaczonych jako przestarzałe w C++11:

* Dynamiczne specyfikacje wyjątków (`throw(...)`) — **całkowicie usunięte** z języka.

* `std::auto_ptr` — **usunięte**.

* `std::unary_function`, `std::binary_function` — **usunięte**.

* Adaptery wskaźników (`ptr_fun`, `mem_fun`, `mem_fun_ref`) — **usunięte**.

* Bindery (`bind1st`, `bind2nd`) — **usunięte**.

* Słowo kluczowe `register` — **usunięte** jako specyfikator klasy przechowywania.

* **Trygrafy** — trzyznakowe sekwencje zastępujące znaki niedostępne na niektórych
  klawiaturach (np. `??=` zamiast `#`, `??(` zamiast `[`) — zostały **usunięte**.
  Były dziedzictwem standardu ISO 646 i praktycznie nieużywane we współczesnym kodzie.
  Kompilatory już od dawna obsługiwały je opcjonalnie.

***

### C++20

* Słowo kluczowe `export` zostało **przywrócone**, ale wyłącznie jako element **modułów**.
  Nie ma żadnego związku z eksportowanymi szablonami z C++98/03.

* Brak dodatkowych usunięć lub deprecacji w zakresie elementów wymienionych w tej sekcji.

***

### C++23

Standard C++23 **nie wprowadza nowych deprecacji ani usunięć** dotyczących elementów opisanych powyżej.
