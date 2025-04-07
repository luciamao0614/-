def llm_response(prompt):
    try:
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0
        )
        return response.choices[0].message['content']
    except openai.OpenAIError:
        st.error(f"❌ OpenAI 接口调用失败：{str(e)}")
        st.session_state.api_key = ""
        st.session_state.ready = False
        st.stop()

# 初始化 Streamlit app
st.set_page_config(page_title="赛博私房菜 · 智能餐评分析", layout="wide")

# 餐厅人设介绍
st.title("🥢 赛博食堂 · 智能评论分析")
st.markdown("""
📍 **费城大学城 · 中国味私房盒饭 · 周一至周五 10AM-6PM 提供三菜一汤 · 每份 $10 外送自提**

> 小店新开张，期待大家的神评！Make Penn street food great again ✨
""")

# 用户输入区
user_input = st.text_area("📝 请输入您的评论：", height=100)

# 初始化会话状态
if "reviews" not in st.session_state:
    st.session_state.reviews = []
if "user_count" not in st.session_state:
    st.session_state.user_count = 0

# 提交评论
if st.button("📩 提交评论") and user_input:
    if st.session_state.user_count >= 10:
        st.warning("⚠️ 评论次数过于频繁，请稍后再试。")
        st.stop()
    st.session_state.reviews.append(user_input)
    st.session_state.user_count += 1

# 检查评论存在
if not st.session_state.reviews:
    st.info("请输入至少一条评论后点击提交")
    st.stop()

# 构造 prompt（判断 Irrelevant）
prompt = '''
你是一个评论分析师。请对下列每条评论执行以下操作：

1. 判断是否与 "餐厅体验/食品/服务/外卖" 相关：
    - 如果无关，请返回： <编号>. Irrelevant
2. 如果有关，请执行：
    - 分类情绪：Positive 或 Negative
    - 提取1-3个关键词（名词/名词短语）
    - 给出1-2个标签（如：服务、食品、餐厅体验、外卖）

输出格式：
<编号>. Sentiment: <Positive/Negative> | Keywords: <关键词> | Tags: <标签>

评论：
'''
for idx, review in enumerate(st.session_state.reviews, 1):
    prompt += f"{idx}. {review}\n"

response = llm_response(prompt)
st.subheader("🌟 GPT 分析结果")
st.code(response, language="text")

# 数据处理
lines = response.strip().split('\n')
data = []
for line in lines:
    if "Irrelevant" in line:
        continue
    parts = line.split('|')
    if len(parts) == 3:
        sentiment = parts[0].split(':')[-1].strip()
        keywords = parts[1].split(':')[-1].strip()
        tags = parts[2].split(':')[-1].strip()
        data.append([sentiment, keywords, tags])

if not data:
    st.warning("未识别出任何有效评论")
    st.stop()

# 创建 DataFrame
df = pd.DataFrame(data, columns=["Sentiment", "Keywords", "Tags"])
st.dataframe(df, use_container_width=True)

# 生成 CSV 下载
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📂 下载 CSV 分析结果",
    data=csv,
    file_name="review_analysis.csv",
    mime="text/csv"
)

# 评分计算
sentiment_counts = df["Sentiment"].value_counts()
positive_count = sentiment_counts.get("Positive", 0)
total_reviews = len(df)
positive_ratio = positive_count / total_reviews
score = round(positive_ratio * 5, 2)

st.metric(label="🍱 客户情绪评分", value=f"{score} / 5.0")

# 使用 TAGS 做词云
all_tags = []
for tag_list in df["Tags"]:
    tags = [tag.strip() for tag in tag_list.split(',') if len(tag.strip()) >= 2]
    all_tags.extend(tags)

if all_tags:
    tag_counter = Counter(all_tags)
    tag_text = ' '.join(tag_counter.elements())
    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color='white',
        font_path=CHINESE_FONT_PATH
    ).generate(tag_text)

    img_buffer = BytesIO()
    wordcloud.to_image().save(img_buffer, format='PNG')
    img_buffer.seek(0)
    st.image(Image.open(img_buffer), caption="客户标签词云（基于 TAG）", use_column_width=True)
else:
    st.info("未能生成词云图（标签不足）")
