import os
import time
import streamlit as st
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)


def load_local_storage_index(storage_dir='./storage'):
    """Load the local storage index for Llama to reduce the need to call OpenAI"""
    storage_context = StorageContext.from_defaults(persist_dir=storage_dir)
    return load_index_from_storage(storage_context)


def persist_data(storage_dir='./storage', data_directory='data'):
    """Persist newly created Llama data or pull in what exists"""
    if not os.path.exists(storage_dir):
        # load the documents and create the index
        documents = SimpleDirectoryReader(data_directory).load_data()
        _index = VectorStoreIndex.from_documents(documents)
        # store it for later
        _index.storage_context.persist(persist_dir=storage_dir)
    else:
        # load the existing index
        _index = load_local_storage_index(storage_dir=storage_dir)
    return _index


@st.cache_resource
def load_llama(storage_dir='./storage', data_directory='data'):
    """Load Llama index data caching it, so we don't have to reload"""
    return persist_data(storage_dir=storage_dir, data_directory=data_directory)


def load_engine(llama_index):
    """Sets up the Llama query engine that invokes OpenAI APIs"""
    return llama_index.as_query_engine()


def stream_data(text_data: str):
    """Nice to have. Makes it look like the AI is typing out a text response"""
    for word in text_data.split(' '):
        yield word + ' '
        time.sleep(0.02)


def setup():
    """Instantiates all necessary objects/data.
    Note, when the page first loads it takes a few moments but by caching things it provides a more fluid experience.
    """
    _index = load_llama()
    _query_engine = load_engine(_index)
    return _index, _query_engine


# Set the page title and favicon
st.set_page_config(page_title="NFL Rules OpenAI",
                   page_icon='🧠')

# Setup the Llama index + OpenAI query engine
index, query_engine = setup()

# Store Q/A Data this is not cached currently or a part of the session state
question_answer_dict = {}

# Create a container to hold the chat inputs and additional information
with st.container():
    st.subheader('Find out about the 2022 NFL Rules')
    prompt = st.chat_input('Ask a question')
    if prompt:
        # If we've received the questions already then use what's stored in the session.
        # Each call to OpenAI costs money, so we want to avoid duplicate calls
        if prompt.lower() in st.session_state:
            response = st.session_state[prompt.lower()]
        else:
            response = query_engine.query(prompt)
            st.session_state[prompt.lower()] = str(response)
            st.session_state['last_llama_response'] = response

        # Display the user question
        user_message = st.chat_message('user')
        user_message.write(prompt)
        # Display the AI response
        ai_message = st.chat_message('ai')
        # Make it look kind of like the AI is typing out a response
        ai_message.write_stream(stream_data(str(response)))

    # Not efficient to iterate over the session state questions/answers but
    # this is just a PoC :)
    for old_question, old_response in st.session_state.to_dict().items():
        if prompt and old_question.lower() == prompt.lower() or old_question == 'last_llama_response':
            continue
        old_message = st.chat_message('user')
        old_message.write(old_question)
        old_ai_response = st.chat_message('ai')
        old_ai_response.write(old_response)
        question_answer_dict[old_question] = old_response


# More of a Debug section/show different information in other ways
st.divider()
with st.expander('Show Session Questions and Answers'):
    # Raw session state values
    st.caption('Session State')
    st.write(st.session_state)
    # Display data in a table
    st.caption('Session State in Table')
    # st.table(data=st.session_state.to_dict())
    st.table(data=question_answer_dict)
    # The actual Response has more data than a chat response that could be beneficial
    st.caption('Last Llama OpenAI Response')
    if 'last_llama_response' in st.session_state:
        st.write(st.session_state['last_llama_response'])
    else:
        st.write('Ask a question before seeing the response data')
