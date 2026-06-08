"""
즐겨찾기 / 레시피 히스토리 DB
테이블은 최초 호출 시 자동 생성됨.
"""

import os
import psycopg2


class UserDB:
    def __init__(self):
        self._conn = None

    @property
    def conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=os.environ.get("DB_HOST"),
                port=int(os.environ.get("DB_PORT", 5432)),
                dbname=os.environ.get("DB_NAME"),
                user=os.environ.get("DB_USER"),
                password=os.environ.get("DB_PASSWORD"),
            )
        return self._conn

    def create_tables(self):
        sql = """
            CREATE TABLE IF NOT EXISTS recipe_history (
                id           SERIAL PRIMARY KEY,
                session_id   TEXT        NOT NULL,
                user_message TEXT        NOT NULL,
                recipe_reply TEXT        NOT NULL,
                intent       TEXT        NOT NULL,
                created_at   TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE TABLE IF NOT EXISTS favorites (
                id           SERIAL PRIMARY KEY,
                session_id   TEXT        NOT NULL,
                user_message TEXT        NOT NULL,
                recipe_reply TEXT        NOT NULL,
                intent       TEXT        NOT NULL,
                created_at   TIMESTAMPTZ DEFAULT NOW()
            );
        """
        with self.conn.cursor() as cur:
            cur.execute(sql)
            self.conn.commit()

    def _to_dict(self, cur, row) -> dict:
        return dict(zip([d[0] for d in cur.description], row))

    # ── 히스토리 ───────────────────────────────────────────────────────────────

    def save_history(self, session_id: str, user_message: str, recipe_reply: str, intent: str) -> dict:
        sql = """
            INSERT INTO recipe_history (session_id, user_message, recipe_reply, intent)
            VALUES (%s, %s, %s, %s)
            RETURNING id, session_id, user_message, recipe_reply, intent, created_at
        """
        print(f"🗄️ 히스토리 INSERT - session: {session_id[:8]}, intent: {intent}")
        with self.conn.cursor() as cur:
            cur.execute(sql, (session_id, user_message, recipe_reply, intent))
            self.conn.commit()
            row = self._to_dict(cur, cur.fetchone())
            print(f"🗄️ 히스토리 INSERT 완료 - id: {row['id']}")
            return row

    def get_history(self, session_id: str, limit: int = 30) -> list[dict]:
        sql = """
            SELECT id, session_id, user_message, recipe_reply, intent, created_at
            FROM recipe_history
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """
        print(f"🗄️ 히스토리 SELECT - session: {session_id[:8]}, limit: {limit}")
        with self.conn.cursor() as cur:
            cur.execute(sql, (session_id, limit))
            rows = [self._to_dict(cur, row) for row in cur.fetchall()]
            print(f"🗄️ 히스토리 SELECT 완료 - {len(rows)}건")
            return rows

    # ── 즐겨찾기 ───────────────────────────────────────────────────────────────

    def save_favorite(self, session_id: str, user_message: str, recipe_reply: str, intent: str) -> dict:
        # 중복 체크
        check_sql = """
            SELECT id, session_id, user_message, recipe_reply, intent, created_at
            FROM favorites
            WHERE session_id = %s AND user_message = %s AND recipe_reply = %s
        """
        with self.conn.cursor() as cur:
            cur.execute(check_sql, (session_id, user_message, recipe_reply))
            row = cur.fetchone()
            if row:
                print(f"🗄️ 즐겨찾기 중복 - 기존 레코드 반환 id: {row[0]}")
                return self._to_dict(cur, row)

        # 중복 없으면 INSERT
        insert_sql = """
            INSERT INTO favorites (session_id, user_message, recipe_reply, intent)
            VALUES (%s, %s, %s, %s)
            RETURNING id, session_id, user_message, recipe_reply, intent, created_at
        """
        print(f"🗄️ 즐겨찾기 INSERT - session: {session_id[:8]}, intent: {intent}")
        with self.conn.cursor() as cur:
            cur.execute(insert_sql, (session_id, user_message, recipe_reply, intent))
            self.conn.commit()
            row = self._to_dict(cur, cur.fetchone())
            print(f"🗄️ 즐겨찾기 INSERT 완료 - id: {row['id']}")
            return row

    def get_favorites(self, session_id: str) -> list[dict]:
        sql = """
            SELECT id, session_id, user_message, recipe_reply, intent, created_at
            FROM favorites
            WHERE session_id = %s
            ORDER BY created_at DESC
        """
        print(f"🗄️ 즐겨찾기 SELECT - session: {session_id[:8]}")
        with self.conn.cursor() as cur:
            cur.execute(sql, (session_id,))
            rows = [self._to_dict(cur, row) for row in cur.fetchall()]
            print(f"🗄️ 즐겨찾기 SELECT 완료 - {len(rows)}건")
            return rows

    def delete_favorite(self, favorite_id: int) -> bool:
        print(f"🗄️ 즐겨찾기 DELETE - id: {favorite_id}")
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM favorites WHERE id = %s RETURNING id", (favorite_id,))
            self.conn.commit()
            result = cur.fetchone() is not None
            print(f"🗄️ 즐겨찾기 DELETE 완료 - 삭제됨: {result}")
            return result


_instance: UserDB | None = None


def get_user_db() -> UserDB:
    global _instance
    if _instance is None:
        _instance = UserDB()
        _instance.create_tables()
    return _instance
