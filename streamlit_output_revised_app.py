import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw

# --- 定数と定義 ---
BASEBALL_FIELD_IMG = "baseballfield.jpg"
DATA_FILENAME = "hitting_data.csv"
REFERENCE_POINT_ORIGINAL = (632, 1069)  # 元画像サイズでの基準点
TARGET_SIZE = (750, 750)  # インプットと同じサイズに揃える

PITCH_TYPE_COLORS = {
    "ストレート": "red",
    "スライダー": "blue",
    "チェンジアップ": "yellow",
    "フォーク": "orange",
    "カットボール": "skyblue",
    "ツーシーム": "pink",
    "カーブ": "purple",
}

HIT_TYPE_SHAPES = {
    "ゴロ": "ellipse",
    "フライ": "rectangle",
    "ライナー": "triangle",
}


# --- ヘルパー関数 ---
def draw_shape(draw_obj, shape, x, y, size, color):
    h_size = size / 2
    if shape == "ellipse":
        draw_obj.ellipse(
            (x - h_size, y - h_size, x + h_size, y + h_size), fill=color, outline=color
        )
    elif shape == "rectangle":
        draw_obj.rectangle(
            (x - h_size, y - h_size, x + h_size, y + h_size), fill=color, outline=color
        )
    elif shape == "triangle":
        points = [(x, y - h_size), (x - h_size, y + h_size), (x + h_size, y + h_size)]
        draw_obj.polygon(points, fill=color, outline=color)


# --- Streamlit アプリケーション ---
st.set_page_config(layout="wide")
st.title("⚾ 打球分析アプリ - データ閲覧")

# 元画像読み込み & リサイズ（インプットと同じサイズに揃える）
try:
    original_img = Image.open(BASEBALL_FIELD_IMG)
    resized_img = original_img.resize(TARGET_SIZE)
except FileNotFoundError:
    st.error(f"{BASEBALL_FIELD_IMG} が見つかりません。")
    st.stop()


# 座標も画像サイズに合わせて変換
def scale_coordinates(x, y, original_size, target_size):
    scale_x = target_size[0] / original_size[0]
    scale_y = target_size[1] / original_size[1]
    return int(x * scale_x), int(y * scale_y)


REFERENCE_POINT = scale_coordinates(
    REFERENCE_POINT_ORIGINAL[0],
    REFERENCE_POINT_ORIGINAL[1],
    original_img.size,
    TARGET_SIZE,
)

# データ読み込み
try:
    hitting_df = pd.read_csv(DATA_FILENAME, encoding="cp932")
except Exception as e:
    st.error(f"{DATA_FILENAME} の読み込みに失敗しました: {e}")
    hitting_df = pd.DataFrame()

if hitting_df.empty:
    st.warning("データファイルが空です。")
    st.stop()

st.sidebar.header("操作パネル")

# --- フィルター ---
team_options = ["すべて"] + sorted(hitting_df["team_name"].dropna().unique())
selected_team = st.sidebar.selectbox("チームを選択", team_options)

player_options = ["すべて"] + sorted(hitting_df["player_name"].dropna().unique())
selected_player = st.sidebar.selectbox("選手を選択", player_options)

opponents_filter = st.sidebar.selectbox("対戦相手", ["京大以外", "京大"])
pitcherLR_filter = st.sidebar.selectbox("対右or対左", ["右", "左"])
runners_filter = st.sidebar.selectbox("塁状況", ["すべて", "なし", "1塁", "得点圏"])
strikes_filter = st.sidebar.selectbox("ストライク", ["すべて", "0", "1", "2"])
pitch_course_filter = st.sidebar.selectbox("コース", ["すべて", "内", "真中", "外"])
pitch_height_filter = st.sidebar.selectbox("高さ", ["すべて", "低め", "真中", "高め"])
pitch_type_filter = st.sidebar.selectbox(
    "球種", options=["すべて", "ストレート系", "スライダー系", "チェンジ系"]
)

hit_type_options = ["すべて"] + sorted(hitting_df["hit_type"].dropna().unique())
selected_hit_type = st.sidebar.selectbox("打球性質", hit_type_options)

# --- データフィルタリング ---
filtered_df = hitting_df.copy()
if selected_team != "すべて":
    filtered_df = filtered_df[filtered_df["team_name"] == selected_team]
if selected_player != "すべて":
    filtered_df = filtered_df[filtered_df["player_name"] == selected_player]
if opponents_filter != "すべて":
    filtered_df = filtered_df[filtered_df["opponents"] == opponents_filter]
if pitcherLR_filter != "すべて":
    filtered_df = filtered_df[filtered_df["pitcherLR"] == pitcherLR_filter]
if runners_filter != "すべて":
    filtered_df = filtered_df[filtered_df["runners"].astype(str) == runners_filter]
if strikes_filter != "すべて":
    filtered_df = filtered_df[filtered_df["strikes"].astype(str) == strikes_filter]
if pitch_course_filter != "すべて":
    filtered_df = filtered_df[
        filtered_df["pitch_course"].astype(str) == pitch_course_filter
    ]
if pitch_height_filter != "すべて":
    filtered_df = filtered_df[
        filtered_df["pitch_height"].astype(str) == pitch_height_filter
    ]
if pitch_type_filter == "ストレート系":
    filtered_df = filtered_df[
        filtered_df["pitch_type"].isin(["ストレート", "ツーシーム"])
    ]
elif pitch_type_filter == "スライダー系":
    filtered_df = filtered_df[
        filtered_df["pitch_type"].isin(["スライダー", "カットボール"])
    ]
elif pitch_type_filter == "チェンジ系":
    filtered_df = filtered_df[
        filtered_df["pitch_type"].isin(["チェンジアップ", "フォーク"])
    ]
if selected_hit_type != "すべて":
    filtered_df = filtered_df[filtered_df["hit_type"] == selected_hit_type]

st.write(f"表示件数: {len(filtered_df)} 件")

# --- 描画処理 ---
img_to_draw = resized_img.copy()
draw = ImageDraw.Draw(img_to_draw)

for _, row in filtered_df.iterrows():
    x, y = int(row["x_coord"]), int(row["y_coord"])
    color = PITCH_TYPE_COLORS.get(row["pitch_type"], "gray")
    shape = HIT_TYPE_SHAPES.get(row["hit_type"], "ellipse")

    draw_shape(draw, shape, x, y, 25, color)
    draw.line([REFERENCE_POINT, (x, y)], fill=color, width=4)

# --- 画像表示 ---
st.image(img_to_draw, use_container_width=True)

# --- データ表示 ---
if st.checkbox("フィルター結果のデータを表示"):
    st.dataframe(filtered_df)
