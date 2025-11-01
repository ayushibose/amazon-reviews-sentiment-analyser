import os
import requests
import pandas as pd
import streamlit as st
import altair as alt

API_URL = os.environ.get("API_URL", "https://amazon-reviews-sentiment-analyser-backend.onrender.com/")

st.set_page_config(page_title="Sentiment Dashboard", layout="wide")

# Load external CSS
with open(os.path.join(os.path.dirname(__file__), "dashboard.css")) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Altair light theme helper
def lightify(chart: alt.Chart) -> alt.Chart:
    return (
        chart
        .configure(background="transparent")
        .configure_axis(
            gridColor="rgba(0,0,0,0.08)",
            domainColor="rgba(0,0,0,0.20)",
            labelColor="#374151",
            titleColor="#111827",
        )
        .configure_legend(labelColor="#374151", titleColor="#111827")
        .configure_title(color="#111827")
    )

st.title("Analytics Dashboard")
st.caption("Analyze and compare reviews across multiple products in near real-time")

@st.cache_data(ttl=15)
def fetch_products(api_url: str):
    try:
        r = requests.get(f"{api_url}/products", timeout=10)
        r.raise_for_status()
        return r.json().get("products", [])
    except Exception as e:
        st.error(f"Failed to load products: {e}")
        return []

@st.cache_data(ttl=15)
def fetch_timeseries(api_url: str, asin: str):
    try:
        r = requests.get(f"{api_url}/timeseries/{asin}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed to load timeseries for {asin}: {e}")
        return None

@st.cache_data(ttl=15)
def fetch_country_sentiment(api_url: str, asin: str):
    try:
        r = requests.get(f"{api_url}/country_sentiment/{asin}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Failed to load country sentiment for {asin}: {e}")
        return None

# Sidebar settings
with st.sidebar:
    st.subheader("Settings")
    API_URL = st.text_input("API URL", API_URL)
    refresh = st.button("Refresh Data")
    st.markdown("---")
    st.caption("Keep the extension running while browsing to ingest reviews.")

products = fetch_products(API_URL)
if refresh:
    st.cache_data.clear()
    products = fetch_products(API_URL)

if not products:
    st.info("No products ingested yet. Open some Amazon product pages with the extension running.")
else:
    # KPIs
    df_products = pd.DataFrame(products)
    total_products = int(df_products.shape[0])
    total_reviews = int(df_products["review_count"].sum()) if total_products else 0
    most_recent = df_products["updated_at"].max() if total_products else "-"

    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown('<div class="kpi-card"><div class="kpi-label">Products Tracked</div><div class="kpi-value">{}</div></div>'.format(total_products), unsafe_allow_html=True)
    with k2:
        st.markdown('<div class="kpi-card"><div class="kpi-label">Total Reviews</div><div class="kpi-value">{}</div></div>'.format(total_reviews), unsafe_allow_html=True)
    with k3:
        st.markdown('<div class="kpi-card"><div class="kpi-label">Last Update (UTC)</div><div class="kpi-value">{}</div></div>'.format(most_recent or "-"), unsafe_allow_html=True)

    st.markdown("")

    # Selection
    asin_titles = {p["asin"]: p["title"] for p in products}
    asin = st.selectbox("Select product", options=list(asin_titles.keys()), format_func=lambda a: f"{asin_titles[a]} ({a})")

    def render_product_section(asin_value: str, header: str):
        st.subheader(header)
        ts = fetch_timeseries(API_URL, asin_value)
        if not ts:
            return
        labels = ts["labels"]
        df = pd.DataFrame({
            "Date": labels,
            "Positive": ts["positive"],
            "Neutral": ts["neutral"],
            "Negative": ts["negative"],
        })
        base = alt.Chart(df).encode(x=alt.X("Date:N", title="Date / Bucket"))
        chart = alt.layer(
            base.mark_line(color="#2ecc71", point=True).encode(y=alt.Y("Positive:Q", title="Count"), tooltip=["Date", "Positive"]),
            base.mark_line(color="#95a5a6", point=True).encode(y="Neutral:Q", tooltip=["Date", "Neutral"]),
            base.mark_line(color="#e74c3c", point=True).encode(y="Negative:Q", tooltip=["Date", "Negative"]),
        ).properties(height=280).interactive()
        st.altair_chart(lightify(chart), use_container_width=True)

    # Main tabs (no product comparison)
    tab1, tab2, tab3 = st.tabs(["Sentiment Distribution","Time Trends", "Country Analysis"])
    
    with tab3:
        st.subheader("Sentiment by Country of Origin")
        
        # Country analysis for selected product
        country_data = fetch_country_sentiment(API_URL, asin)
        if country_data and country_data["countries"]:
            # Create long format data for Altair
            countries = country_data["countries"]
            data_long = []
            for i, country in enumerate(countries):
                data_long.extend([
                    {"Country": country, "Sentiment": "Positive", "Count": country_data["positive"][i]},
                    {"Country": country, "Sentiment": "Neutral", "Count": country_data["neutral"][i]},
                    {"Country": country, "Sentiment": "Negative", "Count": country_data["negative"][i]}
                ])
            
            df_country_long = pd.DataFrame(data_long)
            
            # Stacked bar chart for country sentiment
            chart_country = alt.Chart(df_country_long).mark_bar().encode(
                x=alt.X("Country:N", title="Country"),
                y=alt.Y("Count:Q", title="Number of Reviews"),
                color=alt.Color("Sentiment:N", 
                              scale=alt.Scale(domain=["Positive", "Neutral", "Negative"], 
                                            range=["#2ecc71", "#95a5a6", "#e74c3c"])),
                tooltip=["Country", "Sentiment", "Count"]
            ).properties(height=350, title=f"Sentiment Distribution by Country - {asin_titles[asin]}")
            
            st.altair_chart(lightify(chart_country), use_container_width=True)
            
            # Country comparison table (wide format)
            df_country_wide = pd.DataFrame({
                "Country": country_data["countries"],
                "Positive": country_data["positive"],
                "Neutral": country_data["neutral"],
                "Negative": country_data["negative"]
            })
            
            st.subheader("Country Breakdown")
            st.dataframe(df_country_wide, use_container_width=True, hide_index=True)
        else:
            st.info("No country data available for this product.")
    
    with tab1:
        st.subheader("Sentiment Distribution & Confidence Analysis")
        
        # Get product data for sentiment analysis
        product_data = None
        for p in products:
            if p["asin"] == asin:
                product_data = p
                break
        
        if product_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**{asin_titles[asin]}**")
                # Sentiment distribution pie chart
                counts = product_data["counts"]
                total = sum(counts.values())
                
                if total > 0:
                    df_pie = pd.DataFrame({
                        "Sentiment": ["Positive", "Neutral", "Negative"],
                        "Count": [counts["POSITIVE"], counts["NEUTRAL"], counts["NEGATIVE"]],
                        "Percentage": [
                            round((counts["POSITIVE"] / total) * 100, 1),
                            round((counts["NEUTRAL"] / total) * 100, 1),
                            round((counts["NEGATIVE"] / total) * 100, 1)
                        ]
                    })
                    
                    pie_chart = alt.Chart(df_pie).mark_arc(innerRadius=0).encode(
                        theta=alt.Theta("Count:Q"),
                        color=alt.Color("Sentiment:N", 
                                      scale=alt.Scale(domain=["Positive", "Neutral", "Negative"], 
                                                    range=["#2ecc71", "#95a5a6", "#e74c3c"])),
                        tooltip=["Sentiment", "Count", "Percentage"]
                    ).properties(height=300, title="Sentiment Distribution")
                    
                    st.altair_chart(lightify(pie_chart), use_container_width=True)
                else:
                    st.info("No sentiment data available")
            
            with col2:
                # Average confidence (mock data for now - would need to calculate from individual reviews)
                st.markdown("**Confidence Analysis**")
                
                # Create mock confidence data based on review count
                confidence_data = {
                    "Metric": ["Average Confidence", "High Confidence (>80%)", "Medium Confidence (60-80%)", "Low Confidence (<60%)"],
                    "Count": [total, int(total * 0.3), int(total * 0.5), int(total * 0.2)],
                    "Percentage": [75, 30, 50, 20]
                }
                
                df_conf = pd.DataFrame(confidence_data)
                
                conf_chart = alt.Chart(df_conf).mark_bar().encode(
                    x=alt.X("Metric:N", title="Confidence Level"),
                    y=alt.Y("Percentage:Q", title="Percentage"),
                    color=alt.Color("Metric:N", scale=alt.Scale(range=["#3498db", "#2ecc71", "#f39c12", "#e74c3c"])),
                    tooltip=["Metric", "Count", "Percentage"]
                ).properties(height=300, title="Confidence Distribution")
                
                st.altair_chart(lightify(conf_chart), use_container_width=True)
                
                # Summary stats
                st.markdown("**Summary Statistics**")
                st.metric("Total Reviews", total)
                st.metric("Positive Rate", f"{round((counts['POSITIVE'] / total) * 100, 1)}%" if total > 0 else "0%")
                st.metric("Negative Rate", f"{round((counts['NEGATIVE'] / total) * 100, 1)}%" if total > 0 else "0%")
        else:
            st.error("Product data not found")
    
    with tab2:
        st.subheader("Sentiment Trends Over Time")
        
        # Individual time trends for selected product
        ts = fetch_timeseries(API_URL, asin)
        if ts and ts["labels"]:
            st.markdown(f"**{asin_titles[asin]}**")
            
            # Create time series data (wide -> long for cleaner legend and styling)
            df_time = pd.DataFrame({
                "Date": ts["labels"],
                "Positive": ts["positive"],
                "Neutral": ts["neutral"],
                "Negative": ts["negative"]
            })
            df_time_long = df_time.melt("Date", var_name="Sentiment", value_name="Value")
            # Coerce dates to temporal axis by parsing to pandas datetime where possible
            try:
                df_time_long["DateParsed"] = pd.to_datetime(df_time_long["Date"], errors="coerce")
            except Exception:
                df_time_long["DateParsed"] = pd.NaT

            color_scale = alt.Scale(
                domain=["Positive", "Negative", "Neutral"],
                range=["#2ecc71", "#e74c3c", "#bdc3c7"],
            )

            # Filled areas under Positive and Negative for emphasis
            area_positive = (
                alt.Chart(df_time_long)
                .transform_filter(alt.datum.Sentiment == "Positive")
                .mark_area(opacity=0.15, color="#2ecc71")
                .encode(
                    x=alt.X("DateParsed:T", title="Date", axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y("Value:Q", title="Number of Reviews"),
                )
            )
            area_negative = (
                alt.Chart(df_time_long)
                .transform_filter(alt.datum.Sentiment == "Negative")
                .mark_area(opacity=0.15, color="#e74c3c")
                .encode(
                    x=alt.X("DateParsed:T", title="Date", axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y("Value:Q", title="Number of Reviews"),
                )
            )

            # Lines with open circle points for all three series
            lines_points = (
                alt.Chart(df_time_long)
                .mark_line(point=alt.OverlayMarkDef(filled=False, fillOpacity=0), strokeWidth=2)
                .encode(
                    x=alt.X("DateParsed:T", title="Date", axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y("Value:Q", title="Number of Reviews"),
                    color=alt.Color("Sentiment:N", scale=color_scale, legend=alt.Legend(orient="bottom")),
                    tooltip=["Date", "Sentiment", "Value"],
                )
            )

            chart_time = (area_positive + area_negative + lines_points).properties(height=320, title="Sentiment Trends Over Time").interactive()

            st.altair_chart(lightify(chart_time), use_container_width=True)
            
            # Time series summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Peak Positive", max(ts["positive"]) if ts["positive"] else 0)
            with col2:
                st.metric("Peak Neutral", max(ts["neutral"]) if ts["neutral"] else 0)
            with col3:
                st.metric("Peak Negative", max(ts["negative"]) if ts["negative"] else 0)
        else:
            st.info("No time series data available for this product")

    st.divider()
    st.subheader("Products Summary")
    pretty = df_products[["asin", "title", "review_count", "updated_at"]].rename(columns={
        "asin": "ASIN", "title": "Title", "review_count": "Reviews", "updated_at": "Updated (UTC)"
    })
    st.dataframe(pretty, use_container_width=True, hide_index=True)

st.caption("By Ayushi Bose")