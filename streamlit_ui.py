import streamlit as st
import requests
import json

# Set page config
st.set_page_config(
    page_title="Hamza Corporation - Educational Assistant",
    page_icon="🎓",
    layout="wide"
)

# Initialize chat history in session state if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Header and branding
st.title("🎓 Hamza Corporation Educational Assistant")
st.markdown("""
Welcome to your personal educational advisor! I'm here to help you understand your course materials 
and answer any academic questions you may have. Feel free to ask about any topic in your documents.

---
""")

# Chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("What would you like to know?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Create a placeholder for the assistant's response with a loading spinner
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:5000/ask",
                    json={"question": prompt},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result['status'] == 'success':
                        # Display assistant response
                        st.markdown(result['answer'])
                        # Add assistant response to chat history
                        st.session_state.messages.append(
                            {"role": "assistant", "content": result['answer']}
                        )
                    else:
                        st.error(f"Error: {result['message']}")
                else:
                    st.error(f"Failed to connect to the server. Status code: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to the server: {str(e)}")

# Enhance sidebar with branding and additional information
with st.sidebar:
    st.title("Hamza Corporation")
    st.markdown("*Empowering Education Through AI*")
    st.markdown("---")
    st.title("Options")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("""
    ### About
    This educational assistant is powered by advanced AI technology 
    to help students better understand their course materials.
    
    ### Features
    - Comprehensive document analysis
    - Detailed explanations
    - Interactive learning support
    """)
