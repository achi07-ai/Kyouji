import datetime
import streamlit as st
from supabase import create_client, Client

# ページ設定
st.set_page_config(page_title="Moochi Moochi プロトタイプ", page_icon="🤖", layout="centered")

# ---------------------------------------------------------
# 🔑 Supabase 接続の初期化
# ---------------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
    raw_url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    clean_url = raw_url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
    return create_client(clean_url, key)

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error(f"Supabaseへの接続に失敗しました: {e}")
    st.stop()


# ---------------------------------------------------------
# 🧠 ARCSモデルに基づく：強制しないリマインダー・エンジン
# ---------------------------------------------------------
def check_reminders():
    st.subheader("🤖 今日のエージェントからのメッセージ")

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    two_days_later = today + datetime.timedelta(days=2)

    reminders_triggered = False

    # 1. 翌日の「曜日」を判定して1限チェック
    weekday_idx = tomorrow.weekday() # 0:月, 1:火, 2:水, 3:木, 4:金, 5:土, 6:日
    weekdays_db_cols = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    # 平日（月〜金）の場合のみデータベースを確認する
    if weekday_idx < 5:
        target_col = weekdays_db_cols[weekday_idx]
        try:
            schedule_res = (
                supabase.schema("public")
                .table("user_schedule")
                .select(target_col)
                .eq("id", 1)
                .execute()
            )
            # 明日の曜日にTrue（1限あり）が設定されているか？
            if schedule_res.data and schedule_res.data[0].get(target_col, False):
                st.info(
                    "💬 **明日の一限をクリアすれば、週末のゲーム時間がもっと最高になりますよ！** "
                    "今夜は少しだけ早めに布団に入ってみませんか？"
                )
                reminders_triggered = True
        except Exception as e:
            st.error(f"スケジュール確認エラー: {e}")

    # 2. 2日後の宿題締切チェック
    try:
        assignment_res = (
            supabase.schema("public")
            .table("assignments")
            .select("title")
            .eq("due_date", two_days_later.isoformat())
            .execute()
        )
        if assignment_res.data:
            for item in assignment_res.data:
                st.warning(
                    f"💬 2日後に **【{item['title']}】** の締切がありますね。"
                    "今日のうちにちょっとだけ進めておくと、明日の夜がグッと楽になって自分の時間が作れるかもしれません！"
                )
            reminders_triggered = True
    except Exception as e:
        st.error(f"課題確認エラー: {e}")

    # リマインダーがない場合の並走フィードバック
    if not reminders_triggered:
        st.success(
            "💬 今日も自分のペースで進めていきましょう！何かあればいつでも声をかけてくださいね。"
        )


# ---------------------------------------------------------
# 📱 UI・入力フォーム
# ---------------------------------------------------------
st.title("🤖 Moochi Moochi プロトタイプ")
st.write("〜 監視ゼロ。あなたの自律的な生活にそっと寄り添う伴走AI 〜")
st.markdown("---")

# リマインダーエリアの表示
check_reminders()
st.markdown("---")

# タブで入力を分離
tab1, tab2, tab3 = st.tabs(
    ["⏰ 睡眠ログ記入", "📅 曜日ごとの1限設定", "📝 宿題・課題登録"]
)

# --- タブ1: 睡眠時間記入 ---
with tab1:
    st.header("🛏️ 睡眠データの記録")
    with st.form("sleep_form", clear_on_submit=True):
        sleep_date = st.date_input("就寝日", datetime.date.today())
        bedtime = st.time_input("就寝時刻", datetime.time(23, 0))
        wake_time = st.time_input("起床時刻", datetime.time(7, 0))

        submit_sleep = st.form_submit_button("Supabaseに保存")

        if submit_sleep:
            data = {
                "sleep_date": sleep_date.isoformat(),
                "bedtime": bedtime.isoformat(),
                "wake_time": wake_time.isoformat(),
            }
            try:
                supabase.schema("public").table("sleep_logs").insert(data).execute()
                st.success("睡眠ログを保存しました！しっかり記録できているの、素晴らしいですね！")
            except Exception as e:
                st.error(f"保存に失敗しました: {e}")

# --- タブ2: 時間割記入（曜日ベースに進化！） ---
with tab2:
    st.header("📅 曜日ごとの1限目設定")
    st.write("1限目がある曜日にチェックを入れておくと、自動でリマインドします。（一度設定すればOKです！）")
    
    # 現在のデータベースの設定を取得して、チェックボックスの初期状態にする
    current_settings = {"monday": False, "tuesday": False, "wednesday": False, "thursday": False, "friday": False}
    try:
        res = supabase.schema("public").table("user_schedule").select("*").eq("id", 1).execute()
        if res.data:
            current_settings = res.data[0]
    except:
        pass

    with st.form("schedule_form"):
        col1, col2, col3, col4, col5 = st.columns(5)
        mon = col1.checkbox("月曜", value=current_settings.get("monday", False))
        tue = col2.checkbox("火曜", value=current_settings.get("tuesday", False))
        wed = col3.checkbox("水曜", value=current_settings.get("wednesday", False))
        thu = col4.checkbox("木曜", value=current_settings.get("thursday", False))
        fri = col5.checkbox("金曜", value=current_settings.get("friday", False))

        submit_schedule = st.form_submit_button("曜日設定を保存")

        if submit_schedule:
            data = {
                "id": 1,
                "monday": mon,
                "tuesday": tue,
                "wednesday": wed,
                "thursday": thu,
                "friday": fri
            }
            try:
                # 既存のデータを上書き（upsert）する
                supabase.schema("public").table("user_schedule").upsert(data).execute()
                st.success("曜日設定を保存・更新しました！明日の分から自動で判定します。")
                st.rerun()
            except Exception as e:
                st.error(f"保存に失敗しました: {e}")

# --- タブ3: 宿題の提出期限記入 ---
with tab3:
    st.header("📝 宿題・課題の提出期限")
    with st.form("assignment_form", clear_on_submit=True):
        title = st.text_input("課題名（例: データサイエンス基礎 レポート）")
        due_date = st.date_input("提出期限", datetime.date.today() + datetime.timedelta(days=2))

        submit_assignment = st.form_submit_button("課題を登録")

        if submit_assignment:
            if not title:
                st.error("課題名を入力してください。")
            else:
                data = {"title": title, "due_date": due_date.isoformat()}
                try:
                    supabase.schema("public").table("assignments").insert(data).execute()
                    st.success(f"「{title}」を登録しました。締切を意識できているだけで一歩前進です！")
                    st.rerun()
                except Exception as e:
                    st.error(f"保存に失敗しました: {e}")
