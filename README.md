# Сборщик игр с торрент-трекеров
По Крону собирает информацию о раздачах на торрент трекерах, загружает скриншоты, ищет и качает трейлеры с YouTube, оценки с Metacritic и сохраняет всё на сервере.

Внутри: beautifulsoup4, mysql, requests, origamibot, telebot, yt_dlp, Ubuntu + MySQL.

Зачем: www.zolotorevich.com/works/pirate-parrot/crawler/

## app.py
Создаёт объекты для разных типов торрентов. Сейчас только для игр.

## classTorrents.py
Находит новые раздачи на трекерах и загружает информацию о них

## classWebImage.py
Скачивает картинки с популярных хостингов

## cleanup.py
Удаляет старые файлы с сервера. Запускается по Крону раз неделю.

## config.py
Настройки программы и API ключи

## logger.py
Записывает события в log.txt для дебага

## reportMaster.py
Телеграм бот для отправки человеку отчётов и ошибок в работе программы

## support.py
Мелкие функции, вроде поиска значений в тексте, удаления параметров из URL и т.п.

## telegramLinksWatcher.py
Телеграм бот, который следит за каналом и сохраняет ссылки на новые сообщения в базу данных. Позже из этих ссылок другая программа составляет список игр за неделю.
