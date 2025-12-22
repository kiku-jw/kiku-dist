# KikuAI Distributor — Project Documentation

## Идея проекта

**KikuAI Distributor** — CLI-инструмент для автоматизации релизов и дистрибуции AI API-продуктов KikuAI.

### Проблема

Релиз API-продукта включает множество ручных шагов:
- Бамп версии в нескольких файлах (pyproject.toml, __init__.py)
- Создание changelog
- Git tag + GitHub Release
- Docker build + push в несколько реестров
- Деплой документации
- Публикация на маркетплейсы (RapidAPI, Product Hunt)
- PR в каталоги (awesome-lists)

При этом:
- Разные CI (GitHub Actions, GitLab, Drone, Jenkins)
- Нужен dry-run для проверки
- Часть платформ не имеет безопасного API для автопубликации

### Решение

Единый CLI `kiku-dist`, который:
1. **CLI-first** — все операции из терминала
2. **CI-agnostic** — логика в CLI, CI только вызывает команды
3. **Targets framework** — модульные targets для разных платформ
4. **Dry-run** — preview любого действия
5. **Prepare-only** — генерация launch-kit для платформ без API

---

## Текущий статус (v0.1.0)

### ✅ Реализовано

| Компонент | Статус | Описание |
|-----------|--------|----------|
| **CLI Core** | ✅ Done | Typer-based CLI с 8 командами |
| **Config** | ✅ Done | TOML-конфиг с Pydantic валидацией |
| **Doctor** | ✅ Done | Проверка tools, secrets, API access |
| **Targets** | ✅ Done | 4 targets: gh, container, docs, pr-dirs |
| **CI Templates** | ✅ Done | GHA, GitLab, Drone, Jenkins |
| **Release-it** | ✅ Done | Python version hooks |
| **OpenAPI** | ✅ Done | Python-валидация (без Node) |
| **CI Runner** | ✅ Done | API-триггеры для 4 backends |
| **Tests** | ✅ Done | 17 tests passing |

### Команды CLI

```bash
kiku-dist init                    # Создать конфиг
kiku-dist doctor                  # Проверить prerequisites
kiku-dist plan --targets ...      # Preview плана
kiku-dist release patch|minor|major  # Бамп версии
kiku-dist publish --targets ...   # Публикация
kiku-dist status                  # Текущая версия
kiku-dist ci run --backend gha    # Триггер CI
kiku-dist prepare rapidapi        # Launch kit для RapidAPI
kiku-dist prepare producthunt     # Launch kit для Product Hunt
```

### Targets

| Target | Тип | Описание |
|--------|-----|----------|
| `gh` | Auto | GitHub Release |
| `container` | Auto | Docker → GHCR + Docker Hub |
| `docs` | Auto | MkDocs + ReDoc → GitHub Pages |
| `pr-dirs` | Auto | PR в awesome-lists |
| `rapidapi` | Prepare | Launch kit + checklist |
| `producthunt` | Prepare | Launch kit + checklist |

---

## Что планируется дальше

### Phase 2: Production Testing

| Задача | Приоритет | Описание |
|--------|-----------|----------|
| Интеграция с masker-private | 🔴 High | Первый реальный release cycle |
| End-to-end тесты | 🔴 High | CI pipeline тестирование |
| Документация на kikuai.dev | 🟡 Medium | Публичная документация |

### Phase 3: Enhanced Targets

| Target | Приоритет | Описание |
|--------|-----------|----------|
| PyPI publish | 🔴 High | Автопубликация Python-пакетов |
| npm publish | 🟡 Medium | Для JS/TS SDK |
| Homebrew tap | 🟢 Low | macOS установка |
| Changelog automation | 🟡 Medium | Генерация из Conventional Commits |

### Phase 4: Platform Integrations

| Интеграция | Приоритет | Описание |
|------------|-----------|----------|
| Telegram Bot уведомления | 🟡 Medium | Release notifications в @kikuai_bot |
| Discord/Slack webhooks | 🟢 Low | Team notifications |
| Analytics dashboard | 🟢 Low | Release metrics |

### Phase 5: SDK & Extensions

| Фича | Приоритет | Описание |
|------|-----------|----------|
| Plugin system | 🟡 Medium | Custom targets |
| SDK generation | 🟢 Low | OpenAPI → Python/TS SDKs |
| Monorepo support | 🟢 Low | Независимые версии пакетов |

---

## Архитектура

```
┌────────────────────────────────────────────────────┐
│                  kiku-dist CLI                      │
├────────────────────────────────────────────────────┤
│ init │ doctor │ plan │ release │ publish │ status  │
└───────────────────────┬────────────────────────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    ▼                   ▼                   ▼
┌─────────┐       ┌──────────┐       ┌──────────┐
│ Targets │       │ release  │       │    CI    │
│Framework│       │   -it    │       │  Runner  │
└────┬────┘       └──────────┘       └────┬─────┘
     │                                     │
     ├── gh-release                        ├── GitHub Actions
     ├── container                         ├── GitLab CI
     ├── docs                              ├── Drone/Woodpecker
     ├── pr-dirs                           └── Jenkins
     ├── rapidapi (prepare)
     └── producthunt (prepare)
```

---

## Технологии

| Компонент | Технология |
|-----------|------------|
| CLI | Python 3.11 + Typer |
| Config | TOML + Pydantic |
| Release | release-it (npm) |
| OpenAPI | PyYAML (Python-only) |
| HTTP | httpx |
| Tests | pytest |

---

## Принципы

1. **CLI-first** — никаких "перейди в UI и покликай"
2. **CI-agnostic** — ядро работает везде, CI только обертка
3. **Dry-run** — preview любого действия перед выполнением
4. **Compliance** — никакой серой автоматики (обход капчи, скрейпинг)
5. **Prepare-only** — для платформ без API генерируем чеклист

---

## Ссылки

- Конфиг пример: `examples/kiku-dist.toml.example`
- CI templates: `ci_templates/`
