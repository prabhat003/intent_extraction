import re
import ast
import cohere
import streamlit as st
from logger import logger
from main import GetConfig, Generate, Utils
# from langchain_cohere import Cohere
# from langchain_core.messages import HumanMessage

def remove_surrounding_quotes(s: str) -> str:
    """_summary_

    Args:
        s (str): _description_

    Returns:
        str: _description_
    """
    # Check if the string starts and ends with the same type of quote
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def extract_between_curly_braces(input_str):
    """_summary_

    Args:
        input_str (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Define a regular expression pattern to match text between curly braces
    pattern = r'\{([^{}]*)\}'

    # Use re.findall() to find all matches of the pattern in the input string
    matches = re.findall(pattern, input_str)

    # Join the matches into a single string separated by commas
    result = ', '.join(matches)

    return '{'+result+'}'

# Defining main function 
def main(): 
    
    # App title
    st.set_page_config(page_title="Wolters Kluwers",
                        page_icon="", 
                        layout="wide",
                        initial_sidebar_state="expanded",
                        menu_items={
                            "About": """This is an app for intent classification"""
                        })


    # st.session_state.config = GetConfig()


    if 'CHUNKING_DONE' in st.session_state:
        st.session_state.config.CHUNKING = 0
    
    if 'updated' not in st.session_state:
        st.session_state.updated = False


    # JavaScript to scroll to the bottom of the chat container
    scroll_js = """
    <script>
        function scrollToBottom() {
            var chatContainer = document.getElementById('stChatInput');
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        // Call scrollToBottom() after each 100 milliseconds interval
        setInterval(scrollToBottom, 100);
        
        // Scroll to bottom when the page loads
        window.onload = scrollToBottom;
        window.reload = scrollToBottom;

        // Call scrollToBottom() when send button is clicked
        document.getElementById("stChatInput").onsubmit = scrollToBottom
        }

    </script>
    """
    # Inject the JavaScript
    st.markdown(scroll_js, unsafe_allow_html=True)

    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"]> .main{{
    padding: 0px;
    margin: 0px;
    border-radius: 4px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.8); /* Add shadow effect */

    background-size: 400% 400%;
    -webkit-animation: GradientBackground 30s ease infinite;
    -moz-animation: GradientBackground 30s ease infinite;
    animation: GradientBackground 30s ease infinite;

    }}


    @-webkit-keyframes GradientBackground {{
        0% {{
            background-position: 0% 50%;
        }}
        50% {{
            background-position: 100% 50%;
        }}
        100% {{
            background-position: 0% 50%;
        }}
    }}
    @-moz-keyframes GradientBackground {{
        0% {{
            background-position: 0% 50%;
        }}
        50% {{
            background-position: 100% 50%;
        }}
        100% {{
            background-position: 0% 50%;
        }}
    }}
    @keyframes GradientBackground {{
        0% {{
            background-position: 0% 50%;
        }}
        50% {{
            background-position: 100% 50%;
        }}
        100% {{
            background-position: 0% 50%;
        }}
    }}



    /* Style for the chat messages */
    [data-testid="stChatInput"]{{
        padding: 0px;
        margin: 5px 0px;
        display: flex;!important    
        width: 100%;
        background-color: rgba(0, 255, 255, 0.8); !important/* Set background color for chat messages */
        border-radius: 10px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.9); /* Add shadow effect */
    }}
    
    /* Style for the chat messages */
    [data-testid="stChatMessageContent"] {{
        padding: 20px;
        margin: 10px;
        width:70%;
        max-width:70%;
        
        overflow-y: auto;

        background: linear-gradient(80deg, rgb(0, 200, 255) 60%, rgb(0, 106, 255) 100%); !important
        color: rgba(0, 0, 0, 1);
        
        border-radius: 40px;
        box-shadow: 0 0 30px rgba(0, 0, 0, 0.7); /* Add shadow effect */
        border: 0px solid transparent; !important
        
        font-family: "Source Sans Pro", sans-serif, "Segoe UI", "Roboto", sans-serif; !important
        font-size: 2rem;  !important/* Increase the font size here */
        font-color: red;  !important/* Increase the font size here */
    }}

    /* Style for the chat messages */
    [data-testid="stChatMessage"]{{
        font-family: "Source Sans Pro", sans-serif, "Segoe UI", "Roboto", sans-serif; !important
        font-size:4em; !important
        font-color: red;  !important/* Increase the font size here */

    }}

    .st-emotion-cache-4oy321 {{
            flex-direction: row-reverse;
            text-align: left;
            
        }}



    </style>
    """


    button_style = """
        <style>
        .button {
            display: block; !important
            width: fit-content; !important
            font-size: 14px; !important
            font-weight: bold;
            text-align: center;
            color: black;
            background-color: #6EC1E4; /* Vibrant Orange-Red color */
            border: none;
            border-radius: 10px;
            padding: 8px 20px;
            text-decoration: none;
            margin: 0px ;
            cursor: pointer;
            box-shadow: 4px 4px 10px rgba(0, 0, 0, 0.3);
            transition: background-color 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;
        }

        .button:hover {
            background-color: #c13a1b; /* Darker shade for hover effect */
            transform: translateY(-3px);
            box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4);
        }
        </style>
    """
    # Define the custom CSS for the container
    container_style = """
        <style>
        .custom-container {
            border: 5px solid #FF5733; /* Thicker border with orange-red color */
            border-radius: 10px;        /* Rounded corners */
            background-color: #F5F5DC; /* Light beige background color */
            padding: 20px;              /* Padding inside the container */
            margin: 10px 0;             /* Margin outside the container */
            box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.2); /* Shadow for depth */
        }
        </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)
    # Inject the custom CSS
    st.markdown(container_style, unsafe_allow_html=True)


    # with st.sidebar:
    #     # img_path = "imgs/Oracle_logo.png"
    #     # st.image(img_path, width=250)
    #     st.caption('Powered by 🦙💬 _:blue[Command R+ and Phind Codellama 34B V2]_')

    #     with st.form('testsql'):
    #         sql = st.text_input("Test your SQL:")
    #         submitted = st.form_submit_button(label="Run my SQL", help='Input your SQL Query')
    #         if submitted:

    #             try:
    #                 st.session_state.my_SQL_output_data, code_ = execute_query(sql, data_file_path)


    #                 if code_== 200:
    #                     if 'my_SQL_output_data' in st.session_state:
    #                         st.markdown("<h4 style='text-align: left; color: Black;'>Your SQL Result</h4>", unsafe_allow_html=True)
    #                         with st.expander('Your SQL Output'):
    #                             st.table(st.session_state.my_SQL_output_data)
    #                 else:
    #                     pass
    #                     # with st.expander("See Data"):
    #                     #     st.session_state.data
    #                     st.session_state.generate_sql_captured = True        



    #             except Exception as e:
    #                 logger.error(e)
    #                 st.error(e)
            

    e = st.empty()

    with e.container():
        cols0 = st.columns([3, 3],  gap="medium")

        with cols0[0]:

            with st.form('chunlkerrr'):
                # Injecting the style
                st.markdown(button_style, unsafe_allow_html=True)
                # Creating the button-like markdown
                st.markdown("<h3 class='button'>Query Window</h3>", unsafe_allow_html=True)
                # st.markdown("<h3 style='text-align: center; color: Black;'>Query Window</h3>", unsafe_allow_html=True)
                st.divider()  # 👈 Draws a horizontal rule

                col1, col2 = st.columns(spec=2, gap='medium')

                with col1:
                    select_llm = st.selectbox(
                                "Select a LLM 👇",
                                ("Cohere Command","mistral"))

                st.divider()
                query = st.text_input("Enter your Query in Natural Language 👇 :red[[English]]")
                query = remove_surrounding_quotes(query)
                submitted = st.form_submit_button(label="Generate", help='Please input a valid File Path')
                
                st.session_state.is_ambiguous = 'False'
                
                if submitted:
                    
                    with st.spinner("In progress..."):
                        if len(query)>10:
                            try:
                                vars = GetConfig()
                                COHERE_API_KEY = vars.COHERE_API_KEY
                                generator = Generate(query)
                                st.session_state.prompt = generator.get_prompt()

                                co = cohere.Client(api_key = COHERE_API_KEY)

                                response = co.generate(
                                    model = "command",
                                    prompt=st.session_state.prompt,
                                    seed=32
                                )

                                clean_json_string = extract_between_curly_braces(response.generations[0].text)
                                st.session_state.response = clean_json_string

                                # langchan_cohere_model = Cohere(max_tokens=256, seed=43,  temperature=0, model = "command",api_key = COHERE_API_KEY)
                                # response = langchan_cohere_model.invoke(st.session_state.prompt)

                                # clean_json_string = extract_between_curly_braces(response)
                                # st.session_state.response = clean_json_string
                                
                                
                                logger.info(f'Result generated...')

                            except Exception as e:
                                st.error(e)
                                logger.info("Error occured in ambiguity check => "+str(e))
                        else:
                            st.session_state.response = {"response": "Please enter a meaningful query."}

        
        with cols0[1]:
            
            try:
                with st.container(height=800, border=True):
                        
                        try:
                            with st.spinner("In progress..."):
                                st.markdown(button_style, unsafe_allow_html=True)

                                st.markdown("<h3 class='button' style='text-align: center; color: Black;'>Output Window</h3>", unsafe_allow_html=True)
                                st.divider()
                                st.markdown('\n\n\n\n\n\n\n\n\n\n\n\n\n',
                                                unsafe_allow_html=True,
                                            )
                                st.markdown('\n\n\n\n\n\n\n\n\n\n\n\n\n',
                                                unsafe_allow_html=True,
                                            )   
                                if 'prompt' in st.session_state:
                                    with st.expander("See Prompt"):
                                        st.markdown("<h5 style='text-align: left; color: Black;'>Prompt Used</h5>", unsafe_allow_html=True)
                                        st.code(st.session_state.prompt)

                                if 'response' in st.session_state:
                                    st.markdown("<h5 style='text-align: left; color: Black;'>Generated Response</h5>", unsafe_allow_html=True)
                                    # if code_== 200:
                                    with st.expander("See Data"):
                                        st.code(st.session_state.response, language="JSON", line_numbers=True)
                                    # else:
                                    #     pass

                                try:
                                    col1, col2, col3 = st.columns(3)

                                    utils = Utils()

                                    token_counts = utils.calculate_token_counts(st.session_state.prompt, st.session_state.response)
                                    col1.metric(label="Input Tokens", value=token_counts['input_tokens'],delta_color="inverse")
                                    col2.metric(label="Output Tokens", value=token_counts['output_tokens'],delta_color="inverse")
                                    col3.metric(label="Total Tokens", value=token_counts['total_tokens'],delta_color="inverse")

                                except ValueError as e:
                                    logger.exception(f"An error occurred: {e}")

                        except Exception as e:
                                logger.error(f"There was an error {e}")
            
            except Exception as e:
                    st.error(e)

                
            
# Using the special variable  
if __name__=="__main__": 
    main()  