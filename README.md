### GRIA - Genetic Risk Interpreter and Analysator

[![CI](https://github.com/andreykochegura/gria/actions/workflows/CI.yml/badge.svg)](https://github.com/andreykochegura/gria/actions/workflows/CI.yml)
[![Coverage](https://codecov.io/gh/andreykochegura/gria/branch/master/graph/badge.svg)](https://codecov.io/gh/andreykochegura/gria)


Тестовое на вакансию биоинформатика-разработчика.

### Запуск
``` bash
pip install uv
git clone https://github.com/andreykochegura/gria.git
cd gria
uv sync
uv run gria example.xlsx
```

### Допущения, проблемы, обработка

Мягкая валидация - по возможности не падаем, но показываем только то, что смогли посчитать.
Реальные вклады генотипов не оценивал, как и соответствие генов rsID, номерам хромосом и аллелям, потому что задача модельная.

Что обнаружил:

1. Вкладка "Варианты": палиндромные аллели убрал из расчета, потому что ориентация цепей не указана.
2. Вкладка "Вклады": дубль -> ошибка в консоль, использовал первый.
3. Вкладка "Пороги": "риск в пределах нормы нарушения" - не по русски, но оставил, как есть.
4. Вкладка "Образцы": 
    * Образец S02 генотип GPX1 rs1050450 - результат мог быть получен по обратной цепи -> warning в консоль и заменил A/G на T/C
    * Образец S02 генотип G6PD rs1050828 - X-сцепленный диплоидный генотип у мужчины -> error в консоль и заменил генотип на None
    * ПРОВЕРИТЬ заменил на None и error в консоль

