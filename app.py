import re
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

st.set_page_config(page_title="YouTube Growth Toolkit", page_icon="📈", layout="wide")
st.title("📈 YouTube Growth Toolkit")
st.caption("Analytics • Topic research • SEO drafts • Thumbnail concepts • Content calendar")
SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly"]

def oauth_config():
    g = st.secrets.get("google", {})
    for k in ("client_id", "client_secret", "redirect_uri"):
        if not g.get(k):
            st.error(f"Missing [google].{k} in Streamlit Secrets")
            st.stop()
    return {"web": {"client_id": g["client_id"], "client_secret": g["client_secret"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [g["redirect_uri"]]}}

def flow_for(state=None):
    f = Flow.from_client_config(oauth_config(), scopes=SCOPES, state=state)
    f.redirect_uri = st.secrets["google"]["redirect_uri"]
    return f

def data_api():
    key = st.secrets.get("youtube_data", {}).get("api_key", "")
    return build("youtube", "v3", developerKey=key, cache_discovery=False) if key else None

def words(s):
    return [w for w in re.findall(r"[A-Za-z0-9\u0900-\u097F]+", s.lower()) if len(w) > 2]

def title_ideas(topic, fmt, audience):
    if fmt == "Shorts":
        return [f"{topic} 🙏 #Shorts", f"{topic}: A Moment to Remember #Shorts",
                f"Watch This: {topic} #Shorts", f"{topic} in 30 Seconds #Shorts",
                f"Start Your Day with {topic} ✨ #Shorts"]
    return [f"{topic} | Complete Guide for {audience}", f"{topic}: Meaning and Highlights",
            f"{topic} Explained Simply | Full Video", f"Everything to Know About {topic}",
            f"{topic} | Step-by-Step Guide"]

def description(topic, audience, fmt):
    hashtags = " ".join("#" + w for w in dict.fromkeys(words(topic)[:3]))
    return f"{topic}\n\nIn this video, we explore {topic} for {audience}. Watch till the end and share your thoughts in the comments.\n\nSubscribe for more relevant videos. Verify all facts before publishing.\n\n{hashtags} {'#Shorts' if fmt == 'Shorts' else '#YouTube'}"

def calendar(topics, start, gap, formats):
    items = [x.strip() for x in topics.splitlines() if x.strip()]
    if not items:
        items = ["Audience question", "Follow-up to a best-performing video", "New topic in your niche"]
    return pd.DataFrame([{
        "Publish date": (start + timedelta(days=i * gap)).isoformat(),
        "Format": formats[i % len(formats)],
        "Topic / working title": t,
        "Hook idea": f"Open with the clearest benefit or most interesting moment about: {t}",
        "CTA": "Ask one relevant question or suggest a related video",
        "Status": "Idea"
    } for i, t in enumerate(items)])

if "credentials" not in st.session_state:
    st.session_state.credentials = None

p = st.query_params
if p.get("error"):
    st.error("Google authorization was not completed: " + str(p.get("error")))
elif p.get("code"):
    expected, returned = st.session_state.get("oauth_state"), p.get("state")
    if not expected or not returned or expected != returned:
        st.error("OAuth state validation failed. Clear URL parameters and reconnect.")
    else:
        try:
            f = flow_for(expected)
            f.fetch_token(code=p.get("code"))
            st.session_state.credentials = f.credentials
            st.session_state.pop("oauth_state", None)
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error("OAuth failed. Check the redirect URI and Google OAuth settings.")
            st.code(str(e))

with st.sidebar:
    st.header("Channel connection")
    if st.button("Connect Google / reconnect", type="primary"):
        f = flow_for()
        url, state = f.authorization_url(access_type="offline", include_granted_scopes="true", prompt="consent")
        st.session_state.oauth_state = state
        st.link_button("Continue to Google authorization", url)
    st.caption("Read-only analytics for the channel you authorize.")
    st.divider()
    st.header("Analytics range")
    end = date.today() - timedelta(days=2)
    start = st.date_input("Start date", end - timedelta(days=27))
    finish = st.date_input("End date", end)

tabs = st.tabs(["📊 Analytics", "🔥 Topic Research", "✍️ SEO Helper", "🖼️ Thumbnail Ideas", "🗓️ Content Planner"])

with tabs[0]:
    st.subheader("Channel performance")
    creds = st.session_state.credentials
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            st.session_state.credentials = None
            creds = None
            st.warning("Session expired. Reconnect from the sidebar.")
    if not creds:
        st.info("Connect Google in the sidebar to view analytics. Other tabs work without connecting.")
    elif start > finish:
        st.error("Start date must be on or before end date.")
    else:
        try:
            api = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
            res = api.reports().query(ids="channel==MINE", startDate=start.isoformat(), endDate=finish.isoformat(),
                metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained",
                dimensions="day", sort="day").execute()
            if not res.get("rows"):
                st.warning("No analytics returned. Try another date range or check channel permissions.")
            else:
                df = pd.DataFrame(res["rows"], columns=["Date","Views","Watch time (minutes)","Avg view duration (seconds)","Avg viewed (%)","Subscribers gained"])
                df["Date"] = pd.to_datetime(df["Date"])
                for c in df.columns[1:]:
                    df[c] = pd.to_numeric(df[c], errors="coerce")
                views = int(df.Views.sum())
                hours = df["Watch time (minutes)"].sum() / 60
                avg = ((df["Avg view duration (seconds)"] * df.Views).sum() / views) if views else 0
                a,b,c,d = st.columns(4)
                a.metric("Views", f"{views:,}")
                b.metric("Estimated watch hours", f"{hours:,.1f}")
                c.metric("Weighted avg duration", f"{int(avg//60)}m {int(avg%60)}s")
                d.metric("Subscribers gained", f"{int(df['Subscribers gained'].sum()):,}")
                x,y = st.columns(2)
                x.line_chart(df.set_index("Date")[["Views"]])
                y.bar_chart(df.set_index("Date")[["Watch time (minutes)"]])
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.download_button("Download analytics CSV", df.to_csv(index=False).encode(), "youtube_analytics.csv", "text/csv")
                st.caption("Use YouTube Studio to compare Shorts and long-form retention separately.")
        except Exception as e:
            st.error("Analytics failed. Check API enablement, OAuth settings, permissions, and date range.")
            st.code(str(e))

with tabs[1]:
    st.subheader("Public YouTube topic research")
    st.write("Search videos in your niche and compare public titles, upload dates and available engagement counts. This is research, not a viral guarantee.")
    niche = st.text_input("Niche / search phrase", placeholder="e.g. Hanuman bhajan, SSC CGL preparation")
    region = st.selectbox("Region", ["IN","US","GB","CA","AU"])
    lang = st.selectbox("Language", ["Any","Hindi","English"])
    if st.button("Research topics"):
        yt = data_api()
        if not yt:
            st.warning("Add a YouTube Data API key to Streamlit Secrets; see README.")
        elif not niche.strip():
            st.warning("Enter a topic first.")
        else:
            try:
                args = dict(part="snippet", q=niche.strip(), type="video", maxResults=15, regionCode=region, order="relevance")
                if lang == "Hindi": args["relevanceLanguage"] = "hi"
                if lang == "English": args["relevanceLanguage"] = "en"
                found = yt.search().list(**args).execute().get("items", [])
                ids = [v["id"]["videoId"] for v in found if v.get("id",{}).get("videoId")]
                details = yt.videos().list(part="snippet,statistics", id=",".join(ids)).execute().get("items", []) if ids else []
                rows = []
                for v in details:
                    sn, stt = v.get("snippet",{}), v.get("statistics",{})
                    rows.append({"Title":sn.get("title",""),"Channel":sn.get("channelTitle",""),"Published":sn.get("publishedAt","")[:10],
                        "Views":int(stt.get("viewCount",0)),"Likes":int(stt["likeCount"]) if "likeCount" in stt else None,
                        "Comments":int(stt["commentCount"]) if "commentCount" in stt else None,
                        "Video URL":"https://www.youtube.com/watch?v="+v["id"]})
                if rows:
                    df = pd.DataFrame(rows).sort_values("Views", ascending=False)
                    st.dataframe(df, use_container_width=True, hide_index=True, column_config={"Video URL":st.column_config.LinkColumn("Video URL")})
                    st.download_button("Download topic research CSV", df.to_csv(index=False).encode(), "topic_research.csv", "text/csv")
                else: st.info("No videos found. Try a broader phrase.")
                st.caption("Public counts and search order change over time; high views do not guarantee your video will perform similarly.")
            except Exception as e:
                st.error("Topic research failed. Check the Data API key, quota and API enablement.")
                st.code(str(e))

with tabs[2]:
    st.subheader("SEO title and description drafts")
    topic = st.text_input("Main topic / keyword", key="seo_topic", placeholder="e.g. Hanuman Chalisa")
    audience = st.text_input("Target audience", value="Hindi-speaking viewers", key="seo_audience")
    fmt = st.radio("Video format", ["Shorts","Long video"], horizontal=True)
    if st.button("Generate SEO drafts"):
        if not topic.strip(): st.warning("Enter a topic first.")
        else:
            st.markdown("**Title ideas**")
            for i, t in enumerate(title_ideas(topic,fmt,audience), 1):
                st.write(f"{i}. {t}")
            st.text_area("Draft description", description(topic,audience,fmt), height=180)
            st.caption("Template-based suggestions only; no live keyword volume is measured. Avoid misleading titles and keyword stuffing.")

with tabs[3]:
    st.subheader("Thumbnail concept helper")
    topic = st.text_input("Video topic", key="thumbnail_topic", placeholder="e.g. Panchmukhi Hanuman")
    style = st.radio("Artwork use", ["Long-video thumbnail","Shorts cover"], horizontal=True)
    if st.button("Suggest thumbnail concepts"):
        if not topic.strip(): st.warning("Enter a topic first.")
        else:
            ideas = [
                ("One focal point", f"Use one strong visual representing {topic}; keep the background uncluttered."),
                ("Emotion / curiosity", "Choose one expressive moment or question, without misleading viewers."),
                ("High contrast", "Use 2–3 contrasting colours and clear separation between subject and background."),
                ("Minimal text", "If text is needed, use 2–4 short words and make them readable on a phone."),
                ("Consistent style", "Repeat a recognizable colour palette and visual style across related videos.")
            ]
            for title, detail in ideas:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.write(detail)
            st.caption("This tab generates design directions, not an actual image file. Keep the thumbnail faithful to the video's content.")

with tabs[4]:
    st.subheader("Downloadable content calendar")
    topics = st.text_area("One topic per line", "One strong devotional story\nAnswer a common audience question\nFollow-up to a best-performing video", height=130)
    plan_start = st.date_input("Planning starts", date.today(), key="calendar_start")
    gap = st.selectbox("Days between planned posts", [1,2,3,4,7], index=2)
    formats = st.multiselect("Formats to rotate", ["Shorts","Long video","Community post"], ["Shorts","Long video"])
    if st.button("Build content calendar"):
        if not formats: st.warning("Choose at least one format.")
        else:
            df = calendar(topics, plan_start, gap, formats)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("Download calendar CSV", df.to_csv(index=False).encode(), "youtube_content_calendar.csv", "text/csv")

st.divider()
st.caption("This toolkit helps with analysis and planning. It does not automate playback, create fake engagement, or guarantee views, watch time or virality.")
