"""
Enhanced Production LangGraph Browser Agent
Modern UI with no hardcoded values
"""
import os
import sys
import logging
import asyncio
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
from playwright.async_api import async_playwright
import base64
from PIL import Image
from io import BytesIO
import random
import re
from typing import List, Optional, Dict, Any

# Import configuration
from config import Config

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import LangGraph components
try:
    import nest_asyncio
    from langchain_core.messages import BaseMessage, SystemMessage
    from langchain_core.output_parsers import StrOutputParser
    from langchain_openai import ChatOpenAI
    from langgraph.graph import END, START, StateGraph
    from typing_extensions import TypedDict
    from langchain_core.runnables import RunnableLambda, RunnablePassthrough
    import langchainhub as hub
    
    nest_asyncio.apply()
    
    # Python 3.14 / nest_asyncio compatibility fix for sniffio
    try:
        import sniffio
        _orig_current_async_library = sniffio.current_async_library
        def _safe_current_async_library():
            try:
                return _orig_current_async_library()
            except sniffio.AsyncLibraryNotFoundError:
                try:
                    asyncio.get_running_loop()
                    return "asyncio"
                except RuntimeError:
                    raise
        sniffio.current_async_library = _safe_current_async_library
    except Exception:
        pass

    logger.info(f"{Config.APP_NAME} components loaded successfully")
except ImportError as e:
    logger.error(f"Failed to import required components: {e}")
    sys.exit(1)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
CORS(app)

# TypedDict classes
class BBox(TypedDict):
    x: float
    y: float
    text: str
    type: str
    ariaLabel: str

class Prediction(TypedDict):
    action: str
    args: Optional[List[str]]

class AgentState(TypedDict):
    page: Any
    input: str
    img: str
    bboxes: List[BBox]
    prediction: Prediction
    scratchpad: List[BaseMessage]
    observation: str

mark_page_script = ""
if Config.MARK_PAGE_SCRIPT.exists():
    with open(Config.MARK_PAGE_SCRIPT, 'r', encoding='utf-8') as f:
        mark_page_script = f.read()
    logger.info("mark_page.js loaded successfully")
else:
    logger.error(f"mark_page.js not found at {Config.MARK_PAGE_SCRIPT}")

async def click(state: AgentState):
    """Click on an element"""
    try:
        page = state["page"]
        click_args = state["prediction"]["args"]
        if click_args is None or len(click_args) != 1:
            return f"Failed to click bounding box labeled as number {click_args}"
        bbox_id = int(click_args[0])
        bbox = state["bboxes"][bbox_id]
        x, y = bbox["x"], bbox["y"]
        await page.mouse.click(x, y)
        logger.info(f"Clicked element {bbox_id} at ({x}, {y})")
        return f"Clicked {bbox_id}"
    except Exception as e:
        logger.error(f"Click error: {e}")
        return f"Error clicking: {str(e)}"

async def type_text(state: AgentState):
    """Type text into an element"""
    try:
        page = state["page"]
        type_args = state["prediction"]["args"]
        if type_args is None or len(type_args) != 2:
            return f"Failed to type in element from bounding box labeled as number {type_args}"
        bbox_id = int(type_args[0])
        bbox = state["bboxes"][bbox_id]
        x, y = bbox["x"], bbox["y"]
        text_content = type_args[1]
        await page.mouse.click(x, y)
        select_all = "Meta+A" if sys.platform == "darwin" else "Control+A"
        await page.keyboard.press(select_all)
        await page.keyboard.press("Backspace")
        for char in text_content:
            await page.keyboard.press(char)
            await asyncio.sleep(random.uniform(0.08, 0.15))
        await page.keyboard.press("Enter")
        logger.info(f"Typed '{text_content}' into element {bbox_id}")
        return f"Typed {text_content} and submitted"
    except Exception as e:
        logger.error(f"Type error: {e}")
        return f"Error typing: {str(e)}"

async def scroll(state: AgentState):
    """Scroll the page"""
    try:
        page = state["page"]
        scroll_args = state["prediction"]["args"]
        if scroll_args is None or len(scroll_args) != 2:
            return "Failed to scroll due to incorrect arguments."
        target, direction = scroll_args
        scroll_amount = 500 if target.upper() == "WINDOW" else 200
        scroll_direction = -scroll_amount if direction.lower() == "up" else scroll_amount
        
        if target.upper() == "WINDOW":
            await page.evaluate(f"window.scrollBy(0, {scroll_direction})")
        else:
            target_id = int(target)
            bbox = state["bboxes"][target_id]
            x, y = bbox["x"], bbox["y"]
            await page.mouse.move(x, y)
            await page.mouse.wheel(0, scroll_direction)
        
        logger.info(f"Scrolled {direction}")
        return f"Scrolled {direction} in {'window' if target.upper() == 'WINDOW' else 'element'}"
    except Exception as e:
        logger.error(f"Scroll error: {e}")
        return f"Error scrolling: {str(e)}"

async def wait(state: AgentState):
    """Wait for a period"""
    sleep_time = 5
    await asyncio.sleep(sleep_time)
    logger.info(f"Waited {sleep_time}s")
    return f"Waited for {sleep_time}s."

async def go_back(state: AgentState):
    """Navigate back"""
    try:
        page = state["page"]
        await page.go_back()
        logger.info(f"Navigated back to {page.url}")
        return f"Navigated back a page to {page.url}."
    except Exception as e:
        logger.error(f"Go back error: {e}")
        return f"Error going back: {str(e)}"

async def to_google(state: AgentState):
    """Navigate to Google"""
    try:
        page = state["page"]
        await page.goto("https://www.google.com/")
        logger.info("Navigated to Google")
        return "Navigated to google.com."
    except Exception as e:
        logger.error(f"Navigate error: {e}")
        return f"Error navigating: {str(e)}"

async def mark_page(page):
    """Mark interactive elements on page"""
    try:
        await page.evaluate(mark_page_script)
        for _ in range(10):
            try:
                bboxes = await page.evaluate("markPage()")
                break
            except Exception:
                await asyncio.sleep(3)
        screenshot = await page.screenshot()
        await page.evaluate("unmarkPage()")
        return {
            "img": base64.b64encode(screenshot).decode(),
            "bboxes": bboxes,
        }
    except Exception as e:
        logger.error(f"Mark page error: {e}")
        raise

async def annotate(state):
    """Annotate page with bounding boxes"""
    marked_page = await mark_page(state["page"])
    return {**state, **marked_page}

def format_descriptions(state):
    """Format bounding box descriptions"""
    labels = []
    for i, bbox in enumerate(state["bboxes"]):
        text = bbox.get("ariaLabel") or ""
        if not text.strip():
            text = bbox["text"]
        el_type = bbox.get("type")
        labels.append(f'{i} (<{el_type}/>): "{text}"')
    bbox_descriptions = "\nValid Bounding Boxes:\n" + "\n".join(labels)
    return {**state, "bbox_descriptions": bbox_descriptions}

def parse(text: str) -> dict:
    """Parse LLM output"""
    action_prefix = "Action: "
    if not text.strip().split("\n")[-1].startswith(action_prefix):
        return {"action": "retry", "args": f"Could not parse LLM Output: {text}"}
    action_block = text.strip().split("\n")[-1]
    action_str = action_block[len(action_prefix):]
    split_output = action_str.split(" ", 1)
    if len(split_output) == 1:
        action, action_input = split_output[0], None
    else:
        action, action_input = split_output
    action = action.strip()
    if action_input is not None:
        action_input = [inp.strip().strip("[]") for inp in action_input.strip().split(";")]
    return {"action": action, "args": action_input}

def update_scratchpad(state: AgentState):
    """Update agent scratchpad"""
    old = state.get("scratchpad")
    if old:
        txt = old[0].content
        last_line = txt.rsplit("\n", 1)[-1]
        step = int(re.match(r"\d+", last_line).group()) + 1
    else:
        txt = "Previous action observations:\n"
        step = 1
    txt += f"\n{step}. {state['observation']}"
    return {**state, "scratchpad": [SystemMessage(content=txt)]}

def get_voyager_prompt():
    """Retrieve the Web-Voyager prompt safely from langchainhub or fallback template"""
    try:
        if hasattr(hub, "pull"):
            return hub.pull("wfh/web-voyager")
    except Exception as e:
        logger.debug(f"hub.pull not available: {e}")

    try:
        from langchainhub import Client
        from langchain_core.load import loads
        client = Client()
        res = client.pull("wfh/web-voyager")
        return loads(res)
    except Exception as e:
        logger.warning(f"langchainhub Client pull failed: {e}, using built-in Web-Voyager prompt template")

    from langchain_core.prompts import (
        ChatPromptTemplate,
        SystemMessagePromptTemplate,
        MessagesPlaceholder,
        HumanMessagePromptTemplate,
        PromptTemplate
    )
    from langchain_core.prompts.image import ImagePromptTemplate

    system_text = (
        "Imagine you are a robot browsing the web, just like humans. Now you need to complete a task. "
        "In each iteration, you will receive an Observation that includes a screenshot of a webpage and some texts. "
        "This screenshot will feature Numerical Labels placed in the TOP LEFT corner of each Web Element. "
        "Carefully analyze the visual information to identify the Numerical Label corresponding to the Web Element "
        "that requires interaction, then follow the guidelines and choose one of the following actions:\\n\\n"
        "1. Click a Web Element.\\n"
        "2. Delete existing content in a textbox and then type content.\\n"
        "3. Scroll up or down.\\n"
        "4. Wait \\n"
        "5. Go back\\n"
        "7. Return to google to start over.\\n"
        "8. Respond with the final answer\\n\\n"
        "Correspondingly, Action should STRICTLY follow the format:\\n\\n"
        "- Click [Numerical_Label] \\n"
        "- Type [Numerical_Label]; [Content] \\n"
        "- Scroll [Numerical_Label or WINDOW]; [up or down] \\n"
        "- Wait \\n"
        "- GoBack\\n"
        "- Google\\n"
        "- ANSWER; [content]\\n\\n"
        "Key Guidelines You MUST follow:\\n\\n"
        "* Action guidelines *\\n"
        "1) Execute only one action per iteration.\\n"
        "2) When clicking or typing, ensure to select the correct bounding box.\\n"
        "3) Numeric labels lie in the top-left corner of their corresponding bounding boxes and are colored the same.\\n\\n"
        "* Web Browsing Guidelines *\\n"
        "1) Don't interact with useless web elements like Login, Sign-in, donation that appear in Webpages\\n"
        "2) Select strategically to minimize time wasted.\\n\\n"
        "Your reply should strictly follow the format:\\n\\n"
        "Thought: {Your brief thoughts (briefly summarize the info that will help ANSWER)}\\n"
        "Action: {One Action format you choose}\\n"
        "Then the User will provide:\\n"
        "Observation: {A labeled screenshot Given by User}\\n"
    )

    return ChatPromptTemplate(
        input_variables=["bbox_descriptions", "img", "input"],
        optional_variables=["scratchpad"],
        messages=[
            SystemMessagePromptTemplate(
                prompt=[PromptTemplate(input_variables=[], template=system_text)]
            ),
            MessagesPlaceholder(variable_name="scratchpad", optional=True),
            HumanMessagePromptTemplate(
                prompt=[
                    ImagePromptTemplate(
                        input_variables=["img"],
                        template={"url": "data:image/png;base64,{img}"}
                    ),
                    PromptTemplate(
                        input_variables=["bbox_descriptions"],
                        template="{bbox_descriptions}"
                    ),
                    PromptTemplate(
                        input_variables=["input"],
                        template="{input}"
                    )
                ]
            )
        ]
    )

def create_agent_graph(api_key: str):
    """Create LangGraph agent"""
    try:
        os.environ["OPENAI_API_KEY"] = api_key
        
        prompt = get_voyager_prompt()
        llm = ChatOpenAI(model=Config.OPENAI_MODEL, max_tokens=Config.OPENAI_MAX_TOKENS)
        
        agent = annotate | RunnablePassthrough.assign(
            prediction=format_descriptions | prompt | llm | StrOutputParser() | parse
        )
        
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("agent", agent)
        graph_builder.add_edge(START, "agent")
        graph_builder.add_node("update_scratchpad", update_scratchpad)
        graph_builder.add_edge("update_scratchpad", "agent")
        
        tools = {
            "Click": click,
            "Type": type_text,
            "Scroll": scroll,
            "Wait": wait,
            "GoBack": go_back,
            "Google": to_google,
        }
        
        for node_name, tool in tools.items():
            graph_builder.add_node(
                node_name,
                RunnableLambda(tool) | (lambda observation: {"observation": observation}),
            )
            graph_builder.add_edge(node_name, "update_scratchpad")
        
        def select_tool(state: AgentState):
            action = state["prediction"]["action"].strip().rstrip(";")
            if action == "ANSWER":
                return END
            if action == "retry":
                return "agent"
            return action
        
        graph_builder.add_conditional_edges("agent", select_tool)
        return graph_builder.compile()
    except Exception as e:
        logger.error(f"Error creating agent graph: {e}")
        raise

async def run_browser_agent(task: str, api_key: str, max_steps: int) -> Dict[str, Any]:
    """Run the browser agent"""
    logger.info(f"Starting agent with task: {task}")
    
    try:
        graph = create_agent_graph(api_key)
        
        browser_instance = await async_playwright().start()
        browser = await browser_instance.chromium.launch(headless=Config.BROWSER_HEADLESS)
        page = await browser.new_page()
        await page.goto("https://www.google.com")
        
        event_stream = graph.astream(
            {
                "page": page,
                "input": task,
                "scratchpad": [],
            },
            {
                "recursion_limit": max_steps,
            },
        )
        
        final_answer = None
        steps = []
        final_url = ""
        
        async for event in event_stream:
            if "agent" not in event:
                continue
            pred = event["agent"].get("prediction") or {}
            action = pred.get("action")
            action_input = pred.get("args")
            
            step_info = f"{len(steps) + 1}. {action}: {action_input}"
            steps.append(step_info)
            logger.info(step_info)
            
            if "ANSWER" in action:
                final_answer = action_input[0] if action_input else "Task completed"
                break
        
        final_url = page.url
        
        await browser.close()
        await browser_instance.stop()
        
        logger.info(f"Agent completed. Final URL: {final_url}")
        
        return {
            "success": True,
            "result": final_answer or "Task completed successfully",
            "url": final_url,
            "steps": steps
        }
    except Exception as e:
        logger.error(f"Agent execution error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "url": "",
            "steps": []
        }

from templates import ULTRA_ATTRACTIVE_TEMPLATE

HTML_TEMPLATE = ULTRA_ATTRACTIVE_TEMPLATE


@app.route('/')
def index():
    """Render main page with dynamic configuration"""
    return render_template_string(
        HTML_TEMPLATE,
        app_name=Config.APP_NAME,
        app_description=Config.APP_DESCRIPTION,
        app_version=Config.APP_VERSION,
        default_max_steps=Config.DEFAULT_MAX_STEPS,
        min_max_steps=Config.MIN_MAX_STEPS,
        max_max_steps=Config.MAX_MAX_STEPS,
        openai_model=Config.OPENAI_MODEL,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}"
    )

@app.route('/execute', methods=['POST'])
def execute_agent():
    """Execute browser agent"""
    try:
        data = request.get_json()
        api_key = data.get('api_key', '').strip()
        task = data.get('task', '').strip()
        max_steps = int(data.get('max_steps', Config.DEFAULT_MAX_STEPS))

        # Validation
        if not api_key:
            return jsonify({'success': False, 'error': 'API key is required'}), 400
        if not task:
            return jsonify({'success': False, 'error': 'Task description is required'}), 400
        if max_steps < Config.MIN_MAX_STEPS or max_steps > Config.MAX_MAX_STEPS:
            return jsonify({
                'success': False, 
                'error': f'Max steps must be between {Config.MIN_MAX_STEPS} and {Config.MAX_MAX_STEPS}'
            }), 400

        logger.info(f"Executing agent task: {task[:100]}...")
        
        result = asyncio.run(run_browser_agent(task, api_key, max_steps))
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Execute endpoint error: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'url': '',
            'steps': []
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': Config.APP_VERSION,
        'app_name': Config.APP_NAME
    })

@app.route('/config')
def get_config():
    """Get public configuration (no secrets)"""
    return jsonify({
        'app_name': Config.APP_NAME,
        'version': Config.APP_VERSION,
        'openai_model': Config.OPENAI_MODEL,
        'default_max_steps': Config.DEFAULT_MAX_STEPS,
        'min_max_steps': Config.MIN_MAX_STEPS,
        'max_max_steps': Config.MAX_MAX_STEPS,
    })

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass
    print("\n" + "=" * 80)
    print(f"[+] {Config.APP_NAME} v{Config.APP_VERSION}")
    print("=" * 80)
    print(f"\n Server URLs:")
    print(f"   * Local:      http://localhost:{Config.PORT}")
    print(f"   * Network:    http://{Config.HOST}:{Config.PORT}")
    print(f"   * Health:     http://localhost:{Config.PORT}/health")
    print(f"   * Config:     http://localhost:{Config.PORT}/config")
    print(f"\n Configuration:")
    print(f"   * Model:      {Config.OPENAI_MODEL}")
    print(f"   * Max Steps:  {Config.MIN_MAX_STEPS}-{Config.MAX_MAX_STEPS}")
    print(f"   * Headless:   {Config.BROWSER_HEADLESS}")
    print(f"   * Log Level:  {Config.LOG_LEVEL}")
    print("\n" + "=" * 80 + "\n")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        threaded=True
    )

