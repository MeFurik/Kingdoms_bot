#!/usr/bin/env python3
# tools/patch_aiogram3_fix.py
import re
from pathlib import Path
from shutil import copy2

ROOT = Path("app")
if not ROOT.exists():
    print("Не найден каталог 'app' — запустите скрипт из корня репозитория.")
    raise SystemExit(1)

py_files = list(ROOT.rglob("*.py"))
print(f"Буду обрабатывать {len(py_files)} файлов...\n")

# блок импорта, который вставляем при необходимости
IMPORT_BLOCK = (
    "try:\n"
    "    from aiogram.filters.state import StateFilter\n"
    "except Exception:\n"
    "    try:\n"
    "        from aiogram.fsm.filters import StateFilter\n"
    "    except Exception:\n"
    "        StateFilter = None\n\n"
    "try:\n"
    "    from aiogram.filters import CommandStart, Command\n"
    "except Exception:\n"
    "    try:\n"
    "        from aiogram.dispatcher.filters.builtin import CommandStart, Command\n"
    "    except Exception:\n"
    "        CommandStart = None\n"
    "        Command = None\n\n"
)

def ensure_import_block(text):
    # Если в файле уже есть наш защитный блок — ничего не делаем.
    if "from aiogram.filters.state import StateFilter" in text or "from aiogram.fsm.filters import StateFilter" in text:
        return text
    if "from aiogram.filters import CommandStart" in text or "from aiogram.dispatcher.filters.builtin import CommandStart" in text:
        # если есть CommandStart, но нет StateFilter, вставим только StateFilter (редкий случай)
        if "from aiogram.filters.state import StateFilter" in text or "from aiogram.fsm.filters import StateFilter" in text:
            return text
    # Вставляем после первого блока импортов (последней строки импорта)
    lines = text.splitlines(keepends=True)
    last_import_idx = -1
    for i, line in enumerate(lines[:200]):  # смотрим только в начале файла
        if line.startswith("import ") or line.startswith("from "):
            last_import_idx = i
    insert_at = 0
    if last_import_idx >= 0:
        # вставляем после этого индекса
        insert_at = sum(len(l) for l in lines[:last_import_idx+1])
        text = text[:insert_at] + IMPORT_BLOCK + text[insert_at:]
    else:
        # если импортов нет — вставим в начало
        text = IMPORT_BLOCK + text
    return text

def transform_decorator_args(args_text):
    """
    Преобразует строку аргументов декоратора: перемещает commands=[...] и state="..."
    в начало в виде Command(...) / CommandStart() и StateFilter(...).
    Возвращает (new_args_text, changed_flag)
    """
    orig = args_text
    changed = False
    # ищем commands=[...]
    m_cmd = re.search(r'commands\s*=\s*\[\s*([\'"])([^\'"]+)\1\s*(?:,[^\]]*)?\]', args_text)
    if m_cmd:
        cmdname = m_cmd.group(2)
        if cmdname == "start":
            prefix = "CommandStart()"
        else:
            prefix = f'Command("{cmdname}")'
        # удаляем commands=... (включая возможную запятую справа/слева)
        args_text = re.sub(r'\s*,?\s*commands\s*=\s*\[\s*[\'"][^\'"]+[\'"]\s*(?:,[^\]]*)?\]\s*,?', ',', args_text)
        # теперь clean-up лишних запятых
        args_text = re.sub(r'^\s*,\s*', '', args_text)
        args_text = re.sub(r',\s*,', ',', args_text)
        args_text = args_text.strip()
        if args_text:
            args_text = prefix + ", " + args_text
        else:
            args_text = prefix
        changed = True

    # ищем state="something" (авто-обработка только строковых состояний)
    m_state = re.search(r'state\s*=\s*([\'"])([^\'"]+)\1', args_text)
    if m_state:
        state_name = m_state.group(2)
        state_prefix = f'StateFilter("{state_name}")'
        args_text = re.sub(r'\s*,?\s*state\s*=\s*[\'"][^\'"]+[\'"]\s*,?', ',', args_text)
        args_text = re.sub(r'^\s*,\s*', '', args_text)
        args_text = re.sub(r',\s*,', ',', args_text)
        args_text = args_text.strip()
        if args_text:
            args_text = state_prefix + ", " + args_text
        else:
            args_text = state_prefix
        changed = True

    args_text = args_text.strip()
    return args_text, changed

DECORATOR_PATTERN = re.compile(r'(@router\.(message|callback_query)\s*\()([^\)]*)(\))', re.DOTALL)

for p in py_files:
    text = p.read_text(encoding="utf-8")
    orig_text = text
    modified = False

    # 1) Ensure import block if needed (we decide if file uses router decorators)
    if "@router.message" in text or "@router.callback_query" in text:
        text = ensure_import_block(text)
        if text != orig_text:
            modified = True
            orig_text = text  # update baseline for further changes

    # 2) Transform decorators: move commands= and state= out of kwargs into positional filters
    new_text = text
    any_changes = False
    starts = 0
    for m in DECORATOR_PATTERN.finditer(text):
        s, e = m.span()
        before = m.group(1)
        inner = m.group(3)
        after = m.group(4)
        new_inner, changed = transform_decorator_args(inner)
        if changed:
            any_changes = True
            replacement = before + new_inner + after
            new_text = new_text[:s+starts] + replacement + new_text[e+starts:]
            starts += len(replacement) - (e - s)

    if any_changes:
        text = new_text
        modified = True

    # 3) Add import io if io.BytesIO used and import io missing
    if "io.BytesIO" in text and "import io" not in text:
        # try insert after our IMPORT_BLOCK if present, otherwise at top
        if IMPORT_BLOCK.strip() in text:
            text = text.replace(IMPORT_BLOCK, IMPORT_BLOCK + "import io\n\n")
        else:
            text = "import io\n\n" + text
        modified = True

    # 4) Mark suspicious content_types kwargs for manual review
    if "content_types=" in text:
        text = re.sub(r'content_types\s*=\s*([^\),\n]+)', r'\g<0>  # TODO: replace with ContentTypeFilter or F.content_type', text)
        modified = True

    if modified:
        # backup original
        bak = str(p) + ".bak"
        copy2(p, bak)
        p.write_text(text, encoding="utf-8")
        print(f"Patched: {p} (backup at {bak})")

print("\nГотово. Проверьте файлы (особенно где появились TODO-комментарии).")
print("Запустите 'python -u run.py' и пришлите traceback, если останутся ошибки.")