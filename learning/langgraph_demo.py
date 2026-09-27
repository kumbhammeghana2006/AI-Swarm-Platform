from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    name: str


def greeter(state: State):
    return {
        "name": "Indra"
    }
def responder(state: State):
    return {
        "name": state["name"] + " is ready!"
    }


graph = StateGraph(State)

graph.add_node("greeter", greeter)
graph.add_node("responder", responder)
graph.add_edge(START, "greeter")
graph.add_edge("greeter", "responder")
graph.add_edge("responder", END)
app = graph.compile()
result = app.invoke({
    "name": ""
})
print(result)    