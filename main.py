import os
import base64
import random
import logging
import asyncio
import platform
import re
import signal
import sys
from getpass import getpass
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image
from io import BytesIO
from playwright.async_api import Page, async_playwright, Browser, BrowserContext
import langchainhub as hub
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, chain as chain_decorator
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict
import nest_asyncio
import yaml

nest_asyncio.apply()

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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config.yaml"

@dataclass
class AgentConfig:
    model: str = "gpt-4-turbo"
    max_tokens: int = 4096
    temperature: float = 0.1
    max_steps: int = 150
    start_url: str = "https://www.google.com"
    headless: bool = False
    browser_args: List[str] = field(default_factory=list)
    screenshot_quality: int = 80
    typing_delay_min: float = 0.08
    typing_delay_max: float = 0.15
    scroll_amount: int = 500
    element_scroll_amount: int = 200
    wait_time: int = 5
    retry_attempts: int = 3
    retry_delay: float = 1.0
    log_level: str = "INFO"

def load_config() -> AgentConfig:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            config_data = yaml.safe_load(f)
        return AgentConfig(**config_data)
    return AgentConfig()

config = load_config()

# Set log level from config
logging.getLogger().setLevel(getattr(logging, config.log_level.upper(), logging.INFO))

# Define TypedDict classes
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
    page: Page
    input: str
    img: str
    bboxes: List[BBox]
    prediction: Prediction
    scratchpad: List[BaseMessage]
    observation: str
    bbox_descriptions: str

def _getpass(env_var: str):
    if not os.environ.get(env_var):
        if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
            try:
                os.environ[env_var] = getpass(f"{env_var}=")
            except Exception:
                os.environ[env_var] = "sk-placeholder"
        else:
            os.environ[env_var] = "sk-placeholder"

_getpass("OPENAI_API_KEY")

# Mark page function
with open("mark_page.js") as f:
    mark_page_script = f.read()

@chain_decorator
async def mark_page(page: Page) -> Dict[str, Any]:
    await page.evaluate(mark_page_script)
    for attempt in range(config.retry_attempts):
        try:
            bboxes = await page.evaluate("markPage()")
            break
        except Exception as e:
            logger.warning(f"Mark page attempt {attempt + 1} failed: {e}")
            if attempt < config.retry_attempts - 1:
                await asyncio.sleep(config.retry_delay)
            else:
                raise
    screenshot = await page.screenshot(type="jpeg", quality=config.screenshot_quality)
    await page.evaluate("unmarkPage()")
    return {
        "img": base64.b64encode(screenshot).decode(),
        "bboxes": bboxes,
    }

async def annotate(state: AgentState) -> AgentState:
    marked_page = await mark_page.with_retry().ainvoke(state["page"])
    return {**state, **marked_page}

# Helper functions
def format_descriptions(state: AgentState) -> AgentState:
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
    action_prefix = "Action: "
    if not text.strip().split("\n")[-1].startswith(action_prefix):
        return {"action": "retry", "args": f"Could not parse LLM Output: {text}"}
    action_block = text.strip().split("\n")[-1]

    action_str = action_block[len(action_prefix) :]
    split_output = action_str.split(" ", 1)
    if len(split_output) == 1:
        action, action_input = split_output[0], None
    else:
        action, action_input = split_output
    action = action.strip()
    if action_input is not None:
        action_input = [
            inp.strip().strip("[]") for inp in action_input.strip().split(";")
        ]
    return {"action": action, "args": action_input}

def update_scratchpad(state: AgentState) -> AgentState:
    old = state.get("scratchpad")
    if old:
        txt = old[0].content
        last_line = txt.rsplit("\n", 1)[-1]
        match = re.match(r"\d+", last_line)
        step = int(match.group()) + 1 if match else 1
    else:
        txt = "Previous action observations:\n"
        step = 1
    txt += f"\n{step}. {state['observation']}"
    return {**state, "scratchpad": [SystemMessage(content=txt)]}

def get_voyager_prompt():
    try:
        if hasattr(hub, "pull"):
            return hub.pull("wfh/web-voyager")
    except Exception:
        pass
    try:
        from langchainhub import Client
        from langchain_core.load import loads
        return loads(Client().pull("wfh/web-voyager"))
    except Exception:
        pass
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
        "that requires interaction, then follow the guidelines and choose one of the following actions:\n\n"
        "1. Click a Web Element.\n"
        "2. Delete existing content in a textbox and then type content.\n"
        "3. Scroll up or down.\n"
        "4. Wait\n"
        "5. Go back\n"
        "6. Return to google to start over.\n"
        "7. Respond with the final answer\n\n"
        "Action should follow: Action: <action> [<element_id>; <optional_input>]\n"
    )
    return ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate(prompt=PromptTemplate(template=system_text, input_variables=[])),
            MessagesPlaceholder(variable_name="scratchpad", optional=True),
            HumanMessagePromptTemplate(prompt=[
                PromptTemplate(template="{input}\n\n{bbox_descriptions}", input_variables=["bbox_descriptions", "input"]),
                ImagePromptTemplate(template={"url": "data:image/png;base64,{img}"}, input_variables=["img"]),
            ]),
        ],
        input_variables=["bbox_descriptions", "img", "input"],
    )

prompt = get_voyager_prompt()

# Initialize LLM
llm = ChatOpenAI(
    model=config.model,
    max_tokens=config.max_tokens,
    temperature=config.temperature,
)

# Main graph setup
agent = annotate | RunnablePassthrough.assign(
    prediction=format_descriptions | prompt | llm | StrOutputParser() | parse
)

# Build and compile graph
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", agent)
graph_builder.add_edge(START, "agent")
graph_builder.add_node("update_scratchpad", update_scratchpad)
graph_builder.add_edge("update_scratchpad", "agent")

# Define tools
async def click(state: AgentState) -> Dict[str, str]:
    page = state["page"]
    click_args = state["prediction"]["args"]
    if click_args is None or len(click_args) != 1:
        return {"observation": f"Failed to click bounding box labeled as number {click_args}"}
    bbox_id = int(click_args[0])
    try:
        bbox = state["bboxes"][bbox_id]
    except Exception:
        return {"observation": f"Error: no bbox for: {bbox_id}"}
    x, y = bbox["x"], bbox["y"]
    await page.mouse.click(x, y)
    return {"observation": f"Clicked {bbox_id}"}

async def type_text(state: AgentState) -> Dict[str, str]:
    page = state["page"]
    type_args = state["prediction"]["args"]
    if type_args is None or len(type_args) != 2:
        return {"observation": f"Failed to type in element from bounding box labeled as number {type_args}"}
    bbox_id = int(type_args[0])
    bbox = state["bboxes"][bbox_id]
    x, y = bbox["x"], bbox["y"]
    text_content = type_args[1]
    await page.mouse.click(x, y)
    select_all = "Meta+A" if platform.system() == "Darwin" else "Control+A"
    await page.keyboard.press(select_all)
    await page.keyboard.press("Backspace")
    for char in text_content:
        await page.keyboard.press(char)
        await asyncio.sleep(random.uniform(config.typing_delay_min, config.typing_delay_max))
    await page.keyboard.press("Enter")
    return {"observation": f"Typed '{text_content}' and submitted"}

async def scroll(state: AgentState) -> Dict[str, str]:
    page = state["page"]
    scroll_args = state["prediction"]["args"]
    if scroll_args is None or len(scroll_args) != 2:
        return {"observation": "Failed to scroll due to incorrect arguments."}

    target, direction = scroll_args

    if target.upper() == "WINDOW":
        scroll_direction = -config.scroll_amount if direction.lower() == "up" else config.scroll_amount
        await page.evaluate(f"window.scrollBy(0, {scroll_direction})")
        return {"observation": f"Scrolled {direction} in window"}
    else:
        target_id = int(target)
        bbox = state["bboxes"][target_id]
        x, y = bbox["x"], bbox["y"]
        scroll_direction = -config.element_scroll_amount if direction.lower() == "up" else config.element_scroll_amount
        await page.mouse.move(x, y)
        await page.mouse.wheel(0, scroll_direction)
        return {"observation": f"Scrolled {direction} in element {target_id}"}

async def wait(state: AgentState) -> Dict[str, str]:
    await asyncio.sleep(config.wait_time)
    return {"observation": f"Waited for {config.wait_time}s."}

async def go_back(state: AgentState) -> Dict[str, str]:
    page = state["page"]
    await page.go_back()
    return {"observation": f"Navigated back a page to {page.url}."}

async def navigate_to(state: AgentState) -> Dict[str, str]:
    page = state["page"]
    nav_args = state["prediction"]["args"]
    if nav_args is None or len(nav_args) != 1:
        return {"observation": "Failed to navigate: URL required"}
    url = nav_args[0]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    await page.goto(url, wait_until="networkidle")
    return {"observation": f"Navigated to {url}"}

tools = {
    "Click": click,
    "Type": type_text,
    "Scroll": scroll,
    "Wait": wait,
    "GoBack": go_back,
    "Navigate": navigate_to,
}

for node_name, tool in tools.items():
    graph_builder.add_node(
        node_name,
        RunnableLambda(tool),
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

graph = graph_builder.compile()

class BrowserAgent:
    def __init__(self, config: AgentConfig = None):
        self.config = config or load_config()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._shutdown = False
        
    async def __aenter__(self):
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
        
    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.config.headless,
            args=self.config.browser_args or None
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        self.page = await self.context.new_page()
        await self.page.goto(self.config.start_url, wait_until="networkidle")
        logger.info(f"Browser started at {self.config.start_url}")
        
    async def stop(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        logger.info("Browser stopped")
        
    async def run(self, question: str, max_steps: int = None) -> str:
        max_steps = max_steps or self.config.max_steps
        event_stream = graph.astream(
            {
                "page": self.page,
                "input": question,
                "scratchpad": [],
            },
            {
                "recursion_limit": max_steps,
            },
        )
        final_answer = None
        steps = []

        def clear_console():
            os.system('cls' if os.name == 'nt' else 'clear')

        def show_image(image_data):
            img = Image.open(BytesIO(base64.b64decode(image_data)))
            img.show()

        async for event in event_stream:
            if "agent" not in event:
                continue
            pred = event["agent"].get("prediction") or {}
            action = pred.get("action")
            action_input = pred.get("args")

            clear_console()
            steps.append(f"{len(steps) + 1}. {action}: {action_input}")
            print("\n".join(steps))

            if "img" in event["agent"]:
                show_image(event["agent"]["img"])

            if "ANSWER" in action:
                final_answer = action_input[0] if action_input else "Task completed"
                break

        return final_answer

async def call_agent(question: str, page: Page, max_steps: int = None) -> str:
    max_steps = max_steps or config.max_steps
    event_stream = graph.astream(
        {
            "page": page,
            "input": question,
            "scratchpad": [],
        },
        {
            "recursion_limit": max_steps,
        },
    )
    final_answer = None
    steps = []

    def clear_console():
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_image(image_data):
        img = Image.open(BytesIO(base64.b64decode(image_data)))
        img.show()

    async for event in event_stream:
        if "agent" not in event:
            continue
        pred = event["agent"].get("prediction") or {}
        action = pred.get("action")
        action_input = pred.get("args")

        clear_console()
        steps.append(f"{len(steps) + 1}. {action}: {action_input}")
        print("\n".join(steps))

        if "img" in event["agent"]:
            show_image(event["agent"]["img"])

        if "ANSWER" in action:
            final_answer = action_input[0] if action_input else "Task completed"
            break

    return final_answer

async def main():
    agent = BrowserAgent()
    await agent.start()
    try:
        result = await agent.run("Find me the latest news on CNN, summarize in 30 words")
        print(f"\nFinal Answer: {result}")
    finally:
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())