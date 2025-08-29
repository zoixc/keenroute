Простая утилита для создания пользовательских статических маршрутов для роутеров Keenetic.
Достаточно ввести URL адреса сайтов и сгенерировать список, который можно выгрузить в .bat и залить в роутер.
К каждому маршруту автоматически подставляется комментарий с его URL адресом.

Запуск через docker-compose:
```
services:
  keenroute:
    image: ptabi/kroute:latest
    container_name: kroute
    ports:
      - "5000:5000" 
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
```
