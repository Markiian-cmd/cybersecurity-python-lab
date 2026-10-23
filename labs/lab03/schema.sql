-- Увімкнення перевірки зовнішніх ключів для поточного з'єднання.
PRAGMA foreign_keys = ON;

-- Об'єднання створення таблиць в одну транзакцію.
BEGIN TRANSACTION;

-- Створення категорій із додатними id та унікальними назвами.
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    name TEXT NOT NULL UNIQUE
        CHECK (length(trim(name)) BETWEEN 2 AND 40)
);

-- Створення таблиці вимірювань тривалості для варіантів 7–9.
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY CHECK (id > 0),
    -- Унікальний код обмежено довжиною після обрізання пробілів.
    code TEXT NOT NULL UNIQUE
        CHECK (length(trim(code)) BETWEEN 3 AND 40),
    title TEXT NOT NULL
        CHECK (length(trim(title)) BETWEEN 3 AND 120),
    category_id INTEGER NOT NULL
        CHECK (typeof(category_id) = 'integer' AND category_id > 0),
    -- Дозволена невід'ємна скінченна тривалість без прикладної верхньої межі.
    value REAL NOT NULL
        CHECK (typeof(value) IN ('integer', 'real')
               AND value >= 0
               AND value <= 1.7976931348623157e308),
    -- Дозволені лише три визначені стани опрацювання запису.
    status TEXT NOT NULL
        CHECK (status IN ('new', 'in_progress', 'done')),
    -- Заборона видалення категорії, доки вона містить вимірювання.
    FOREIGN KEY (category_id) REFERENCES categories(id)
        ON DELETE RESTRICT
);

-- Підтвердження створення таблиць і встановлених обмежень.
COMMIT;
