# Yatube
Cоциальная сеть, платформа для блогов.

Возможности:
* Регистрация пользователя, создание собственного профиля
* Создание, редактирование и удаление постов
* Прикрепление картинок к постам
* Создание и редактирование комментариев к посту
* Подписка на интересующих авторов
* Группы по интересам

**Технологии:** Python 3.7, Django 2.2
**Автор:** [@tan-dem](https://github.com/tan-dem)

__

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/tan-dem/hw05_final.git
```

```
cd hw05_final
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv venv
```

```
source venv/bin/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

