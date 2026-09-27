# Sequence for a Named Flow

Shows one flow the user names, such as "one chat turn" or "checkout", as the ordered messages between its participants. A reviewer reads it to follow a single request end to end, so the order and the returns must match what the sources say.

- **The flow must be described in a source.** Find where the spine, spec or UX docs walk through it (a flow section, a UX journey, the ADs covering each step) and name that in the diagram's title or first cite. If no source describes the flow, say so, list what's missing as gaps, and don't assemble it from fragments.
- **Participants**: the people, containers, services and external systems the flow touches, left to right in the order they first appear. Kinds as for the containers diagram; `service` for an Azure resource and `external` for a third party.
- **Messages**, in order: each call or event, labelled with what is asked or sent ("POST /messages", "retrieve context"), cited to the step's source. A reply is its own message with `"return": true`, drawn only when the source states what comes back. `data` marks PII or PHI on a message under the same rule as the data flow diagram.
- **Branches and loops**: draw the main path the source describes. Alternatives the source mentions go in the gaps as "not drawn: <alternative>", so the reader knows they exist.

Gaps this diagram usually turns up: timeouts and retries; what the user sees on failure; whether a step is synchronous; steps the UX describes that no AD assigns to a container.
