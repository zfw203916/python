from typing import TypedDict
from langgraph.graph import StateGraph, END


class State(TypedDict):
    text: str


def node_a(state: State) -> State:
    return {"text": state["text"] + " -> A"}


def node_b(state: State) -> State:
    return {"text": state["text"] + " -> B"}


graph = StateGraph(State)
graph.add_node("a", node_a)
graph.add_node("b", node_b)
graph.set_entry_point("a")
graph.add_edge("a", "b")
graph.add_edge("b", END)

app = graph.compile()
print(app.invoke({"text": "start"}))