"""Opt-in shadow ledger for coordinate-level task responsibility.

This module never blocks or rewrites an action.  It derives a compact current
view from the latest task graph, explicit current-leader assignments, and
verified local completion.  The runtime can append that view to a worker prompt
for controlled experiments.
"""
from collections import defaultdict
import re


COORD = re.compile(r"\(\s*(-?\d+)\s*,\s*(-?\d+)\s*\)")
ARROW_ASSIGN = re.compile(
    r"(?:AGENT[_ ]?)?(\d+)\s*(?:→|->)\s*(\(\s*-?\d+\s*,\s*-?\d+\s*\))", re.I)
DIRECT_ASSIGN = re.compile(
    r"\b(?:you\s+(?:take|own|handle)|proceed\s+to|please\s+(?:take|proceed\s+to)|"
    r"finish\s+cutting|keep\s+cutting|move\s+to|head\s+to|then\s+take)\s+"
    r"((?:\(\s*-?\d+\s*,\s*-?\d+\s*\))(?:\s*(?:,|/|and|then)\s*"
    r"\(\s*-?\d+\s*,\s*-?\d+\s*\))*)", re.I)
NEGATIVE = re.compile(r"\b(?:avoid|do not|don't|skip|leave|not take|not go)\b", re.I)


def coordinates(text, targets):
    return [tuple(map(int, match)) for match in COORD.findall(text or "")
            if tuple(map(int, match)) in targets]


def task_targets(text, targets):
    """Only explicit cutting tasks establish graph ownership."""
    if not re.match(r"\s*(?:continue\s+)?cut\b", text or "", re.I):
        return []
    return coordinates(text, targets)


def explicit_assignments(content, recipient, targets, direct=True):
    found = defaultdict(set)
    for agent, raw_coord in ARROW_ASSIGN.findall(content or ""):
        coord = tuple(map(int, COORD.search(raw_coord).groups()))
        if coord in targets:
            found[str(agent)].add(coord)
    if direct:
        for match in DIRECT_ASSIGN.finditer(content or ""):
            if NEGATIVE.search((content or "")[max(0, match.start() - 20):match.start()]):
                continue
            found[str(recipient)].update(coordinates(match.group(1), targets))
    return {agent: sorted(values) for agent, values in found.items()}


class ResponsibilityLedger:
    """Small event-derived index used only for prompt advice and audit events."""

    def __init__(self, emit):
        self.emit = emit
        self.version = -1
        self.message_cursor = 0
        self.targets = set()
        self.owners = defaultdict(set)       # target -> {(agent, edge)}
        self.provisional = defaultdict(set)  # target -> {(agent, edge)}
        self.completed = set()

    def sync(self, graph):
        raw_targets = graph.world.get("task_parameters", {}).get("target_trees", [])
        self.targets = {tuple(map(int, coord)) for coord in raw_targets}
        if graph.version != self.version:
            owners = defaultdict(set)
            for edge in graph.edges.values():
                for agent, task in edge.get("tasks", {}).items():
                    for target in task_targets(task, self.targets):
                        if target not in self.completed:
                            owners[target].add((str(agent), edge["id"]))
            self.owners = owners
            self.provisional = defaultdict(set)
            self.version = graph.version
            self.emit("TASK_RESPONSIBILITY_LEDGER_SYNCED", {
                "graph_version": graph.version,
                "owned_target_count": len(owners),
                "collision_target_count": sum(
                    len({agent for agent, _ in records}) > 1
                    for records in owners.values()),
                "completed_target_count": len(self.completed),
                "mode": "shadow_prompt_only"})
        self._sync_messages(graph)

    def _sync_messages(self, graph):
        for message in graph.messages[self.message_cursor:]:
            source = graph.edges.get(message.get("source"))
            if (not source or source.get("leader") != message.get("sender") or
                    message.get("graph_version") != graph.version):
                continue
            recipient = str(message.get("recipient"))
            fanout = [item for item in graph.messages
                      if item.get("sender") == message.get("sender")
                      and item.get("source") == message.get("source")
                      and item.get("step") == message.get("step")
                      and item.get("content") == message.get("content")]
            assignments = explicit_assignments(
                message.get("content", ""), recipient, self.targets,
                direct=len({item.get("recipient") for item in fanout}) == 1)
            for assignee, targets in assignments.items():
                if assignee not in source.get("members", []):
                    continue
                for target in targets:
                    if target in self.completed:
                        continue
                    existing_edges = {edge for _, edge in self.owners.get(target, set())}
                    record = (assignee, source["id"])
                    if not existing_edges or existing_edges == {source["id"]}:
                        self.owners[target] = {record}
                        self.provisional[target].clear()
                    else:
                        self.provisional[target].add(record)
        self.message_cursor = len(graph.messages)

    def record_returned_cut(self, agent, command, before, after, step):
        if not before or not after or list(command or []) != [1, 0, 0]:
            return False
        try:
            target = tuple(map(int, before["position"]))
            before_count = int(before.get("facts", {}).get("current_cell"))
            after_count = int(after.get("facts", {}).get("current_cell"))
        except (KeyError, TypeError, ValueError):
            return False
        if target not in self.targets or before_count <= 0 or after_count != 0:
            return False
        status = self.status(agent, target)
        self.completed.add(target)
        self.owners.pop(target, None)
        self.provisional.pop(target, None)
        self.emit("TASK_RESPONSIBILITY_ENV_COMPLETE", {
            "step": step, "agent": str(agent), "target": list(target),
            "authority_at_completion": status["status"]})
        return True

    def status(self, agent, target):
        agent = str(agent)
        target = tuple(map(int, target))
        owners = sorted(self.owners.get(target, set()))
        claims = sorted(self.provisional.get(target, set()))
        owner_agents = {item[0] for item in owners}
        provisional_agents = {item[0] for item in claims}
        if target in self.completed:
            kind = "ALREADY_COMPLETE"
        elif agent in owner_agents:
            kind = "CURRENT_OWNER"
        elif agent in provisional_agents:
            kind = "PROVISIONAL_ALLOWED"
        elif len(owner_agents) > 1:
            kind = "AMBIGUOUS_MULTI_OWNER"
        elif owner_agents:
            kind = "UNAUTHORIZED_AGAINST_OWNER"
        else:
            kind = "UNOWNED"
        return {"status": kind, "target": list(target), "owners": owners,
                "provisional_claims": claims, "graph_version": self.version}

    def current_cell_status(self, agent, position):
        if position is None:
            return None
        target = tuple(map(int, position))
        return self.status(agent, target) if target in self.targets else None

    @staticmethod
    def reminder(status):
        if not status or status["status"] in {"CURRENT_OWNER", "UNOWNED"}:
            return ""
        target = tuple(status["target"])
        if status["status"] == "PROVISIONAL_ALLOWED":
            detail = ("Your current leader explicitly assigned this target. The cross-group "
                      "transfer is provisional but may proceed; report verified completion.")
        elif status["status"] == "UNAUTHORIZED_AGAINST_OWNER":
            agents = sorted({agent for agent, _ in status["owners"]})
            detail = (f"Current owner(s): {agents}. You have no current assignment for this "
                      "target. Do not modify it based only on an older task or proximity; "
                      "choose current non-conflicting work.")
        elif status["status"] == "ALREADY_COMPLETE":
            detail = "Verified environment evidence already closed this target; do not repeat it."
        else:
            detail = ("Multiple current owners remain. Treat this as an unresolved collision; "
                      "coordinate rather than assuming exclusive responsibility.")
        return ("\n[VERSIONED RESPONSIBILITY LEDGER — SHADOW ADVICE, NOT AN ACTION GATE]\n"
                f"Graph version: {status['graph_version']}; target: {target}; "
                f"status: {status['status']}. {detail}\n"
                "Environment completion > newer graph/leader event > older assignment.\n"
                "[/VERSIONED RESPONSIBILITY LEDGER]\n")
