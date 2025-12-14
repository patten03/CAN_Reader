# Инструкция по сборке
При сборке применялся Python 3.12.10

Создайте виртуральное окружение и запустите его:
```
python -m venv ./.venv
```
```
./.vevn/Scripts/Activate.ps1
```
Установите библиотеки из requirements.txt:
```
pip install -r requirements.txt
```
Создайте файл ui_form.py через команду:
```
pyside6-uic form.ui -o ui_form.py
```
Готово, можно запускать проект через команду:
```
python mainwindow.py
```
