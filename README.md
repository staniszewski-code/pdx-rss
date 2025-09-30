# ytm-rss-builder

Generator RSS (Apple Podcasts/YouTube Music compatible) na podstawie feedu Acast.

## Co robi?
- Pobiera Twój feed Acast
- Kopiuje metadane kanału i odcinków
- Czyści linki audio z parametrów typu `?utm=...`, `&adParam=...`, `?audio_id=...` itp.
- Buduje nowy RSS zgodny ze strukturą Apple Podcasts (akceptowaną przez YouTube Music)
- Publikuje gotowy plik `podcast.xml` na GitHub Pages

## Szybki start
1. **Utwórz publiczne repo na GitHubie** (np. `ytm-rss`).
2. Dodaj pliki z tego projektu do repo.
3. Zmień `site_base_path` w `config.yaml`:
   - dla **User/Org Pages** (repo `twojanazwa/twojanazwa.github.io`): `/`
   - dla **Project Pages** (repo `twojanazwa/ytm-rss`): `/ytm-rss/`
4. Włącz **GitHub Pages**:
   - Settings → Pages → Build and deployment: **Deploy from a branch**
   - Branch: **gh-pages** / root
5. Pierwsze uruchomienie:
   - Wejdź do zakładki **Actions** i zezwól na workflow (Enable)
   - Kliknij **Run workflow** przy „Publish cleaned RSS”
6. Docelowy URL feedu:
   - `https://<twoja-nazwa>.github.io/<repo>/podcast.xml` (Project Pages)
   - albo `https://<twoja-nazwa>.github.io/podcast.xml` (User/Org Pages)

## Uwaga dot. YouTube Music
YouTube Music akceptuje standardowy RSS w stylu Apple Podcasts. Najważniejsze elementy:
- `<channel>` z podstawowymi metadanymi + przestrzenie nazw iTunes/Atom
- Każdy `<item>` z `<enclosure url=... type="audio/mpeg" length=...>` (length jest opcjonalne)
- Stabilny `<guid>` na odcinek
- `pubDate` w formacie RFC‑2822

Skrypt zachowuje oryginalne GUID-y i metadane; czyści parametry zapytań w URL-u enclosures, aby uniknąć problemów z weryfikacją po stronie YT.
