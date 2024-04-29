import streamlit as st
from unify import AsyncUnify
from unify import Unify
import os
from unify.exceptions import UnifyError
import asyncio
import pandas as pd
import json
import requests
import random

st.set_page_config(
    page_title="Chatbot arena",
    page_icon="🤖",
    layout="wide",
)

keys = ["chat_input", "winner_selected", "api_key_provided",
        "vote1", "vote2", "model1", "model2", "api_key", "scores",
        "authenticated"]

for key in keys:
    if key not in st.session_state.keys():
        st.session_state[key] = None

st.session_state.code_input = " "
st.session_state.chat_history1 = []
st.session_state.chat_history2 = []

# Load JSON data from file
with open("models.json", "r") as f:
    data = json.load(f)
all_models = tuple(data['models'])
#model_options = [model.split("@")[0] for model in all_models]
data = pd.read_csv("leaderboard.csv")  # This will raise an error if the file does not exist   
json_data = {model:votes for model,votes in zip(data["Model Name"],data["Votes ⭐"])}

def select_model(api_key=st.session_state.api_key, authenticated=st.session_state.authenticated):
    global json_data, all_models
    disabled = not (bool(api_key) and bool(authenticated))
    model1_other_disabled = True
    model2_other_disabled = True
    models = json_data
    if 'vote_counts' not in st.session_state:
        st.session_state['vote_counts'] = models
    st.selectbox("Select the first model's endpoint:",
                         all_models,
                         placeholder='mixtral-8x7b-instruct-v0.1@fireworks-ai',
                         disabled=disabled,
                         key="model1_selectbox")
    if st.session_state.model1_selectbox == 'other':
        model1_other_disabled = False
    st.text_input('If "other", provide your own model:', placeholder='model@provider',
                          disabled=model1_other_disabled, key='model1_other')
    st.selectbox("Select the second model's endpoint:",
                         all_models,
                         placeholder='mixtral-8x7b-instruct-v0.1@fireworks-ai',
                         disabled=disabled,
                         key="model2_selectbox")
    if st.session_state.model2_selectbox == 'other':
        model2_other_disabled = False
    st.text_input('If "other", provide your own model:', placeholder='model@provider',
                          disabled=model2_other_disabled, key='model2_other')
    st.session_state.winner_selected = False
    selected_model1 = st.session_state.model1_selectbox if st.session_state.model1_selectbox != "other" else st.session_state.model1_other
    selected_model2 = st.session_state.model2_selectbox if st.session_state.model2_selectbox != "other" else st.session_state.model2_other

    selected_models = [selected_model1, selected_model2]
    random.shuffle(selected_models)
    st.session_state['model1'] = selected_models.pop(0)
    st.session_state['model2'] = selected_models.pop(0)

def history(model='model1', output='how are you'):
    if model == 'model1':
        st.session_state['chat_history1'].append({"role": "assistant", "content": output})
    elif model == 'model2':
        st.session_state['chat_history2'].append({"role": "assistant", "content": output})

    else:
        st.write("Please, enter the model1 or model2 in history function.")
    if len(st.session_state['chat_history1'])>=10:
        st.session_state['chat_history1'].pop(0)
    if len(st.session_state['chat_history2'])>=10:
        st.session_state['chat_history2'].pop(0)

# Define function to input API key
def input_api_key(api_key=" "):
    authorisation_url = "https://api.unify.ai/v0/get_credits"
    r = requests.get(authorisation_url, headers={"accept": "application/json", "Authorization": f"Bearer {api_key}"}).json()

    if "id" in r.keys():
        st.session_state.__setattr__("api_key_provided", True)
        st.session_state.__setattr__("authenticated", True)
        st.sidebar.write(f"Session user credits: {r['credits']}")
        st.session_state['api_key'] = api_key
    elif "detail" in r.keys():
        st.session_state.__setattr__("api_key_provided", False)
        st.session_state.__setattr__("authenticated", False)
        st.sidebar.write(f"{r['detail']}")
    elif "error" in r.keys():
        st.session_state.__setattr__("api_key_provided", False)
        st.session_state.__setattr__("authenticated", False)
        st.sidebar.write(f"{r['error']}")
        
def print_history(contain):
    cont1, cont2 = contain
    for i in st.session_state["chat_history1"]:
            if i['role']=="user":
                cont1.write("🧑‍💻" +"  "+ i["content"])
            else:
                cont1.write("🤖" +"  "+ i["content"])
    for i in st.session_state["chat_history2"]:
        if i['role']=="user": 
            cont2.write("🧑‍💻" +"  "+ i["content"])
        else:
            cont2.write("🤖" +"  "+ i["content"])       
def call_model(Endpoint):
    async_unify = AsyncUnify(
    api_key=st.session_state['api_key'],
    endpoint=Endpoint)
    return async_unify
st.set_option('deprecation.showPyplotGlobalUse', False)
async def main():
    global all_models, data
    st.session_state.code_input = ""
    st.markdown(
    """
    <h1 style='text-align: center; color: green;'>
        Unify's LLM Playground 🚀
    </h1>
    """,
    unsafe_allow_html=True)
    st.sidebar.subheader("Unify API Key")
    api_key = st.sidebar.text_input("UNIFY KEY", placeholder="API key is required to proceed.",type="password")
    input_api_key(api_key)
    # Display sidebar widgets
    with st.sidebar:
        select_model(st.session_state.api_key, st.session_state.authenticated)
    col11, col21 = st.columns(2)
    # Display chat UI
    with col11:
        if st.session_state.winner_selected is True:
            st.markdown("<span style='font-size:20px; color:blue;'>Model 1: " + st.session_state['model1'] + "</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='font-size:20px; color:blue;'>Model 1: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span>", unsafe_allow_html=True)
    with col21:
        if st.session_state.winner_selected is True:
            st.markdown("<span style='font-size:20px; color:blue;'>Model 2: " + st.session_state['model2'] + "</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='font-size:20px; color:blue;'>Model 2: ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        cont1 = st.container(height=500)
    with col2:
        cont2 = st.container(height=500)
    if "chat_history1" not in st.session_state:
        st.session_state["chat_history1"] = []
    if "chat_history2" not in st.session_state:
        st.session_state["chat_history2"] = []
    if prompt := st.chat_input("Say something", disabled=False if st.session_state.api_key_provided is True else True, on_submit=lambda: st.session_state.__setattr__("winner_selected", False)):
        st.session_state["chat_input"] = prompt
        st.session_state.code_input = prompt
        st.session_state['chat_history1'].append({"role": "user", "content": st.session_state["chat_input"]})
        st.session_state['chat_history2'].append({"role": "user", "content": st.session_state["chat_input"]})
        message1 = st.session_state['chat_history1']
        message2 = st.session_state['chat_history2']
        print_history(contain=(cont1, cont2))
        u1 = None
        u2 = None
        try:
            u1 = call_model(st.session_state['model1'])
            if st.session_state['model1'] not in all_models:
                with open("models.json", "w") as models_file_update:
                    upd_models = [model for model in all_models]
                    upd_models[-1] = st.session_state['model1']
                    upd_models.append("other")
                    upd_models = {"models": tuple(upd_models)}
                    json.dump(upd_models, models_file_update)
            if (model1_to_add := st.session_state['model1'][:st.session_state['model1'].find("@")]) not in data.keys():
                st.session_state['vote_counts'][f"{model1_to_add}"] = 0
                    
        except UnifyError:
            st.session_state.__setattr__("winner_selected", True)
            if "@" not in st.session_state['model1']:
                cont1.error("Model endpoints have to follow the '<model>@<provider>' format")
                cont2.error("Model endpoints have to follow the '<model>@<provider>' format")
            else:
                cont1.error("One of the models is not currently supported.")
                cont2.error("One of the models is not currently supported.")
        try:
            u2 = call_model(st.session_state['model2'])
            if st.session_state['model2'] not in all_models:
                with open("models.json", "w") as models_file_update:
                    upd_models = [model for model in all_models]
                    upd_models[-1] = st.session_state['model2']
                    upd_models.append("other")
                    upd_models = {"models": tuple(upd_models)}
                    json.dump(upd_models, models_file_update)
            if (model2_to_add := st.session_state['model2'][:st.session_state['model2'].find("@")]) not in data.keys():
                st.session_state['vote_counts'][f"{model2_to_add}"] = 0
        except UnifyError:
            st.session_state.__setattr__("winner_selected", True)
            if "@" not in st.session_state['model2']:
                cont1.error("Model endpoints have to follow the '<model>@<provider>' format")
                cont2.error("Model endpoints have to follow the '<model>@<provider>' format")
            else:
                cont1.error("One of the models is not currently supported.")
                cont2.error("One of the models is not currently supported.")                
        async def call(unify_obj,model,contain,message):
            try:
                async_stream = await unify_obj.generate(messages=message, stream=True)
                placeholder = contain.empty()
                full_response = ''
                async for chunk in async_stream:
                    full_response += chunk
                    placeholder.markdown(full_response)
                placeholder.markdown("🤖  "+ full_response)
                history(model=model, output=full_response)
            except:
                contain.error(f"The selected model and/or provider might not be available.", icon="🚨")
                st.session_state.__setattr__("winner_selected", True)

        await asyncio.gather(
            call(u1,model='model1', contain=cont1,message=message1),
            call(u2,model='model2', contain=cont2,message=message2)
        )
    c1, c2= st.columns(2)
    # Display the vote buttons
    vote_disabled = True if st.session_state.winner_selected in [None, True] else False
    with c1:
        left_button_clicked = st.button("👍 Vote First Model", disabled=vote_disabled,
                                        on_click=lambda: st.session_state.__setattr__("winner_selected", True))
        if left_button_clicked:
                
                # Increase the vote count for the selected model by 1 when the button is clicked
                model = st.session_state['model1'].split("@")[0]
                st.session_state['vote_counts'][model] += 1
                print_history(contain=(cont1, cont2))
                try:
                    st.session_state.code_input = st.session_state["chat_history1"][-2]['content']
                except IndexError:
                    st.session_state.code_input = "<No response>"
    with c2:
        right_button_clicked = st.button("👍 Vote Second Model", disabled=vote_disabled,
                                         on_click=lambda: st.session_state.__setattr__("winner_selected", True))
        if right_button_clicked:
                # Increase the vote count for the selected model by 1 when the button is clicked
                model2 = st.session_state['model2'].split("@")[0]
                st.session_state['vote_counts'][model2] += 1
                print_history(contain=(cont1, cont2))
                try:
                    st.session_state.code_input = st.session_state["chat_history2"][-2]['content']
                except IndexError:
                    st.session_state.code_input = "<No response>"
            # Add custom CSS for the buttons
    history_button_clicked = st.button("Clear Histroy")
    if history_button_clicked:
            st.session_state["chat_history1"] = []
            st.session_state["chat_history2"] = []
        
if __name__ == "__main__":
    asyncio.run(main())
    
    
     

