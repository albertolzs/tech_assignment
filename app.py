import os
import datetime as dt
import ollama
import pandas as pd
import pytz
import streamlit as st

from src import UI_CONTEXT_PROMPT, DBManager, NewsFetcher, PLOT_CONTEXT_PROMPT
from settings import REGIONS, AVAILABLE_MODELS, MARKETS, DB_PATH, DEFAULT_START_DATE, HTTP_TIMEOUT

st.set_page_config(page_title="NBIM Regulatory News Dashboard", layout="wide")
st.title("Regulatory news dashboard")
st.logo(os.path.join("figures", "logo.svg"), size="large")

db_manager = DBManager(DB_PATH)
db_manager.init()

fetcher = NewsFetcher(time_out=HTTP_TIMEOUT, utc=pytz.UTC)

st.sidebar.title("Settings ⚙️️")

with st.sidebar.expander("Markets", expanded=True):
    selected_markets = st.pills(label="markets", options=MARKETS, selection_mode="multi",
                                label_visibility="hidden")

countries = list(REGIONS.keys())
with st.sidebar.expander("Regions", expanded=True):
    selected_regions = st.pills(label="region", options=countries, selection_mode="multi", default=countries,
                                label_visibility="hidden")

with st.sidebar.expander("Sort by", expanded=True):
    sort_by = st.selectbox(label="Sort by", options= ["Score", "Date"], index=0, label_visibility="hidden")

with st.sidebar.expander("Period", expanded=True):
    today = dt.date.today()
    default_start = today - dt.timedelta(days=7)
    start_date = st.date_input("Start date", value=default_start)
    end_date = st.date_input("End date", value=today)

with st.sidebar.expander("Advanced options", expanded=True):
    use_llm = st.checkbox(label="Deep analysis", value=True)
    if use_llm:
        selected_model = st.selectbox(label="Choose an LLM", options=AVAILABLE_MODELS, index=0)

col1 = st.columns(1)
with col1[0]:
    if st.button("Refresh database"):
        with st.spinner("Fetching and storing latest items..."):
            total_new = 0
            for region in REGIONS:
                items = fetcher.fetch_news(
                    region=region,
                    end_date=dt.date.today(),
                    model=selected_model,
                    use_llm=use_llm,
                )
                total_new += db_manager.update(items)
        st.success(f"Updated database with {total_new} items.")
        st.rerun()

total_items = []
for region in selected_regions:
    items = db_manager.get(
        region=region,
        start_date=start_date,
        end_date=end_date,
        markets_filter=selected_markets,
    )
    total_items.append(items)

columns = ['id', 'uid', 'title', 'link', 'date', 'time', 'region', 'zone', 'source', *MARKETS,
           'reasons', 'score', 'summary', 'created_at']
df = pd.DataFrame([item for items in total_items for item in items], columns=columns)
df = df.rename(columns={"date": "Day", "region": "Region", "score": "Score"})
cont = st.container(border=True)
with cont:
    selected_plot = st.segmented_control(label= "To plot", options=["Region", "Market"], default=["Market", "Region"],
                                         selection_mode="multi", label_visibility="hidden")
    if "Region" in selected_plot:
        col1, col2 = st.columns(2)
        with col1:
            df1 = df[["Day", "Region"]].value_counts().rename("Count").reset_index()
            st.line_chart(df1, x="Day", y="Count",
                          color="Region", width=750)
        with col2:
            df2 = df[df["Score"] > 0]
            df2 = df2.groupby(["Day", "Region"], as_index=False)["Score"].mean()
            st.line_chart(df2, x="Day", y="Score", color="Region", width=750)
        if st.button("What is happening in the regions?"):
            df1 = df1.to_dict()
            df2 = df2.to_dict()
            resp = ollama.chat(
                model=selected_model,
                messages=[
                    {"role": "user", "content": UI_CONTEXT_PROMPT + f"Input: {df1} {df2}"}
                ],
                options={"temperature": 0.0},
            )
            content = resp.get("message", {}).get("content", "")
            st.write(content)

    if "Market" in selected_plot:
        col1, col2 = st.columns(2)
        if not selected_markets:
            selected_markets = MARKETS
        with col1:
            df1 = df.groupby("Day", as_index=False)[selected_markets].sum()
            st.line_chart(df1,
                          x="Day", y=selected_markets, y_label="Count", width=750)
        with col2:
            df2 = df[df["Score"] > 0]
            df2 = df2.melt(id_vars=['Day', 'Score'], value_vars=selected_markets,
                           var_name='Market', value_name='Present')
            df2 = df2[df2['Present'] > 0]
            df2 = df2.groupby(['Day', 'Market'], as_index=False)['Score'].mean()
            st.line_chart(df2, x="Day", y="Score", color="Market", width=750)
        if st.button("What is happening in the markets?"):
            df1 = df1.to_dict()
            df2 = df2.to_dict()
            resp = ollama.chat(
                model=selected_model,
                messages=[
                    {"role": "user", "content": PLOT_CONTEXT_PROMPT + f"Input: {df1} {df2}"}
                ],
                options={"temperature": 0.0},
            )
            content = resp.get("message", {}).get("content", "")
            st.write(content)

prompt = st.chat_input("Would you like to discuss something?")
if prompt:
    cont = st.container(border=True)
    with cont:
        resp = ollama.chat(
            model=selected_model,
            messages=[
                {"role": "user", "content": UI_CONTEXT_PROMPT + f"Input: {prompt}"}
            ],
            options={"temperature": 0.0},
        )
        content = resp.get("message", {}).get("content", "")
        st.write(content)

for region, items in zip(selected_regions, total_items):
    st.header(region)
    if not items:
        st.write("No items found.")
        continue
    if sort_by == "Score":
        items = sorted(items, key=lambda x: x.get('score'), reverse=True)
    elif sort_by == "Date":
        items = sorted(items, key=lambda x: x.get('date', DEFAULT_START_DATE), reverse=True)
    for item in items:
        cont = st.container(border=True)
        with cont:
            top = st.columns([9, 1])
            with top[0]:
                st.subheader(f"{item.get('title','(no title)')}")
                meta_bits = [
                    item.get('source'),
                    item.get('region'),
                    item.get('date').strftime("%Y-%m-%d"),
                    item.get('time')
                ]
                st.caption(" · ".join([b for b in meta_bits if b]))
            with top[1]:
                if url := item.get('link'):
                    st.link_button("Open", url)
            if markets := [market for market in MARKETS if item[market]]:
                label = " · ".join(markets)
                st.write(label)
            if score:= item.get('score'):
                if score <= 2:
                    score = f":blue[{score}]"
                elif score <= 4:
                    score = f":yellow[{score}]"
                else:
                    score = f":red[{score}]"
                label = f"Score: {score}"
                st.write(label)

            if summary := item.get('summary'):
                st.write(summary)
            if reasons := item.get('reasons'):
                with st.expander("More info"):
                    st.write("\n".join(f"- {r}" for r in eval(reasons)))