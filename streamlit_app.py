import datetime
import streamlit as st
from supabase import create_client, Client

# ページ設定
st.set_page_config(page_title="Moochi Moochi プロトタイプ", page_icon="🤖", layout="centered")

# ---------------------------------------------------------
# 🔑 Supabase 接続の初期化（診断ツールで成功した最強の設定）
# ---------------------------------------------------------
@st.cache_resource
def init_supabase() -> Client:
    # Secretsから読み込み
    raw_url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    
    # 念のため、URLに不要なパスが混ざっていても自動で綺麗にする処理
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

    # 1. 翌日の1限チェック
    try:
        schedule_res = (
            supabase.schema("public")
            .table("schedules")
            .select("has_first_period")
            .eq("target_date", tomorrow.isoformat())
            .execute()
        )
        if schedule_res.data and schedule_res.data[0]["has_first_period"]:
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
    ["⏰ 睡眠ログ記入", "📅 明日の予定記入", "📝 宿題・課題登録"]
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
                st.success(
                    "睡眠ログを保存しました！しっかり記録できているの、素晴らしいですね！"
                )
            except Exception as e:
                st.error(f"保存に失敗しました: {e}")

# --- タブ2: 時間割記入 ---
with tab2:
    st.header("📅 明日の時間割・予定")
    with st.form("schedule_form", clear_on_submit=True):
        target_date = st.date_input("対象日", datetime.date.today() + datetime.timedelta(days=1))
        has_first_period = st.checkbox("この日は「1限目」がありますか？")

        submit_schedule = st.form_submit_button("スケジュールを更新")

        if submit_schedule:
            data = {
                "target_date": target_date.isoformat(),
                "has_first_period": has_first_period,
            }
            try:
                supabase.schema("public").table("schedules").insert(data).execute()
                st.success("予定を保存しました。これで明日の準備もバッチリですね。")
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
                    st.success(
                        f"「{title}」を登録しました。締切を意識できているだけで一歩前進です！"
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"保存に失敗しました: {e}")
