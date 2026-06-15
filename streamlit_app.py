import streamlit as st
from supabase import create_client

st.title("🔧 接続診断ツール")

try:
    # 1. Secretsの読み込みテスト
    raw_url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    
    # URLに余計なパスが含まれていないか自動補正
    clean_url = raw_url.replace("/rest/v1/", "").replace("/rest/v1", "").rstrip("/")
    
    st.success(f"✅ Secrets読み込み成功\n\n接続先URL: `{clean_url}`")

    # 2. クライアントの作成テスト
    supabase = create_client(clean_url, key)
    st.success("✅ Supabaseクライアント作成成功")

    # 3. データベースへのアクセス（通信）テスト
    res = supabase.table("schedules").select("*").limit(1).execute()
    st.success("✅ データベースへのアクセス成功！Invalid pathの壁を越えました！")
    
    # 取得したデータを表示
    st.json(res.data)

except KeyError as e:
    st.error(f"❌ Secretsエラー: シークレット設定内に {str(e)} が見つかりません。")
except Exception as e:
    st.error(f"❌ 通信/その他エラー: {type(e).__name__} - {str(e)}")
