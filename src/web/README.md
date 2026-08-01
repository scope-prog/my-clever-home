# backend — веб-сервер My Clever Home

Актуальная (третья) версия управления светом: [Litestar](https://litestar.dev/) +
[python-yeelight](https://github.com/stavros/python-yeelight), REST API и веб-панель.

Установка зависимостей:

```bash
uv sync
```

Запуск (обязательно из каталога `app` — шаблоны ищутся относительно текущей директории):

```bash
cd app && uv run python main.py
```

Сервер поднимется на <http://127.0.0.1:8000>.

📖 Полное описание проекта, схема работы, разбор библиотек и история версий —
в [корневом README](../../README.md).
