import os
import ast

import streamlit as st
from langgraph_supervisor import create_supervisor

from src.app.agents import analysis_agent, comparison_agent, search_agent
from src.app.config import CHAT_MODEL, LANGFUSE_HANDLER, SUPERVISOR_PROMPT, HISTORY_CONTEXT_LENGTH
from langchain_core.messages import ToolMessage


def create_app_supervisor():
    workflow = create_supervisor(
        model=CHAT_MODEL,
        prompt=SUPERVISOR_PROMPT,
        agents=[analysis_agent, search_agent, comparison_agent]
    )

    supervisor = workflow.compile()
    return supervisor

def submit_prompt(app, prompt, config):
    result = app.invoke({"messages":[
        {"role": "user", "content": prompt},
    ]}, config=config)

    answer = result["messages"][-1].content

    total_input_tokens = 0
    total_output_tokens = 0

    for message in result["messages"]:
        if "usage_metadata" in message.response_metadata:
            total_input_tokens += message.response_metadata["usage_metadata"]["input_tokens"]
            total_output_tokens += message.response_metadata["usage_metadata"]["output_tokens"]
        elif "token_usage" in message.response_metadata:
            # Fallback for older or different structures
            total_input_tokens += message.response_metadata["token_usage"].get("prompt_tokens", 0)
            total_output_tokens += message.response_metadata["token_usage"].get("completion_tokens", 0)

    price = 17.828,10*(total_input_tokens*0.15 + total_output_tokens*0.6)/1_000_000

    tool_messages = []
    for message in result["messages"]:
        if isinstance(message, ToolMessage):
            tool_message_content = message.content
            tool_messages.append(tool_message_content)

    response = {
        "answer": answer,
        "price": price,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "tool_messages": tool_messages
    }
    return response


if __name__ == "__main__" :

    if os.environ.get("OPENAI_API_KEY"):
        app = create_app_supervisor()
        app_config={"callbacks": [LANGFUSE_HANDLER]}

        if app:
            print("App's Supervisor is created")


        # st.title(None)
        st.image("./assets/header.webp")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # membuat tampilan chat antara user dan AI
        for messages in st.session_state.messages:
            with st.chat_message(messages["role"]):
                st.markdown(messages["content"])


        if prompt_U := st.chat_input("Hi! How can I help you?"):
            messages_history = st.session_state.get("messages", [])[HISTORY_CONTEXT_LENGTH:]

            history = ''
            if len(messages_history) > 0:
                print(messages_history)
                history = "\n\n".join(
                    f"> History Ke-{i+1}. {msg['role']}: {msg['content']}"
                    for i, msg in enumerate(messages_history)
                ) or "::"

            with st.chat_message("user"):
                st.markdown(prompt_U)

            st.session_state.messages.append({"role": "user", "content": prompt_U})

            with st.chat_message("assistant"):
                final_prompt = f"{prompt_U}"
                if history.strip():
                    final_prompt += f"\n\n Recent Histories : \n\n{history}"

                loading = st.empty()

                with loading.container():
                    with st.spinner("Loading ..."):
                        response = submit_prompt(
                            app,
                            final_prompt,
                            app_config)
                loading.empty()

                answer = response["answer"]
                st.markdown(answer)

            st.session_state.messages.append({"role": "assistant", "content": answer})
            with st.expander("**Tool Calls:**"):
                st.code(response["tool_messages"])

            if history :
                with st.expander("**History Chat:**"):
                    st.code(history)

            with st.expander("**Usage Details:**"):
                st.code(
                    f'input token  : {response["total_input_tokens"]}\n'
                    f'output token : {response["total_output_tokens"]}\n'
                    f'request cost : ${response["price"][1]}'
                )
