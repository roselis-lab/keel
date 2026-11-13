# Where a control is usually enforced

Open it at step 7, when you turn a linked control into a requirement for this system. A card's `control_mechanism` starts with where the control is enforced, in general terms: model or prompt, agent runtime, tool handler or connector, downstream service or data store, identity, network or platform, repository host or CI, human process. This page maps those layers onto the shapes of system an assessment usually meets, so the requirement names a real component instead of a layer.

It is a starting guess, not a finding. Confirm each enforcement point in the system's code or configuration. A control the system enforces in the model or the prompt is a soft link whatever the card says.

## Function-calling chat application

The application server calls a model API, receives tool calls, and runs them in its own code.

- **Agent runtime** is the application server's tool loop: the code that receives a tool call and dispatches it. Tool allowlist, schema validation, risk-based approval and the approval view live here.
- **Tool handler** is each function the loop calls. Per-operation access control, system-bound recipients and resolved-path checks live here, with the caller's identity taken from the server's session, not from the call.
- **Downstream service** is the database or API the handler calls. Data-level access control lives here when the store supports it.
- **Conversation history** is the server's own record. A model API that takes the full message list makes the application the only place history can be held.
- **Client** is the web or mobile front end. Render-time destination allowlist lives here, through its content security policy.

## Agent in CI

An agent runs as a step of a pipeline, on a runner, with a checkout of the repository.

- **Agent runtime** is the agent's command-line tool on the runner; its permission settings come from the pipeline configuration, not from a prompt, because nobody answers prompts.
- **Platform** is the runner: what it mounts, which secrets the job exposes to which step, its network egress. Credentials kept out of the agent's reach, isolated execution and the destination allowlist are decided here.
- **Repository host** holds branch protection, required reviews, version-bound approval and the independent-approver rule. The agent's token should not carry an exemption from them.
- **CI** decides what later jobs run from what the agent wrote: build-state isolation.

## Workflow tool (n8n, Zapier, Make and similar)

A model node sits among other nodes; each connector node acts with a stored credential.

- **Agent runtime** is the workflow engine. A model node's output becomes another node's input by wiring; the gate is a node placed on that wire, such as an approval node or a validation node, and it holds only if nothing routes around it.
- **Tool handler** is the connector node. Its stored credential is usually the organisation's, not the triggering person's, so per-operation access control must be designed into which credential each node uses.
- **Recipients and destinations** are node parameters. Bind them in the node's configuration instead of mapping them from the model node's output.
- **Platform** is where the workflow tool runs and what it can reach on the network.

## IDE agent (coding assistant on a developer's machine)

The agent runs inside the editor or a terminal with the developer's user account.

- **Agent runtime** is the assistant's own permission layer: per-call prompts, session grants, the approval view, its configuration loader and workspace trust. Most controls for this shape are the vendor's, and the assessment checks which are on.
- **Platform** is the developer's machine: the operating-system user the agent runs as, its credential files, its network. Without a sandbox, the agent can reach whatever the developer can, so credentials kept out of reach and isolated execution decide the blast radius.
- **Repository host** is the backstop for anything the agent pushes.
- **Human process** is the developer approving prompts; the approval view and session-grant scope decide whether that is a control or a formality.

## RAG

A retriever fills the context from an index built from source documents.

- **Downstream data store** is the index. Data-level access control is enforced here, by filtering on the requester's permissions before ranking, when the index supports it.
- **Connector** is the ingestion pipeline and the retrieval code. Where the index has no access lists, the connector carries each document's permissions and re-checks them; ingestion is also where source integrity is checked.
- **Model or prompt** is where "answer only from the provided documents" lives. That instruction is a soft control: it does not stop a document's text from acting as instruction.
- **Client** renders the answer, with its links and images: render-time destination allowlist.
