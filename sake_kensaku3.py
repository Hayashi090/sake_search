# アプリの目的：日本酒に関する情報をAPIを通じて取得し、ユーザーが日本酒の特徴を視覚で理解出来るものにする

# 必要なライブラリのインポート
import pandas as pd  # データの操作
import requests  # HTTPリクエストによりAPIからデータを取得する
import streamlit as st  # Webアプリの構築、UI作成
import plotly.express as px  # フレーバーチャートの可視化
import math  # フレーバーデータの処理（切り上げ）

# 指定したURL（APIの窓口）からデータを取得
def fetch_data(url, params=None):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"APIエラー: {e}")
        return None

# 都道府県や酒蔵のリスト作成（辞書形式で返す）    
def get_dropdown_options(data, key_name, filter_key=None, filter_value=None):
    if filter_key and filter_value:
        data = [item for item in data if item.get(filter_key) == filter_value]
    return {item["name"]: item["id"] for item in data}
    # 名前が空欄またはNoneのデータを除外
    options = {item[key_name]: item["id"] for item in data if item.get(key_name)}
    return options

# フレーバーチャート要約を選択した特徴に基づいて抽出する
def filter_flavor_by_feature(flavor_chart, selected_feature):
    feature_mapping = {
        "華やか": "f1",
        "芳醇": "f2",
        "重厚": "f3",
        "穏やか": "f4",
        "ドライ": "f5",
        "軽快": "f6"
    }
    feature_column = feature_mapping.get(selected_feature)
    if not feature_column:
        return None
    return flavor_chart[feature_column]

# アプリのタイトルと説明
st.markdown("## 日本酒検索アプリ")
st.markdown("[さけのわAPI](https://sakenowa.com)のデータをお借りしています。")

# APIの窓口（エンドポイント）設定
API_URLS = {
    "都道府県一覧": "https://muro.sakenowa.com/sakenowa-data/api/areas",
    "酒蔵一覧": "https://muro.sakenowa.com/sakenowa-data/api/breweries",
    "銘柄一覧": "https://muro.sakenowa.com/sakenowa-data/api/brands",
    "フレーバーチャート": "https://muro.sakenowa.com/sakenowa-data/api/flavor-charts",
}

# 都道府県のデータ取得
areas_data = fetch_data(API_URLS["都道府県一覧"])
if not areas_data:
    st.stop()

# 都道府県選択
areas_options = get_dropdown_options(areas_data["areas"], "name")
selected_area = st.sidebar.selectbox("検索したい都道府県を選択してください", list(areas_options.keys()))
selected_area_id = areas_options[selected_area]


# 酒蔵のデータ取得
breweries_data = fetch_data(API_URLS["酒蔵一覧"])
if not breweries_data:
    st.stop()

# 空欄データを除外後、酒蔵選択
breweries_options = {
    item["name"]: item["id"]
    for item in breweries_data["breweries"]
    if item.get("name")  # nameが空欄またはNoneではないデータのみ
    and item.get("areaId") == selected_area_id  # 選択された都道府県のデータのみ
}
selected_brewery = st.sidebar.selectbox("検索したい酒蔵を選択してください", list(breweries_options.keys()))
selected_brewery_id = breweries_options[selected_brewery]

# 銘柄のデータ取得
brands_data = fetch_data(API_URLS["銘柄一覧"])
if not brands_data:
    st.stop()

# 銘柄選択
brands_options = get_dropdown_options(
    brands_data["brands"], "name", "breweryId", selected_brewery_id
)
if not brands_options:
    st.error("選択可能な銘柄が見つかりません。")
    st.stop()
selected_brand = st.sidebar.selectbox(
    "検索したい銘柄を選択してください", list(brands_options.keys())
)

if not selected_brand:
    st.error("銘柄が選択されていません。")
    st.stop()
selected_brand_id = brands_options[selected_brand]

# サイドバーの背景色をオレンジに設定
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-color: #FFE4B5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# フレーバーの特徴選択、サイドバーにフレーバーの特徴を表示
with st.sidebar:
    flavor_features = [
        "華やか", "芳醇", "重厚", "穏やか", "ドライ", "軽快"
    ]
    selected_flavor_feature = st.selectbox("フレーバーの特徴を選んでください", flavor_features)

    st.markdown(" **華やか**: 果実や花のような香りがある")
    st.markdown(" **芳醇**: 濃厚でリッチな味わい")
    st.markdown(" **重厚**: 酸味や苦味、コクのある味わい")
    st.markdown(" **穏やか**: 静かで穏やかな香りと味わい")
    st.markdown(" **ドライ**: すっきりとして甘さが少ない")
    st.markdown(" **軽快**: 口当たりが軽く、飲みやすい")  

# フレーバーチャートのデータ取得
flavor_chart_data = fetch_data(API_URLS["フレーバーチャート"])
if not flavor_chart_data:
    st.stop()
    st.write("フレーバーチャートデータ:", flavor_chart_data)  # デバッグ用

flavor_chart = next(
    (
        chart
        for chart in flavor_chart_data["flavorCharts"]
        if chart["brandId"] == selected_brand_id
    ),
    None,
)

# フレーバーチャートの要約と表示、特徴に基づいてフレーバーのデータ（上位2つ）を抽出する
st.markdown(f"### {selected_brand}のフレーバーチャート")
if flavor_chart:
    filtered_flavor_value = filter_flavor_by_feature(flavor_chart, selected_flavor_feature)
    if filtered_flavor_value is not None:
        rounded_value = math.ceil(filtered_flavor_value * 100) / 100  # 小数点第2位まで切り上げ
        st.markdown(f"**{selected_flavor_feature}の値**: {rounded_value}")

        try:
            df = pd.DataFrame([flavor_chart]).drop("brandId", axis=1)
            df = df.rename(
                columns={
                    "f1": "華やか",
                    "f2": "芳醇",
                    "f3": "重厚",
                    "f4": "穏やか",
                    "f5": "ドライ",
                    "f6": "軽快",
                }
            ).T
            df.columns = ["値"]
            top_flavors = df.sort_values(by="値", ascending=False).head(2).index.tolist()
            summary = f"これは{top_flavors[0]}と{top_flavors[1]}が特徴のフレーバーを持つ日本酒です。"
            st.markdown(
                f"""
                <div style='background-color: rgba(0, 123, 255, 0.1); padding: 10px; border-radius: 5px;'>
                <strong>特徴の要約:</strong> {summary}
                </div>
                """,
                unsafe_allow_html=True,
            )

            # フレーバーチャートを描画
            fig = px.line_polar(df, r="値", theta=df.index, line_close=True, range_r=[0, 1])
            fig.update_traces(
                opacity=0.8,  # チャートを半透明化
                fill="toself",
                fillcolor="rgba(0, 123, 255, 0.2)",
                line=dict(color="rgba(0, 123, 255, 0.8)", width=3),
            )
            st.plotly_chart(fig)
        except Exception as e:
            st.error(f"フレーバーチャートの描画中にエラーが発生しました: {e}")
    else:
        st.info(f"{selected_flavor_feature}の情報は見つかりませんでした。")
else:
    st.markdown(
        """
        <div style='background-color: rgba(255, 0, 0, 0.1); padding: 10px; border-radius: 5px;'>
        フレーバーチャートの情報は現在ありません。
        </div>
        """,
        unsafe_allow_html=True,
    )
