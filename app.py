import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(page_title='SupeRR Selector | Pressure Analytics', page_icon='🏏', layout='wide')
st.markdown('''<style>.block-container{padding-top:1.6rem;max-width:1300px}.hero{padding:24px 28px;background:linear-gradient(110deg,#102943,#176b87);color:white;border-radius:16px;margin-bottom:18px}.hero h1{color:white;margin:0;font-size:2.2rem}.hero p{color:#d7edf4;margin:6px 0 0}.smallnote{color:#6b7280;font-size:0.85rem}</style>''',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🏏 SupeRR Selector — Season 2</h1><p>Round 1 · Pressure Performance Intelligence · IPL & T20I</p></div>',unsafe_allow_html=True)
st.caption('Research dashboard based on supplied CSV analysis. Rankings are model-derived, not official competition results.')
ROOT=Path(__file__).parent
@st.cache_data
def load():
    return (pd.read_csv(ROOT/'batting_full_rankings.csv'),pd.read_csv(ROOT/'bowling_full_rankings.csv'))
try: bat,bowl=load()
except FileNotFoundError:
    st.error('Missing ranking CSVs. Keep batting_full_rankings.csv and bowling_full_rankings.csv alongside app.py.');st.stop()

with st.sidebar:
    st.header('Explore rankings')
    page=st.radio('Section',['Overview','Batters','Bowlers','Player comparison','Methodology'])
    st.divider()
    st.info('Unstop requires two ranked Top-10 lists and a methodology report. Dashboard hosting is optional.')

def chart(df,x,y,title,labels=None):
    fig=px.bar(df,x=x,y=y,orientation='h',title=title,labels=labels or {},color=y,color_continuous_scale='Blues')
    fig.update_layout(height=max(350,len(df)*36),coloraxis_showscale=False,margin=dict(l=10,r=15,t=55,b=15),yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig,use_container_width=True)

def table(df,kind):
    name='striker_name' if kind=='Batters' else 'bowler_name'
    cols=['rank',name,'score','balls_pressure','matches_pressure','pressure_rate','normal_rate','uplift','confidence']
    pretty={'rank':'Rank',name:'Player','score':'Final score','balls_pressure':'Pressure balls','matches_pressure':'Pressure matches','pressure_rate':'Pressure SR' if kind=='Batters' else 'Pressure economy','normal_rate':'Normal SR' if kind=='Batters' else 'Normal economy','uplift':'Uplift','confidence':'Confidence'}
    st.dataframe(df[cols].rename(columns=pretty).style.format({'Final score':'{:.2f}','Pressure SR' if kind=='Batters' else 'Pressure economy':'{:.2f}','Normal SR' if kind=='Batters' else 'Normal economy':'{:.2f}','Uplift':'{:+.2f}','Confidence':'{:.2f}'}),hide_index=True,use_container_width=True)

if page=='Overview':
    a,b,c,d=st.columns(4)
    a.metric('Matches with delivery data','867')
    b.metric('Delivery records','200,961')
    c.metric('Pressure delivery records','65,060')
    d.metric('Pressure share','32.4%')
    st.caption('Summary counts from the prior analysis run; ranking tables are loaded from the CSVs below.')
    left,right=st.columns(2)
    with left:
        st.subheader('🏏 Leading batters')
        chart(bat.head(10).iloc[::-1],'score','striker_name','Top 10 batting pressure scores',{'striker_name':'Batter','score':'Rating'})
    with right:
        st.subheader('🎯 Leading bowlers')
        chart(bowl.head(10).iloc[::-1],'score','bowler_name','Top 10 bowling pressure scores',{'bowler_name':'Bowler','score':'Rating'})
    st.warning('Batting and bowling ratings use different scales; do not compare their numeric scores directly.')
elif page in ['Batters','Bowlers']:
    isbat=page=='Batters';df=bat if isbat else bowl;name='striker_name' if isbat else 'bowler_name'
    st.header('Top 10 '+page)
    count=st.slider('Show top N',10,min(50,len(df)),10)
    view=df.head(count)
    table(view,page)
    chart(view.iloc[::-1],'score',name,'Pressure rating by player',{name:'Player','score':'Rating'})
    st.subheader('Pressure vs ordinary performance')
    melted=view[[name,'pressure_rate','normal_rate']].melt(id_vars=name,var_name='Situation',value_name='Rate')
    fig=px.bar(melted,x=name,y='Rate',color='Situation',barmode='group',labels={name:'Player','Rate':'Strike rate (runs per 100 balls)' if isbat else 'Economy (runs per over)'})
    fig.update_layout(xaxis_tickangle=-40)
    st.plotly_chart(fig,use_container_width=True)
    st.download_button('Download full '+page.lower()+' rankings',df.to_csv(index=False).encode(),file_name=page.lower()+'_full_rankings.csv',mime='text/csv')
elif page=='Player comparison':
    kind=st.radio('Role',['Batters','Bowlers'],horizontal=True)
    df=bat if kind=='Batters' else bowl;name='striker_name' if kind=='Batters' else 'bowler_name'
    names=df[name].tolist()
    p1,p2=st.columns(2)
    with p1: x=st.selectbox('Player A',names,index=0)
    with p2: y=st.selectbox('Player B',names,index=min(1,len(names)-1))
    selected=df[df[name].isin([x,y])].copy()
    st.subheader('Head-to-head metrics')
    table(selected,kind)
    fig=px.bar(selected,x=name,y=['pressure_rate','normal_rate'],barmode='group',title='Pressure vs normal',labels={'value':'Strike rate' if kind=='Batters' else 'Economy','variable':'Situation'})
    st.plotly_chart(fig,use_container_width=True)
    st.info('Player comparisons are descriptive and do not control for all differences in opponents, roles, or playing conditions.')
else:
    st.header('Methodology & reproducibility')
    st.markdown('''**Goal.** Compare each player’s performance in high-pressure deliveries against their own ordinary-delivery baseline.\n\n**Pressure flags (existing model).** A delivery is flagged when the match state meets one or more late-innings, required-run-rate, wicket-loss or close-chase criteria. The existing analysis is a heuristic, not a win-probability model.\n\n**Batting metrics.** Pressure strike rate, normal strike rate, uplift, boundary rate, dot-ball rate, adjusted rate, and a sample-size confidence factor.\n\n**Bowling metrics.** Pressure economy, normal economy, economy improvement, wickets per 100 legal balls, adjusted rate, and confidence factor.\n\n**Eligibility (existing model).** At least 80 pressure balls, 100 normal balls, and 6 pressure matches.\n\n**Caveats.** Wicket attribution, extras, revised targets, competition effects and match-level ranking stability need additional independent validation. Scores are not comparable across batting and bowling roles.\n\n**Source files.** The dashboard reads the precomputed `batting_full_rankings.csv` and `bowling_full_rankings.csv`; it does not rerun the raw ball-by-ball pipeline. See the methodology PDF for the complete model description.''')
    st.code('streamlit run app.py',language='bash')
st.divider()
st.caption('SupeRR Selector Season 2 | Round 1 | Independent data analysis dashboard')
