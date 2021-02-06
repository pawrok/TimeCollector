import sqlite3

class SqliteDB:
    " Singleton class "
    __instance__ = None
    c = None # cursor
    conn = None # connection

    def __init__(self):
        # Constructor.
        if SqliteDB.__instance__ is None:
            SqliteDB.__instance__ = self
            SqliteDB.c, SqliteDB.conn = SqliteDB.start_connection()
            SqliteDB.create_table()
        else:
            raise Exception("You cannot create another SqliteDB class")

    @staticmethod
    def get_instance():
        # Static method to fetch the current instance.
        if not SqliteDB.__instance__:
            SqliteDB()
        return SqliteDB.__instance__

    def start_connection():
        conn = sqlite3.connect('example.db')
        conn.row_factory = sqlite3.Row
        return conn.cursor(), conn

    def close_connection():
        SqliteDB.conn.close()

    def create_table(table_name = "booktable"):
        SqliteDB.c.execute('''CREATE TABLE if not exists %s
        (
            ID INTEGER,
            title TEXT,
            author TEXT,
            category TEXT,
            rating INTEGER,
            isRent INTEGER,
            rentedPerson TEXT,
            dateCompleted TEXT,
            pageCount INTEGER
        )''' % table_name)

    def add_book_toDB(
            title, author, category = '', rating = 0, \
            isRent = 0, rentedPerson = '', dateCompleted = '', \
            pageCount = 0):
        # set ID to max(ID) + 1; fetchone() sometimes haven't worked
        SqliteDB.c.execute("SELECT MAX(ID) FROM booktable")
        xxx = [dict(row) for row in SqliteDB.c.fetchall()]
        try:
            max_id = xxx[0]['MAX(ID)'] + 1
        except:
            max_id = 1
        SqliteDB.c.execute("INSERT INTO booktable VALUES ('%d', '%s', '%s', '%s', '%d', '%d', '%s', '%s', '%d')" % \
            (max_id, title, author, category, rating, isRent, rentedPerson, dateCompleted, pageCount))
        SqliteDB.conn.commit()

    def get_books_fromDB():
        SqliteDB.c.execute('SELECT * FROM booktable')
        return [dict(row) for row in SqliteDB.c.fetchall()]

    def get_single_book_fromDB(ID):
        SqliteDB.c.execute('SELECT * FROM booktable WHERE ID = %d' % ID)
        selected_book = SqliteDB.c.fetchone()
        if selected_book != None:
            return dict(selected_book)
        else:
            return 0

    def del_book_fromDB(ID):
        SqliteDB.c.execute('DELETE FROM booktable where ID = %d' % ID)
        SqliteDB.conn.commit()

    def edit_book_inDB(ID, title, author, category = '', rating = 0, \
            isRent = 0, rentedPerson = '', dateCompleted = '', \
            pageCount = 0):
        sql = """
            UPDATE booktable SET 
                title = ?,
                author = ?,
                category = ?,
                rating = ?,
                isRent = ?,
                rentedPerson = ?,
                dateCompleted = ?,
                pageCount = ?
            WHERE 
                ID = ?
            """
        SqliteDB.c.execute(sql, (title, author, category, rating, isRent, 
                                rentedPerson, dateCompleted, pageCount, ID))
        SqliteDB.conn.commit()

    def sort_books(books, param, rev):
        return [tpl for tpl in sorted(books, key=lambda item: item[param], reverse=rev)]

    def filter_books(books, param, value):
        return [tpl for tpl in books if tpl[param] == value]

    #  ------------- DEVELOPER FUNCTIONS ------------------
    def delete_table():
        SqliteDB.c.execute("DROP TABLE booktable")
        SqliteDB.conn.commit()
        SqliteDB.create_table()



debug_mode = 0
if debug_mode:
    SqliteDB()
    # SqliteDB.create_table()
    # SqliteDB.add_book_toDB(1, 'title1', 'author1')
    # SqliteDB.del_book_fromDB(1)
    # SqliteDB.c.execute("SELECT * FROM booktable")
    # print(SqliteDB.c.fetchall())
    # SqliteDB.c.execute("SELECT MAX(ID) FROM booktable")
    # xxx = [dict(row) for row in SqliteDB.c.fetchall()]
    # print(xxx[0]['MAX(ID)'])
    # print(SqliteDB.get_single_book_fromDB(555))
    print(SqliteDB.get_books_fromDB())
 