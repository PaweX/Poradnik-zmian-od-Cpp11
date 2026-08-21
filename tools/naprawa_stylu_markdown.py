#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import shutil
from pathlib import Path

HEADER_RE = re.compile(r'^(#{1,6})\s+(.+)$')
HEADER_ANY_RE = re.compile(r'^\s*#{1,6}\s')
CODEBLOCK_RE = re.compile(r'^```')

def analyze(lines):
    """
    Zwraca:
      - header_issues: błędy hierarchii nagłówków (skoki w górę > 1)
      - trailing_backslashes: linie z końcowym '\'
      - codeblock_issue: nieparzysta liczba bloków ```
    """
    header_issues = []
    trailing = []

    inside_code = False
    codeblock_count = 0
    prev_header_level = None
    prev_header_line = None

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        # blok kodu
        if CODEBLOCK_RE.match(line):
            inside_code = not inside_code
            codeblock_count += 1
            continue

        if inside_code:
            continue

        # nagłówki
        m = HEADER_RE.match(line)
        if m:
            level = len(m.group(1))

            if prev_header_level is not None:
                delta = level - prev_header_level
                if delta > 1:
                    header_issues.append({
                        "line": idx,
                        "line_text": line,
                        "prev_line": prev_header_line,
                        "prev_level": prev_header_level,
                        "curr_level": level,
                        "delta": delta
                    })

            prev_header_level = level
            prev_header_line = idx
            continue

        # końcowy '\'
        if line.endswith("\\") and line.strip() != "\\":
            trailing.append({"line": idx, "line_text": line})

    codeblock_issue = (codeblock_count % 2 != 0)
    return header_issues, trailing, codeblock_issue


def extract_headers(lines):
    headers = []
    inside_code = False

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        if CODEBLOCK_RE.match(line):
            inside_code = not inside_code
            continue

        if inside_code:
            continue

        m = HEADER_RE.match(line)
        if m:
            headers.append({
                "line": idx,
                "level": len(m.group(1)),
                "text": m.group(2)
            })

    return headers


def print_headers_tree(headers):
    print("\n--- Struktura nagłówków ---")
    for h in headers:
        indent = "  " * (h["level"] - 1)
        print(f"{indent}- (linia {h['line']}) {h['text']}")
    print("--- Koniec struktury ---\n")


def apply_fixes(lines):
    new_lines = []
    inside_code = False
    prev_header_level = None

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        # blok kodu
        if CODEBLOCK_RE.match(line):
            inside_code = not inside_code
            new_lines.append(raw)
            continue

        if inside_code:
            new_lines.append(raw)
            continue

        # naprawa nagłówków
        m = HEADER_RE.match(line)
        if m:
            hashes = m.group(1)
            text = m.group(2)
            level = len(hashes)

            if prev_header_level is not None and level > prev_header_level + 1:
                level = prev_header_level + 1
                hashes = "#" * level
                line = f"{hashes} {text}"

            prev_header_level = level

        # naprawa końcowego '\'
        if line.endswith("\\") and line.strip() != "\\":
            line = line[:-1]

        # ZAWSZE zapisujemy poprawioną linię
        new_lines.append(line + "\n")

    return new_lines



def print_report(header_issues, trailing, codeblock_issue):
    if not header_issues and not trailing and not codeblock_issue:
        print("Brak wykrytych problemów.")
        return

    if header_issues:
        print("\nProblemy z hierarchią nagłówków (skoki w górę > 1):")
        for it in header_issues:
            print(f"  - Linia {it['line']}: \"{it['line_text']}\"")
            print(f"    Poprzedni nagłówek: linia {it['prev_line']} poziom {it['prev_level']}, "
                  f"obecny poziom {it['curr_level']} (delta {it['delta']})")

    if trailing:
        print("\nLinie kończące się '\\' do poprawy:")
        for t in trailing:
            print(f"  - Linia {t['line']}: \"{t['line_text']}\"")

    if codeblock_issue:
        print("\n⚠️ UWAGA: Nieparzysta liczba bloków ``` — dokument może być uszkodzony!")


def clean_colon_codeblocks(lines):
    """Usuwa WSZYSTKIE puste linie między linią kończącą się na ':' a blokiem kodu ```"""
    new_lines = []
    removed_count = 0
    i = 0
    n = len(lines)

    while i < n:
        raw_line = lines[i]
        current_line = raw_line.rstrip("\n\r")

        new_lines.append(raw_line)

        # Jeśli linia kończy się na ':' 
        if current_line.endswith(":") and not current_line.lstrip().startswith("```"):
            j = i + 1
            empty_lines_found = 0
            while j < n and lines[j].strip() == "":
                empty_lines_found += 1
                j += 1

            if j < n and CODEBLOCK_RE.match(lines[j].lstrip()):
                if empty_lines_found > 0:
                    print(f"✓ Linia {i+1}: usunięto {empty_lines_found} pustych linii po ':'")
                    removed_count += empty_lines_found
                
                # Przeskakujemy wszystkie puste linie (nie dodajemy żadnej)
                i = j - 1

        i += 1

    if removed_count == 0:
        print("✓ Nie znaleziono pustych linii do usunięcia po ':'.")

    return new_lines
    
    
SEPARATORS = {"***", "---", "___"}


def _header_level(line):
    """Zwraca poziom nagłówka (1-6) dla linii pasującej do HEADER_ANY_RE, albo None."""
    m = HEADER_ANY_RE.match(line)
    if not m:
        return None
    level = 0
    for ch in line.lstrip():
        if ch == "#":
            level += 1
        else:
            break
    return level if 1 <= level <= 6 else None


def add_header_separators(lines):
    """
    Reguły, egzekwowane łącznie:

      1) Przed KAŻDYM nagłówkiem (poza pierwszą linią całego dokumentu) ma być
         co najmniej jedna pusta linia. Linia otwierająca lub zamykająca blok
         kodu ``` liczy się przy tym jak pusta linia (jest niewidoczna po
         wyrenderowaniu) — ale sama nigdy nie jest ruszana ani przesuwana.

      2) Separator '***' wolno mieć TYLKO między nagłówkiem a kolejnym
         nagłówkiem o RÓWNYM LUB PŁYTSZYM poziomie i tylko gdy jest między
         nimi realna treść — nigdy między nagłówkiem a kolejnym GŁĘBSZYM.
         Gdy jest wskazany, dostaje dokładnie jedną pustą linię przed i po
         (to nadpisuje regułę 1 dla samego separatora). Brakujący separator
         jest dodawany, niedozwolony usuwany, źle rozstawiony poprawiany.

      3) "Separator rozwinięty": dwie linie '***' z treścią pomiędzy nimi
         (bez nagłówka w środku), gdzie pierwsza '***' nie ma pustej linii
         zaraz po sobie, a druga nie ma pustej linii zaraz przed sobą. Taki
         blok jest traktowany jako całość — zwykła, nietykalna treść — nigdy
         nie jest dzielony ani zarządzany jak zwykły separator.

    Bloki kodu ``` ``` `` są całkowicie nietykalne.
    """
    n = len(lines)

    in_code = [False] * n
    inside_code = False
    for i in range(n):
        if lines[i].strip().startswith("```"):
            in_code[i] = True
            inside_code = not inside_code
            continue
        in_code[i] = inside_code

    headers = []
    for i in range(n):
        if in_code[i]:
            continue
        level = _header_level(lines[i].rstrip("\n\r"))
        if level is not None:
            headers.append((i, level))

    if not headers:
        return lines[:]

    # --- Wykrywanie "separatorów rozwiniętych" ---
    all_seps = [i for i in range(n) if not in_code[i] and lines[i].strip() in SEPARATORS]
    protected = set()
    si = 0
    while si < len(all_seps) - 1:
        p, q = all_seps[si], all_seps[si + 1]
        no_blank_after_p = p + 1 < n and lines[p + 1].strip() != ""
        no_blank_before_q = q - 1 >= 0 and lines[q - 1].strip() != ""
        header_between = any(
            not in_code[k] and _header_level(lines[k].rstrip("\n\r")) is not None
            for k in range(p + 1, q)
        )
        if no_blank_after_p and no_blank_before_q and not header_between:
            protected.add(p)
            protected.add(q)
            si += 2
        else:
            si += 1

    def strip_tail(seg_start, seg_end):
        """Cofa się od seg_end. Zwraca (core_end, sep_idx_lub_None, blanks_before,
        real_blanks_after, fence_after, fence_before) - fence_after/fence_before
        mówią, czy odpowiednią granicę wyznaczyło ogrodzenie ``` (a nie prawdziwa
        pusta linia)."""
        j = seg_end
        real_blanks_after = 0
        while j > seg_start and not in_code[j - 1] and lines[j - 1].strip() == "":
            real_blanks_after += 1
            j -= 1

        fence_after = (
            real_blanks_after == 0
            and j > seg_start
            and lines[j - 1].strip().startswith("```")
        )

        if (
            j > seg_start
            and not in_code[j - 1]
            and lines[j - 1].strip() in SEPARATORS
            and (j - 1) not in protected
        ):
            sep_idx = j - 1
            j -= 1
            blanks_before = 0
            while j > seg_start and not in_code[j - 1] and lines[j - 1].strip() == "":
                blanks_before += 1
                j -= 1
            fence_before = (
                blanks_before == 0
                and j > seg_start
                and lines[j - 1].strip().startswith("```")
            )
            return j, sep_idx, blanks_before, real_blanks_after, fence_after, fence_before

        return j, None, 0, real_blanks_after, fence_after, False

    added_count = 0
    removed_count = 0
    normalized_count = 0
    spaced_count = 0
    specs = []

    def process_segment(seg_start, seg_end, header_line_no, level_a, level_b):
        nonlocal added_count, removed_count, normalized_count, spaced_count
        core_end, sep_idx, blanks_before, real_blanks_after, fence_after, fence_before = strip_tail(seg_start, seg_end)
        has_content = any(lines[k].strip() != "" for k in range(seg_start, core_end))
        # jeśli tuż przed core_end stoi zamykające *** separatora rozwiniętego,
        # ono już wizualnie pełni rolę granicy - nie dokładamy drugiego
        tail_is_protected = core_end > seg_start and (core_end - 1) in protected
        want_separator = (
            has_content
            and (level_a is not None)
            and (level_b <= level_a)
            and not tail_is_protected
        )

        before_ok = blanks_before == 1 or (blanks_before == 0 and fence_before)
        after_ok = real_blanks_after == 1 or (real_blanks_after == 0 and fence_after)

        if sep_idx is not None and not want_separator:
            removed_count += 1
            reason = "brak treści" if not has_content else "kolejny nagłówek jest głębszy"
            print(f"✓ Usunięto *** w linii {sep_idx + 1} (nagłówek w linii {header_line_no} — {reason}, separator tam niedozwolony)")
        elif sep_idx is None and want_separator:
            added_count += 1
            print(f"✓ Dodano *** przed nagłówkiem w linii {header_line_no}")
        elif sep_idx is not None and want_separator:
            if not (before_ok and after_ok):
                normalized_count += 1
                print(f"✓ Poprawiono odstępy wokół separatora *** przed nagłówkiem w linii {header_line_no}")
        else:  # sep_idx is None and not want_separator
            if not after_ok:
                spaced_count += 1
                print(f"✓ Dodano brakującą pustą linię przed nagłówkiem w linii {header_line_no}")

        need_blank_before = not (blanks_before == 0 and fence_before)
        need_blank_after = not (real_blanks_after == 0 and fence_after)
        specs.append((seg_start, core_end, want_separator, need_blank_before, need_blank_after))

    first_idx, first_level = headers[0]
    if first_idx > 0:
        process_segment(0, first_idx, first_idx + 1, None, first_level)

    for (idx_a, level_a), (idx_b, level_b) in zip(headers, headers[1:]):
        process_segment(idx_a + 1, idx_b, idx_b + 1, level_a, level_b)

    new_lines = []
    spec_i = 0

    def emit_tail(want_separator, need_blank_before, need_blank_after):
        if want_separator:
            if need_blank_before:
                new_lines.append("\n")
            new_lines.append("***\n")
            if need_blank_after:
                new_lines.append("\n")
        elif need_blank_after:
            new_lines.append("\n")
        # w przeciwnym razie (ogrodzenie kodu tuż przy granicy) nic nie doklejamy

    if first_idx > 0:
        seg_start, core_end, want_separator, need_blank_before, need_blank_after = specs[spec_i]
        spec_i += 1
        new_lines.extend(lines[seg_start:core_end])
        emit_tail(want_separator, need_blank_before, need_blank_after)

    for i, (idx, _level) in enumerate(headers):
        new_lines.append(lines[idx])
        if i < len(headers) - 1:
            seg_start, core_end, want_separator, need_blank_before, need_blank_after = specs[spec_i]
            spec_i += 1
            new_lines.extend(lines[seg_start:core_end])
            emit_tail(want_separator, need_blank_before, need_blank_after)

    new_lines.extend(lines[headers[-1][0] + 1:])

    if added_count:
        print(f"✓ Dodano {added_count} separatorów ***.")
    if removed_count:
        print(f"✓ Usunięto {removed_count} niedozwolonych separatorów ***.")
    if normalized_count:
        print(f"✓ Poprawiono odstępy wokół {normalized_count} istniejących separatorów ***.")
    if spaced_count:
        print(f"✓ Dodano {spaced_count} brakujących pustych linii przed nagłówkami.")
    if not (added_count or removed_count or normalized_count or spaced_count):
        print("✓ Nie znaleziono niczego do poprawy — separatory i odstępy są już zgodne z regułami.")

    return new_lines


def export_headers_to_txt(headers, output_path):
    """Eksportuje nagłówki w formie drzewa do pliku .txt"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("STRUKTURA NAGŁÓWKÓW\n")
        f.write("=" * 50 + "\n\n")
        
        for h in headers:
            indent = "  " * (h["level"] - 1)
            bullet = "-" * h["level"]
            f.write(f"{indent}{bullet} {h['text']}\n")
    
    print(f"Zapisano strukturę nagłówków do: {output_path}")


_TXT_HEADER_LINE_RE = re.compile(r'^(-+)\s+(.*)$')


def parse_headers_txt(txt_lines):
    """Parsuje plik .txt w formacie identycznym jak eksport z opcji 5.
    Zwraca listę (poziom, tekst) w kolejności występowania w pliku."""
    entries = []
    for raw in txt_lines:
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped == "STRUKTURA NAGŁÓWKÓW" or set(stripped) == {"="}:
            continue
        m = _TXT_HEADER_LINE_RE.match(stripped)
        if not m:
            continue
        entries.append((len(m.group(1)), m.group(2)))
    return entries


def validate_level_sequence(entries):
    """Sprawdza skoki poziomów > 1 w liście (poziom, tekst) - analogicznie do
    tego, co analyze() robi dla samego dokumentu. Zwraca listę problemów."""
    issues = []
    prev_level = None
    prev_text = None
    for i, (level, text) in enumerate(entries, start=1):
        if prev_level is not None and level - prev_level > 1:
            issues.append({
                "index": i,
                "text": text,
                "level": level,
                "prev_text": prev_text,
                "prev_level": prev_level,
                "delta": level - prev_level,
            })
        prev_level, prev_text = level, text
    return issues


def extract_header_blocks(lines):
    """Jak extract_headers, ale zwraca też granice bloku: od linii nagłówka
    do linii tuż przed kolejnym nagłówkiem (dowolnego poziomu) albo do EOF."""
    raw_headers = []
    inside_code = False
    for idx, raw in enumerate(lines):
        line = raw.rstrip("\n")
        if CODEBLOCK_RE.match(line):
            inside_code = not inside_code
            continue
        if inside_code:
            continue
        m = HEADER_RE.match(line)
        if m:
            raw_headers.append((idx, len(m.group(1)), m.group(2)))

    blocks = []
    for k, (idx, level, text) in enumerate(raw_headers):
        end = raw_headers[k + 1][0] if k + 1 < len(raw_headers) else len(lines)
        blocks.append({"level": level, "text": text, "start": idx, "end": end})
    return blocks


def _identity_keys(level_text_pairs):
    """Dla każdego nagłówka buduje jednoznaczny klucz dopasowania: pełną ścieżkę
    od korzenia (poziom,tekst każdego przodka + jego samego), a nie samą
    kolejność występowania - dzięki temu powtarzające się nazwy (np. wiele
    „Uzupełnienie (...)” pod różnymi rodzicami) są rozróżniane poprawnie,
    nawet jeśli same sekcje-rodzice też zmieniają kolejność. Gdyby mimo to
    dwie ścieżki wyszły identyczne, dokładamy numer wystąpienia tej ścieżki."""
    stack = []
    path_counts = {}
    keys = []
    for level, text in level_text_pairs:
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, text))
        path = tuple(stack)
        n = path_counts.get(path, 0)
        keys.append((path, n))
        path_counts[path] = n + 1
    return keys


def _lcs_length(seq_a, seq_b):
    """Długość najdłuższego wspólnego podciągu - do policzenia, ile pozycji
    trzeba faktycznie przestawić."""
    n, m = len(seq_a), len(seq_b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if seq_a[i - 1] == seq_b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]


def reorder_headers_interactive(p, lines):
    """Realizuje opcję 'Uporządkuj nagłówki według kolejności z pliku .txt'.
    Zwraca nową listę linii, jeśli użytkownik nadpisał nimi plik (żeby main()
    zaktualizował stan w pamięci), albo oryginalną listę bez zmian."""
    txt_path_str = input("Podaj ścieżkę do pliku .txt z kolejnością nagłówków: ").strip().strip('"')
    txt_path = Path(txt_path_str)
    if not txt_path.exists():
        print("Plik .txt nie istnieje. Anulowano.")
        return lines

    txt_raw_lines = txt_path.read_text(encoding="utf-8").splitlines()
    txt_entries = parse_headers_txt(txt_raw_lines)

    if not txt_entries:
        print("Nie znaleziono żadnych nagłówków w pliku .txt. Anulowano.")
        return lines

    # 1) walidacja hierarchii w pliku .txt
    txt_issues = validate_level_sequence(txt_entries)
    if txt_issues:
        print("\n⚠️ Plik .txt zawiera niepoprawną hierarchię nagłówków (skok > 1):")
        for it in txt_issues:
            print(f"  - Pozycja {it['index']}: \"{it['text']}\" (poziom {it['level']}) "
                  f"po \"{it['prev_text']}\" (poziom {it['prev_level']}), skok {it['delta']}")
        print("Popraw plik .txt i spróbuj ponownie. Anulowano.")
        return lines

    # 2) zgodność zbioru nagłówków (ilość i nazwy, z uwzględnieniem poziomu)
    blocks = extract_header_blocks(lines)
    doc_counts = {}
    for b in blocks:
        key = (b["level"], b["text"])
        doc_counts[key] = doc_counts.get(key, 0) + 1

    txt_counts = {}
    for level, text in txt_entries:
        key = (level, text)
        txt_counts[key] = txt_counts.get(key, 0) + 1

    mismatches = []
    for key in sorted(set(doc_counts) | set(txt_counts)):
        dc, tc = doc_counts.get(key, 0), txt_counts.get(key, 0)
        if dc != tc:
            mismatches.append((key, dc, tc))

    if mismatches:
        print("\n⚠️ Nagłówki w dokumencie i w pliku .txt nie zgadzają się:")
        for (level, text), dc, tc in mismatches:
            print(f"  - poziom {level} \"{text}\": w dokumencie {dc}x, w pliku .txt {tc}x")
        print("Popraw plik .txt (albo dokument) i spróbuj ponownie. Anulowano.")
        return lines

    # diagnostyka: ile nagłówków trzeba faktycznie przestawić
    doc_seq = _identity_keys([(b["level"], b["text"]) for b in blocks])
    txt_seq = _identity_keys(txt_entries)
    moved = len(doc_seq) - _lcs_length(doc_seq, txt_seq)

    print(f"\nZnaleziono {len(blocks)} nagłówków, zgodnych z plikiem .txt.")
    if moved == 0:
        print("Kolejność jest już zgodna z plikiem .txt - nic do przestawienia.")
    else:
        print(f"Trzeba przestawić {moved} nagłówków, żeby dopasować kolejność do pliku .txt.")
    if any(c > 1 for c in doc_counts.values()):
        print("Uwaga: część nazw nagłówków się powtarza - duplikaty są dopasowywane")
        print("według kolejności występowania (pierwszy z pierwszym, drugi z drugim...).")

    input("\nNaciśnij Enter, aby kontynuować (Ctrl+C, żeby przerwać)...")

    # 3) budowa nowej kolejności - blok to nagłówek + treść do kolejnego nagłówka/EOF
    id_to_block = {doc_seq[i]: blocks[i] for i in range(len(blocks))}
    prefix = lines[:blocks[0]["start"]] if blocks else lines[:]
    new_body = []
    for key in txt_seq:
        block = id_to_block[key]
        new_body.extend(lines[block["start"]:block["end"]])
    new_lines = prefix + new_body

    # 4) weryfikacja hierarchii po przestawieniu (powinno zawsze wyjść OK)
    post_issues, _trailing, _codeblock_issue = analyze(new_lines)
    if post_issues:
        print("\n⚠️ UWAGA: po przestawieniu wykryto błędy hierarchii nagłówków (nie powinno się zdarzyć):")
        for it in post_issues:
            print(f"  - Linia {it['line']}: \"{it['line_text']}\"")
    else:
        print("✓ Hierarchia nagłówków po przestawieniu jest poprawna.")

    # 5) opcjonalne odpalenie separatorów/odstępów (jak opcja 4)
    resp = input("\nCzy przy okazji poprawić separatory *** i odstępy wokół nagłówków "
                 "(jak opcja 4)? [t/N]: ").strip().lower()
    if resp == "t":
        new_lines = add_header_separators(new_lines)

    # 6) zapis - tak samo jak przy pozostałych akcjach modyfikujących
    while True:
        print("\nCo zrobić z tymi zmianami?")
        print("  1) Nadpisz oryginalny plik (utworzę kopię .bak)")
        print("  2) Zapisz do nowego pliku (_fixed)")
        print("  3) Anuluj i wróć do menu")

        save_choice = input("Wybór: ").strip()

        if save_choice == "1":
            backup = p.with_suffix(p.suffix + ".bak")
            shutil.copy2(p, backup)
            print(f"Utworzono kopię zapasową: {backup}")
            p.write_text("".join(new_lines), encoding="utf-8")
            print(f"✓ Zapisano zmiany w pliku: {p}")
            return new_lines

        elif save_choice == "2":
            out = p.with_name(p.stem + "_fixed" + p.suffix)
            out.write_text("".join(new_lines), encoding="utf-8")
            print(f"✓ Zapisano do nowego pliku: {out}")
            return lines

        elif save_choice == "3":
            print("Zmiany anulowane.")
            return lines


def prompt_choice():
    print("\nCo chcesz zrobić?")
    print("  1) Napraw poziomy nagłówków i nadpisz plik (zrobię kopię .bak)")
    print("     - Naprawia hierarchię nagłówków (zmniejsza skoki >1 poziomu)")
    print("     - Usuwa niechciane końcowe backslashe '\\' na końcach linii")
    print("     - Wykrywa nieparzystą liczbę bloków kodu ``` (tylko ostrzega)")
    print("  2) Napraw poziomy nagłówków i zapisz do nowego pliku")
    print("     - Jak powyżej, bez nadpisywania oryginału")
    print("  3) Usuń puste linie po ':' przed blokami kodu")
    print("     - Usuwa nadmiarowe puste linie między linią kończącą się na ':'")
    print("       a blokiem kodu ```")
    print("  4) Napraw separatory *** i odstępy wokół nagłówków")
    print("     - Dodaje brakujące separatory, usuwa niedozwolone")
    print("     - Poprawia odstępy, dba o pustą linię przed każdym nagłówkiem")
    print("  5) Wyeksportuj listę nagłówków do pliku .txt")
    print("     - Zapisuje drzewiastą strukturę nagłówków do pliku tekstowego")
    print("  6) Uporządkuj nagłówki według kolejności z pliku .txt")
    print("     - Przestawia bloki nagłówków (z treścią) w kolejność z pliku .txt")
    print("       (ten sam format co eksport z opcji 5)")
    print("  7) Pokaż podgląd zmian (pierwsze 20 linii)")
    print("     - Pokazuje różnice między oryginalnym a naprawionym plikiem")
    print("  8) Pokaż strukturę nagłówków")
    print("     - Wyświetla drzewo nagłówków z poziomami")
    print("  9) Anuluj")

    mapping = {
        "1": "overwrite",
        "2": "newfile",
        "3": "clean_colon_codeblocks",
        "4": "add_header_separators",
        "5": "export_headers",
        "6": "reorder_headers",
        "7": "preview",
        "8": "headers",
        "9": "abort",
    }

    return mapping.get(input("Wybór: ").strip())



def show_preview(old, new, max_lines=20):
    print("\n--- Podgląd zmian ---")
    for i in range(min(max_lines, max(len(old), len(new)))):
        old_line = old[i].rstrip("\n") if i < len(old) else ""
        new_line = new[i].rstrip("\n") if i < len(new) else ""
        if old_line != new_line:
            print(f"{i+1:4d}: - {old_line}")
            print(f"{i+1:4d}: + {new_line}")
    print("--- Koniec podglądu ---\n")


def main():
    path_str = input("Podaj ścieżkę do pliku .md (Markdown): \n(żadne zmiany nie będą jeszcze wprowadzone)").strip().strip('"')
    p = Path(path_str)

    if not p.exists():
        print("Plik nie istnieje.")
        input("Naciśnij klawisz aby zakończyć...")
        return

    original_lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    lines = original_lines[:]  # kopia do modyfikacji

    header_issues, trailing, codeblock_issue = analyze(lines)
    headers = extract_headers(lines)

    print_report(header_issues, trailing, codeblock_issue)

    while True:
        action = prompt_choice()

        if action == "headers":
            print_headers_tree(headers)
            continue

        if action == "export_headers":
            txt_path = p.with_suffix(".headers.txt")
            export_headers_to_txt(headers, txt_path)
            continue

        if action == "reorder_headers":
            lines = reorder_headers_interactive(p, lines)
            headers = extract_headers(lines)
            continue

        if action == "preview":
            fixed = apply_fixes(lines) if action in ["overwrite", "newfile"] else lines
            show_preview(original_lines, fixed)
            continue

        # === Akcje modyfikujące ===
        fixed_lines = None
        action_name = ""

        if action == "clean_colon_codeblocks":
            fixed_lines = clean_colon_codeblocks(lines)
            action_name = "Czyszczenie pustych linii"

        elif action == "add_header_separators":
            fixed_lines = add_header_separators(lines)
            action_name = "Dodawanie separatorów ***"

        elif action in ["overwrite", "newfile"]:
            fixed_lines = apply_fixes(lines)
            action_name = "Naprawa nagłówków"

        if fixed_lines is not None:
            print(f"\n→ {action_name} zakończone.")

            # Zawsze pytamy o zapis przy każdej modyfikacji
            while True:
                print("\nCo zrobić z tymi zmianami?")
                print("  1) Nadpisz oryginalny plik (utworzę kopię .bak)")
                print("  2) Zapisz do nowego pliku (_fixed)")
                print("  3) Anuluj i wróć do menu")

                save_choice = input("Wybór: ").strip()

                if save_choice == "1":
                    backup = p.with_suffix(p.suffix + ".bak")
                    shutil.copy2(p, backup)
                    print(f"Utworzono kopię zapasową: {backup}")

                    p.write_text("".join(fixed_lines), encoding="utf-8")
                    print(f"✓ Zapisano zmiany w pliku: {p}")
                    lines = fixed_lines[:]   # aktualizujemy stan w pamięci
                    headers = extract_headers(lines)
                    break

                elif save_choice == "2":
                    out = p.with_name(p.stem + "_fixed" + p.suffix)
                    out.write_text("".join(fixed_lines), encoding="utf-8")
                    print(f"✓ Zapisano do nowego pliku: {out}")
                    break

                elif save_choice == "3":
                    print("Zmiany anulowane.")
                    break

            if action in ["clean_colon_codeblocks", "add_header_separators"]:
                continue   # wracamy do menu

            break  # po naprawie nagłówków wychodzimy

        if action == "abort":
            print("Anulowano.")
            break

    input("\nNaciśnij klawisz aby zakończyć...")


if __name__ == "__main__":
    main()#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import shutil
from pathlib import Path

HEADER_RE = re.compile(r'^(#{1,6})\s+(.+)$')
HEADER_ANY_RE = re.compile(r'^\s*#{1,6}\s')
CODEBLOCK_RE = re.compile(r'^```')

def analyze(lines):
    """
    Zwraca:
      - header_issues: błędy hierarchii nagłówków (skoki w górę > 1)
      - trailing_backslashes: linie z końcowym '\'
      - codeblock_issue: nieparzysta liczba bloków ```
    """
    header_issues = []
    trailing = []

    inside_code = False
    codeblock_count = 0
    prev_header_level = None
    prev_header_line = None

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        # blok kodu
        if CODEBLOCK_RE.match(line):
            inside_code = not inside_code
            codeblock_count += 1
            continue

        if inside_code:
            continue

        # nagłówki
        m = HEADER_RE.match(line)
        if m:
            level = len(m.group(1))

            if prev_header_level is not None:
                delta = level - prev_header_level
                if delta > 1:
                    header_issues.append({
                        "line": idx,
                        "line_text": line,
                        "prev_line": prev_header_line,
                        "prev_level": prev_header_level,
                        "curr_level": level,
                        "delta": delta
                    })

            prev_header_level = level
            prev_header_line = idx
            continue

        # końcowy '\'
        if line.endswith("\\") and line.strip() != "\\":
            trailing.append({"line": idx, "line_text": line})

    codeblock_issue = (codeblock_count % 2 != 0)
    return header_issues, trailing, codeblock_issue


def extract_headers(lines):
    headers = []
    inside_code = False

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        if CODEBLOCK_RE.match(line):
            inside_code = not inside_code
            continue

        if inside_code:
            continue

        m = HEADER_RE.match(line)
        if m:
            headers.append({
                "line": idx,
                "level": len(m.group(1)),
                "text": m.group(2)
            })

    return headers


def print_headers_tree(headers):
    print("\n--- Struktura nagłówków ---")
    for h in headers:
        indent = "  " * (h["level"] - 1)
        print(f"{indent}- (linia {h['line']}) {h['text']}")
    print("--- Koniec struktury ---\n")


def apply_fixes(lines):
    new_lines = []
    inside_code = False
    prev_header_level = None

    for idx, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")

        # blok kodu
        if CODEBLOCK_RE.match(line):
            inside_code = not inside_code
            new_lines.append(raw)
            continue

        if inside_code:
            new_lines.append(raw)
            continue

        # naprawa nagłówków
        m = HEADER_RE.match(line)
        if m:
            hashes = m.group(1)
            text = m.group(2)
            level = len(hashes)

            if prev_header_level is not None and level > prev_header_level + 1:
                level = prev_header_level + 1
                hashes = "#" * level
                line = f"{hashes} {text}"

            prev_header_level = level

        # naprawa końcowego '\'
        if line.endswith("\\") and line.strip() != "\\":
            line = line[:-1]

        # ZAWSZE zapisujemy poprawioną linię
        new_lines.append(line + "\n")

    return new_lines



def print_report(header_issues, trailing, codeblock_issue):
    if not header_issues and not trailing and not codeblock_issue:
        print("Brak wykrytych problemów.")
        return

    if header_issues:
        print("\nProblemy z hierarchią nagłówków (skoki w górę > 1):")
        for it in header_issues:
            print(f"  - Linia {it['line']}: \"{it['line_text']}\"")
            print(f"    Poprzedni nagłówek: linia {it['prev_line']} poziom {it['prev_level']}, "
                  f"obecny poziom {it['curr_level']} (delta {it['delta']})")

    if trailing:
        print("\nLinie kończące się '\\' do poprawy:")
        for t in trailing:
            print(f"  - Linia {t['line']}: \"{t['line_text']}\"")

    if codeblock_issue:
        print("\n⚠️ UWAGA: Nieparzysta liczba bloków ``` — dokument może być uszkodzony!")


def clean_colon_codeblocks(lines):
    """Usuwa WSZYSTKIE puste linie między linią kończącą się na ':' a blokiem kodu ```"""
    new_lines = []
    removed_count = 0
    i = 0
    n = len(lines)

    while i < n:
        raw_line = lines[i]
        current_line = raw_line.rstrip("\n\r")

        new_lines.append(raw_line)

        # Jeśli linia kończy się na ':' 
        if current_line.endswith(":") and not current_line.lstrip().startswith("```"):
            j = i + 1
            empty_lines_found = 0
            while j < n and lines[j].strip() == "":
                empty_lines_found += 1
                j += 1

            if j < n and CODEBLOCK_RE.match(lines[j].lstrip()):
                if empty_lines_found > 0:
                    print(f"✓ Linia {i+1}: usunięto {empty_lines_found} pustych linii po ':'")
                    removed_count += empty_lines_found
                
                # Przeskakujemy wszystkie puste linie (nie dodajemy żadnej)
                i = j - 1

        i += 1

    if removed_count == 0:
        print("✓ Nie znaleziono pustych linii do usunięcia po ':'.")

    return new_lines
    
    
SEPARATORS = {"***", "---", "___"}


def _header_level(line):
    """Zwraca poziom nagłówka (1-6) dla linii pasującej do HEADER_ANY_RE, albo None."""
    m = HEADER_ANY_RE.match(line)
    if not m:
        return None
    level = 0
    for ch in line.lstrip():
        if ch == "#":
            level += 1
        else:
            break
    return level if 1 <= level <= 6 else None


def add_header_separators(lines):
    """
    Reguły, egzekwowane łącznie:

      1) Przed KAŻDYM nagłówkiem (poza pierwszą linią całego dokumentu) ma być
         co najmniej jedna pusta linia. Linia otwierająca lub zamykająca blok
         kodu ``` liczy się przy tym jak pusta linia (jest niewidoczna po
         wyrenderowaniu) — ale sama nigdy nie jest ruszana ani przesuwana.

      2) Separator '***' wolno mieć TYLKO między nagłówkiem a kolejnym
         nagłówkiem o RÓWNYM LUB PŁYTSZYM poziomie i tylko gdy jest między
         nimi realna treść — nigdy między nagłówkiem a kolejnym GŁĘBSZYM.
         Gdy jest wskazany, dostaje dokładnie jedną pustą linię przed i po
         (to nadpisuje regułę 1 dla samego separatora). Brakujący separator
         jest dodawany, niedozwolony usuwany, źle rozstawiony poprawiany.

      3) "Separator rozwinięty": dwie linie '***' z treścią pomiędzy nimi
         (bez nagłówka w środku), gdzie pierwsza '***' nie ma pustej linii
         zaraz po sobie, a druga nie ma pustej linii zaraz przed sobą. Taki
         blok jest traktowany jako całość — zwykła, nietykalna treść — nigdy
         nie jest dzielony ani zarządzany jak zwykły separator.

    Bloki kodu ``` ``` `` są całkowicie nietykalne.
    """
    n = len(lines)

    in_code = [False] * n
    inside_code = False
    for i in range(n):
        if lines[i].strip().startswith("```"):
            in_code[i] = True
            inside_code = not inside_code
            continue
        in_code[i] = inside_code

    headers = []
    for i in range(n):
        if in_code[i]:
            continue
        level = _header_level(lines[i].rstrip("\n\r"))
        if level is not None:
            headers.append((i, level))

    if not headers:
        return lines[:]

    # --- Wykrywanie "separatorów rozwiniętych" ---
    all_seps = [i for i in range(n) if not in_code[i] and lines[i].strip() in SEPARATORS]
    protected = set()
    si = 0
    while si < len(all_seps) - 1:
        p, q = all_seps[si], all_seps[si + 1]
        no_blank_after_p = p + 1 < n and lines[p + 1].strip() != ""
        no_blank_before_q = q - 1 >= 0 and lines[q - 1].strip() != ""
        header_between = any(
            not in_code[k] and _header_level(lines[k].rstrip("\n\r")) is not None
            for k in range(p + 1, q)
        )
        if no_blank_after_p and no_blank_before_q and not header_between:
            protected.add(p)
            protected.add(q)
            si += 2
        else:
            si += 1

    def strip_tail(seg_start, seg_end):
        """Cofa się od seg_end. Zwraca (core_end, sep_idx_lub_None, blanks_before,
        real_blanks_after, fence_after) - fence_after mówi, czy granicę core
        wyznaczyło ogrodzenie ``` (a nie prawdziwa pusta linia)."""
        j = seg_end
        real_blanks_after = 0
        while j > seg_start and not in_code[j - 1] and lines[j - 1].strip() == "":
            real_blanks_after += 1
            j -= 1

        fence_after = (
            real_blanks_after == 0
            and j > seg_start
            and lines[j - 1].strip().startswith("```")
        )

        if (
            j > seg_start
            and not in_code[j - 1]
            and lines[j - 1].strip() in SEPARATORS
            and (j - 1) not in protected
        ):
            sep_idx = j - 1
            j -= 1
            blanks_before = 0
            while j > seg_start and not in_code[j - 1] and lines[j - 1].strip() == "":
                blanks_before += 1
                j -= 1
            return j, sep_idx, blanks_before, real_blanks_after, fence_after

        return j, None, 0, real_blanks_after, fence_after

    added_count = 0
    removed_count = 0
    normalized_count = 0
    spaced_count = 0
    specs = []

    def process_segment(seg_start, seg_end, header_line_no, level_a, level_b):
        nonlocal added_count, removed_count, normalized_count, spaced_count
        core_end, sep_idx, blanks_before, real_blanks_after, fence_after = strip_tail(seg_start, seg_end)
        has_content = any(lines[k].strip() != "" for k in range(seg_start, core_end))
        # jeśli tuż przed core_end stoi zamykające *** separatora rozwiniętego,
        # ono już wizualnie pełni rolę granicy - nie dokładamy drugiego
        tail_is_protected = core_end > seg_start and (core_end - 1) in protected
        want_separator = (
            has_content
            and (level_a is not None)
            and (level_b <= level_a)
            and not tail_is_protected
        )

        if sep_idx is not None and not want_separator:
            removed_count += 1
            reason = "brak treści" if not has_content else "kolejny nagłówek jest głębszy"
            print(f"✓ Usunięto *** w linii {sep_idx + 1} (nagłówek w linii {header_line_no} — {reason}, separator tam niedozwolony)")
        elif sep_idx is None and want_separator:
            added_count += 1
            print(f"✓ Dodano *** przed nagłówkiem w linii {header_line_no}")
        elif sep_idx is not None and want_separator:
            if blanks_before != 1 or real_blanks_after != 1:
                normalized_count += 1
                print(f"✓ Poprawiono odstępy wokół separatora *** przed nagłówkiem w linii {header_line_no}")
        else:  # sep_idx is None and not want_separator
            if real_blanks_after == 0 and not fence_after:
                spaced_count += 1
                print(f"✓ Dodano brakującą pustą linię przed nagłówkiem w linii {header_line_no}")

        # czy trzeba doklejać pustą linię po core (gdy nie ma separatora)?
        need_blank_line = not (real_blanks_after == 0 and fence_after)
        specs.append((seg_start, core_end, want_separator, need_blank_line))

    first_idx, first_level = headers[0]
    if first_idx > 0:
        process_segment(0, first_idx, first_idx + 1, None, first_level)

    for (idx_a, level_a), (idx_b, level_b) in zip(headers, headers[1:]):
        process_segment(idx_a + 1, idx_b, idx_b + 1, level_a, level_b)

    new_lines = []
    spec_i = 0

    def emit_tail(want_separator, need_blank_line):
        if want_separator:
            new_lines.append("\n"); new_lines.append("***\n"); new_lines.append("\n")
        elif need_blank_line:
            new_lines.append("\n")
        # w przeciwnym razie (ogrodzenie kodu tuż przed nagłówkiem) nic nie doklejamy

    if first_idx > 0:
        seg_start, core_end, want_separator, need_blank_line = specs[spec_i]
        spec_i += 1
        new_lines.extend(lines[seg_start:core_end])
        emit_tail(want_separator, need_blank_line)

    for i, (idx, _level) in enumerate(headers):
        new_lines.append(lines[idx])
        if i < len(headers) - 1:
            seg_start, core_end, want_separator, need_blank_line = specs[spec_i]
            spec_i += 1
            new_lines.extend(lines[seg_start:core_end])
            emit_tail(want_separator, need_blank_line)

    new_lines.extend(lines[headers[-1][0] + 1:])

    if added_count:
        print(f"✓ Dodano {added_count} separatorów ***.")
    if removed_count:
        print(f"✓ Usunięto {removed_count} niedozwolonych separatorów ***.")
    if normalized_count:
        print(f"✓ Poprawiono odstępy wokół {normalized_count} istniejących separatorów ***.")
    if spaced_count:
        print(f"✓ Dodano {spaced_count} brakujących pustych linii przed nagłówkami.")
    if not (added_count or removed_count or normalized_count or spaced_count):
        print("✓ Nie znaleziono niczego do poprawy — separatory i odstępy są już zgodne z regułami.")

    return new_lines


def export_headers_to_txt(headers, output_path):
    """Eksportuje nagłówki w formie drzewa do pliku .txt"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("STRUKTURA NAGŁÓWKÓW\n")
        f.write("=" * 50 + "\n\n")
        
        for h in headers:
            indent = "  " * (h["level"] - 1)
            bullet = "-" * h["level"]
            f.write(f"{indent}{bullet} {h['text']}\n")
    
    print(f"Zapisano strukturę nagłówków do: {output_path}")


def prompt_choice():
    print("\nCo chcesz zrobić?")
    print("  1) Napraw poziomy nagłówków i nadpisz plik (zrobię kopię .bak)")
    print("     - Naprawia hierarchię nagłówków (zmniejsza skoki >1 poziomu)")
    print("     - Usuwa niechciane końcowe backslashe '\\' na końcach linii")
    print("     - Wykrywa nieparzystą liczbę bloków kodu ``` (tylko ostrzega)")
    print("  2) Napraw poziomy nagłówków i zapisz do nowego pliku")
    print("     - Jak powyżej, bez nadpisywania oryginału")
    print("  3) Usuń puste linie po ':' przed blokami kodu")
    print("     - Usuwa nadmiarowe puste linie między linią kończącą się na ':'")
    print("       a blokiem kodu ```")
    print("  4) Zarządzaj separatorami *** i odstępami wokół nagłówków")
    print("     - Dodaje brakujące separatory '***' między nagłówkami tego")
    print("       samego lub płytszego poziomu")
    print("     - Usuwa separatory niedozwolone (np. przed nagłówkiem głębszym)")
    print("     - Poprawia odstępy wokół już istniejących separatorów")
    print("     - Dba o co najmniej jedną pustą linię przed każdym nagłówkiem")
    print("     - Nie rusza bloków kodu ani „separatorów rozwiniętych” (dwa ***")
    print("       z treścią pomiędzy nimi, bez nagłówka w środku)")
    print("  5) Wyeksportuj listę nagłówków do pliku .txt")
    print("     - Zapisuje drzewiastą strukturę nagłówków do pliku tekstowego")
    print("  6) Pokaż podgląd zmian (pierwsze 20 linii)")
    print("     - Pokazuje różnice między oryginalnym a naprawionym plikiem")
    print("  7) Pokaż strukturę nagłówków")
    print("     - Wyświetla drzewo nagłówków z poziomami")
    print("  8) Anuluj")

    mapping = {
        "1": "overwrite",
        "2": "newfile",
        "3": "clean_colon_codeblocks",
        "4": "add_header_separators",
        "5": "export_headers",
        "6": "preview",
        "7": "headers",
        "8": "abort",
    }

    return mapping.get(input("Wybór: ").strip())



def show_preview(old, new, max_lines=20):
    print("\n--- Podgląd zmian ---")
    for i in range(min(max_lines, max(len(old), len(new)))):
        old_line = old[i].rstrip("\n") if i < len(old) else ""
        new_line = new[i].rstrip("\n") if i < len(new) else ""
        if old_line != new_line:
            print(f"{i+1:4d}: - {old_line}")
            print(f"{i+1:4d}: + {new_line}")
    print("--- Koniec podglądu ---\n")


def main():
    path_str = input("Podaj ścieżkę do pliku .md (Markdown): \n(żadne zmiany nie będą jeszcze wprowadzone)").strip().strip('"')
    p = Path(path_str)

    if not p.exists():
        print("Plik nie istnieje.")
        input("Naciśnij klawisz aby zakończyć...")
        return

    original_lines = p.read_text(encoding="utf-8").splitlines(keepends=True)
    lines = original_lines[:]  # kopia do modyfikacji

    header_issues, trailing, codeblock_issue = analyze(lines)
    headers = extract_headers(lines)

    print_report(header_issues, trailing, codeblock_issue)

    while True:
        action = prompt_choice()

        if action == "headers":
            print_headers_tree(headers)
            continue

        if action == "export_headers":
            txt_path = p.with_suffix(".headers.txt")
            export_headers_to_txt(headers, txt_path)
            continue

        if action == "preview":
            fixed = apply_fixes(lines) if action in ["overwrite", "newfile"] else lines
            show_preview(original_lines, fixed)
            continue

        # === Akcje modyfikujące ===
        fixed_lines = None
        action_name = ""

        if action == "clean_colon_codeblocks":
            fixed_lines = clean_colon_codeblocks(lines)
            action_name = "Czyszczenie pustych linii"

        elif action == "add_header_separators":
            fixed_lines = add_header_separators(lines)
            action_name = "Dodawanie separatorów ***"

        elif action in ["overwrite", "newfile"]:
            fixed_lines = apply_fixes(lines)
            action_name = "Naprawa nagłówków"

        if fixed_lines is not None:
            print(f"\n→ {action_name} zakończone.")

            # Zawsze pytamy o zapis przy każdej modyfikacji
            while True:
                print("\nCo zrobić z tymi zmianami?")
                print("  1) Nadpisz oryginalny plik (utworzę kopię .bak)")
                print("  2) Zapisz do nowego pliku (_fixed)")
                print("  3) Anuluj i wróć do menu")

                save_choice = input("Wybór: ").strip()

                if save_choice == "1":
                    backup = p.with_suffix(p.suffix + ".bak")
                    shutil.copy2(p, backup)
                    print(f"Utworzono kopię zapasową: {backup}")

                    p.write_text("".join(fixed_lines), encoding="utf-8")
                    print(f"✓ Zapisano zmiany w pliku: {p}")
                    lines = fixed_lines[:]   # aktualizujemy stan w pamięci
                    break

                elif save_choice == "2":
                    out = p.with_name(p.stem + "_fixed" + p.suffix)
                    out.write_text("".join(fixed_lines), encoding="utf-8")
                    print(f"✓ Zapisano do nowego pliku: {out}")
                    break

                elif save_choice == "3":
                    print("Zmiany anulowane.")
                    break

            if action in ["clean_colon_codeblocks", "add_header_separators"]:
                continue   # wracamy do menu

            break  # po naprawie nagłówków wychodzimy

        if action == "abort":
            print("Anulowano.")
            break

    input("\nNaciśnij klawisz aby zakończyć...")


if __name__ == "__main__":
    main()
