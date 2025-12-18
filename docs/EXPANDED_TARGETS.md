# KikuAI Distributor — Expanded Targets

## Категории публикации

### 1. Developer Platforms (API)

| Platform | API/CLI | Auto | Что нужно |
|----------|---------|------|-----------|
| **GitHub** | `gh` CLI | ✅ | GH_TOKEN |
| **GitLab** | REST API | ✅ | GITLAB_TOKEN |
| **npm** | `npm publish` | ✅ | NPM_TOKEN |
| **PyPI** | `twine` | ✅ | PYPI_TOKEN |
| **Docker Hub** | `docker push` | ✅ | DOCKERHUB_TOKEN |
| **GHCR** | `docker push` | ✅ | GH_TOKEN |
| **Homebrew** | PR to tap | ✅ | GH_TOKEN |
| **crates.io** | `cargo publish` | ✅ | CARGO_TOKEN |
| **Go modules** | git tag | ✅ | GH_TOKEN |

### 2. API Marketplaces

| Platform | API | Auto | Что нужно |
|----------|-----|------|-----------|
| **RapidAPI** | REST API | ⚠️ Partial | RAPIDAPI_KEY, hub_id |
| **API Layer** | No public API | ❌ Prepare | Manual submit |
| **Postman** | REST API | ✅ | POSTMAN_API_KEY |
| **SwaggerHub** | REST API | ✅ | SWAGGERHUB_KEY |

### 3. Product Directories

| Platform | API | Auto | Что нужно |
|----------|-----|------|-----------|
| **Product Hunt** | GraphQL API | ⚠️ Limited | PH_ACCESS_TOKEN |
| **Hacker News** | No API | ❌ Prepare | Manual |
| **Indie Hackers** | No API | ❌ Prepare | Manual |
| **BetaList** | No API | ❌ Prepare | Manual |
| **AlternativeTo** | No API | ❌ Prepare | Manual |

### 4. Social Media

| Platform | API | Auto | Что нужно |
|----------|-----|------|-----------|
| **Twitter/X** | REST API v2 | ✅ | TWITTER_BEARER |
| **LinkedIn** | REST API | ✅ | LINKEDIN_TOKEN |
| **Telegram** | Bot API | ✅ | TG_BOT_TOKEN |
| **Discord** | Webhook | ✅ | DISCORD_WEBHOOK |
| **Slack** | Webhook | ✅ | SLACK_WEBHOOK |
| **Mastodon** | REST API | ✅ | MASTODON_TOKEN |
| **Reddit** | REST API | ⚠️ Careful | REDDIT_TOKEN |
| **Bluesky** | AT Protocol | ✅ | BSKY_PASSWORD |

### 5. Developer Communities

| Platform | API | Auto | Что нужно |
|----------|-----|------|-----------|
| **Dev.to** | REST API | ✅ | DEVTO_API_KEY |
| **Hashnode** | GraphQL | ✅ | HASHNODE_TOKEN |
| **Medium** | REST API | ✅ | MEDIUM_TOKEN |
| **GitHub Discussions** | GraphQL | ✅ | GH_TOKEN |

### 6. Awesome Lists / Directories

| Target | Метод | Auto |
|--------|-------|------|
| **awesome-python** | PR | ✅ |
| **public-apis** | PR | ✅ |
| **awesome-selfhosted** | PR | ✅ |
| **awesome-docker** | PR | ✅ |

---

## Agent Prompt для Smart Distribution

```markdown
# KikuAI Distribution Agent

Ты — агент дистрибуции продуктов KikuAI. Твоя задача — определить оптимальные каналы публикации для каждого релиза.

## Входные данные
- product_type: api | cli | library | saas
- target_audience: developers | devops | data_scientists | general
- pricing: free | freemium | paid
- maturity: alpha | beta | stable
- previous_launches: list of platforms already used

## Правила выбора

### Обязательные (всегда)
1. GitHub Release — всегда при наличии GH_TOKEN
2. Docker Registry — если есть Dockerfile
3. Package Registry (PyPI/npm) — если публичная библиотека

### По типу продукта

**API Product:**
- RapidAPI (если freemium/paid)
- Postman Public Workspace
- SwaggerHub
- public-apis PR

**CLI Tool:**
- Homebrew (если macOS-friendly)
- awesome-cli-apps PR
- Dev.to tutorial

**Library:**
- PyPI/npm/crates.io
- Соответствующий awesome-* list
- Dev.to/Hashnode статья

### По зрелости

**Alpha:**
- Только GitHub + Package Registry
- НЕ постить в Product Hunt / социалки
- Можно в BetaList

**Beta:**
- + Telegram/Discord анонс
- + Dev.to пост
- + Целевые awesome-lists

**Stable (v1.0+):**
- + Product Hunt launch
- + Twitter/LinkedIn анонс
- + Hacker News (Show HN)
- + Все релевантные directories

### Частота

| Канал | Частота |
|-------|---------|
| GitHub/Registry | Каждый релиз |
| Telegram/Discord | Minor+ релизы |
| Twitter/LinkedIn | Minor+ релизы |
| Dev.to | Major релизы или фичи |
| Product Hunt | Только major milestones |
| HN | Раз в 6 месяцев max |
| Awesome-lists | Один раз при стабильности |

## Output Format

```json
{
  "auto_publish": ["gh", "pypi", "ghcr", "telegram"],
  "prepare_only": ["rapidapi", "producthunt"],
  "skip": ["hackernews"],
  "schedule": {
    "twitter": "immediate",
    "devto": "in 2 days",
    "producthunt": "next tuesday 00:01 PST"
  },
  "reasoning": "..."
}
```

## Ограничения

1. НЕ спамить — max 1 пост в неделю на платформу
2. НЕ постить alpha в широкие каналы
3. НЕ использовать Reddit для self-promo без value
4. Product Hunt — только по вторникам, max 1 раз в 6 месяцев
5. HN — честный "Show HN", не каждый релиз
```

---

## Реализация в kiku-dist

### Новые targets

```python
# targets/social.py
class TwitterTarget(Target):
    name = "twitter"
    required_secrets = ["TWITTER_BEARER", "TWITTER_API_KEY", "TWITTER_API_SECRET"]
    
class TelegramTarget(Target):
    name = "telegram"
    required_secrets = ["TG_BOT_TOKEN", "TG_CHANNEL_ID"]

class LinkedInTarget(Target):
    name = "linkedin"
    required_secrets = ["LINKEDIN_TOKEN"]

# targets/devcom.py
class DevToTarget(Target):
    name = "devto"
    required_secrets = ["DEVTO_API_KEY"]

class HashnodeTarget(Target):
    name = "hashnode"
    required_secrets = ["HASHNODE_TOKEN"]
```

### Новые команды

```bash
# Автоматический выбор через agent
kiku-dist distribute --auto

# С параметрами
kiku-dist distribute --maturity stable --audience developers

# Социалки
kiku-dist publish --targets twitter,telegram,linkedin

# Communities
kiku-dist publish --targets devto,hashnode
```

### Config extension

```toml
[social.twitter]
template = "🚀 {name} v{version} released! {description} {url}"

[social.telegram]
channel = "@kikuai_releases"
template = "templates/telegram_release.md.j2"

[social.linkedin]
visibility = "public"

[distribution]
auto_select = true
maturity = "beta"
audience = ["developers", "devops"]
```
