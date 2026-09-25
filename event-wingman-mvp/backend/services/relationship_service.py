"""Relationship Service for Networking Intelligence and Network Graph Generation.

Computes topic overlaps, explainable networking recommendations ('Why?'),
proactive insights, and interactive force-directed graph structures.
"""

from typing import Any, Dict, List, Optional
from services.memory_service import MemoryService


class RelationshipService:
    def __init__(self, memory_service: MemoryService):
        self.memory = memory_service

    def find_related_people(self, query_name_or_id: str) -> Dict[str, Any]:
        """Find people with shared interests and provide explainable 'Why?' rationale."""
        target_person = self.memory.get_person_by_name(query_name_or_id)
        if not target_person:
            target_person = self.memory.get_person_by_id(query_name_or_id)

        all_people = self.memory.list_people()
        if not target_person:
            # If not a specific person, search broadly for people sharing top topics
            return {
                "query": query_name_or_id,
                "targetPerson": None,
                "matches": self._find_general_clusters(all_people),
            }

        target_topics = set(t.lower() for t in target_person.get("topics", []))
        target_id = target_person["id"]
        matches = []

        for p in all_people:
            if p["id"] == target_id:
                continue

            p_topics = set(t.lower() for t in p.get("topics", []))
            common_topics = target_topics.intersection(p_topics)

            # Check for partial topic matches and shared keyword tokens (e.g. 'voice' in 'voice agents' and 'multimodal voice AI')
            partial_matches = set()
            for tt in target_topics:
                for pt in p_topics:
                    if (tt in pt or pt in tt) and tt != pt:
                        partial_matches.add(f"{tt} ~ {pt}")

            target_tokens = {
                w for tt in target_topics for w in tt.replace("-", " ").split()
                if len(w) > 2 and w not in {"and", "the", "for", "with", "about", "using"}
            }
            p_tokens = {
                w for pt in p_topics for w in pt.replace("-", " ").split()
                if len(w) > 2 and w not in {"and", "the", "for", "with", "about", "using"}
            }
            shared_tokens = target_tokens.intersection(p_tokens)
            for tok in shared_tokens:
                partial_matches.add(f"shared domain: {tok}")

            shared_company = (
                p.get("company") and target_person.get("company") and
                p["company"].lower() == target_person["company"].lower()
            )

            if common_topics or partial_matches or shared_company:
                shared_str = ", ".join(t.title() for t in common_topics)
                why_explanation = self._build_why_explanation(
                    target_person=target_person,
                    matched_person=p,
                    common_topics=common_topics,
                    partial_matches=partial_matches,
                    shared_company=shared_company,
                )

                matches.append({
                    "person": p,
                    "commonTopics": list(common_topics),
                    "sharedCompany": p.get("company") if shared_company else None,
                    "explanation": why_explanation,
                    "score": len(common_topics) * 2 + len(partial_matches) + (2 if shared_company else 0),
                })

        # Sort by match score
        matches.sort(key=lambda x: x["score"], reverse=True)

        return {
            "query": query_name_or_id,
            "targetPerson": target_person,
            "matches": matches,
        }

    def _build_why_explanation(
        self,
        target_person: Dict[str, Any],
        matched_person: Dict[str, Any],
        common_topics: set,
        partial_matches: set,
        shared_company: bool,
    ) -> str:
        parts = []
        if common_topics:
            topic_str = ", ".join(f"'{t.title()}'" for t in common_topics)
            parts.append(f"Both {target_person['name']} and {matched_person['name']} are interested in {topic_str}.")

        if partial_matches:
            partial_str = "; ".join(partial_matches)
            parts.append(f"Related areas discussed include: {partial_str}.")

        if shared_company:
            parts.append(f"Both work at {target_person['company']}.")

        if not parts:
            parts.append(f"Both have discussed adjacent topics at the event.")

        return " ".join(parts)

    def _find_general_clusters(self, people: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify pairs or clusters of people with overlapping interests."""
        clusters = []
        for i in range(len(people)):
            for j in range(i + 1, len(people)):
                p1 = people[i]
                p2 = people[j]
                t1 = set(t.lower() for t in p1.get("topics", []))
                t2 = set(t.lower() for t in p2.get("topics", []))
                common = t1.intersection(t2)
                if common:
                    clusters.append({
                        "personA": p1,
                        "personB": p2,
                        "commonTopics": list(common),
                        "explanation": f"{p1['name']} ({p1.get('company') or 'Independent'}) and {p2['name']} ({p2.get('company') or 'Independent'}) both share interests in {', '.join(common).title()}.",
                    })
        return clusters

    def get_proactive_insights(self) -> List[Dict[str, Any]]:
        """Generate grounded proactive observations without hallucination."""
        insights = []
        people = self.memory.list_people()
        topics = self.memory.list_topics()
        followups = self.memory.list_followups()

        # 1. Topic frequency insight
        topic_counts: Dict[str, List[str]] = {}
        for p in people:
            for t in p.get("topics", []):
                t_key = t.strip().title()
                if t_key not in topic_counts:
                    topic_counts[t_key] = []
                topic_counts[t_key].append(p["name"])

        for t_name, names in topic_counts.items():
            if len(names) >= 2:
                insights.append({
                    "type": "topic_concentration",
                    "title": f"Strong interest in {t_name}",
                    "message": f"You've met {len(names)} people interested in {t_name}: {', '.join(names)}.",
                    "actionable": True,
                })

        # 2. Overlapping connections
        clusters = self._find_general_clusters(people)
        for c in clusters[:2]:
            insights.append({
                "type": "potential_introduction",
                "title": f"Overlap: {c['personA']['name']} & {c['personB']['name']}",
                "message": c["explanation"],
                "actionable": True,
            })

        # 3. Follow-up reminder
        pending_followups = [f for f in followups if f.get("status") == "draft"]
        for pf in pending_followups[:2]:
            insights.append({
                "type": "pending_followup",
                "title": f"Follow-up with {pf.get('personName', 'Contact')}",
                "message": f"You have an unapproved follow-up draft: '{pf.get('action')}'.",
                "actionable": True,
            })

        return insights

    def get_network_graph(self) -> Dict[str, Any]:
        """Generate structured node-link data for the visual network graph."""
        nodes = []
        links = []
        node_ids = set()

        # Center Node: User
        nodes.append({
            "id": "user_me",
            "label": "Me (You)",
            "type": "me",
            "size": 26,
            "color": "#6366F1",  # Indigo
        })
        node_ids.add("user_me")

        people = self.memory.list_people()
        relationships = self.memory.list_relationships()

        # Add People
        for p in people:
            pid = p["id"]
            nodes.append({
                "id": pid,
                "label": p["name"],
                "type": "person",
                "company": p.get("company"),
                "role": p.get("role"),
                "topics": p.get("topics", []),
                "firstMetAt": p.get("firstMetAt"),
                "size": 20,
                "color": "#10B981",  # Emerald
            })
            node_ids.add(pid)

            # Ensure link from Me -> Person
            links.append({
                "source": "user_me",
                "target": pid,
                "label": "MET",
                "color": "#94A3B8",
            })

            # Add Company Node & Link
            if p.get("company"):
                comp_id = f"comp_{p['company'].lower().replace(' ', '_')}"
                if comp_id not in node_ids:
                    nodes.append({
                        "id": comp_id,
                        "label": p["company"],
                        "type": "company",
                        "size": 16,
                        "color": "#F59E0B",  # Amber
                    })
                    node_ids.add(comp_id)

                links.append({
                    "source": pid,
                    "target": comp_id,
                    "label": "WORKS_AT",
                    "color": "#FBBF24",
                })

            # Add Topic Nodes & Links
            for topic in p.get("topics", []):
                t_clean = topic.strip()
                if not t_clean:
                    continue
                tid = f"topic_{t_clean.lower().replace(' ', '_')}"
                if tid not in node_ids:
                    nodes.append({
                        "id": tid,
                        "label": t_clean,
                        "type": "topic",
                        "size": 14,
                        "color": "#06B6D4",  # Cyan
                    })
                    node_ids.add(tid)

                links.append({
                    "source": pid,
                    "target": tid,
                    "label": "INTERESTED_IN",
                    "color": "#38BDF8",
                })

        # Add Recommendations / Ideas
        recs = self.memory.list_recommendations()
        for r in recs:
            if r.get("recommendedByPersonId") and r["recommendedByPersonId"] in node_ids:
                rid = r["id"]
                content_trunc = (r["content"][:24] + "...") if len(r["content"]) > 24 else r["content"]
                nodes.append({
                    "id": rid,
                    "label": content_trunc,
                    "fullText": r["content"],
                    "type": "recommendation",
                    "size": 12,
                    "color": "#EC4899",  # Pink
                })
                node_ids.add(rid)
                links.append({
                    "source": r["recommendedByPersonId"],
                    "target": rid,
                    "label": "RECOMMENDED",
                    "color": "#F472B6",
                })

        return {
            "nodes": nodes,
            "links": links,
        }
