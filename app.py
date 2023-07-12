import streamlit as st
import openai
from utils.token_utils import num_tokens_from_messages
import glob



st.title('Prompt IDE')

openai.api_key = st.secrets['OPANAI_API_KEY']

# @st.cache(ttl=360)
def get_available_models():
    resp = openai.Model.list()
    models = []
    if 'data' in resp:
        for model in resp['data']:
            if 'gpt' in model['id']:
                models.append(model['id'])
    return models



import glob

def get_available_system_prompts():
    available_prompts = {}

    for prompt_file in glob.glob("prompts/system_prompts/*.md"):
        prompt_name = prompt_file.split("/")[-1].split(".md")[0]
        with open(prompt_file, "r") as file:
            prompt_text = file.read()
        available_prompts[prompt_name] = prompt_text

    return available_prompts




available_models = sorted(get_available_models())


if 'default_first_message' not in st.session_state:
    st.session_state['default_first_message'] = "Hi! How can I help you?"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize usage stats
if "usage" not in st.session_state:
    model_usage = {}
    for model in available_models:
        model_usage[model] = {"prompt_tokens":0,
                              "completion_tokens":0,
                              "total_tokens":0,
                              "num_requests":0}

    st.session_state.usage = model_usage

if "available_system_prompts" not in st.session_state:
    st.session_state["available_system_prompts"] = get_available_system_prompts()



model_tab, system_tab, usage_tab = st.tabs(["Model", "System", "Usage"])

# Sytem prompt tab:
with system_tab:
        
    # st.session_state['selected_system_prompt'] = st.selectbox('System Prompts', 
    #                                                           st.session_state["available_system_prompts"].keys(),
    #                                                           index=2
    #                                                           )
    
    # system_text = st.session_state["available_system_prompts"][st.session_state['selected_system_prompt']]

    # st.session_state["system_prompt"] = st.text_area("System Message", system_text)

    left_column, right_column = st.columns(2)

    # Left column for editing the system prompt in markdown
    with left_column:
        st.session_state['selected_system_prompt'] = st.selectbox('System Prompts',
                                                                  list(st.session_state["available_system_prompts"].keys()),
                                                                  index=2
                                                                  )

        system_text = st.session_state["available_system_prompts"][st.session_state['selected_system_prompt']]

        st.session_state["system_prompt"] = st.text_area("System Message", system_text)

    # Right column for rendering the markdown
    with right_column:
        st.markdown(st.session_state["system_prompt"])


with model_tab:
    st.session_state['selected_model'] = st.selectbox('Open AI Models', 
                                                      available_models)
    
    
    st.session_state['temperature'] = st.slider("Temperature", 
                                                step=5,
                                                min_value=0,
                                                max_value=200, 
                                                value=100)


with usage_tab:
    model = st.session_state.selected_model
    model_usage = st.session_state.usage
    usage_stats = [
        {
            "Model": model,
            "Prompt Tokens": model_usage[model]["prompt_tokens"],
            "Completion Tokens": model_usage[model]["completion_tokens"],
            "Total Tokens": model_usage[model]["total_tokens"],
            "Num Requests": model_usage[model]["num_requests"]
        }
        for model in model_usage
    ]

    # Display the usage stats table
    st.table(usage_stats)


st.divider()

with st.container():
    if user_input := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            chat_messages = [{"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]

            messages = [{"role":'system', "content":st.session_state['system_prompt']}]
            messages.extend(chat_messages)

            prompt_tokens_count = num_tokens_from_messages(messages, model=st.session_state["selected_model"])  # count tokens here
            st.session_state.usage[st.session_state["selected_model"]]["prompt_tokens"] += prompt_tokens_count
            st.session_state.usage[st.session_state["selected_model"]]["total_tokens"] += prompt_tokens_count

            for response in openai.ChatCompletion.create(
                model=st.session_state["selected_model"],
                temperature=st.session_state['temperature']/100,
                messages=messages,
                stream=True,
            ):
                full_response += response.choices[0].delta.get("content", "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        
        response_message = {"role": "assistant", "content": full_response}
        st.session_state.messages.append(response_message)
        completion_tokens_count = num_tokens_from_messages([response_message], model=st.session_state["selected_model"])  # count tokens here
        st.session_state.usage[st.session_state["selected_model"]]["prompt_tokens"] += completion_tokens_count
        st.session_state.usage[st.session_state["selected_model"]]["total_tokens"] += completion_tokens_count
        st.session_state.usage[st.session_state["selected_model"]]["num_requests"] += 1

        

        st.write(f"Consumed prompt tokens: {prompt_tokens_count} ")  # displaying the prompt tokens count
        st.write(f"Consumed prompt tokens: {completion_tokens_count} ")  # displaying the generated tokens count
        num_reqs = st.session_state.usage[st.session_state["selected_model"]]["num_requests"]
        st.write(f"Consumed prompt tokens: {num_reqs} ")  # displaying the consumed tokens






