import streamlit as st
import pandas as pd

st.set_page_config(page_title="Property Calling Copilot", page_icon="🏠", layout="wide")
st.title("🏠 Property Calling Copilot — Calling MVP")
st.caption("4 + 1 个问题 → 快速匹配项目 → Sales Hook")

@st.cache_data
def load_projects():
    return pd.read_csv("projects.csv")

projects = load_projects()

st.sidebar.header("客户画像")
purpose = st.sidebar.radio("① 购房目的", ["🏠 自住", "💰 投资"])
budget = st.sidebar.number_input("② 预算（RM）", min_value=0, max_value=5000000, value=600000, step=50000)
locations = ["Singapore / CIQ", "JB Sentral", "Iskandar Puteri", "Bukit Indah", "Mount Austin", "Meridin East / Pasir Gudang", "Kulai", "未确定"]
location = st.sidebar.selectbox("③ 工作 / 生活区域", locations)
bedrooms_list = ["不限", "1BR", "2BR", "3BR", "4BR+"]
bedrooms = st.sidebar.selectbox("④ 房型", bedrooms_list)
priority_list = ["地点", "价格", "空间", "设施", "靠近 CIQ", "Developer / 品质"]
priority = st.sidebar.selectbox("⑤ 最在意", priority_list)

def bedroom_match(client, project):
    if client == "不限": return 1.0
    if client == project: return 1.0
    if client == "4BR+" and project in ("4BR", "5BR"): return 1.0
    return 0.0

def location_match(client, row):
    text = f"{row['location']} {row['area_tags']} {row['commute_tags']}".lower()
    if client == "未确定": return 0.6
    keys = {
        "Singapore / CIQ": ["ciq", "jb sentral", "singapore"],
        "JB Sentral": ["jb sentral", "ciq"],
        "Iskandar Puteri": ["iskandar puteri"],
        "Bukit Indah": ["bukit indah"],
        "Mount Austin": ["mount austin", "crest@austin", "tebrau"],
        "Meridin East / Pasir Gudang": ["meridin east", "pasir gudang", "masai"],
        "Kulai": ["kulai"],
    }
    hits = sum(k in text for k in keys[client])
    return min(1.0, 0.45 + 0.25 * hits)

def price_match(budget, lo, hi):
    if lo <= budget <= hi: return 1.0
    distance = min(abs(budget-lo), abs(budget-hi))
    return max(0.0, 1.0 - distance / max(budget*0.15, 1))

def priority_score(name, row):
    mapping = {
        "地点": row["location_score"], "价格": row["price_score"],
        "空间": row["space_score"], "设施": row["facility_score"],
        "靠近 CIQ": row["ciq_score"], "Developer / 品质": row["developer_score"]
    }
    return float(mapping[name])

def match_projects(df):
    results=[]
    for _, r in df.iterrows():
        p=price_match(budget,r.min_price,r.max_price)
        b=bedroom_match(bedrooms,r.bedroom)
        l=location_match(location,r)
        pr=priority_score(priority,r)
        score=0.35*p+0.20*b+0.25*l+0.20*pr
        results.append({**r.to_dict(),"match_score":round(score*100,1),"budget_fit":round(p*100),"bedroom_fit":round(b*100),"location_fit":round(l*100),"priority_fit":round(pr*100)})
    return pd.DataFrame(results).sort_values("match_score",ascending=False).head(5)

matches=match_projects(projects)

left,right=st.columns([1,1.2])
with left:
    st.subheader("📞 Calling Script — 4 + 1")
    st.markdown("""
**Q1 目的**  
「你这次主要是自己住，还是投资呢？」

**Q2 预算**  
「那你大概预算会抓在哪个范围呢？」

**Q3 地点**  
「你平时主要在哪里工作，或者生活会比较常跑哪一区？」

**Q4 房型**  
「房型方面呢，你比较想要两房、三房，还是其实空间大一点比较重要？」

**Q5 兴趣钩子**  
「如果预算和地点都合适，你买房最希望它特别好的是哪一点？」
""")
with right:
    st.subheader("🔥 当前 Top Projects")
    for i,(_,r) in enumerate(matches.iterrows(),1):
        st.markdown(f"**{i}. {r.project_name} — {r.match_score:.0f}% Match**  \nRM{r.min_price:,.0f}–RM{r.max_price:,.0f} · {r.bedroom} · {r.location}")
        st.caption(f"Budget {r.budget_fit}% · Location {r.location_fit}% · Bedroom {r.bedroom_fit}% · Priority {r.priority_fit}%")
    st.divider()
    st.subheader("🎣 Sales Hook")
    top1=matches.iloc[0]
    hook=f"「根据你刚刚讲的预算、{bedrooms}、还有你比较看重的{priority}，我这边大概筛到几个比较接近的项目。"
    if len(matches)>1:
        top2=matches.iloc[1]
        hook+=f" 其中 {top1.project_name} 的{priority}比较符合，{top2.project_name}则是在价格／空间方面比较有优势。"
    hook+=" 我不太想在电话里面随便讲一个给你，因为我这边符合条件的不只一个。如果你方便，我可以安排一个免费的 Zoom，把几个项目放在一起比较，你直接看哪个适合你就可以了。」"
    st.info(hook)

st.divider()
st.caption("MVP：Calling 阶段只收集会改变项目排序的 4 个核心信息 + 1 个兴趣点；详细需求留到 Zoom / 见面。")
with st.expander("查看筛选数据"):
    st.dataframe(matches,use_container_width=True)
