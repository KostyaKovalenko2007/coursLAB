# Логика работы бота

- пользователь заходит в чат и оставляет сообщение
- бот-программа подключается к БД и по id пользователя ищет, есть ли этот пользователь в базе:
	если пользователя в базе нет, то создает запись о пользователе, запросив перед этим все данные в API VK
	если пользователь уже имеетс я в базе, то бот-программа вытаскивает из базы необходимые данные о пользователе
- далее идет взаимодействие с ботом:
	если какой-либо информации не хватает, бот пробует запросить ее (отсутствует возраст, пол, город)
	по команде выводит результат поиска, либо лайкает и т.д.