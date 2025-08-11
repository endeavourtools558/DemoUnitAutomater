def Run_Demounit_report_scrapper(uploaded_file):
    import streamlit as st
    import pandas as pd
    import altair as alt
    from io import BytesIO
    from datetime import datetime

    # --- SPACE FUNCTION ---
    def add_space(lines=1):
        for _ in range(lines):
            st.write(" ")

    # --- CONFIGURE PAGE ---
    st.set_page_config(page_title="Monthly Demo Unit Report", layout="wide")

    # --- BRAND COLORS ---
    primary_color = "#003366"  # Endeavour Tools navy blue
    accent_green = "#2ecc71"
    accent_orange = "#f39c12"

    if uploaded_file:
        # --- LOAD & CLEAN DATA ---
        df = pd.read_excel(uploaded_file, sheet_name="DEMO UNIT HISTORICAL DATA", skiprows=1)
        df.dropna(subset=["STATUS", "LOCATION", "DATE OUT"], inplace=True)

        df["STATUS"] = df["STATUS"].astype(str).str.strip().str.title()
        df["END USER STATE"] = df["END USER STATE"].astype(str).str.strip().str.upper()
        df["DATE OUT"] = pd.to_datetime(df["DATE OUT"], errors="coerce")

        # --- Generate proper Month-Year labels and sort chronologically ---
        month_periods = df["DATE OUT"].dropna().dt.to_period("M").unique()
        month_periods = sorted(month_periods, key=lambda x: x.start_time)  # earliest to latest
        month_labels = [p.strftime("%b %Y") for p in month_periods]

        selected_month = st.selectbox("📅 Select Month/Year", month_labels)
        filtered = df[df["DATE OUT"].dt.strftime("%b %Y") == selected_month]

        # --- KPI SUMMARY ---
        st.markdown(f"### Key Metrics for {selected_month}")
        kpi_style = "background-color:#f8f9fa; border:1px solid #ddd; border-radius:6px; padding:15px; text-align:center;"

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.markdown(f"<div style='{kpi_style}'><h2>{len(filtered)}</h2><p>Total Units</p></div>", unsafe_allow_html=True)
        col2.markdown(f"<div style='{kpi_style}'><h2>{(filtered['STATUS']=='Sold').sum()}</h2><p>Sold Units</p></div>", unsafe_allow_html=True)
        col3.markdown(f"<div style='{kpi_style}'><h2>{(filtered['STATUS']=='Pending').sum()}</h2><p>Pending Units</p></div>", unsafe_allow_html=True)
        col4.markdown(f"<div style='{kpi_style}'><h2>{filtered['RETAILER'].nunique()}</h2><p>Retailers</p></div>", unsafe_allow_html=True)
        col5.markdown(f"<div style='{kpi_style}'><h2>{filtered['END USER STATE'].nunique()}</h2><p>States</p></div>", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # --- DETAILED DATA TABLE ---
        st.markdown(f"### Detailed Records ({selected_month})")
        st.dataframe(
            filtered[["SKU", "MODEL", "LOCATION", "STATUS", "RETAILER", "END USER STATE"]],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("<hr>", unsafe_allow_html=True)

        # --- CHARTS SECTION (BOTH ALTAIR) ---
        col_left, col_right = st.columns(2)

        # --- Status Breakdown Chart ---
        status_counts = filtered["STATUS"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        status_colors = {"Sold": accent_green, "Pending": accent_orange}

        status_chart = alt.Chart(status_counts).mark_bar(size=50).encode(
            x=alt.X("Status:N", sort="-y", title="Status"),
            y=alt.Y("Count:Q", title="Units"),
            color=alt.Color("Status:N", scale=alt.Scale(domain=list(status_colors.keys()), range=list(status_colors.values()))),
            tooltip=["Status", "Count"]
        ).properties(
            width='container',
            height=350
        ).configure_axis(grid=False).configure_view(strokeWidth=0)

        with col_left:
            st.markdown("<div style='text-align: center; font-size: 1.5em; font-weight: bold;'>Units by Status</div>",
                        unsafe_allow_html=True)
            st.altair_chart(status_chart, use_container_width=True)

        # --- State Breakdown Chart ---
        location_counts = filtered["END USER STATE"].value_counts().reset_index()
        location_counts.columns = ["State", "Count"]
        state_colors = {
            "NSW": "#1f77b4", "VIC": "#ff7f0e", "QLD": "#2ca02c", "SA": "#d62728",
            "WA": "#9467bd", "TAS": "#8c564b", "NT": "#e377c2", "ACT": "#7f7f7f"
        }

        state_chart = alt.Chart(location_counts).mark_bar(size=35).encode(
            x=alt.X("State:N", sort="-y", title="State"),
            y=alt.Y("Count:Q", title="Units"),
            color=alt.Color("State:N", scale=alt.Scale(domain=list(state_colors.keys()), range=list(state_colors.values()))),
            tooltip=["State", "Count"]
        ).properties(
            width='container',
            height=350
        ).configure_axis(grid=False).configure_view(strokeWidth=0)

        with col_right:
            st.markdown("<div style='text-align: center; font-size: 1.5em; font-weight: bold;'>Units by State</div>",
                        unsafe_allow_html=True)
            st.altair_chart(state_chart, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # --- RETAILER OF THE MONTH ---
        st.markdown("### 🏆 Retailer of the Month")
        sold_units = filtered[filtered["STATUS"] == "Sold"]

        if not sold_units.empty:
            top_retailer = (
                sold_units.groupby("RETAILER")
                .size()
                .reset_index(name="Units Sold")
                .sort_values("Units Sold", ascending=False)
                .iloc[0]
            )

            st.markdown(
                f"""
                <div style="background-color:#f0fdf4; padding:20px; border-left:6px solid {accent_green};
                            border-radius:8px; margin-bottom:20px;">
                    <h3 style="margin:0;">{top_retailer['RETAILER']}</h3>
                    <p style="margin:5px 0;">Top retailer for {selected_month}!</p>
                    <p style="font-size:20px; color:{primary_color}; margin:0;"><b>{int(top_retailer['Units Sold'])} Units Sold</b></p>
                </div>
                """, unsafe_allow_html=True
            )
        else:
            st.info("No sold units this month. Retailer of the Month not awarded.")

        st.markdown("<hr>", unsafe_allow_html=True)

        # --- DOWNLOAD SECTION ---
        st.markdown("### 📥 Download Filtered Report")
        towrite = BytesIO()
        filtered.to_excel(towrite, index=False, sheet_name="Filtered Report")
        towrite.seek(0)

        st.download_button(
            label="Download Excel Report",
            data=towrite,
            file_name=f"Demo_Report_{selected_month}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
