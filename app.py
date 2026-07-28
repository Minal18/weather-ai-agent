"""Weather assistant — name a place, then ask about it."""

from datetime import date
import streamlit as st
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from weather import getting_current_weather
from main import system_prompt, get_current_weather, get_weather_forecast, llm_model

st.set_page_config(
    page_title="Weather Assistant",
    page_icon="🌤",
    layout="centered",
)


# styling

STYLES = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;700&family=Inter:wght@400;500&display=swap');

:root {
    --ink:      #2B3A42;
    --muted:    #6B8189;
    --harbour:  #4F7C82;
    --line:     #DAE4E7;
    --mist:     #EDF2F4;
}

/* page */
.stApp { background-color: var(--mist) !important; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* every piece of text defaults to ink unless told otherwise */
.stApp, .stApp p, .stApp li, .stApp span, .stApp div,
.stApp label, .stApp strong, .stApp summary {
    color: var(--ink);
}

/* masthead */
.masthead { padding: 0.5rem 0 1.5rem 0; }
.masthead h1 {
    font-family: 'Manrope', sans-serif;
    font-size: 2.1rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink) !important;
    margin: 0 0 0.4rem 0;
}
.masthead p {
    color: var(--muted) !important;
    font-size: 0.97rem;
    line-height: 1.55;
    margin: 0;
    max-width: 34rem;
}

/* captions and widget labels */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: var(--muted) !important;
    font-size: 0.86rem !important;
}

/* selected-place bar */
.placebar {
    display: flex;
    align-items: baseline;
    gap: 0.65rem;
    flex-wrap: wrap;
    padding: 0.85rem 1.1rem;
    background: #FFFFFF;
    border: 1px solid var(--line);
    border-left: 3px solid var(--harbour);
    border-radius: 10px;
    margin-bottom: 1.25rem;
}
.placebar .place-name {
    font-family: 'Manrope', sans-serif;
    font-size: 1.08rem;
    font-weight: 700;
    color: var(--ink) !important;
}
.placebar .place-meta {
    font-size: 0.85rem;
    color: var(--muted) !important;
}

/* chat bubbles */
[data-testid="stChatMessage"] {
    background: #FFFFFF !important;
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.65rem;
}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] summary {
    color: var(--ink) !important;
}

/* text inputs */
[data-testid="stTextInput"] input {
    background: #FFFFFF !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
}
[data-testid="stTextInput"] input::placeholder { color: #A9BAC0 !important; }

/* chat input */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div {
    background: #FFFFFF !important;
    border-color: var(--line) !important;
}
[data-testid="stChatInput"] textarea {
    background: #FFFFFF !important;
    color: var(--ink) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #A9BAC0 !important; }

/* secondary buttons — starters, change place */
.stButton button {
    background: #FFFFFF !important;
    color: var(--ink) !important;
    border: 1px solid var(--line) !important;
    border-radius: 8px !important;
    font-family: 'Manrope', sans-serif;
    font-weight: 500;
    transition: border-color 120ms ease, color 120ms ease;
}
.stButton button:hover {
    border-color: var(--harbour) !important;
    color: var(--harbour) !important;
}
.stButton button p { color: inherit !important; }

/* primary action — the one accented control on the page */
[data-testid="stFormSubmitButton"] button {
    background: var(--harbour) !important;
    color: #FFFFFF !important;
    border: 1px solid var(--harbour) !important;
    border-radius: 8px !important;
    font-family: 'Manrope', sans-serif;
    font-weight: 700;
}
[data-testid="stFormSubmitButton"] button p { color: #FFFFFF !important; }
[data-testid="stFormSubmitButton"] button:hover {
    background: #3F686D !important;
    border-color: #3F686D !important;
}

/* containers and expanders */
[data-testid="stForm"] {
    background: #FFFFFF;
    border: 1px solid var(--line) !important;
    border-radius: 12px;
    padding: 1.25rem 1.25rem 0.5rem 1.25rem;
}
[data-testid="stExpander"] details {
    background: #FFFFFF;
    border: 1px solid var(--line) !important;
    border-radius: 8px;
}

/* alerts */
[data-testid="stAlert"] { border-radius: 8px; }

/* quieten streamlit chrome */
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; }

@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
}
</style>
"""

st.markdown(STYLES, unsafe_allow_html=True)


# helpers

@st.cache_resource(show_spinner=False)
def build_agent(city: str):
    """One agent per place, so it knows where 'here' is."""
    return create_agent(
        model=llm_model,
        tools=[get_current_weather, get_weather_forecast],
        system_prompt=(
            system_prompt
            + f"\n\nToday's date is {date.today().isoformat()}."
            + f"\n\nThe user has already chosen a location: {city}. "
            f'When they ask about the weather without naming a city, use "{city}" '
            "as the city argument. Do not ask them which city they mean. "
            "If they name a different city, use that one instead."
        ),
    )


def reset_place():
    for key in ("place", "messages", "pending"):
        st.session_state.pop(key, None)


# search screen

if "place" not in st.session_state:
    st.markdown(
        """
        <div class="masthead">
            <h1>Weather Assistant</h1>
            <p>Name your place first, then ask whatever you like —
            what it's doing now, what the week looks like,
            or whether to bother taking a coat.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("place_form"):
        col_city, col_country = st.columns([3, 1])
        with col_city:
            city = st.text_input("Town or city", placeholder="Liverpool")
        with col_country:
            country = st.text_input("Country code", placeholder="GB", max_chars=2)

        submitted = st.form_submit_button("Find this place")

    st.caption(
        "The country code is optional, but it settles it when a name is used in "
        "more than one country — Liverpool is in both the UK and Australia."
    )

    if submitted and city.strip():
        query = f"{city.strip()},{country.strip()}" if country.strip() else city.strip()

        with st.spinner("Looking it up..."):
            data = getting_current_weather(query)

        if isinstance(data, str):
            st.warning(data)
        else:
            st.session_state.place = {
                "query": query,
                "name": data["name"],
                "country": data["sys"]["country"],
                "temp": round(data["main"]["temp"]),
                "conditions": data["weather"][0]["description"],
            }
            st.session_state.messages = []
            st.rerun()

    elif submitted:
        st.warning("Type a town or city name to look up.")


# chat screen

else:
    place = st.session_state.place
    agent = build_agent(place["query"])

    col_bar, col_change = st.columns([4, 1])
    with col_bar:
        st.markdown(
            f"""
            <div class="placebar">
                <span class="place-name">{place['name']}</span>
                <span class="place-meta">{place['country']} ·
                {place['temp']}°C · {place['conditions']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_change:
        st.write("")
        if st.button("Change place", use_container_width=True):
            reset_place()
            st.rerun()

    if not st.session_state.messages:
        st.caption("Something to start with")
        starters = [
            "What's it like right now?",
            "Should I cycle tomorrow?",
            "What does the week look like?",
        ]
        for i, col in enumerate(st.columns(3)):
            with col:
                if st.button(starters[i], key=f"start_{i}", use_container_width=True):
                    st.session_state.pending = starters[i]
                    st.rerun()

    for msg in st.session_state.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role, avatar="🌤" if role == "assistant" else None):
            st.markdown(msg.content)

    question = st.chat_input(f"Ask about the weather in {place['name']}")
    if st.session_state.get("pending"):
        question = st.session_state.pop("pending")

    if question:
        st.session_state.messages.append(HumanMessage(question))
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant", avatar="🌤"):
            with st.spinner("Checking..."):
                result = agent.invoke({"messages": st.session_state.messages})
                reply = result["messages"][-1]
            st.markdown(reply.content)

            calls = [
                f"{c['name']}({c['args']})"
                for m in result["messages"]
                for c in getattr(m, "tool_calls", []) or []
            ]
            if calls:
                with st.expander("What it looked up"):
                    for call in calls:
                        st.code(call, language="python")

        st.session_state.messages.append(AIMessage(reply.content))