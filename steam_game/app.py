import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'mirim4',
    'database': 'game_project'
}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

STATUS_OPTIONS = ["playing", "clear", "not_started", "dropped"]
DEFAULT_GENRES = ["Action", "RPG", "Indie", "Strategy", "Simulation", "Adventure"]


class GameFormModal(ctk.CTkToplevel):
    """게임 등록 및 수정을 모두 처리하는 통합 모달 창 (상태 연동형 플레이타임 제어 포함)"""
    def __init__(self, parent, edit_data=None):
        super().__init__(parent)
        self.parent = parent
        self.edit_data = edit_data

        is_edit = self.edit_data is not None
        self.title("Edit Game Record" if is_edit else "Add Game Record")
        self.geometry("400x510")
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

        # DB에서 장르 목록(장르명 -> genre_id 매핑) 불러오기
        self.genre_map = self._load_genres()
        self.genre_names = list(self.genre_map.keys())

        self._init_ui(is_edit)

    def _load_genres(self):
        """genre 테이블에서 장르 목록 조회 (비어있을 경우 기본 장르 자동 등록)"""
        genre_map = {}
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            # [SQL - SELECT] genre 테이블에서 모든 장르 ID와 장르명 조회
            cursor.execute("SELECT genre_id, genre_name FROM genre ORDER BY genre_id ASC;")
            rows = cursor.fetchall()

            # 테이블이 비어있는 경우 기본 장르 데이터 초기 삽입
            if not rows:
                for g_name in DEFAULT_GENRES:
                    # [SQL - INSERT] 기본 장르 목록을 genre 테이블에 등록
                    cursor.execute("INSERT INTO genre (genre_name) VALUES (%s);", (g_name,))
                conn.commit()

                # [SQL - SELECT] 방금 삽입한 장르 목록 재조회
                cursor.execute("SELECT genre_id, genre_name FROM genre ORDER BY genre_id ASC;")
                rows = cursor.fetchall()

            for r in rows:
                genre_map[r['genre_name']] = r['genre_id']

            cursor.close()
            conn.close()
        except Error as e:
            print(f"[Error] 장르 목록 조회 오류: {e}")
            genre_map = {"Action": 1}

        return genre_map

    def _on_status_change(self, selected_status):
        """진행 상태(Status) 변경에 따라 플레이타임 입력칸 활성/비활성 제어"""
        if selected_status == "not_started":
            # not_started 선택 시 값을 0으로 초기화하고 수정 불가 상태로 잠금
            self.entry_hours.configure(state="normal")
            self.entry_minutes.configure(state="normal")
            self.entry_hours.delete(0, "end")
            self.entry_minutes.delete(0, "end")
            self.entry_hours.insert(0, "0")
            self.entry_minutes.insert(0, "0")
            self.entry_hours.configure(state="disabled", fg_color="#1c1c1c", text_color="gray50")
            self.entry_minutes.configure(state="disabled", fg_color="#1c1c1c", text_color="gray50")
        else:
            # 그 외 상태(playing, clear, dropped)에서는 입력 가능하도록 잠금 해제
            self.entry_hours.configure(state="normal", fg_color="#343638", text_color="white")
            self.entry_minutes.configure(state="normal", fg_color="#343638", text_color="white")

    def _init_ui(self, is_edit):
        header_text = "EDIT GAME RECORD" if is_edit else "NEW GAME RECORD"
        ctk.CTkLabel(self, text=header_text, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 15))

        # 1. 게임 제목
        ctk.CTkLabel(self, text="Game Title", font=ctk.CTkFont(size=11), text_color="gray70").pack(anchor="w", padx=30)
        self.entry_title = ctk.CTkEntry(self, placeholder_text="e.g. Elden Ring", width=340)
        self.entry_title.pack(padx=30, pady=(2, 10))

        # 2. 장르 선택 (Genre 드롭다운)
        ctk.CTkLabel(self, text="Genre", font=ctk.CTkFont(size=11), text_color="gray70").pack(anchor="w", padx=30)
        self.combo_genre = ctk.CTkOptionMenu(
            self,
            values=self.genre_names,
            width=340,
            fg_color="#2b2b2b",
            button_color="#1f538d",
            button_hover_color="#14375e"
        )
        self.combo_genre.pack(padx=30, pady=(2, 10))

        # 3. 정가
        ctk.CTkLabel(self, text="Original Price (KRW)", font=ctk.CTkFont(size=11), text_color="gray70").pack(anchor="w", padx=30)
        self.entry_price = ctk.CTkEntry(self, placeholder_text="e.g. 64800", width=340)
        self.entry_price.pack(padx=30, pady=(2, 10))

        # 4. 진행 상태 (플레이타임보다 먼저 선택하도록 배치)
        ctk.CTkLabel(self, text="Status", font=ctk.CTkFont(size=11), text_color="gray70").pack(anchor="w", padx=30)
        self.combo_status = ctk.CTkOptionMenu(
            self,
            values=STATUS_OPTIONS,
            width=340,
            fg_color="#2b2b2b",
            button_color="#1f538d",
            button_hover_color="#14375e",
            command=self._on_status_change
        )
        self.combo_status.pack(padx=30, pady=(2, 10))

        # 5. 플레이 타임 (시간 + 분 분리 입력)
        ctk.CTkLabel(self, text="Playtime (Hours / Minutes)", font=ctk.CTkFont(size=11), text_color="gray70").pack(anchor="w", padx=30)
        time_frame = ctk.CTkFrame(self, fg_color="transparent")
        time_frame.pack(fill="x", padx=30, pady=(2, 20))

        self.entry_hours = ctk.CTkEntry(time_frame, placeholder_text="Hours (e.g. 42)", width=165)
        self.entry_hours.pack(side="left", padx=(0, 10))

        self.entry_minutes = ctk.CTkEntry(time_frame, placeholder_text="Minutes (0~59)", width=165)
        self.entry_minutes.pack(side="left")

        # 수정 모드일 경우 기존 데이터 자동 채우기
        if is_edit:
            self.entry_title.insert(0, self.edit_data['game_title'])
            self.entry_price.insert(0, str(int(self.edit_data['original_price'])))

            existing_genres = self.edit_data.get('genre_names')
            first_genre = existing_genres.split(", ")[0] if existing_genres else None
            if first_genre in self.genre_names:
                self.combo_genre.set(first_genre)
            elif self.genre_names:
                self.combo_genre.set(self.genre_names[0])

            current_status = (self.edit_data['status'] or "playing").lower()
            valid_status = current_status if current_status in STATUS_OPTIONS else "playing"
            self.combo_status.set(valid_status)

            total_mins = self.edit_data['total_play_minutes']
            self.entry_hours.insert(0, str(total_mins // 60))
            self.entry_minutes.insert(0, str(total_mins % 60))
            self._on_status_change(valid_status)
        else:
            if self.genre_names:
                self.combo_genre.set(self.genre_names[0])
            self.combo_status.set("playing")
            self._on_status_change("playing")

        btn_save = ctk.CTkButton(
            self,
            text="Update Record" if is_edit else "Save Record",
            command=self.save_record,
            width=340,
            fg_color="#1f538d",
            hover_color="#14375e"
        )
        btn_save.pack(padx=30, pady=5)

        self.lbl_modal_status = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11), text_color="gray60")
        self.lbl_modal_status.pack(pady=(5, 0))

    def save_record(self):
        title = self.entry_title.get().strip()
        selected_genre = self.combo_genre.get()
        genre_id = self.genre_map.get(selected_genre)
        price_str = self.entry_price.get().strip()
        status = self.combo_status.get().lower()

        if not title or not price_str:
            self.lbl_modal_status.configure(text="Title and Price are required.", text_color="#FF9800")
            return

        try:
            price = float(price_str)

            # not_started 상태라면 플레이타임을 무조건 0으로 강제 고정
            if status == "not_started":
                total_minutes = 0
            else:
                hours_str = self.entry_hours.get().strip() or "0"
                mins_str = self.entry_minutes.get().strip() or "0"
                hours = int(hours_str)
                mins = int(mins_str)

                if hours < 0 or mins < 0 or mins >= 60:
                    self.lbl_modal_status.configure(text="Minutes must be between 0 and 59.", text_color="#FF9800")
                    return

                total_minutes = (hours * 60) + mins

                # 시작하지 않은(0분) 게임을 playing/clear/dropped로 저장하려는 경우 안내
                if total_minutes == 0:
                    self.lbl_modal_status.configure(
                        text="Playtime is 0m. Choose 'not_started' or enter playtime.",
                        text_color="#FF9800"
                    )
                    return

            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            if self.edit_data:
                game_id = self.edit_data['game_id']
                library_id = self.edit_data['library_id']

                # [SQL - UPDATE] 기존 게임 마스터 정보(제목, 정가) 수정
                cursor.execute(
                    "UPDATE game SET game_title = %s, original_price = %s WHERE game_id = %s;",
                    (title, price, game_id)
                )

                # [SQL - DELETE & INSERT] 중간 매핑 테이블(game_genre)의 기존 연결을 초기화하고 새 장르 매핑 저장
                if genre_id is not None:
                    cursor.execute("DELETE FROM game_genre WHERE game_id = %s;", (game_id,))
                    cursor.execute(
                        "INSERT INTO game_genre (game_id, genre_id) VALUES (%s, %s);",
                        (game_id, genre_id)
                    )

                # [SQL - UPDATE] 사용자 라이브러리의 누적 플레이 시간(분)과 진행 상태 수정
                cursor.execute(
                    "UPDATE user_library SET total_play_minutes = %s, status = %s WHERE library_id = %s;",
                    (total_minutes, status, library_id)
                )
            else:
                # [SQL - SELECT] 입력한 게임 제목이 game 테이블에 이미 존재하는지 조회 (중복 등록 방지)
                cursor.execute("SELECT game_id FROM game WHERE game_title = %s;", (title,))
                row = cursor.fetchone()

                if row:
                    game_id = row[0]
                    # [SQL - UPDATE] 이미 존재하는 게임이라면 최신 정가 정보로 갱신
                    cursor.execute(
                        "UPDATE game SET original_price = %s WHERE game_id = %s;",
                        (price, game_id)
                    )
                else:
                    # [SQL - INSERT] 신규 게임인 경우 game 테이블에 새 레코드 추가 후 생성된 game_id 획득
                    cursor.execute(
                        "INSERT INTO game (game_title, original_price) VALUES (%s, %s);",
                        (title, price)
                    )
                    game_id = cursor.lastrowid

                # [SQL - DELETE & INSERT] 중간 매핑 테이블(game_genre)에 해당 게임과 장르의 관계(game_id, genre_id) 등록
                if genre_id is not None:
                    cursor.execute("DELETE FROM game_genre WHERE game_id = %s;", (game_id,))
                    cursor.execute(
                        "INSERT INTO game_genre (game_id, genre_id) VALUES (%s, %s);",
                        (game_id, genre_id)
                    )

                # [SQL - SELECT] 해당 게임(game_id)이 Steam(platform_id=1) 라이브러리에 이미 등록되어 있는지 확인
                cursor.execute("SELECT library_id FROM user_library WHERE game_id = %s AND platform_id = 1;", (game_id,))
                lib_row = cursor.fetchone()

                if lib_row:
                    # [SQL - UPDATE] 이미 라이브러리에 있다면 기존 기록의 플레이 시간과 상태만 덮어쓰기
                    cursor.execute(
                        "UPDATE user_library SET total_play_minutes = %s, status = %s WHERE library_id = %s;",
                        (total_minutes, status, lib_row[0])
                    )
                else:
                    # [SQL - INSERT] 라이브러리에 없는 게임이라면 오늘 날짜(CURRENT_DATE)를 구매일로 하여 신규 등록
                    cursor.execute(
                        """
                        INSERT INTO user_library (game_id, platform_id, total_play_minutes, buy_date, status)
                        VALUES (%s, 1, %s, CURRENT_DATE, %s);
                        """,
                        (game_id, total_minutes, status)
                    )

            conn.commit()
            cursor.close()
            conn.close()

            self.parent.load_library_data()
            self.destroy()

        except ValueError:
            self.lbl_modal_status.configure(text="Price, Hours, and Minutes must be numbers.", text_color="#FF9800")
        except Exception as e:
            print(f"[Error] 데이터 저장 오류: {e}")
            self.lbl_modal_status.configure(text=f"Error: {e}", text_color="#F44336")


class SteamDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Steam Library & Analytics System")
        self.geometry("1040x640")
        self.resizable(False, False)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 정렬 드롭다운 선택값에 대응하는 SQL ORDER BY 절 매핑
        self.sort_mapping = {
            "Playtime (High to Low)": "ul.total_play_minutes DESC",
            "Playtime (Low to High)": "ul.total_play_minutes ASC",
            "Price (High to Low)": "g.original_price DESC",
            "Price (Low to High)": "g.original_price ASC",
            "Title (A to Z)": "g.game_title ASC",
            "Genre (A to Z)": "genre_names ASC",
            "Purchase Date (Newest)": "ul.buy_date DESC"
        }

        self._init_main_panel()
        self.load_library_data()

    def _init_main_panel(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=25, pady=25)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # 1. 상단 통계 카드
        stats_frame = ctk.CTkFrame(main_frame, height=85, fg_color="#2b2b2b")
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.card_total_games = self._create_stat_card(stats_frame, "TOTAL GAMES", "0", 0)
        self.card_total_hours = self._create_stat_card(stats_frame, "TOTAL PLAY TIME", "0h 0m", 1)
        self.card_avg_hours = self._create_stat_card(stats_frame, "AVG PLAY TIME", "0.0 hrs", 2)

        # 2. 목록 타이틀 및 정렬 컨트롤 바
        control_bar = ctk.CTkFrame(main_frame, fg_color="transparent")
        control_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        list_label = ctk.CTkLabel(control_bar, text="LIBRARY ANALYTICS", font=ctk.CTkFont(size=14, weight="bold"))
        list_label.pack(side="left")

        self.sort_dropdown = ctk.CTkOptionMenu(
            control_bar,
            values=list(self.sort_mapping.keys()),
            command=lambda _: self.load_library_data(),
            width=190,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#2b2b2b",
            button_color="#3a3a3a",
            button_hover_color="#4a4a4a"
        )
        self.sort_dropdown.set("Playtime (High to Low)")
        self.sort_dropdown.pack(side="right")

        ctk.CTkLabel(control_bar, text="Sort by:", font=ctk.CTkFont(size=11), text_color="gray60").pack(side="right", padx=(0, 8))

        # 3. 스크롤 리스트 프레임
        self.scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="#1a1a1a")
        self.scroll_frame.grid(row=2, column=0, sticky="nsew")
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # 4. 우측 하단 플로팅 + 버튼
        self.fab_button = ctk.CTkButton(
            self,
            text="+",
            font=ctk.CTkFont(size=24, weight="bold"),
            width=54,
            height=54,
            corner_radius=27,
            fg_color="#FFFFFF",
            text_color="#1f538d",
            hover_color="#E0E0E0",
            command=self.open_add_modal
        )
        self.fab_button.place(relx=0.95, rely=0.92, anchor="center")

    def _create_stat_card(self, parent, title, value, col):
        card = ctk.CTkFrame(parent, fg_color="transparent")
        card.grid(row=0, column=col, padx=15, pady=12, sticky="nsew")

        lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color="gray60")
        lbl_title.pack(anchor="w")

        lbl_val = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=18, weight="bold"))
        lbl_val.pack(anchor="w")
        return lbl_val

    def open_add_modal(self):
        GameFormModal(self, edit_data=None)

    def open_edit_modal(self, row_data):
        GameFormModal(self, edit_data=row_data)

    def update_status_inline(self, library_id, new_status, dropdown_widget):
        """메인 화면 드롭다운에서 상태 변경 시 즉시 DB 업데이트 (not_started 전환 시 플레이타임 0 초기화)"""
        new_status = new_status.lower()
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            if new_status == "not_started":
                # [SQL - UPDATE] not_started로 변경 시 상태와 함께 플레이타임도 0분으로 동기화
                cursor.execute(
                    "UPDATE user_library SET status = %s, total_play_minutes = 0 WHERE library_id = %s;",
                    (new_status, library_id)
                )
            else:
                # [SQL - UPDATE] 메인 목록에서 선택한 게임(library_id)의 진행 상태(status)만 즉시 변경
                cursor.execute(
                    "UPDATE user_library SET status = %s WHERE library_id = %s;",
                    (new_status, library_id)
                )

            affected = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()

            if affected == 0:
                print(f"[Warning] DB에 반영된 행이 없습니다. (library_id={library_id})")
            else:
                print(f"[Success] 상태 변경 완료 -> library_id={library_id}, status='{new_status}'")
                if new_status == "not_started":
                    # 플레이타임 0분 반영 및 상단 통계 재계산을 위해 목록 새로고침
                    self.load_library_data()
                else:
                    bg_color, btn_color = self._get_status_badge_colors(new_status)
                    dropdown_widget.configure(fg_color=bg_color, button_color=btn_color)

        except Error as e:
            print(f"[Error] 인라인 상태 변경 오류 (library_id={library_id}, status={new_status}): {e}")
            messagebox.showerror("Database Error", f"DB 업데이트 실패:\n{e}")
            self.load_library_data()

    def delete_record(self, library_id, game_title):
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{game_title}' from your library?"
        )
        if not confirm:
            return

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # [SQL - DELETE] 사용자 라이브러리 테이블에서 해당 게임 기록(library_id) 삭제 (마스터 game 및 game_genre는 유지)
            cursor.execute("DELETE FROM user_library WHERE library_id = %s;", (library_id,))
            conn.commit()
            cursor.close()
            conn.close()

            self.load_library_data()
        except Error as e:
            print(f"[Error] 삭제 오류: {e}")
            messagebox.showerror("Database Error", "Failed to delete the record.")

    def _get_status_badge_colors(self, status):
        palette = {
            "playing": ("#1e4620", "#285e2b"),
            "clear": ("#1a3c5e", "#224e7a"),
            "not_started": ("#383838", "#474747"),
            "dropped": ("#5c2323", "#752c2c")
        }
        return palette.get(status.lower(), ("#333333", "#444444"))

    def load_library_data(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        selected_sort = self.sort_dropdown.get()
        order_clause = self.sort_mapping.get(selected_sort, "ul.total_play_minutes DESC")

        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)

            # [SQL - SELECT & MULTI-JOIN & GROUP_CONCAT]
            # 1) user_library(ul)와 game(g)을 INNER JOIN하여 보유 게임 정보 결합
            # 2) 중간 매핑 테이블 game_genre(gg)와 장르 마스터 genre(gr)를 순차적으로 LEFT JOIN하여 장르 연결
            # 3) 한 게임에 여러 장르가 매핑되어 있더라도 행이 중복되지 않도록 GROUP BY ul.library_id와
            #    GROUP_CONCAT(gr.genre_name)을 사용해 장르명을 쉼표로 합쳐서 조회
            query = f"""
                SELECT 
                    ul.library_id,
                    g.game_id,
                    g.game_title,
                    g.original_price,
                    GROUP_CONCAT(gr.genre_name ORDER BY gr.genre_name SEPARATOR ', ') AS genre_names,
                    ul.total_play_minutes,
                    ul.buy_date,
                    ul.status
                FROM user_library ul
                JOIN game g ON ul.game_id = g.game_id
                LEFT JOIN game_genre gg ON g.game_id = gg.game_id
                LEFT JOIN genre gr ON gg.genre_id = gr.genre_id
                GROUP BY 
                    ul.library_id,
                    g.game_id,
                    g.game_title,
                    g.original_price,
                    ul.total_play_minutes,
                    ul.buy_date,
                    ul.status
                ORDER BY {order_clause};
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            total_games = len(rows)
            total_minutes = sum(r['total_play_minutes'] for r in rows) if rows else 0
            avg_minutes = (total_minutes / total_games) if total_games > 0 else 0

            self.card_total_games.configure(text=f"{total_games}")
            self.card_total_hours.configure(text=f"{total_minutes // 60}h {total_minutes % 60}m")
            self.card_avg_hours.configure(text=f"{avg_minutes / 60:.1f} hrs")

            # 컬럼 헤더 (TITLE, GENRE, PRICE, PLAY TIME, STATUS, ACTIONS 총 6열)
            header = ctk.CTkFrame(self.scroll_frame, fg_color="#333333", height=32)
            header.pack(fill="x", padx=5, pady=(5, 3))
            header.grid_columnconfigure(0, weight=3)
            header.grid_columnconfigure((1, 2, 3, 4), weight=2)
            header.grid_columnconfigure(5, weight=1)

            ctk.CTkLabel(header, text="TITLE", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, sticky="w", padx=12)
            ctk.CTkLabel(header, text="GENRE", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(header, text="PRICE", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=2, sticky="w")
            ctk.CTkLabel(header, text="PLAY TIME", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=3, sticky="w")
            ctk.CTkLabel(header, text="STATUS", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=4, sticky="w")
            ctk.CTkLabel(header, text="ACTIONS", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=5, sticky="e", padx=15)

            # 리스트 행 출력
            for row_data in rows:
                item_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#242424", height=42)
                item_frame.pack(fill="x", padx=5, pady=2)
                item_frame.grid_columnconfigure(0, weight=3)
                item_frame.grid_columnconfigure((1, 2, 3, 4), weight=2)
                item_frame.grid_columnconfigure(5, weight=1)

                mins = row_data['total_play_minutes']
                playtime_display = f"{mins // 60}h {mins % 60}m"
                genre_display = row_data['genre_names'] if row_data['genre_names'] else "-"
                status_val = (row_data['status'] or "playing").lower()
                lid = row_data['library_id']

                ctk.CTkLabel(item_frame, text=row_data['game_title']).grid(row=0, column=0, sticky="w", padx=12)
                ctk.CTkLabel(item_frame, text=genre_display, text_color="gray75").grid(row=0, column=1, sticky="w")
                ctk.CTkLabel(item_frame, text=f"\\{row_data['original_price']:,.0f}").grid(row=0, column=2, sticky="w")
                ctk.CTkLabel(item_frame, text=playtime_display).grid(row=0, column=3, sticky="w")

                bg_color, btn_color = self._get_status_badge_colors(status_val)
                widget_holder = {}
                status_menu = ctk.CTkOptionMenu(
                    item_frame,
                    values=STATUS_OPTIONS,
                    width=125,
                    height=24,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color=bg_color,
                    button_color=btn_color,
                    button_hover_color=btn_color,
                    command=lambda val, l_id=lid, holder=widget_holder: self.update_status_inline(l_id, val, holder["menu"])
                )
                widget_holder["menu"] = status_menu
                status_menu.set(status_val if status_val in STATUS_OPTIONS else "playing")
                status_menu.grid(row=0, column=4, sticky="w")

                # 수정 및 삭제 버튼 영역
                action_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
                action_frame.grid(row=0, column=5, sticky="e", padx=10, pady=6)

                btn_edit = ctk.CTkButton(
                    action_frame,
                    text="Edit",
                    width=45,
                    height=24,
                    font=ctk.CTkFont(size=11),
                    fg_color="#3a3a3a",
                    hover_color="#4a4a4a",
                    command=lambda r=row_data: self.open_edit_modal(r)
                )
                btn_edit.pack(side="left", padx=(0, 5))

                btn_del = ctk.CTkButton(
                    action_frame,
                    text="Del",
                    width=40,
                    height=24,
                    font=ctk.CTkFont(size=11),
                    fg_color="#5c2b2b",
                    hover_color="#7a3636",
                    command=lambda l_id=lid, title=row_data['game_title']: self.delete_record(l_id, title)
                )
                btn_del.pack(side="left")

            cursor.close()
            conn.close()

        except Error as e:
            print(f"[Error] 데이터 조회 오류: {e}")


if __name__ == '__main__':
    app = SteamDashboard()
    app.mainloop()