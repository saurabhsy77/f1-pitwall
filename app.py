import os
import fastf1
from fastf1 import utils
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

os.makedirs('cache', exist_ok=True)
fastf1.Cache.enable_cache('cache')

st.set_page_config(page_title="F1 Pit Wall Dashboard", layout="wide", page_icon="🏁")

PLOTLY_TEMPLATE = "plotly_dark"
COMPOUND_COLORS = {
    'SOFT': '#DA291C', 'MEDIUM': '#FFD700', 'HARD': '#F0F0F0',
    'INTERMEDIATE': '#43B02A', 'WET': '#0067B1'
}
DRIVER_COLORS = ['#E10600', '#00A3FF']

def format_laptime(td):
    if pd.isna(td):
        return "N/A"
    total_seconds = td.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = total_seconds - minutes * 60
    return f"{minutes}:{seconds:06.3f}"

st.title("🏁 F1 Pit Wall Dashboard")

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.header("📅 Session")

    years = list(range(2018, 2027))[::-1]
    year = st.selectbox("Year", years, index=0)

    @st.cache_data(show_spinner=False)
    def get_schedule(yr):
        schedule = fastf1.get_event_schedule(yr)
        return schedule[schedule['EventFormat'] != 'testing']

    schedule = get_schedule(year)
    race_names = schedule['EventName'].tolist()
    gp = st.selectbox("Grand Prix", race_names)

    session_type = st.selectbox("Session type", ["R", "Q", "FP1", "FP2", "FP3", "S"], index=0)

    load_button = st.button("🔄 Load Session", use_container_width=True)

    st.divider()
    st.header("👥 Drivers to Compare")
    driver1_slot = st.empty()
    driver2_slot = st.empty()

if "session" not in st.session_state:
    st.session_state.session = None

if load_button:
    with st.spinner(f"Loading {gp} {year} {session_type}..."):
        session = None
        last_error = None
        for attempt in range(2):
            try:
                session = fastf1.get_session(year, gp, session_type)
                session.load(laps=True, telemetry=True, weather=False, messages=False)
                if session.laps is not None and not session.laps.empty:
                    break
                else:
                    session = None
                    last_error = "Session loaded but returned no lap data."
            except Exception as e:
                last_error = str(e)
                session = None

        if session is not None:
            st.session_state.session = session
            st.session_state.session_label = f"{gp} {year} — {session_type}"
        else:
            st.error(f"Could not load this session after 2 attempts: {last_error}. Please try clicking Load Session again.")
            st.session_state.session = None

if st.session_state.session is not None:
    session = st.session_state.session
    drivers = sorted(session.laps['Driver'].unique())

    with st.sidebar:
        driver1 = driver1_slot.selectbox("Driver 1", drivers, index=0, key="d1")
        driver2 = driver2_slot.selectbox("Driver 2", drivers, index=min(1, len(drivers) - 1), key="d2")

    st.subheader(f"📊 {st.session_state.session_label}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏎️ Telemetry Comparison", "🛞 Tyre Degradation", "📈 Track Evolution", "📋 Lap Times", "🗺️ Track Map"])

    # ---------------- TAB 1: TELEMETRY ----------------
    with tab1:
        lap1 = session.laps.pick_drivers(driver1).pick_fastest()
        lap2 = session.laps.pick_drivers(driver2).pick_fastest()

        tel1 = lap1.get_car_data().add_distance()
        tel2 = lap2.get_car_data().add_distance()
        delta_time, ref_tel, compare_tel = utils.delta_time(lap1, lap2)

        c1, c2 = st.columns(2)
        c1.metric(f"{driver1} lap time", format_laptime(lap1['LapTime']))
        c2.metric(f"{driver2} lap time", format_laptime(lap2['LapTime']))

        fig = make_subplots(
            rows=4, cols=1, shared_xaxes=True,
            row_heights=[0.3, 0.2, 0.15, 0.25],
            vertical_spacing=0.04,
            subplot_titles=("Speed (km/h)", "Throttle (%)", "Brake", f"Delta (s) — {driver2} vs {driver1}")
        )

        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Speed'], name=driver1,
                                  line=dict(color=DRIVER_COLORS[0]),
                                  hovertemplate='%{y:.0f} km/h<br>Dist: %{x:.0f}m<extra>' + driver1 + '</extra>'), row=1, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Speed'], name=driver2,
                                  line=dict(color=DRIVER_COLORS[1]),
                                  hovertemplate='%{y:.0f} km/h<br>Dist: %{x:.0f}m<extra>' + driver2 + '</extra>'), row=1, col=1)

        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Throttle'], name=driver1,
                                  line=dict(color=DRIVER_COLORS[0]), showlegend=False,
                                  hovertemplate='%{y:.0f}%<br>Dist: %{x:.0f}m<extra>' + driver1 + '</extra>'), row=2, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Throttle'], name=driver2,
                                  line=dict(color=DRIVER_COLORS[1]), showlegend=False,
                                  hovertemplate='%{y:.0f}%<br>Dist: %{x:.0f}m<extra>' + driver2 + '</extra>'), row=2, col=1)

        fig.add_trace(go.Scatter(x=tel1['Distance'], y=tel1['Brake'], name=driver1,
                                  line=dict(color=DRIVER_COLORS[0]), showlegend=False,
                                  hovertemplate='Brake: %{y}<br>Dist: %{x:.0f}m<extra>' + driver1 + '</extra>'), row=3, col=1)
        fig.add_trace(go.Scatter(x=tel2['Distance'], y=tel2['Brake'], name=driver2,
                                  line=dict(color=DRIVER_COLORS[1]), showlegend=False,
                                  hovertemplate='Brake: %{y}<br>Dist: %{x:.0f}m<extra>' + driver2 + '</extra>'), row=3, col=1)

        fig.add_trace(go.Scatter(x=ref_tel['Distance'], y=delta_time, name='Delta',
                                  line=dict(color='#B24BF3'), showlegend=False,
                                  hovertemplate='%{y:.3f}s<br>Dist: %{x:.0f}m<extra></extra>'), row=4, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=4, col=1)

        fig.update_layout(
            template=PLOTLY_TEMPLATE, height=850,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(t=60, b=40, l=60, r=20),
        )
        fig.update_yaxes(title_text="Speed (km/h)", row=1, col=1)
        fig.update_yaxes(title_text="Throttle (%)", row=2, col=1)
        fig.update_yaxes(title_text="Brake", row=3, col=1)
        fig.update_yaxes(title_text="Delta (s)", row=4, col=1)
        fig.update_xaxes(title_text="Distance around lap (m)", row=4, col=1)

        st.plotly_chart(fig, use_container_width=True)

    # ---------------- TAB 2: TYRE DEGRADATION ----------------
    with tab2:
        tyre_driver = st.selectbox("Driver for tyre analysis", drivers, index=0, key="tyre_driver")

        driver_laps = session.laps.pick_drivers(tyre_driver)
        if session_type in ["R", "S"]:
            driver_laps = driver_laps.pick_quicklaps()
        driver_laps = driver_laps.dropna(subset=['LapTime', 'Stint', 'TyreLife']).copy()
        driver_laps['LapTimeSeconds'] = driver_laps['LapTime'].dt.total_seconds()

        if driver_laps.empty:
            st.warning("No valid tyre-stint data for this driver/session (try a Race session).")
        else:
            fig2 = go.Figure()
            for stint_number in sorted(driver_laps['Stint'].unique()):
                stint_laps = driver_laps[driver_laps['Stint'] == stint_number].sort_values('TyreLife')
                if stint_laps.empty:
                    continue
                compound = stint_laps['Compound'].iloc[0]
                color = COMPOUND_COLORS.get(compound, '#888888')
                fig2.add_trace(go.Scatter(
                    x=stint_laps['TyreLife'], y=stint_laps['LapTimeSeconds'],
                    mode='lines+markers', name=f'Stint {int(stint_number)} ({compound})',
                    line=dict(color=color, width=2), marker=dict(size=6)
                ))

            fig2.update_layout(
                template=PLOTLY_TEMPLATE, height=550,
                title=f"{tyre_driver} — Tyre Degradation by Stint",
                xaxis_title="Tyre life (laps on this tyre)",
                yaxis_title="Lap time (seconds)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(t=80, b=40, l=60, r=20),
            )
            st.plotly_chart(fig2, use_container_width=True)

# ---------------- TAB 3: TRACK EVOLUTION ----------------
    with tab3:
        st.caption("How lap times trend across the whole session as track grip changes")

        all_laps = session.laps.dropna(subset=['LapTime', 'LapNumber']).copy()
        if session_type in ["R", "S"]:
            all_laps = all_laps.pick_quicklaps()
        all_laps['LapTimeSeconds'] = all_laps['LapTime'].dt.total_seconds()

        if all_laps.empty:
            st.warning("No valid lap data available for this session.")
        else:
            fig3 = go.Figure()

            # Faint line per driver (context)
            for drv in sorted(all_laps['Driver'].unique()):
                drv_laps = all_laps[all_laps['Driver'] == drv].sort_values('LapNumber')
                fig3.add_trace(go.Scatter(
                    x=drv_laps['LapNumber'], y=drv_laps['LapTimeSeconds'],
                    mode='lines', line=dict(color='gray', width=1),
                    opacity=0.25, showlegend=False, hoverinfo='skip'
                ))

            # Bold median line = the actual "track evolution" trend
            median_by_lap = all_laps.groupby('LapNumber')['LapTimeSeconds'].median().reset_index()
            fig3.add_trace(go.Scatter(
                x=median_by_lap['LapNumber'], y=median_by_lap['LapTimeSeconds'],
                mode='lines+markers', name='Median lap time',
                line=dict(color='#E10600', width=3),
                hovertemplate='Lap %{x}<br>Median: %{y:.3f}s<extra></extra>'
            ))

            fig3.update_layout(
                template=PLOTLY_TEMPLATE, height=550,
                title="Track Evolution — Median Lap Time by Lap Number",
                xaxis_title="Lap number", yaxis_title="Lap time (seconds)",
                margin=dict(t=60, b=40, l=60, r=20),
            )
            st.plotly_chart(fig3, use_container_width=True)

# ---------------- TAB 4: LAP TIMES TABLE ----------------
    with tab4:
        st.caption("Browse every lap of the session")

        table_laps = session.laps.dropna(subset=['LapTime', 'Stint', 'TyreLife']).copy()

        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            lap_view_driver = st.selectbox("Driver", ["All drivers"] + drivers, key="lap_table_driver")
        with col_b:
            available_compounds = sorted(table_laps['Compound'].dropna().unique())
            selected_compounds = st.multiselect("Tyre compound", available_compounds, default=available_compounds, key="lap_table_compound")
        with col_c:
            min_lap = int(table_laps['LapNumber'].min())
            max_lap = int(table_laps['LapNumber'].max())
            lap_range = st.slider("Lap number range", min_lap, max_lap, (min_lap, max_lap), key="lap_table_range")

        if lap_view_driver != "All drivers":
            table_laps = table_laps[table_laps['Driver'] == lap_view_driver]
        table_laps = table_laps[table_laps['Compound'].isin(selected_compounds)]
        table_laps = table_laps[
            (table_laps['LapNumber'] >= lap_range[0]) & (table_laps['LapNumber'] <= lap_range[1])
        ]

        # Work out lap status: Fastest Overall > Personal Best > Lost Time > none
        table_laps = table_laps.sort_values(['Driver', 'LapNumber'])
        table_laps['PrevLapTime'] = table_laps.groupby('Driver')['LapTime'].shift(1)
        table_laps['LostTime'] = table_laps['LapTime'] > table_laps['PrevLapTime']

        session_fastest_time = table_laps['LapTime'].min() if not table_laps.empty else None

        def classify(row):
            if session_fastest_time is not None and row['LapTime'] == session_fastest_time:
                return 'Fastest Overall'
            elif row['IsPersonalBest']:
                return 'Personal Best'
            elif row['LostTime']:
                return 'Lost Time'
            else:
                return '—'

        table_laps['Lap Status'] = table_laps.apply(classify, axis=1)
        table_laps['LapTime_str'] = table_laps['LapTime'].apply(format_laptime)

        # Convert number columns to text so Streamlit left-aligns them like the others
        table_laps['Lap_str'] = table_laps['LapNumber'].astype(int).astype(str)
        table_laps['Stint_str'] = table_laps['Stint'].astype(int).astype(str)
        table_laps['TyreLife_str'] = table_laps['TyreLife'].astype(int).astype(str)

        display_cols = table_laps[[
            'Driver', 'LapTime_str', 'Compound', 'Lap_str', 'Stint_str', 'TyreLife_str', 'Lap Status'
        ]].rename(columns={
            'LapTime_str': 'Lap Time', 'Lap_str': 'Lap', 'Stint_str': 'Stint', 'TyreLife_str': 'Tyre Life'
        })

        st.caption(f"Showing {len(display_cols)} laps")

        def style_compound(val):
            color = COMPOUND_COLORS.get(val, '#FFFFFF')
            return f'color: {color}; font-weight: 600'

        status_colors = {'Fastest Overall': '#B24BF3', 'Personal Best': '#43B02A', 'Lost Time': '#FFD700'}
        def style_status(val):
            color = status_colors.get(val, '#888888')
            return f'color: {color}; font-weight: 600'

        styled = display_cols.style.map(style_compound, subset=['Compound']).map(style_status, subset=['Lap Status'])

        st.dataframe(styled, use_container_width=True, hide_index=True, height=500)            

# ---------------- TAB 5: TRACK MAP ----------------
    with tab5:
        st.caption("Racing line colored by speed, with corner markers")

        map_driver = st.selectbox("Driver", drivers, index=0, key="map_driver")

        driver_all_laps = session.laps.pick_drivers(map_driver).dropna(subset=['LapTime', 'Stint', 'TyreLife']).copy()
        driver_all_laps = driver_all_laps.sort_values('LapNumber')

        fastest_lap_number = int(driver_all_laps.loc[driver_all_laps['LapTime'].idxmin(), 'LapNumber'])
        lap_options = driver_all_laps['LapNumber'].astype(int).tolist()
        default_index = lap_options.index(fastest_lap_number)

        selected_lap_number = st.selectbox(
            "Lap", lap_options, index=default_index,
            format_func=lambda n: f"Lap {n}" + (" (fastest)" if n == fastest_lap_number else ""),
            key="map_lap_number"
        )

        map_lap = driver_all_laps[driver_all_laps['LapNumber'] == selected_lap_number].iloc[0]

        # --- Scorecard ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Driver", map_driver)
        c2.metric("Lap Time", format_laptime(map_lap['LapTime']))
        c3.metric("Compound", f"{map_lap['Compound']} (life {int(map_lap['TyreLife'])})")

        pos = map_lap.get_pos_data()
        car_tel = map_lap.get_car_data()

        pos = map_lap.get_pos_data()

        if pos is None or pos.empty or 'X' not in pos.columns:
            st.warning(f"⚠️ Position data isn't available for {map_driver}'s Lap {selected_lap_number}. Try a different lap or driver.")
            st.stop()

        car_tel = map_lap.get_car_data()
        pos = pos.copy()
        pos['Speed'] = car_tel['Speed'].reindex(pos.index, method='nearest') if len(car_tel) != len(pos) else car_tel['Speed'].values

        try:
            circuit_info = session.get_circuit_info()
            corners_available = True
        except Exception:
            circuit_info = None
            corners_available = False

        fig5 = go.Figure()

        fig5.add_trace(go.Scatter(
            x=pos['X'], y=pos['Y'], mode='markers',
            marker=dict(
                size=4, color=pos['Speed'], colorscale='Turbo',
                colorbar=dict(title="km/h"), showscale=True
            ),
            hovertemplate='%{marker.color:.0f} km/h<extra></extra>',
            name=map_driver
        ))

        if corners_available:
            fig5.add_trace(go.Scatter(
                x=circuit_info.corners['X'], y=circuit_info.corners['Y'],
                mode='markers+text',
                marker=dict(size=14, color='white', symbol='circle-open', line=dict(width=2)),
                text=circuit_info.corners['Number'].astype(str),
                textposition='top center',
                textfont=dict(color='white', size=11),
                hoverinfo='skip',
                name='Corners'
            ))
        else:
            st.caption("⚠️ Corner markers unavailable for this specific session — showing racing line only.")

        fig5.update_layout(
            template=PLOTLY_TEMPLATE, height=700,
            title=f"{map_driver} — Lap {selected_lap_number} Racing Line (colored by speed)",
            xaxis=dict(visible=False, scaleanchor='y', scaleratio=1, autorange=True),
            yaxis=dict(visible=False, autorange=True),
            margin=dict(t=60, b=20, l=20, r=20),
            showlegend=False
        )

        st.plotly_chart(fig5, use_container_width=True)
else:
    st.info("Choose a Year, Grand Prix, and Session in the sidebar, then click **Load Session** to begin.")