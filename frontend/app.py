import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Video Script Studio", layout="wide")
st.title("Video Script Studio")
st.caption(
    "Generate duration-aware, teleprompter-ready video scripts with sourced research and fact-checking."
)

STYLE_OPTIONS = [
    "news",
    "curiosity",
    "documentary",
    "storytelling",
    "dramatic",
    "horror",
    "motivational",
    "comedic",
    "neutral",
]

DURATION_OPTIONS = {
    "30 seconds": "30s",
    "60 seconds": "60s",
    "90 seconds": "90s",
    "3 minutes": "3min",
    "8 minutes": "8min",
    "Custom": "custom",
}


# ---------------------------------------------------------------------------
# Sidebar - inputs
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Create a script")

    input_mode = st.radio("Input mode", ["Topic", "Paste transcript"])

    topic = None
    transcript = None
    strict_mode = False

    if input_mode == "Topic":
        topic = st.text_input("Topic", placeholder="e.g. fake medicines racket Bangalore hospitals")
    else:
        transcript = st.text_area("Paste transcript or content", height=200)
        topic = st.text_input(
            "Optional: topic (adds fresh research alongside your content)", value=""
        )
        if transcript:
            strict_mode = st.checkbox("Only use my content (no external research)")

    duration_label = st.selectbox("Duration", list(DURATION_OPTIONS.keys()))
    duration_value = DURATION_OPTIONS[duration_label]

    custom_seconds = None
    if duration_value == "custom":
        custom_seconds = st.number_input(
            "Custom duration (seconds)", min_value=5, max_value=1800, value=60
        )

    style = st.selectbox("Style", STYLE_OPTIONS)

    generate_clicked = st.button("Generate Script", type="primary", use_container_width=True)


# ---------------------------------------------------------------------------
# Generate script
# ---------------------------------------------------------------------------

if generate_clicked:
    if not topic and not transcript:
        st.error("Please provide a topic or paste a transcript.")
    else:
        payload = {
            "topic": topic or None,
            "transcript": transcript or None,
            "duration": duration_value,
            "style": style,
            "strict_mode": strict_mode,
        }
        if duration_value == "custom":
            payload["custom_duration_seconds"] = int(custom_seconds)

        with st.spinner(
            "Researching, fact-checking, and writing your script... this can take a minute."
        ):
            try:
                resp = requests.post(f"{API_BASE}/generate-script", json=payload, timeout=300)
                resp.raise_for_status()
                st.session_state["script_result"] = resp.json()
                st.session_state.pop("timeline_result", None)
            except Exception as e:
                st.error(f"Failed to generate script: {e}")


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

if "script_result" in st.session_state:
    result = st.session_state["script_result"]

    tab_script, tab_sources, tab_factcheck = st.tabs(["Script", "Sources", "Fact-Check"])

    with tab_script:
        st.text_area("Teleprompter script (copy-paste ready)", value=result["script"], height=300)
        st.caption(
            f"Word count: {result['word_count']} | "
            f"Estimated duration: {result['estimated_duration_seconds']} seconds"
        )

        if st.button("Help for Video Editing"):
            with st.spinner("Building your shot-by-shot timeline..."):
                try:
                    tl_resp = requests.post(
                        f"{API_BASE}/generate-timeline",
                        json={"script": result["script"], "duration": duration_value},
                        timeout=180,
                    )
                    tl_resp.raise_for_status()
                    st.session_state["timeline_result"] = tl_resp.json()
                except Exception as e:
                    st.error(f"Failed to generate timeline: {e}")

        if "timeline_result" in st.session_state:
            st.subheader("Editing Timeline")
            for entry in st.session_state["timeline_result"]["timeline"]:
                st.markdown(
                    f"**[{entry['start_seconds']}s - {entry['end_seconds']}s]** "
                    f"{entry['shot_type'].replace('_', ' ').title()} - {entry['camera_angle']}"
                )
                st.write(entry["voiceover_chunk"])
                if entry.get("onscreen_text"):
                    st.caption(f"On-screen text: {entry['onscreen_text']}")
                if entry.get("resource_suggestion"):
                    st.caption(f"Resource: {entry['resource_suggestion']}")
                st.divider()

    with tab_sources:
        if not result["sources"]:
            st.info("No external sources for this script (strict mode / your own content only).")
        for src in result["sources"]:
            cols = st.columns([1, 4])
            with cols[0]:
                if src.get("image_url"):
                    st.image(src["image_url"], width=100)
            with cols[1]:
                st.markdown(f"**[{src['title']}]({src['url']})**")
                if src.get("published_date"):
                    st.caption(src["published_date"])
                if src.get("snippet"):
                    st.write(src["snippet"])
            st.divider()

    with tab_factcheck:
        status_emoji = {"supported": "\u2705", "uncertain": "\u26a0\ufe0f", "unverified": "\u2753"}
        if not result["fact_check"]:
            st.info("No claims were fact-checked for this script.")
        for fc in result["fact_check"]:
            emoji = status_emoji.get(fc["status"], "")
            st.markdown(f"{emoji} **{fc['status'].upper()}**: {fc['claim']}")
            st.caption(fc["explanation"])
            if fc.get("source_url"):
                st.caption(f"Source: {fc['source_url']}")
            st.divider()


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------

st.markdown("---")
st.caption("Ramu R - RSLB Systems")
