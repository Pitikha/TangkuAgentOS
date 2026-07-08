# 📊 TangkuAgentOS Runtime Communication Flow Diagrams

This document contains Mermaid diagrams illustrating the communication flow in TangkuAgentOS.

---

## 🏗️ **1. Overall System Architecture**

```mermaid
graph TD
    subgraph Kernel["Kernel Runtime (Orchestrator)"]
        KM[KernelManager]
        CR[Communication Framework]
        RR[RuntimeRegistry]
        RD[RuntimeDiscovery]
        RH[RuntimeHealthService]
    end

    subgraph Runtimes["All Runtimes"]
        MR[MemoryRuntime]
        KR[KnowledgeRuntime]
        WR[WorkflowRuntime]
        PR[ProviderRuntime]
        MoR[ModelRuntime]
        TR[TerminalRuntime]
        SR[SecurityRuntime]
        AR[AutomationRuntime]
        WSR[WorkspaceRuntime]
        ...[...]
    end

    subgraph Buses["Communication Buses"]
        MB[MessageBus]
        EB[EventBus]
        CB[CommandBus]
        QB[QueryBus]
        BB[BroadcastBus]
        RRB[RequestResponseBus]
    end

    subgraph Services["Runtime Services"]
        RS[RuntimeRegistry]
        DS[DiscoveryService]
        HS[HealthService]
        SS[StatusManager]
        MS[MetadataRegistry]
        CS[ContextManager]
        SES[SessionManager]
    end

    KM -->|initializes| CR
    CR -->|creates| MB
    CR -->|creates| EB
    CR -->|creates| CB
    CR -->|creates| QB
    CR -->|creates| BB
    CR -->|creates| RRB

    CR -->|starts| RS
    CR -->|starts| DS
    CR -->|starts| HS
    CR -->|starts| SS
    CR -->|starts| MS
    CR -->|starts| CS
    CR -->|starts| SES

    MR -->|uses| MB
    MR -->|uses| EB
    MR -->|uses| CB
    MR -->|uses| QB
    MR -->|uses| BB
    MR -->|uses| RRB

    KR -->|uses| MB
    KR -->|uses| EB
    KR -->|uses| CB
    KR -->|uses| QB

    WR -->|uses| MB
    WR -->|uses| EB
    WR -->|uses| CB
    WR -->|uses| QB

    PR -->|uses| MB
    PR -->|uses| EB
    PR -->|uses| CB
    PR -->|uses| QB

    MB -->|routes to| MR
    MB -->|routes to| KR
    MB -->|routes to| WR
    MB -->|routes to| PR

    EB -->|publishes to| MR
    EB -->|publishes to| KR
    EB -->|publishes to| WR
    EB -->|publishes to| PR

    CB -->|sends to| MR
    CB -->|sends to| KR
    CB -->|sends to| WR
    CB -->|sends to| PR

    QB -->|asks| MR
    QB -->|asks| KR
    QB -->|asks| WR
    QB -->|asks| PR

    style KM fill:#f9f,stroke:#333
    style CR fill:#bbf,stroke:#333
    style MR fill:#9f9,stroke:#333
    style KR fill:#9f9,stroke:#333
    style WR fill:#9f9,stroke:#333
    style PR fill:#9f9,stroke:#333
    style MB fill:#99f,stroke:#333
    style EB fill:#99f,stroke:#333
    style CB fill:#99f,stroke:#333
    style QB fill:#99f,stroke:#333
```

---

## 📬 **2. Message Flow: Old vs New**

### **Old Communication (DEPRECATED)**

```mermaid
graph LR
    subgraph RuntimeA["Runtime A"]
        A1[Method Call]
    end

    subgraph RuntimeB["Runtime B"]
        B1[Method Implementation]
    end

    A1 -->|direct call| B1

    style A1 fill:#f99,stroke:#333
    style B1 fill:#f99,stroke:#333
```

### **New Communication (REQUIRED)**

```mermaid
graph LR
    subgraph RuntimeA["Runtime A"]
        A1[BaseRuntime]
        A2[send_command]
        A3[send_query]
        A4[publish_event]
    end

    subgraph Framework["Runtime Communication Framework"]
        CB[CommandBus]
        QB[QueryBus]
        EB[EventBus]
    end

    subgraph RuntimeB["Runtime B"]
        B1[BaseRuntime]
        B2[handle_command]
        B3[handle_query]
        B4[handle_event]
    end

    A2 -->|sends| CB
    A3 -->|sends| QB
    A4 -->|publishes| EB

    CB -->|delivers| B2
    QB -->|delivers| B3
    EB -->|delivers| B4

    style A1 fill:#9f9,stroke:#333
    style A2 fill:#9f9,stroke:#333
    style A3 fill:#9f9,stroke:#333
    style A4 fill:#9f9,stroke:#333
    style CB fill:#99f,stroke:#333
    style QB fill:#99f,stroke:#333
    style EB fill:#99f,stroke:#333
    style B1 fill:#9f9,stroke:#333
    style B2 fill:#9f9,stroke:#333
    style B3 fill:#9f9,stroke:#333
    style B4 fill:#9f9,stroke:#333
```

---

## 🔄 **3. Runtime Lifecycle**

```mermaid
graph TD
    subgraph Lifecycle["Runtime Lifecycle"]
        UN[UNINITIALIZED]
        INI[INITIALIZING]
        INIT[INITIALIZED]
        STA[STARTING]
        RUN[RUNNING]
        PAU[PAUSED]
        STO[STOPPING]
        STOP[STOPPED]
        FAI[FAILED]
        RES[RESTARTING]
    end

    UN -->|initialize()| INI
    INI -->|_initialize()| INIT
    INIT -->|start()| STA
    STA -->|_start()| RUN
    RUN -->|pause()| PAU
    PAU -->|resume()| RUN
    RUN -->|stop()| STO
    STO -->|start()| STA
    RUN -->|restart()| RES
    RES -->|stop()| STO
    RES -->|start()| STA

    INI -->|error| FAI
    STA -->|error| FAI
    RUN -->|error| FAI
    PAU -->|error| FAI
    STO -->|error| FAI

    style UN fill:#fff,stroke:#333
    style INI fill:#ff9,stroke:#333
    style INIT fill:#9f9,stroke:#333
    style STA fill:#ff9,stroke:#333
    style RUN fill:#9f9,stroke:#333
    style PAU fill:#ff9,stroke:#333
    style STO fill:#ff9,stroke:#333
    style STOP fill:#fff,stroke:#333
    style FAI fill:#f99,stroke:#333
    style RES fill:#ff9,stroke:#333
```

---

## 🎯 **4. Command Flow**

```mermaid
sequenceDiagram
    participant RuntimeA
    participant CommandBus
    participant RuntimeRegistry
    participant RuntimeB

    RuntimeA->>CommandBus: send_command(
        target="RuntimeB",
        type="SaveData",
        payload={...}
    )
    
    CommandBus->>RuntimeRegistry: lookup("RuntimeB")
    RuntimeRegistry-->>CommandBus: RuntimeInfo
    
    CommandBus->>RuntimeB: deliver_command(
        sender="RuntimeA",
        type="SaveData",
        payload={...}
    )
    
    RuntimeB->>RuntimeB: handle_command(command)
    RuntimeB->>RuntimeB: Process command
    
    RuntimeB-->>CommandBus: Response
    CommandBus-->>RuntimeA: Return response
```

---

## 📡 **5. Event Flow**

```mermaid
sequenceDiagram
    participant RuntimeA
    participant EventBus
    participant RuntimeB
    participant RuntimeC

    RuntimeA->>EventBus: publish_event(
        type="memory.updated",
        payload={...}
    )
    
    EventBus->>RuntimeB: deliver_event(
        sender="RuntimeA",
        type="memory.updated",
        payload={...}
    )
    
    EventBus->>RuntimeC: deliver_event(
        sender="RuntimeA",
        type="memory.updated",
        payload={...}
    )
    
    RuntimeB->>RuntimeB: handle_event(event)
    RuntimeC->>RuntimeC: handle_event(event)
```

---

## 🔍 **6. Query Flow**

```mermaid
sequenceDiagram
    participant RuntimeA
    participant QueryBus
    participant RuntimeRegistry
    participant RuntimeB

    RuntimeA->>QueryBus: ask(
        target="RuntimeB",
        type="GetMemory",
        payload={...}
    )
    
    QueryBus->>RuntimeRegistry: lookup("RuntimeB")
    RuntimeRegistry-->>QueryBus: RuntimeInfo
    
    QueryBus->>RuntimeB: deliver_query(
        sender="RuntimeA",
        type="GetMemory",
        payload={...}
    )
    
    RuntimeB->>RuntimeB: handle_query(query)
    RuntimeB->>RuntimeB: Process query
    
    RuntimeB-->>QueryBus: Response
    QueryBus-->>RuntimeA: Return response
```

---

## 🌐 **7. System Startup Sequence**

```mermaid
gantt
    title System Startup Sequence
    dateFormat  X
    section Kernel
    Initialize Framework   :a1, 0, 1
    Create Buses           :a2, after a1, 1
    Create Services        :a3, after a2, 1
    Create Integration Reg :a4, after a3, 1
    
    section Runtimes
    Register Runtime 1     :b1, after a4, 1
    Initialize Runtime 1   :b2, after b1, 1
    Start Runtime 1        :b3, after b2, 1
    
    Register Runtime 2     :b4, after b1, 1
    Initialize Runtime 2   :b5, after b4, 1
    Start Runtime 2        :b6, after b5, 1
    
    Register Runtime N     :b7, after b1, 1
    Initialize Runtime N   :b8, after b7, 1
    Start Runtime N        :b9, after b8, 1
    
    section System
    Publish kernel.started  :c1, after a4, 1
    Publish kernel.ready    :c2, after b9, 1
```

---

## 🛑 **8. Error Recovery Flow**

```mermaid
graph TD
    subgraph Detection["Error Detection"]
        H1[Heartbeat Timeout]
        H2[Health Check Failure]
        H3[Exception in Runtime]
    end

    subgraph Supervisor["Supervisor"]
        S1[Detect Error]
        S2[Publish runtime.failed]
    end

    subgraph Recovery["Recovery Manager"]
        R1[Check Recovery Policy]
        R2[Check Max Restarts]
        R3[Check Criticality]
        R4[Decide Action]
    end

    subgraph Actions["Actions"]
        A1[Restart Runtime]
        A2[Keep Offline]
        A3[Escalate]
    end

    H1 --> S1
    H2 --> S1
    H3 --> S1

    S1 --> S2
    S2 --> R1

    R1 --> R2
    R2 --> R3
    R3 --> R4

    R4 -->|Restart| A1
    R4 -->|Keep Offline| A2
    R4 -->|Escalate| A3

    A1 -->|Success| S1
    A1 -->|Failure| A2

    style H1 fill:#f99,stroke:#333
    style H2 fill:#f99,stroke:#333
    style H3 fill:#f99,stroke:#333
    style S1 fill:#99f,stroke:#333
    style S2 fill:#99f,stroke:#333
    style R1 fill:#9f9,stroke:#333
    style R2 fill:#9f9,stroke:#333
    style R3 fill:#9f9,stroke:#333
    style R4 fill:#9f9,stroke:#333
    style A1 fill:#99f,stroke:#333
    style A2 fill:#f99,stroke:#333
    style A3 fill:#f99,stroke:#333
```

---

## 📊 **9. Communication Matrix**

```mermaid
quadrantChart
    title Communication Patterns
    x-axis Direct --> Indirect
    y-axis Synchronous --> Asynchronous
    
    quadrant-1 "Synchronous Direct"
        MessageBus: [0.8, 0.2]
        RequestResponseBus: [0.9, 0.3]
    
    quadrant-2 "Asynchronous Direct"
        CommandBus: [0.7, 0.8]
        QueryBus: [0.6, 0.7]
    
    quadrant-3 "Asynchronous Indirect"
        EventBus: [0.2, 0.9]
        BroadcastBus: [0.3, 0.8]
    
    quadrant-4 "Synchronous Indirect"
        : [0.1, 0.1]
```

---

## 🔗 **10. Runtime Dependencies**

```mermaid
graph TD
    subgraph Core["Core Runtimes"]
        KR[KernelRuntime]
        CR[CoreRuntime]
        MI[MessageInfrastructure]
    end

    subgraph Engines["Engine Runtimes"]
        MR[MemoryEngine]
        KR2[KnowledgeEngine]
        WR[WorkflowEngine]
        RI[RepositoryIntelligence]
        SE[SecurityEngine]
        CE[ContextEngine]
        CO[Coordination]
        WE[WorkspaceEngine]
        AP[AutomationPlatform]
    end

    subgraph Providers["Provider Runtimes"]
        PR[ProviderRuntime]
        MoR[ModelRuntime]
    end

    subgraph Agents["Agent Runtimes"]
        AR[Agent]
        AF[AgentFramework]
        AI[AgentIntelligence]
    end

    subgraph Specialized["Specialized Runtimes"]
        RR[ReasoningRuntime]
        PR2[PlanningRuntime]
        DR[DecisionRuntime]
        TR[TerminalRuntime]
    end

    KR --> CR
    KR --> MI
    KR --> MR
    KR --> KR2
    KR --> WR
    KR --> RI
    KR --> SE
    KR --> CE
    KR --> CO
    KR --> WE
    KR --> AP
    KR --> PR
    KR --> MoR
    KR --> AR
    KR --> AF
    KR --> AI
    KR --> RR
    KR --> PR2
    KR --> DR
    KR --> TR

    CR --> MI
    MI --> MR
    MI --> KR2

    MR --> KR2
    WR --> CO
    AP --> TR

    style KR fill:#f9f,stroke:#333
    style CR fill:#bbf,stroke:#333
    style MI fill:#bbf,stroke:#333
```

---

## 📈 **11. Performance Metrics Flow**

```mermaid
flowchart TD
    subgraph Collection["Metrics Collection"]
        M1[Message Sent]
        M2[Message Received]
        M3[Message Processed]
        M4[Error Occurred]
        M5[Retry Attempt]
    end

    subgraph Processing["Metrics Processing"]
        P1[Track Latency]
        P2[Track Processing Time]
        P3[Track Throughput]
        P4[Track Errors]
        P5[Track Retries]
    end

    subgraph Storage["Metrics Storage"]
        S1[In-Memory Metrics]
        S2[Time-Series Database]
        S3[Logging System]
    end

    subgraph Visualization["Visualization"]
        V1[Dashboard]
        V2[Alerts]
        V3[Reports]
    end

    M1 --> P1
    M1 --> P3
    M2 --> P1
    M2 --> P3
    M3 --> P2
    M3 --> P3
    M4 --> P4
    M5 --> P5

    P1 --> S1
    P2 --> S1
    P3 --> S1
    P4 --> S1
    P5 --> S1

    S1 --> S2
    S1 --> S3

    S1 --> V1
    S1 --> V2
    S2 --> V1
    S3 --> V3

    style M1 fill:#99f,stroke:#333
    style M2 fill:#99f,stroke:#333
    style M3 fill:#99f,stroke:#333
    style M4 fill:#f99,stroke:#333
    style M5 fill:#ff9,stroke:#333
    style P1 fill:#9f9,stroke:#333
    style P2 fill:#9f9,stroke:#333
    style P3 fill:#9f9,stroke:#333
    style P4 fill:#f99,stroke:#333
    style P5 fill:#ff9,stroke:#333
```

---

## 🔐 **12. Security Flow**

```mermaid
sequenceDiagram
    participant Client
    participant SecurityEngine
    participant Runtime

    Client->>SecurityEngine: Authenticate(user, credentials)
    SecurityEngine->>SecurityEngine: Validate credentials
    SecurityEngine-->>Client: AuthenticationResult
    
    Client->>SecurityEngine: Authorize(user, action, resource)
    SecurityEngine->>SecurityEngine: Check permissions
    SecurityEngine-->>Client: AuthorizationResult
    
    Client->>Runtime: Send command
    Runtime->>SecurityEngine: Check access(user, action, resource)
    SecurityEngine-->>Runtime: AccessResult
    
    alt Allowed
        Runtime->>Runtime: Process command
        Runtime-->>Client: Response
    else Denied
        Runtime-->>Client: AccessDeniedError
    end
```

---

## 📝 **13. Backward Compatibility Flow**

```mermaid
graph TD
    subgraph OldRuntime["Old Runtime"]
        OR[Old Method Call]
    end

    subgraph Adapter["LegacyRuntimeAdapter"]
        LA[LegacyRuntimeAdapter]
        CA[CommandAdapter]
        QA[QueryAdapter]
        EA[EventAdapter]
    end

    subgraph Framework["Runtime Communication Framework"]
        CB[CommandBus]
        QB[QueryBus]
        EB[EventBus]
    end

    subgraph NewRuntime["New Runtime"]
        NR[BaseRuntime]
    end

    OR -->|intercepted by| LA
    LA -->|convert to command| CA
    CA -->|send to| CB
    CB -->|deliver to| NR

    OR -->|intercepted by| LA
    LA -->|convert to query| QA
    QA -->|send to| QB
    QB -->|deliver to| NR

    OR -->|intercepted by| LA
    LA -->|convert to event| EA
    EA -->|publish to| EB
    EB -->|deliver to| NR

    style OR fill:#f99,stroke:#333
    style LA fill:#ff9,stroke:#333
    style CA fill:#ff9,stroke:#333
    style QA fill:#ff9,stroke:#333
    style EA fill:#ff9,stroke:#333
    style CB fill:#99f,stroke:#333
    style QB fill:#99f,stroke:#333
    style EB fill:#99f,stroke:#333
    style NR fill:#9f9,stroke:#333
```

---

## 🎉 **Summary**

These diagrams illustrate:

1. **Overall System Architecture** - How all components fit together
2. **Old vs New Communication** - The transition from direct calls to bus-based communication
3. **Runtime Lifecycle** - The states a runtime goes through
4. **Command Flow** - How commands are routed and processed
5. **Event Flow** - How events are published and delivered
6. **Query Flow** - How queries are asked and answered
7. **System Startup Sequence** - The order of operations during startup
8. **Error Recovery Flow** - How errors are detected and recovered from
9. **Communication Matrix** - Different communication patterns
10. **Runtime Dependencies** - How runtimes depend on each other
11. **Performance Metrics Flow** - How metrics are collected and processed
12. **Security Flow** - How authentication and authorization work
13. **Backward Compatibility Flow** - How old runtimes work with the new framework

All diagrams use Mermaid syntax and can be rendered in any Mermaid-compatible viewer.

---

*Generated on: July 9, 2026*
*Part of: TangkuAgentOS Runtime Communication Framework*
