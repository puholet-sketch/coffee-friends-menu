# Coffee Friends — цифровое меню

Автопрокрутка слайдов напитков и еды для экрана кофейни (MP4 / fullscreen).

## Онлайн

Откройте: **[board.html на GitHub Pages](https://puholet-sketch.github.io/coffee-friends-menu/board.html)**

## Локально

```powershell
.\scripts\serve-menu.ps1
```

Или из корня репозитория: `python -m http.server 8080` → http://localhost:8080/board.html

## Содержимое

- `board.html` — карусель
- `data/drinks.json`, `data/food.json` — карточки меню
- `assets/css/menu.css`, `assets/images/` — стили и фото
- `docs/` — настройка дисплея и workflow

## Не публикуется

Секреты, Telegram-бот, `.env`, импорт из приватных источников — вне этого репозитория.
