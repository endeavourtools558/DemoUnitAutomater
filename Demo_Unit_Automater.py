def Run_Demo_Unit_Automater(uploaded_file):
    import streamlit as st
    import pandas as pd
    from datetime import timedelta
    import plotly.express as px
    import pydeck as pdk
    import numpy as np

    # --- PAGE CONFIG ---
    st.set_page_config(page_title="Demo Unit Dashboard", layout="wide", page_icon="📊")

    # --- HEADER ---
    st.markdown("<h1 style='color:#003366;'>Endeavour Tools - Demo Unit Dashboard</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#555;'>Generated on: {pd.Timestamp('today').strftime('%B %d, %Y')}</p>", unsafe_allow_html=True)
    st.write("---")

    if uploaded_file:
        # --- Load Data ---
        df = pd.read_excel(uploaded_file, sheet_name="REMOTE DEMO UNITS", skiprows=1)

        # Remove blank rows
        def is_row_empty(row):
            return all(pd.isna(cell) or (isinstance(cell, str) and cell.strip() == "") for cell in row)

        blank_indices = [idx for idx, row in df.iterrows() if is_row_empty(row)]
        if blank_indices:
            df = df.iloc[:blank_indices[0]] if blank_indices[0] > 0 else df.iloc[0:0]

        if 'SKU' in df.columns:
            df = df[df['SKU'] == 'ET2608']

        # Convert date columns
        date_cols = ['DATE OUT', 'EXPIRY', 'LAST UPDATED']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        today = pd.Timestamp('today').normalize()

        # --- KPI METRICS ---
        total_units = len(df)
        onsite_units = df[df['STATUS'] == 'ONSITE'] if 'STATUS' in df.columns else pd.DataFrame()
        mel_units = df[df['STATUS'] == 'MEL OFFICE'] if 'STATUS' in df.columns else pd.DataFrame()
        expiring_soon = df[df['EXPIRY'].notnull() & (df['EXPIRY'] <= today + timedelta(days=30))] if 'EXPIRY' in df.columns else pd.DataFrame()
        overdue_expiry = df[df['EXPIRY'].notnull() & (df['EXPIRY'] < today)] if 'EXPIRY' in df.columns else pd.DataFrame()

        # --- Dynamic KPI Squares ---
        st.write("### Dashboard Overview")
        kpi_style = """
            background-color: #f8f9fa;
            border: 1px solid #ddd;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.05);
        """
        number_style = "font-size: 2.5em; font-weight: bold; color: #003366; margin:0;"
        label_style = "font-size: 1em; color: #555; margin:0;"

        standard_colour = "#082426"
        accent_colors = {
            'ONSITE':  standard_colour,
            'MEL OFFICE':standard_colour,
            'INTERIM': standard_colour,
            'INBOUND': standard_colour,
            'IN TRANSIT': standard_colour,
            'OUTBOUND': standard_colour,
            'TOTAL UNITS':standard_colour
        }

        # Count all statuses
        status_counts = df['STATUS'].value_counts().to_dict()
        status_counts['TOTAL UNITS'] = total_units

        cols = st.columns(min(6, len(status_counts)))
        for i, (label, count) in enumerate(status_counts.items()):
            col = cols[i % len(cols)]
            color = accent_colors.get(label.upper(), standard_colour)
            col.markdown(
                f"<div style='{kpi_style}'>"
                f"<p style='{number_style}; color:{color};'>{count}</p>"
                f"<p style='{label_style}'>{label.title()} Units</p>"
                f"</div>",
                unsafe_allow_html=True
            )
        st.write("---")

        # You can leave the rest of your code unchanged
        # Overdue Expiry Table, Visual Insights, Tabs, Map, and Export CSV

        # [ ... keep the rest of your app unchanged here ... ]


        # --- Overdue Breakdown ---
        red_listed_cols = ['STATUS', 'END USER STATE', 'RETAILER']
        st.write("#### Overdue Expiry Breakdown by Key Columns")
        for col in red_listed_cols:
            if col in overdue_expiry.columns and not overdue_expiry.empty:
                st.write(f"**By {col}:**")
                counts = overdue_expiry[col].value_counts().head(10)
                st.table(counts.to_frame().reset_index().rename(columns={col: col, col: 'Count'}))
        st.write("---")

        # --- Charts ---
        onsite_df = onsite_units.copy()
        state_options = onsite_df['END USER STATE'].dropna().unique() if 'END USER STATE' in onsite_df.columns else []
        selected_states = st.multiselect("Filter charts by End User State (ONSITE units)", options=state_options, default=state_options)
        filtered_onsite = onsite_df[onsite_df['END USER STATE'].isin(selected_states)] if selected_states else onsite_df

        st.write("### 📊 Visual Insights")
        col1, col2 = st.columns(2)
        with col1:
            if not filtered_onsite.empty:
                state_counts = filtered_onsite['END USER STATE'].value_counts().reset_index()
                state_counts.columns = ['End User State', 'Count']
                fig_state = px.pie(state_counts, names='End User State', values='Count',
                                   title='ONSITE Demo Units by State', hole=0.4,
                                   color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_state, use_container_width=True)
        with col2:
            if not filtered_onsite.empty:
                retailer_counts = filtered_onsite['RETAILER'].value_counts().head(10).reset_index()
                retailer_counts.columns = ['Retailer', 'Units']
                fig_retailer = px.bar(retailer_counts, x='Retailer', y='Units',
                                      title='Top 10 Retailers (ONSITE)',
                                      color='Units', color_continuous_scale='Blues')
                st.plotly_chart(fig_retailer, use_container_width=True)
        st.write("---")

        # --- Tabs (Tracker, MEL, Expiry, Map) ---
        tab1, tab2, tab3, tab4 = st.tabs(["📍 ONSITE Tracker", "🏢 MEL OFFICE", "⏰ Expiry Reminders", "🗺️ Map View"])

        # TAB 1: ONSITE Tracker
        with tab1:
            if not onsite_units.empty:
                df_onsite = onsite_units.copy()
                df_onsite = df_onsite[df_onsite['DATE OUT'].notnull()]
                df_onsite['Days Out'] = (today - df_onsite['DATE OUT']).dt.days

                def return_status(days_out):
                    if days_out > 10: return "🔴 Overdue (10+ days)"
                    elif days_out >= 0: return f"🟢 {10 - days_out} days remaining"
                    else: return "🟢 Not yet out"

                df_onsite['Return Status'] = df_onsite['Days Out'].apply(return_status)

                def highlight_overdue(row): return ['background-color:#FFCCCC' if row['Days Out'] > 10 else '' for _ in row]

                st.subheader("ONSITE Demo Units (10-Day Return Policy)")
                st.dataframe(df_onsite[['RETAILER', 'REMARKS', 'DATE OUT', 'Days Out', 'Return Status', 'STATUS', 'END USER STATE']].style.apply(highlight_overdue, axis=1))
            else:
                st.info("No ONSITE units to display.")

        # TAB 2: MEL OFFICE
        with tab2:
            st.subheader("Demo Units in MEL OFFICE")
            if not mel_units.empty:
                mel_df = mel_units.copy()
                search_term = st.text_input("Search Retailer or Model", "")
                if search_term:
                    mel_df = mel_df[
                        mel_df['RETAILER'].str.contains(search_term, case=False, na=False) |
                        mel_df['MODEL'].str.contains(search_term, case=False, na=False)
                    ]
                st.dataframe(mel_df[['SKU', 'MODEL', 'RETAILER', 'DATE OUT', 'STATUS', 'END USER STATE', 'NOTES']])
            else:
                st.info("No demo units in MEL OFFICE.")

        # TAB 3: Expiry Reminders
        with tab3:
            st.subheader("Upcoming Expiry Dates")
            days_ahead = st.slider("Show units expiring within X days", 0, 60, 14)
            upcoming = df[df['EXPIRY'].notnull() & (df['EXPIRY'] <= today + timedelta(days=days_ahead))]

            def expiry_color(row):
                if pd.isna(row['EXPIRY']): return [''] * len(row)
                if row['EXPIRY'] < today: return ['background-color:#FFC7CE'] * len(row)
                elif row['EXPIRY'] <= today + timedelta(days=7): return ['background-color:#FFEB9C'] * len(row)
                else: return [''] * len(row)

            if not upcoming.empty:
                st.dataframe(upcoming[['SKU', 'MODEL', 'RETAILER', 'EXPIRY', 'STATUS', 'END USER STATE', 'NOTES']].style.apply(expiry_color, axis=1))
            else:
                st.info("No units expiring in the selected timeframe.")
            if not overdue_expiry.empty:
                st.warning(f"🚨 {len(overdue_expiry)} units are PAST their expiry date!")

    
        # TAB 4: Map View
        # --- TAB 4: Map of All Demo Units ---
        # --- TAB 4: Map of All Demo Units ---
        with tab4:
            st.subheader("📍 Map of All Demo Units")

        
            # Define base coordinates for Australian states (approximate centers)
            state_coords = {
                'VIC': [-37.8136, 144.9631],
                'NSW': [-33.8688, 151.2093],
                'QLD': [-27.4698, 153.0251],
                'SA': [-34.9285, 138.6007],
                'WA': [-31.9505, 115.8605],
                'TAS': [-42.8821, 147.3272],
                'NT': [-12.4634, 130.8456],
                'ACT': [-35.2809, 149.1300]
            }

            # Color mapping for statuses
            status_colors = {
                'ONSITE': 'red',
                'ONSITE - DEMO DONE': 'orange',
                'PENDING': 'blue',
                'SOLD': 'green',
                'INTERIM': 'purple',
                'OUTBOUND': 'pink',
                'QLD': 'cyan',
                'LOST SALE': 'black',
                'OTHER': 'gray'
            }

            # Assign jittered coordinates
            def assign_coords(row):
                status = str(row['STATUS']).upper()
                end_state = str(row.get('END USER STATE', 'VIC')).upper()
                base_coords = state_coords.get(end_state, state_coords['VIC']) \
                    if status in ['ONSITE', 'ONSITE - DEMO DONE'] else state_coords['VIC']

                # Larger jitter (spread more) for clarity
                lat_jitter = np.random.uniform(-0.6, 0.6)
                lon_jitter = np.random.uniform(-0.6, 0.6)
                return [base_coords[0] + lat_jitter, base_coords[1] + lon_jitter]

            df['coords'] = df.apply(assign_coords, axis=1)
            df[['lat', 'lon']] = pd.DataFrame(df['coords'].tolist(), index=df.index)

            # Assign colors
            df['color'] = df['STATUS'].apply(lambda x: status_colors.get(str(x).upper(), status_colors['OTHER']))

            # Hover info
            df['hover_info'] = df.apply(
                lambda row: f"Serial: {row.get('SERIAL NUMBER (TABLET)', 'N/A')}<br>Remarks: {row.get('REMARKS', '')}<br>Status: {row.get('STATUS', '')}",
                axis=1
            )

            # Plot the map
            fig_map = px.scatter_mapbox(
                df,
                lat='lat',
                lon='lon',
                hover_name='hover_info',
                color='color',
                color_discrete_map="identity",
                size=[12] * len(df),  # Bigger dots (fixed size for all)
                zoom=3,
                height=600
            )

            # Style map
            fig_map.update_layout(
                mapbox_style="carto-positron",
                mapbox_center={"lat": -25, "lon": 135},
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                showlegend=False
            )

            st.plotly_chart(fig_map, use_container_width=True)




        # --- Export CSV ---
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Full Dataset (CSV)", data=csv, file_name="demo_units_export.csv", mime="text/csv")
